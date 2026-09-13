import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.automation_service import clear_automation_runs_for_testing
from app.services.application_state_service import clear_states_for_testing
from app.services.browser_automation_service import BrowserAutomationService
from app.services.document_service import clear_document_store_for_testing
from app.services.notification_service import clear_notifications_for_testing

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    clear_automation_runs_for_testing()
    clear_states_for_testing()
    clear_document_store_for_testing()
    clear_notifications_for_testing()
    BrowserAutomationService.close_all_sessions()
    yield
    clear_automation_runs_for_testing()
    clear_states_for_testing()
    clear_document_store_for_testing()
    clear_notifications_for_testing()
    BrowserAutomationService.close_all_sessions()


def test_scenario_1_browser_barrier_detection_and_pause():
    """
    Scenario 1: Automation agent starts, launches browser in headless mode against mock portal,
    detects the LOGIN barrier, and pauses without attempting any credential bypass.
    """
    start_res = client.post(
        "/api/automation/start",
        json={"scheme_id": "SCH-HLT-001", "profile_id": "citizen-pw-01"},
    )
    assert start_res.status_code == 201
    run_id = start_res.json()["run_id"]
    assert start_res.json()["automation_status"] == "AWAITING_HUMAN_ACTION"
    assert start_res.json()["human_action_required"]["action_type"] == "LOGIN"

    # Launch browser session via the automation service
    session_res = BrowserAutomationService.start_session(
        run_id=run_id,
        scheme_id="SCH-HLT-001",
        profile_id="citizen-pw-01",
        headless=True,
    )
    assert session_res["status"] in ("ACTIVE", "ERROR")

    # If the Vite mock-portal server is running on 5174, page_state will be LOGIN.
    # If not running in unit test sandbox, it degrades cleanly to ERROR without hanging!
    if session_res["status"] == "ACTIVE":
        assert session_res["page_state"] in ("LOGIN", "UNKNOWN")
        # Ensure session info is recorded
        info = BrowserAutomationService.get_session_info(run_id)
        assert info is not None
        assert info["is_open"] is True

    # Verify notification fired for citizen-pw-01
    notifs = client.get("/api/notifications?profile_id=citizen-pw-01").json()["notifications"]
    assert len(notifs) >= 1
    assert notifs[0]["action_type"] == "LOGIN"
    assert notifs[0]["status"] == "ACTION_REQUIRED"


def test_scenario_2_form_filling_and_no_auto_submit():
    """
    Scenario 2: Verify that fill_application_form populates form fields using citizen data,
    and strictly does NOT click the final submission button.
    """
    # Create an HTML page containing the mock portal form for deterministic testing
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()

    mock_form_html = """
    <!DOCTYPE html>
    <html>
    <body>
        <form class="portal-form">
            <select id="scheme_id"><option value="SCH-HLT-001">Scheme 1</option></select>
            <input id="applicant_name" type="text" value="" />
            <input id="age" type="number" value="" />
            <select id="gender"><option value="Female">Female</option><option value="Male">Male</option></select>
            <input id="state" type="text" value="" />
            <input id="district" type="text" value="" />
            <input id="annual_income" type="number" value="" />
            <input id="aadhaar_last_four" type="text" value="" />
            <input id="declaration_agreed" type="checkbox" />
            <button id="submitApplicationBtn" type="submit">Confirm & Submit Application</button>
        </form>
    </body>
    </html>
    """
    page.set_content(mock_form_html)

    # Register in active browser sessions
    test_run_id = "test-run-form-fill"
    BrowserAutomationService.register_session(
        run_id=test_run_id,
        page=page,
        browser=browser,
        playwright=pw,
    )


    # Verify page state detected as APPLICATION_FORM
    detected = BrowserAutomationService.detect_page_state(test_run_id)
    assert detected == "APPLICATION_FORM"

    # Fill form with citizen dossier
    form_data = {
        "scheme_id": "SCH-HLT-001",
        "applicant_name": "Rohan Verma",
        "age": 42,
        "gender": "Male",
        "state": "Maharashtra",
        "district": "Pune",
        "annual_income": 250000,
        "aadhaar_last_four": "9988",
    }

    fill_res = BrowserAutomationService.fill_application_form(test_run_id, form_data)
    assert fill_res["status"] == "FORM_FILLED"
    assert "applicant_name" in fill_res["filled_fields"]
    assert "annual_income" in fill_res["filled_fields"]

    # Verify DOM values
    assert page.input_value("#applicant_name") == "Rohan Verma"
    assert page.input_value("#age") == "42"
    assert page.input_value("#state") == "Maharashtra"
    assert page.input_value("#district") == "Pune"
    assert page.input_value("#annual_income") == "250000"
    assert page.input_value("#aadhaar_last_four") == "9988"
    assert page.is_checked("#declaration_agreed") is True

    # CRITICAL GUARDRAIL VERIFICATION:
    # Verify the submit button was NOT clicked (page URL/state did not submit)
    assert BrowserAutomationService.detect_page_state(test_run_id) == "APPLICATION_FORM"
    assert fill_res["paused_at"] == "FINAL_SUBMISSION_REVIEW"

    # Clean up
    BrowserAutomationService.close_session(test_run_id)


