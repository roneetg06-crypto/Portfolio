import pytest
from fastapi.testclient import TestClient
from app.main import app as mock_portal_app
from app.api.auth import clear_sessions_for_testing

client = TestClient(mock_portal_app)


@pytest.fixture(autouse=True)
def reset_mock_sessions():
    clear_sessions_for_testing()
    yield
    clear_sessions_for_testing()


def test_mock_portal_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "Mock Government Demo Portal" in res.json()["portal"]


def test_login_invalid_credentials():
    res = client.post("/api/auth/login", json={"username": "wrong_user", "password": "wrong_password"})
    assert res.status_code == 401
    assert "Invalid mock credentials" in res.json()["error"]


def test_sequential_barrier_enforcement():
    """Verify that skipping steps (e.g. calling OTP or submit before login) is rejected."""
    # Attempting OTP verify with dummy session id
    res = client.post("/api/auth/otp/verify", json={"session_id": "non_existent_session", "otp_code": "123456"})
    assert res.status_code == 404

    # Login properly
    login_res = client.post("/api/auth/login", json={"username": "citizen_demo", "password": "Password123!"})
    assert login_res.status_code == 200
    sid = login_res.json()["session_id"]
    assert login_res.json()["current_step"] == "CAPTCHA"

    # Try skipping CAPTCHA to verify OTP directly
    otp_res = client.post("/api/auth/otp/verify", json={"session_id": sid, "otp_code": "123456"})
    assert otp_res.status_code == 400
    assert "Cannot verify OTP" in otp_res.json()["error"]

    # Try skipping directly to submit
    submit_res = client.post("/api/application/submit", json={
        "session_id": sid,
        "scheme_id": "SCH-HLT-001",
        "applicant_name": "Test Citizen",
        "age": 30,
        "state": "Andhra Pradesh",
        "declaration_agreed": True,
    })
    assert submit_res.status_code == 400
    assert "Cannot submit application" in submit_res.json()["error"]


def test_full_mock_portal_workflow():
    """Walkthrough: Login -> CAPTCHA -> OTP -> Application Submit -> Acknowledgment."""
    # Step 1: Login
    login_res = client.post("/api/auth/login", json={"username": "citizen_demo", "password": "Password123!"})
    assert login_res.status_code == 200
    sid = login_res.json()["session_id"]

    # Step 2: CAPTCHA
    captcha_get = client.get(f"/api/auth/captcha?session_id={sid}")
    assert captcha_get.status_code == 200
    captcha_text = captcha_get.json()["captcha_text"]

    # Verify with incorrect CAPTCHA
    bad_captcha = client.post("/api/auth/captcha/verify", json={"session_id": sid, "captcha_response": "WRONG"})
    assert bad_captcha.status_code == 400

    # Fetch newly generated CAPTCHA
    new_captcha_get = client.get(f"/api/auth/captcha?session_id={sid}")
    correct_text = new_captcha_get.json()["captcha_text"]

    # Verify with correct CAPTCHA
    good_captcha = client.post("/api/auth/captcha/verify", json={"session_id": sid, "captcha_response": correct_text})
    assert good_captcha.status_code == 200
    assert good_captcha.json()["current_step"] == "OTP"

    # Step 3: OTP
    otp_hint_res = client.get(f"/api/auth/otp/hint?session_id={sid}")
    assert otp_hint_res.status_code == 200
    simulated_otp = otp_hint_res.json()["otp_hint"]
    assert len(simulated_otp) == 6

    # Verify with wrong OTP
    bad_otp = client.post("/api/auth/otp/verify", json={"session_id": sid, "otp_code": "000000"})
    assert bad_otp.status_code == 400

    # Verify with correct OTP
    good_otp = client.post("/api/auth/otp/verify", json={"session_id": sid, "otp_code": simulated_otp})
    assert good_otp.status_code == 200
    assert good_otp.json()["current_step"] == "APPLICATION_FORM"

    # Step 4: Submit Application Form
    incomplete_submit = client.post("/api/application/submit", json={
        "session_id": sid,
        "scheme_id": "SCH-HLT-001",
        "applicant_name": "Priya Sharma",
        "age": 34,
        "state": "Andhra Pradesh",
        "declaration_agreed": False,
    })
    assert incomplete_submit.status_code == 422

    # Proper submission
    final_submit = client.post("/api/application/submit", json={
        "session_id": sid,
        "scheme_id": "SCH-HLT-001",
        "applicant_name": "Priya Sharma",
        "age": 34,
        "gender": "Female",
        "state": "Andhra Pradesh",
        "district": "Visakhapatnam",
        "annual_income": 180000,
        "aadhaar_last_four": "5821",
        "declaration_agreed": True,
    })
    assert final_submit.status_code == 201
    ack_data = final_submit.json()
    assert ack_data["status"] == "SUBMITTED"
    assert ack_data["acknowledgment_number"].startswith("ACK-GOV-2026-")

    # Step 5: Check session status after submit
    status_res = client.get(f"/api/application/session?session_id={sid}")
    assert status_res.status_code == 200
    assert status_res.json()["current_step"] == "CONFIRMED"


