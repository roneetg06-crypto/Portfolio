"""
Tests for SCH-EDU-001 (National Student Education Loan Scheme — DEMO):
- Verifies scheme loading and metadata integrity.
- Verifies dynamic form required information schema.
- Verifies submission and storage in _submitted_info_store.
- Verifies Document Agent recognizes the 4 required education loan documents.
"""
import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.agents.document_agent.graph import run_document_agent
from app.agents.automation_agent.graph import build_mapped_form_data, plan_application_node
from app.services import document_service
from app.services.document_service import (
    clear_document_store_for_testing,
    get_submitted_information,
)
from app.services.automation_service import clear_automation_runs_for_testing
from app.services.profile_service import create_profile, clear_profiles_for_testing
from app.schemas.citizen_profile_schema import CitizenProfileCreate

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_stores():
    clear_document_store_for_testing()
    clear_automation_runs_for_testing()
    clear_profiles_for_testing()
    yield
    clear_document_store_for_testing()
    clear_automation_runs_for_testing()
    clear_profiles_for_testing()


def test_scenario_1_education_scheme_loads_correctly():
    """Verify SCH-EDU-001 exists and loads correctly via API and service."""
    scheme = document_service.get_scheme_by_id("SCH-EDU-001")
    assert scheme is not None
    assert scheme.scheme_id == "SCH-EDU-001"
    assert scheme.name == "National Student Education Loan"
    assert scheme.sector == "education"
    assert scheme.level == "central"

    # Verify API endpoint returns requirements
    res = client.get("/api/schemes/SCH-EDU-001/information-requirements")
    assert res.status_code == 200
    data = res.json()
    assert data["scheme_id"] == "SCH-EDU-001"
    assert "required_info" in data
    assert len(data["required_info"]) == 13


def test_scenario_2_dynamic_form_fields_verification():
    """Verify all Step 4 and Step 5 dynamic form fields are correctly defined in required_info."""
    res = client.get("/api/schemes/SCH-EDU-001/information-requirements")
    assert res.status_code == 200
    fields = {f["name"]: f for f in res.json()["required_info"]}

    # Step 4: Student & Parent Details (not already in Profile)
    assert "date_of_birth" in fields
    assert fields["date_of_birth"]["type"] == "date"
    assert fields["date_of_birth"]["required"] is True

    assert "category" in fields
    assert fields["category"]["type"] == "dropdown"
    assert "General" in fields["category"]["options"]
    assert "OBC" in fields["category"]["options"]

    assert "parent_name" in fields
    assert fields["parent_name"]["type"] == "text"

    assert "parent_occupation" in fields
    assert fields["parent_occupation"]["type"] == "dropdown"

    assert "annual_family_income" in fields
    assert fields["annual_family_income"]["type"] == "number"

    assert "aadhaar_last_four" in fields
    assert fields["aadhaar_last_four"]["type"] == "text"

    # Step 5: Loan Information
    assert "course" in fields
    assert fields["course"]["type"] == "text"

    assert "college" in fields
    assert fields["college"]["type"] == "text"

    assert "loan_amount" in fields
    assert fields["loan_amount"]["type"] == "number"

    assert "tuition_fee" in fields
    assert fields["tuition_fee"]["type"] == "number"

    assert "living_expenses" in fields
    assert fields["living_expenses"]["type"] == "number"

    assert "bank_preference" in fields
    assert fields["bank_preference"]["type"] == "dropdown"
    assert "State Bank of India" in fields["bank_preference"]["options"]

    assert "loan_tenure" in fields
    assert fields["loan_tenure"]["type"] == "dropdown"
    assert "10 Years" in fields["loan_tenure"]["options"]