def test_scenario_3_error_handling_and_degradation():
    """
    Scenario 3: Verify that invalid run_id, closed session, or missing targets
    produce clear error status and never hang or silently fail.
    """
    # 1. Invalid run ID
    res_empty = BrowserAutomationService.start_session(run_id="")
    assert res_empty["status"] == "ERROR"
    assert res_empty["page_state"] == "ERROR"

    # 2. Non-existent session
    res_nonexistent = BrowserAutomationService.detect_page_state("non-existent-id")
    assert res_nonexistent == "SESSION_CLOSED"

    # 3. Filling on non-existent session
    res_fill = BrowserAutomationService.fill_application_form("non-existent-id", {})
    assert res_fill["status"] == "ERROR"

    # 4. Closing non-existent session
    closed = BrowserAutomationService.close_session("non-existent-id")
    assert closed is False


def test_scenario_4_strict_guardrail_code_review():
    """
    Scenario 4: Static / code review verification that no code path exists in
    browser_automation_service that automates CAPTCHA solving, OTP filling,
    or final submission clicking.
    """
    import inspect
    from app.services import browser_automation_service

    source = inspect.getsource(browser_automation_service)

    # 1. Ensure no CAPTCHA solving logic
    assert "solve_captcha" not in source.lower()
    assert "captcha_solver" not in source.lower()
    assert "fill(#captchaanswer" not in source.lower().replace(" ", "").replace('"', "'")

    # 2. Ensure no OTP auto-fill logic
    assert "fill(#otpinput" not in source.lower().replace(" ", "").replace('"', "'")
    assert "auto_fill_otp" not in source.lower()

    # 3. Ensure no final submission click
    assert "click(#submitapplicationbtn" not in source.lower().replace(" ", "").replace('"', "'")
    assert "click('button[type=\"submit\"]')" not in source.lower()