def test_education_loan_mock_portal_workflow():
    """Verify Education Loan scheme submission produces ACK-EDU prefix and preserves student/loan info."""
    # 1. Login
    login_res = client.post("/api/auth/login", json={"username": "citizen_demo", "password": "Password123!"})
    sid = login_res.json()["session_id"]

    # 2. CAPTCHA
    c_res = client.get(f"/api/auth/captcha?session_id={sid}")
    client.post("/api/auth/captcha/verify", json={"session_id": sid, "captcha_response": c_res.json()["captcha_text"]})

    # 3. OTP
    otp_hint = client.get(f"/api/auth/otp/hint?session_id={sid}").json()["otp_hint"]
    client.post("/api/auth/otp/verify", json={"session_id": sid, "otp_code": otp_hint})

    # 4. Education Loan Submit
    loan_submit = client.post("/api/application/submit", json={
        "session_id": sid,
        "scheme_id": "SCH-EDU-001",
        "student_name": "Priya Sharma",
        "date_of_birth": "2003-05-15",
        "gender": "Female",
        "state": "Andhra Pradesh",
        "district": "Visakhapatnam",
        "category": "OBC",
        "parent_name": "Ramesh Sharma",
        "parent_occupation": "Salaried / Private",
        "annual_family_income": 350000,
        "aadhaar_last_four": "5821",
        "course": "B.Tech Computer Science and Engineering",
        "college": "National Institute of Technology",
        "loan_amount": 750000,
        "tuition_fee": 500000,
        "living_expenses": 250000,
        "bank_preference": "State Bank of India",
        "loan_tenure": "10 Years",
        "declaration_agreed": True,
    })
    assert loan_submit.status_code == 201
    ack = loan_submit.json()
    assert ack["status"] == "SUBMITTED"
    assert ack["acknowledgment_number"].startswith("ACK-EDU-2026-")
    assert ack["student_name"] == "Priya Sharma"


def test_prefill_dossier_structure():
    """Verify that get_application_prefill returns all 17 education loan fields and documents."""
    res = client.get("/api/application/prefill?scheme_id=SCH-EDU-001")
    assert res.status_code == 200
    data = res.json()
    required_keys = [
        "student_name",
        "date_of_birth",
        "gender",
        "state",
        "district",
        "category",
        "parent_name",
        "parent_occupation",
        "annual_family_income",
        "aadhaar_last_four",
        "course",
        "college",
        "loan_amount",
        "tuition_fee",
        "living_expenses",
        "bank_preference",
        "loan_tenure",
        "documents",
    ]
    for key in required_keys:
        assert key in data, f"Missing key '{key}' in prefill response"

    assert isinstance(data["documents"], dict)
    assert "admission_letter" in data["documents"]
    assert "fee_structure" in data["documents"]
    assert "student_aadhaar" in data["documents"]
    assert "parent_income_certificate" in data["documents"]


def test_milestone_synchronization():
    """Verify that milestone events update session step and progress properly."""
    # 1. Login
    login_res = client.post("/api/auth/login", json={"username": "citizen_demo", "password": "Password123!"})
    sid = login_res.json()["session_id"]

    # 2. CAPTCHA
    c_res = client.get(f"/api/auth/captcha?session_id={sid}")
    client.post("/api/auth/captcha/verify", json={"session_id": sid, "captcha_response": c_res.json()["captcha_text"]})

    # 3. OTP
    otp_hint = client.get(f"/api/auth/otp/hint?session_id={sid}").json()["otp_hint"]
    client.post("/api/auth/otp/verify", json={"session_id": sid, "otp_code": otp_hint})

    # 4. Milestone: STUDENT_INFO_COMPLETED
    m1 = client.post("/api/application/milestone", json={
        "session_id": sid,
        "milestone": "STUDENT_INFO_COMPLETED",
        "data": {"student_name": "Priya Sharma", "state": "Andhra Pradesh"}
    })
    assert m1.status_code == 200
    assert m1.json()["current_step"] == "LOAN_INFO"

    # 5. Milestone: LOAN_INFO_COMPLETED
    m2 = client.post("/api/application/milestone", json={
        "session_id": sid,
        "milestone": "LOAN_INFO_COMPLETED",
        "data": {"course": "B.Tech Computer Science and Engineering", "loan_amount": 750000}
    })
    assert m2.status_code == 200
    assert m2.json()["current_step"] == "DOC_UPLOAD"

    # 6. Milestone: DOCUMENTS_UPLOADED
    m3 = client.post("/api/application/milestone", json={
        "session_id": sid,
        "milestone": "DOCUMENTS_UPLOADED",
        "data": {"admission_letter": "NIT_Admission.pdf"}
    })
    assert m3.status_code == 200
    assert m3.json()["current_step"] == "FINAL_REVIEW"

    # 7. Milestone: FINAL_REVIEW_REQUIRED
    m4 = client.post("/api/application/milestone", json={
        "session_id": sid,
        "milestone": "FINAL_REVIEW_REQUIRED",
    })
    assert m4.status_code == 200
    assert m4.json()["current_step"] == "FINAL_REVIEW"

    # 8. Milestone: APPLICATION_SUBMITTED
    m5 = client.post("/api/application/milestone", json={
        "session_id": sid,
        "milestone": "APPLICATION_SUBMITTED",
    })
    assert m5.status_code == 200
    assert m5.json()["current_step"] == "CONFIRMED"