def test_scenario_3_submitted_information_storage():
    """Verify submitted loan application information is stored in the existing submitted-information store."""
    payload = {
        "profile_id": "prof-student-001",
        "data": {
            "date_of_birth": "2003-05-15",
            "category": "OBC",
            "parent_name": "Ramesh Kumar",
            "parent_occupation": "Salaried / Private",
            "annual_family_income": 350000,
            "aadhaar_last_four": "9876",
            "course": "B.Tech Computer Science and Engineering",
            "college": "National Institute of Technology",
            "loan_amount": 750000,
            "tuition_fee": 500000,
            "living_expenses": 250000,
            "bank_preference": "State Bank of India",
            "loan_tenure": "10 Years",
        },
    }

    res = client.post("/api/schemes/SCH-EDU-001/information", json=payload)
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["status"] == "saved"
    assert res_json["missing_information"] == []

    # Verify directly from backend store
    stored = get_submitted_information("SCH-EDU-001", "prof-student-001")
    assert stored is not None
    assert stored["course"] == "B.Tech Computer Science and Engineering"
    assert stored["college"] == "National Institute of Technology"
    assert stored["loan_amount"] == 750000
    assert stored["parent_name"] == "Ramesh Kumar"
    assert stored["aadhaar_last_four"] == "9876"


def test_scenario_4_document_agent_recognizes_four_required_documents():
    """Verify Document Agent correctly identifies all 4 required education loan documents."""
    # Direct agent call
    agent_output = run_document_agent(scheme_id="SCH-EDU-001")
    assert "required_documents" in agent_output
    docs = {d["name"]: d for d in agent_output["required_documents"]}

    assert len(docs) == 4
    # 1. Admission Letter — required
    assert "admission_letter" in docs
    assert docs["admission_letter"]["required"] is True

    # 2. Fee Structure — required
    assert "fee_structure" in docs
    assert docs["fee_structure"]["required"] is True

    # 3. Student Aadhaar — required
    assert "student_aadhaar" in docs
    assert docs["student_aadhaar"]["required"] is True

    # 4. Parent Income Certificate — required
    assert "parent_income_certificate" in docs
    assert docs["parent_income_certificate"]["required"] is True

    # API endpoint check
    api_res = client.get("/api/schemes/SCH-EDU-001/documents/required")
    assert api_res.status_code == 200
    api_docs = {d["name"]: d for d in api_res.json()["required_documents"]}
    assert len(api_docs) == 4
    assert "admission_letter" in api_docs
    assert "fee_structure" in api_docs
    assert "student_aadhaar" in api_docs
    assert "parent_income_certificate" in api_docs


def test_scenario_5_document_upload_and_status_tracking():
    """Verify documents can be uploaded and tracked for SCH-EDU-001 using existing storage."""
    dummy_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"

    upload_res = client.post(
        "/api/documents/upload",
        data={
            "document_name": "admission_letter",
            "scheme_id": "SCH-EDU-001",
            "profile_id": "prof-student-001",
        },
        files={"file": ("admission_offer.pdf", io.BytesIO(dummy_pdf), "application/pdf")},
    )
    assert upload_res.status_code == 201

    # Check document statuses
    status_res = client.get("/api/documents/status?scheme_id=SCH-EDU-001&profile_id=prof-student-001")
    assert status_res.status_code == 200
    doc_statuses = {d["name"]: d for d in status_res.json()["documents"]}

    assert doc_statuses["admission_letter"]["status"] in ("VERIFIED", "MANUAL_VERIFICATION_REQUIRED")
    assert doc_statuses["fee_structure"]["status"] == "MISSING"
    assert doc_statuses["student_aadhaar"]["status"] == "MISSING"
    assert doc_statuses["parent_income_certificate"]["status"] == "MISSING"