def test_scenario_5_detect_all_education_loan_page_states():
    """
    Scenario 5: Verify detect_page_state correctly identifies all 8 mock portal states:
    LOGIN, CAPTCHA, OTP, STUDENT_PARENT_INFO, LOAN_INFO, DOC_UPLOAD, FINAL_REVIEW, CONFIRMATION.
    """
    from playwright.sync_api import sync_playwright
    from app.services.browser_automation_service import is_human_barrier

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()

    run_id = "test-run-states-detection"
    BrowserAutomationService.register_session(run_id=run_id, page=page, browser=browser, playwright=pw)

    # 1. LOGIN
    page.set_content("""
        <div><input id="username" /><input id="password" /><button>Sign In to Portal</button></div>
    """)
    assert BrowserAutomationService.detect_page_state(run_id) == "LOGIN"
    assert is_human_barrier("LOGIN") is True

    # 2. CAPTCHA
    page.set_content("""
        <div class="captcha-box"><input id="captchaAnswer" /><button>Verify CAPTCHA</button></div>
    """)
    assert BrowserAutomationService.detect_page_state(run_id) == "CAPTCHA"
    assert is_human_barrier("CAPTCHA") is True

    # 3. OTP
    page.set_content("""
        <div class="simulated-otp-box"><input id="otpInput" /><button>Verify OTP</button></div>
    """)
    assert BrowserAutomationService.detect_page_state(run_id) == "OTP"
    assert is_human_barrier("OTP") is True

    # 4. STUDENT_PARENT_INFO
    page.set_content("""
        <form id="studentParentForm">
            <input id="studentName" /><input id="parentName" /><input id="annualFamilyIncome" />
            <button id="nextToLoanBtn" type="submit">Save & Proceed</button>
        </form>
    """)
    assert BrowserAutomationService.detect_page_state(run_id) == "STUDENT_PARENT_INFO"
    assert is_human_barrier("STUDENT_PARENT_INFO") is False

    # 5. LOAN_INFO
    page.set_content("""
        <form id="loanDetailsForm">
            <input id="course" /><input id="college" /><input id="loanAmount" />
            <button id="nextToDocsBtn" type="submit">Save & Proceed</button>
        </form>
    """)
    assert BrowserAutomationService.detect_page_state(run_id) == "LOAN_INFO"
    assert is_human_barrier("LOAN_INFO") is False

    # 6. DOC_UPLOAD
    page.set_content("""
        <form id="documentUploadForm">
            <input id="admissionLetter" type="file" /><input id="feeStructure" type="file" />
            <button id="nextToReviewBtn" type="submit">Save & Proceed</button>
        </form>
    """)
    assert BrowserAutomationService.detect_page_state(run_id) == "DOC_UPLOAD"
    assert is_human_barrier("DOC_UPLOAD") is False

    # 7. FINAL_REVIEW
    page.set_content("""
        <div id="finalReviewContainer">
            <h2>Application Final Review & Citizen Verification</h2>
            <input id="declaration_agreed" class="confirmDeclaration" type="checkbox" />
            <button id="submitApplicationBtn" class="submitFinalApplicationBtn">Confirm & Submit</button>
        </div>
    """)
    assert BrowserAutomationService.detect_page_state(run_id) == "FINAL_REVIEW"
    assert is_human_barrier("FINAL_REVIEW") is True

    # 8. CONFIRMATION
    page.set_content("""
        <div class="ack-receipt-box">
            <h2>Education Loan Application Submitted Successfully</h2>
            <div class="ack-number-box">ACK-EDU-2026-123456</div>
        </div>
    """)
    assert BrowserAutomationService.detect_page_state(run_id) == "CONFIRMATION"
    assert is_human_barrier("CONFIRMATION") is True

    BrowserAutomationService.close_session(run_id)


def test_scenario_6_fill_student_parent_info():
    """
    Scenario 6: Test fill_student_parent_info fills all student & parent details,
    advances by clicking #nextToLoanBtn, and synchronizes STUDENT_INFO_COMPLETED milestone.
    """
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()

    html = """
    <form id="studentParentForm">
        <input id="studentName" type="text" />
        <input id="dateOfBirth" type="date" />
        <select id="gender"><option value="Female">Female</option><option value="Male">Male</option></select>
        <input id="state" type="text" />
        <input id="district" type="text" />
        <select id="category"><option value="General">General</option><option value="OBC">OBC</option></select>
        <input id="parentName" type="text" />
        <select id="parentOccupation">
            <option value="Salaried / Private">Salaried / Private</option>
            <option value="Agriculture / Farmer">Agriculture / Farmer</option>
        </select>
        <input id="annualFamilyIncome" type="number" />
        <input id="aadhaarLastFour" type="text" />
        <button id="nextToLoanBtn" type="button">Next to Loan</button>
    </form>
    """
    page.set_content(html)

    run_id = "test-run-student-fill"
    BrowserAutomationService.register_session(run_id=run_id, page=page, browser=browser, playwright=pw)

    # Click listener to simulate transition
    page.evaluate("""
        document.getElementById('nextToLoanBtn').addEventListener('click', () => {
            document.getElementById('studentParentForm').innerHTML = '<form id="loanDetailsForm"><input id="course" /></form>';
        });
    """)

    form_data = {
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
    }

    res = BrowserAutomationService.fill_student_parent_info(run_id, form_data)
    assert res["status"] == "STUDENT_INFO_COMPLETED"
    assert "student_name" in res["filled_fields"]
    assert "annual_family_income" in res["filled_fields"]
    assert res["milestone"] == "STUDENT_INFO_COMPLETED"

    BrowserAutomationService.close_session(run_id)


def test_scenario_7_fill_loan_info():
    """
    Scenario 7: Test fill_loan_info fills loan attributes,
    advances by clicking #nextToDocsBtn, and synchronizes LOAN_INFO_COMPLETED milestone.
    """
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()

    html = """
    <form id="loanDetailsForm">
        <input id="course" type="text" />
        <input id="college" type="text" />
        <input id="loanAmount" type="number" />
        <input id="tuitionFee" type="number" />
        <input id="livingExpenses" type="number" />
        <select id="bankPreference">
            <option value="State Bank of India">State Bank of India</option>
            <option value="Punjab National Bank">Punjab National Bank</option>
        </select>
        <select id="loanTenure">
            <option value="5 Years">5 Years</option>
            <option value="10 Years">10 Years</option>
        </select>
        <button id="nextToDocsBtn" type="button">Next to Docs</button>
    </form>
    """
    page.set_content(html)

    run_id = "test-run-loan-fill"
    BrowserAutomationService.register_session(run_id=run_id, page=page, browser=browser, playwright=pw)

    page.evaluate("""
        document.getElementById('nextToDocsBtn').addEventListener('click', () => {
            document.getElementById('loanDetailsForm').innerHTML = '<form id="documentUploadForm"><input id="admissionLetter" type="file" /></form>';
        });
    """)

    loan_data = {
        "course": "B.Tech Computer Science and Engineering",
        "college": "National Institute of Technology",
        "loan_amount": 750000,
        "tuition_fee": 500000,
        "living_expenses": 250000,
        "bank_preference": "State Bank of India",
        "loan_tenure": "10 Years",
    }

    res = BrowserAutomationService.fill_loan_info(run_id, loan_data)
    assert res["status"] == "LOAN_INFO_COMPLETED"
    assert "course" in res["filled_fields"]
    assert "loan_amount" in res["filled_fields"]
    assert res["milestone"] == "LOAN_INFO_COMPLETED"

    BrowserAutomationService.close_session(run_id)


def test_scenario_8_upload_documents_and_final_review_guardrail(tmp_path):
    """
    Scenario 8: Test upload_application_documents uses real storage paths,
    advances to Step 7 (FINAL_REVIEW), and strictly stops at the human barrier.
    """
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()

    # Create real test files on disk
    adm_file = tmp_path / "test_admission_offer.pdf"
    adm_file.write_bytes(b"%PDF-1.4 Offer Letter")
    fee_file = tmp_path / "test_fee_structure.pdf"
    fee_file.write_bytes(b"%PDF-1.4 Fee Structure")
    adh_file = tmp_path / "test_aadhaar.pdf"
    adh_file.write_bytes(b"%PDF-1.4 Aadhaar Card")
    inc_file = tmp_path / "test_income.pdf"
    inc_file.write_bytes(b"%PDF-1.4 Income Cert")

    html = """
    <form id="documentUploadForm">
        <input id="admissionLetter" type="file" />
        <input id="feeStructure" type="file" />
        <input id="studentAadhaar" type="file" />
        <input id="parentIncomeCertificate" type="file" />
        <button id="nextToReviewBtn" type="button">Next to Review</button>
    </form>
    """
    page.set_content(html)

    run_id = "test-run-doc-upload"
    BrowserAutomationService.register_session(run_id=run_id, page=page, browser=browser, playwright=pw)

    # When nextToReviewBtn is clicked, render final review card
    page.evaluate("""
        document.getElementById('nextToReviewBtn').addEventListener('click', () => {
            document.body.innerHTML = `
                <div id="finalReviewContainer">
                    <h2>Application Final Review & Citizen Verification</h2>
                    <input id="declaration_agreed" class="confirmDeclaration" type="checkbox" />
                    <button id="submitApplicationBtn" class="submitFinalApplicationBtn">Confirm & Submit</button>
                </div>
            `;
        });
    """)

    form_data = {
        "documents": [
            {"document_name": "admission_letter", "storage_path": str(adm_file)},
            {"document_name": "fee_structure", "storage_path": str(fee_file)},
            {"document_name": "student_aadhaar", "storage_path": str(adh_file)},
            {"document_name": "parent_income_certificate", "storage_path": str(inc_file)},
        ]
    }

    res = BrowserAutomationService.upload_application_documents(run_id, form_data)
    assert res["status"] == "DOCUMENTS_UPLOADED"
    assert len(res["uploaded_fields"]) == 4
    assert res["paused_at"] == "FINAL_REVIEW"
    assert res["human_action_required"] is True

    # Check DOM state is now FINAL_REVIEW
    assert BrowserAutomationService.detect_page_state(run_id) == "FINAL_REVIEW"

    # CRITICAL GUARDRAIL VERIFICATION:
    # Ensure final submit button was NOT clicked (remains on FINAL_REVIEW)
    assert BrowserAutomationService.detect_page_state(run_id) != "CONFIRMATION"

    BrowserAutomationService.close_session(run_id)