def test_scenario_6_target_8_step_workflow_plan():
    """Verify plan_application_node() for SCH-EDU-001 generates the exact 8-step target workflow."""
    state = {
        "scheme_id": "SCH-EDU-001",
        "user_profile": {"name": "Aarav Gupta", "state": "Delhi", "district": "New Delhi"},
        "submitted_information": {
            "student_name": "Aarav Gupta",
            "course": "B.Tech Electrical",
            "college": "IIT Delhi",
            "loan_amount": 900000.0,
        },
        "uploaded_documents": [],
    }

    result = plan_application_node(state)
    steps = result["planned_steps"]
    assert len(steps) == 8

    # Step 1: LOGIN — HUMAN
    assert steps[0]["step_id"] == "portal_login"
    assert steps[0]["type"] == "human_action"
    assert steps[0]["action_type"] == "LOGIN"

    # Step 2: CAPTCHA — HUMAN
    assert steps[1]["step_id"] == "captcha_challenge"
    assert steps[1]["type"] == "human_action"
    assert steps[1]["action_type"] == "CAPTCHA"

    # Step 3: OTP — HUMAN
    assert steps[2]["step_id"] == "mobile_otp"
    assert steps[2]["type"] == "human_action"
    assert steps[2]["action_type"] == "OTP"

    # Step 4: STUDENT_INFORMATION — AUTO
    assert steps[3]["step_id"] == "student_information"
    assert steps[3]["type"] == "auto"
    assert steps[3]["action_type"] == "STUDENT_INFORMATION"

    # Step 5: LOAN_INFORMATION — AUTO
    assert steps[4]["step_id"] == "loan_information"
    assert steps[4]["type"] == "auto"
    assert steps[4]["action_type"] == "LOAN_INFORMATION"

    # Step 6: DOCUMENT_UPLOAD — AUTO
    assert steps[5]["step_id"] == "document_upload"
    assert steps[5]["type"] == "auto"
    assert steps[5]["action_type"] == "DOCUMENT_UPLOAD"

    # Step 7: FINAL_REVIEW — HUMAN
    assert steps[6]["step_id"] == "final_review"
    assert steps[6]["type"] == "human_action"
    assert steps[6]["action_type"] == "FINAL_REVIEW"

    # Step 8: COMPLETION — SYSTEM
    assert steps[7]["step_id"] == "completion"
    assert steps[7]["type"] == "auto"
    assert steps[7]["action_type"] == "COMPLETION"


def test_scenario_7_mapped_dossier_structure_and_source_layers():
    """
    Verify mapped_form_data is structured strictly from layers without fake defaults:
    - Profile -> name, gender, state, district, aadhaar_last_four
    - Dynamic Form -> submitted_information
    - Document Agent -> uploaded_documents with storage paths
    - No unrelated health-specific hardcoded fields remain.
    """
    user_profile = {
        "name": "Sneha Reddy",
        "gender": "Female",
        "state": "Telangana",
        "district": "Hyderabad",
        "annual_income": 450000.0,
        "aadhaar_number": "123456789012",
    }

    submitted_info = {
        "date_of_birth": "2004-08-20",
        "category": "General",
        "parent_name": "Venkat Reddy",
        "parent_occupation": "Business / Self-Employed",
        "annual_family_income": 450000.0,
        "course": "M.S. Data Science",
        "college": "IIIT Hyderabad",
        "loan_amount": 1200000.0,
        "tuition_fee": 900000.0,
        "living_expenses": 300000.0,
        "bank_preference": "Canara Bank",
        "loan_tenure": "7 Years",
    }

    uploaded_docs = [
        {
            "name": "admission_letter",
            "label": "Admission Letter",
            "required": True,
            "status": "VERIFIED",
            "original_filename": "IIIT_Admission_Letter.pdf",
            "storage_path": "/mock/uploads/IIIT_Admission_Letter.pdf",
            "document_id": "doc-uuid-001",
            "size_bytes": 102400,
        },
        {
            "name": "fee_structure",
            "label": "Fee Structure",
            "required": True,
            "status": "VERIFIED",
            "original_filename": "IIIT_Fee_Structure.pdf",
            "storage_path": "/mock/uploads/IIIT_Fee_Structure.pdf",
            "document_id": "doc-uuid-002",
            "size_bytes": 81920,
        },
    ]

    dossier = build_mapped_form_data(
        scheme_id="SCH-EDU-001",
        user_profile=user_profile,
        submitted_info=submitted_info,
        uploaded_documents=uploaded_docs,
    )

    # 1. Verify exact top-level fields
    expected_fields = [
        "scheme_id",
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
    for field in expected_fields:
        assert field in dossier, f"Field '{field}' missing from education loan dossier"

    # 2. Verify values sourced from Profile
    assert dossier["student_name"] == "Sneha Reddy"
    assert dossier["gender"] == "Female"
    assert dossier["state"] == "Telangana"
    assert dossier["district"] == "Hyderabad"
    assert dossier["aadhaar_last_four"] == "9012"

    # 3. Verify values sourced from Dynamic Form
    assert dossier["date_of_birth"] == "2004-08-20"
    assert dossier["category"] == "General"
    assert dossier["parent_name"] == "Venkat Reddy"
    assert dossier["parent_occupation"] == "Business / Self-Employed"
    assert dossier["annual_family_income"] == 450000.0
    assert dossier["course"] == "M.S. Data Science"
    assert dossier["college"] == "IIIT Hyderabad"
    assert dossier["loan_amount"] == 1200000.0
    assert dossier["tuition_fee"] == 900000.0
    assert dossier["living_expenses"] == 300000.0
    assert dossier["bank_preference"] == "Canara Bank"
    assert dossier["loan_tenure"] == "7 Years"

    # 4. Verify documents list contains storage paths and file references
    assert isinstance(dossier["documents"], list)
    assert len(dossier["documents"]) == 2
    doc1 = dossier["documents"][0]
    assert doc1["name"] == "admission_letter"
    assert doc1["original_filename"] == "IIIT_Admission_Letter.pdf"
    assert doc1["storage_path"] == "/mock/uploads/IIIT_Admission_Letter.pdf"
    assert doc1["document_id"] == "doc-uuid-001"

    # 5. Verify NO unrelated health-specific hardcoded fields remain
    assert "applicant_name" not in dossier
    assert "declaration_agreed" not in dossier
    assert "annual_income" not in dossier


def test_scenario_8_no_fake_defaults_when_data_missing():
    """Verify missing dynamic information fields evaluate to None rather than fake defaults."""
    dossier = build_mapped_form_data(
        scheme_id="SCH-EDU-001",
        user_profile={},
        submitted_info={},
        uploaded_documents=[],
    )

    assert dossier["scheme_id"] == "SCH-EDU-001"
    assert dossier["student_name"] is None
    assert dossier["parent_name"] is None
    assert dossier["course"] is None
    assert dossier["college"] is None
    assert dossier["loan_amount"] is None
    assert dossier["annual_family_income"] is None
    assert dossier["aadhaar_last_four"] is None
    assert dossier["documents"] == []


def test_scenario_9_workflow_execution_progression_and_pauses():
    """
    Verify complete progression:
    - Starts -> Awaiting LOGIN
    - Resumes LOGIN -> Awaiting CAPTCHA
    - Resumes CAPTCHA -> Awaiting OTP
    - Resumes OTP -> Executes Steps 4, 5, 6 (auto) -> Pauses awaiting Step 7 (FINAL_REVIEW)
    - Resumes FINAL_REVIEW -> Completes Step 8 (COMPLETION) -> Generates ACK-EDU acknowledgment
    """
    prof = create_profile(
        CitizenProfileCreate(
            name="Rahul Verma",
            age=22,
            gender="Male",
            state="Maharashtra",
            district="Pune",
        )
    )
    profile_id = prof.profile_id

    # 1. Submit dynamic form
    info_res = client.post(
        "/api/schemes/SCH-EDU-001/information",
        json={
            "profile_id": profile_id,
            "data": {
                "date_of_birth": "2002-11-10",
                "category": "General",
                "parent_name": "Suresh Verma",
                "parent_occupation": "Salaried / Private",
                "annual_family_income": 500000,
                "aadhaar_last_four": "4321",
                "course": "MBA",
                "college": "Symbiosis Institute of Business Management",
                "loan_amount": 1000000,
                "tuition_fee": 800000,
                "living_expenses": 200000,
                "bank_preference": "Bank of Baroda",
                "loan_tenure": "5 Years",
            },
        },
    )
    assert info_res.status_code == 200

    # 2. Upload one document to check document inclusion
    dummy_file = b"%PDF-1.4 mock admission letter"
    client.post(
        "/api/documents/upload",
        data={
            "document_name": "admission_letter",
            "scheme_id": "SCH-EDU-001",
            "profile_id": profile_id,
        },
        files={"file": ("symbiosis_offer.pdf", io.BytesIO(dummy_file), "application/pdf")},
    )

    # 3. Start automation run
    start_res = client.post(
        "/api/automation/start",
        json={"scheme_id": "SCH-EDU-001", "profile_id": profile_id},
    )
    assert start_res.status_code == 201
    run_state = start_res.json()
    run_id = run_state["run_id"]

    # Verify initial state awaits LOGIN
    assert run_state["automation_status"] == "AWAITING_HUMAN_ACTION"
    assert run_state["human_action_required"]["action_type"] == "LOGIN"
    assert run_state["current_step_index"] == 0

    # Verify mapped dossier is present in start response
    dossier = run_state["mapped_form_data"]
    assert dossier["student_name"] == "Rahul Verma"
    assert dossier["course"] == "MBA"
    assert len(dossier["documents"]) == 4  # 4 required documents tracked
    adm_doc = next(d for d in dossier["documents"] if d["name"] == "admission_letter")
    assert adm_doc["original_filename"] == "symbiosis_offer.pdf"
    assert adm_doc["storage_path"] is not None

    # 4. Resume LOGIN -> should advance to CAPTCHA
    r_login = client.post(
        "/api/automation/resume",
        json={"run_id": run_id, "action_type": "LOGIN"},
    )
    assert r_login.status_code == 200
    assert r_login.json()["automation_status"] == "AWAITING_HUMAN_ACTION"
    assert r_login.json()["human_action_required"]["action_type"] == "CAPTCHA"
    assert r_login.json()["current_step_index"] == 1

    # 5. Resume CAPTCHA -> should advance to OTP
    r_captcha = client.post(
        "/api/automation/resume",
        json={"run_id": run_id, "action_type": "CAPTCHA"},
    )
    assert r_captcha.status_code == 200
    assert r_captcha.json()["automation_status"] == "AWAITING_HUMAN_ACTION"
    assert r_captcha.json()["human_action_required"]["action_type"] == "OTP"
    assert r_captcha.json()["current_step_index"] == 2

    # 6. Resume OTP -> Auto steps 3, 4, 5 execute automatically -> Pauses at Step 6 (FINAL_REVIEW)
    r_otp = client.post(
        "/api/automation/resume",
        json={"run_id": run_id, "action_type": "OTP"},
    )
    assert r_otp.status_code == 200
    after_otp = r_otp.json()
    assert after_otp["automation_status"] == "AWAITING_HUMAN_ACTION"
    assert after_otp["human_action_required"]["action_type"] == "FINAL_REVIEW"
    assert after_otp["current_step_index"] == 6

    # Verify steps 0-5 are now marked completed
    steps = after_otp["planned_steps"]
    assert steps[0]["status"] == "completed"  # LOGIN
    assert steps[1]["status"] == "completed"  # CAPTCHA
    assert steps[2]["status"] == "completed"  # OTP
    assert steps[3]["status"] == "completed"  # STUDENT_INFORMATION (auto)
    assert steps[4]["status"] == "completed"  # LOAN_INFORMATION (auto)
    assert steps[5]["status"] == "completed"  # DOCUMENT_UPLOAD (auto)
    assert steps[6]["status"] == "pending"    # FINAL_REVIEW (awaiting human)

    # 7. Resume FINAL_REVIEW -> Completes Step 7 & 8 -> COMPLETED with ACK-EDU prefix
    r_final = client.post(
        "/api/automation/resume",
        json={"run_id": run_id, "action_type": "FINAL_REVIEW"},
    )
    assert r_final.status_code == 200
    final_res = r_final.json()
    assert final_res["automation_status"] == "COMPLETED"
    assert final_res["application_status"] == "SUBMITTED"
    assert final_res["human_action_required"] is None
    assert final_res["acknowledgment_number"].startswith("ACK-EDU-2026-")

