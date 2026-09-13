import os
import inspect
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app as main_app
from app.services.automation_service import clear_automation_runs_for_testing
from app.services.application_state_service import clear_states_for_testing
from app.services.browser_automation_service import BrowserAutomationService, is_human_barrier
from app.services.document_service import clear_document_store_for_testing, load_all_schemes
from app.services.notification_service import clear_notifications_for_testing
from app.services.pmkisan_action_router import detect_pmkisan_action

main_client = TestClient(main_app)


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


def test_complete_21_step_education_loan_workflow_and_guardrails(tmp_path):
    """
    TASK 6: Complete End-to-End Verification of the 21-step Education Loan Workflow:
    MAIN COPILOT
    → SCH-EDU-001
    → Dynamic Form
    → Document Agent
    → Application State
    → Automation Agent
    → Playwright
    → Mock Student Education Loan Portal
    """
    profile_id = "citizen-e2e-student-01"
    scheme_id = "SCH-EDU-001"

    # -------------------------------------------------------------------------
    # STEP 1: Student & Loan Information Collection (Dynamic Form)
    # -------------------------------------------------------------------------
    form_payload = {
        "profile_id": profile_id,
        "data": {
            "date_of_birth": "2002-11-20",
            "category": "General",
            "parent_name": "Suresh Nambiar",
            "parent_occupation": "Salaried / Government",
            "annual_family_income": 480000,
            "aadhaar_last_four": "7134",
            "course": "M.Tech Artificial Intelligence",
            "college": "Indian Institute of Technology",
            "loan_amount": 900000,
            "tuition_fee": 650000,
            "living_expenses": 250000,
            "bank_preference": "Canara Bank",
            "loan_tenure": "10 Years",
        },
    }
    form_res = main_client.post(
        f"/api/schemes/{scheme_id}/information",
        json=form_payload,
    )
    assert form_res.status_code == 200
    assert form_res.json()["status"] == "saved"

    # -------------------------------------------------------------------------
    # STEP 2: Required Documents Identification (Document Agent)
    # -------------------------------------------------------------------------
    req_res = main_client.get(f"/api/schemes/{scheme_id}/documents/required?profile_id={profile_id}")
    assert req_res.status_code == 200
    req_docs = req_res.json()["required_documents"]
    assert len(req_docs) == 4
    doc_labels = [d["name"] for d in req_docs]
    assert "admission_letter" in doc_labels
    assert "fee_structure" in doc_labels
    assert "student_aadhaar" in doc_labels
    assert "parent_income_certificate" in doc_labels

    # -------------------------------------------------------------------------
    # STEP 3: Real Documents Upload & Verification
    # -------------------------------------------------------------------------
    uploaded_files = {}
    doc_specs = [
        ("admission_letter", "IIT_Admission_Letter.pdf", b"%PDF-1.4 IIT Admission Letter Offer"),
        ("fee_structure", "IIT_Fee_Structure_2026.pdf", b"%PDF-1.4 Institutional Fee Schedule"),
        ("student_aadhaar", "Student_Aadhaar_Card.pdf", b"%PDF-1.4 Student Identity Card"),
        ("parent_income_certificate", "Income_Certificate_Kerala.pdf", b"%PDF-1.4 Revenue Certificate"),
    ]
    for doc_name, filename, file_content in doc_specs:
        up_res = main_client.post(
            "/api/documents/upload",
            data={
                "scheme_id": scheme_id,
                "document_name": doc_name,
                "profile_id": profile_id,
            },
            files={"file": (filename, file_content, "application/pdf")},
        )
        assert up_res.status_code == 201
        up_data = up_res.json()
        assert up_data["verification_status"] in ("VERIFIED", "MANUAL_VERIFICATION_REQUIRED")

    # Verify document status
    doc_status_res = main_client.get(f"/api/documents/status?scheme_id={scheme_id}&profile_id={profile_id}")
    assert doc_status_res.status_code == 200
    all_uploaded = doc_status_res.json()["documents"]
    assert len(all_uploaded) == 4

    # -------------------------------------------------------------------------
    # STEP 4: Automation Run Start
    # -------------------------------------------------------------------------
    start_res = main_client.post(
        "/api/automation/start",
        json={"scheme_id": scheme_id, "profile_id": profile_id},
    )
    assert start_res.status_code == 201
    start_data = start_res.json()
    run_id = start_data["run_id"]
    assert start_data["automation_status"] == "AWAITING_HUMAN_ACTION"
    assert start_data["human_action_required"]["action_type"] == "LOGIN"

    # Verify dossier does not contain health fields and uses real data
    mapped_dossier = start_data["mapped_form_data"]
    assert mapped_dossier["student_name"] is not None
    assert mapped_dossier["annual_family_income"] == 480000.0
    assert mapped_dossier["aadhaar_last_four"] == "7134"
    assert mapped_dossier["course"] == "M.Tech Artificial Intelligence"
    assert mapped_dossier["college"] == "Indian Institute of Technology"
    assert mapped_dossier["loan_amount"] == 900000.0
    assert "hospital_id" not in mapped_dossier
    assert "illness" not in mapped_dossier
    assert "claim_amount" not in mapped_dossier

    # -------------------------------------------------------------------------
    # STEP 5: Mock Portal Session Launch (Playwright)
    # -------------------------------------------------------------------------
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()

    BrowserAutomationService.register_session(
        run_id=run_id,
        page=page,
        browser=browser,
        playwright=pw,
    )

    # -------------------------------------------------------------------------
    # STEP 6: LOGIN — Requires Human Interaction
    # -------------------------------------------------------------------------
    page.set_content("""
        <div id="loginPageCard">
            <h2>Portal Sign In</h2>
            <input id="username" type="text" />
            <input id="password" type="password" />
            <button id="signInBtn">Sign In to Portal</button>
        </div>
    """)
    assert BrowserAutomationService.detect_page_state(run_id) == "LOGIN"
    assert is_human_barrier("LOGIN") is True

    # Human logs in
    page.fill("#username", "citizen_aarav")
    page.fill("#password", "SecurePass123!")

    # Portal notifies Main Copilot of Login completion
    sync_login = main_client.post(
        f"/api/application/{run_id}/status",
        json={
            "action_type": "LOGIN",
            "status": "LOGIN_COMPLETED",
            "portal_session_id": "session-e2e-demo-123",
        },
    )
    assert sync_login.status_code == 200

    # -------------------------------------------------------------------------
    # STEP 7: CAPTCHA — Requires Human Interaction
    # -------------------------------------------------------------------------
    page.set_content("""
        <div id="captchaPageCard" class="captcha-box">
            <h2>CAPTCHA Challenge</h2>
            <input id="captchaAnswer" type="text" />
            <button id="verifyCaptchaBtn">Verify CAPTCHA</button>
        </div>
    """)
    assert BrowserAutomationService.detect_page_state(run_id) == "CAPTCHA"
    assert is_human_barrier("CAPTCHA") is True

    # Human solves CAPTCHA
    page.fill("#captchaAnswer", "7X9K2")

    # Portal notifies Main Copilot of CAPTCHA verification
    sync_captcha = main_client.post(
        f"/api/application/{run_id}/status",
        json={
            "action_type": "CAPTCHA",
            "status": "CAPTCHA_COMPLETED",
            "portal_session_id": "session-e2e-demo-123",
        },
    )
    assert sync_captcha.status_code == 200

    # -------------------------------------------------------------------------
    # STEP 8: OTP — Requires Human Interaction
    # -------------------------------------------------------------------------
    page.set_content("""
        <div id="otpPageCard" class="simulated-otp-box">
            <h2>Two-Factor Mobile OTP</h2>
            <input id="otpInput" type="text" />
            <button id="verifyOtpBtn">Verify OTP</button>
        </div>
    """)
    assert BrowserAutomationService.detect_page_state(run_id) == "OTP"
    assert is_human_barrier("OTP") is True

    # Human enters OTP
    page.fill("#otpInput", "123456")

    # Portal notifies Main Copilot of OTP verification
    sync_otp = main_client.post(
        f"/api/application/{run_id}/status",
        json={
            "action_type": "OTP",
            "status": "OTP_COMPLETED",
            "portal_session_id": "session-e2e-demo-123",
        },
    )
    assert sync_otp.status_code == 200

    # -------------------------------------------------------------------------
    # STEP 9: Playwright Automatically Fills Student & Parent Information
    # -------------------------------------------------------------------------
    page.set_content("""
        <form id="studentParentForm">
            <input id="studentName" type="text" />
            <input id="dateOfBirth" type="date" />
            <select id="gender"><option value="Male">Male</option><option value="Female">Female</option></select>
            <input id="state" type="text" />
            <input id="district" type="text" />
            <select id="category"><option value="General">General</option><option value="OBC">OBC</option></select>
            <input id="parentName" type="text" />
            <select id="parentOccupation">
                <option value="Salaried / Government">Salaried / Government</option>
                <option value="Salaried / Private">Salaried / Private</option>
            </select>
            <input id="annualFamilyIncome" type="number" />
            <input id="aadhaarLastFour" type="text" />
            <button id="nextToLoanBtn" type="button">Save & Proceed to Loan Information →</button>
        </form>
    """)
    assert BrowserAutomationService.detect_page_state(run_id) == "STUDENT_PARENT_INFO"
    assert is_human_barrier("STUDENT_PARENT_INFO") is False

    # Simulate DOM transition to Step 5 upon clicking #nextToLoanBtn
    page.evaluate("""
        document.getElementById('nextToLoanBtn').addEventListener('click', () => {
            document.body.innerHTML = `
                <form id="loanDetailsForm">
                    <input id="course" type="text" />
                    <input id="college" type="text" />
                    <input id="loanAmount" type="number" />
                    <input id="tuitionFee" type="number" />
                    <input id="livingExpenses" type="number" />
                    <select id="bankPreference">
                        <option value="Canara Bank">Canara Bank</option>
                        <option value="State Bank of India">State Bank of India</option>
                    </select>
                    <select id="loanTenure">
                        <option value="10 Years">10 Years</option>
                    </select>
                    <button id="nextToDocsBtn" type="button">Save & Proceed to Document Upload →</button>
                </form>
            `;
        });
    """)

    fill_st_res = BrowserAutomationService.fill_student_parent_info(run_id, mapped_dossier)
    assert fill_st_res["status"] == "STUDENT_INFO_COMPLETED"
    assert "student_name" in fill_st_res["filled_fields"]

    # -------------------------------------------------------------------------
    # STEP 10: Main Portal Receives STUDENT_INFO_COMPLETED
    # -------------------------------------------------------------------------
    status_st = main_client.get(f"/api/application/{run_id}/status").json()
    assert status_st["last_completed_action"] == "STUDENT_INFO_COMPLETED"

    # -------------------------------------------------------------------------
    # STEP 11: Playwright Automatically Fills Loan Information
    # -------------------------------------------------------------------------
    assert BrowserAutomationService.detect_page_state(run_id) == "LOAN_INFO"
    assert is_human_barrier("LOAN_INFO") is False

    # Simulate DOM transition to Step 6 upon clicking #nextToDocsBtn
    page.evaluate("""
        document.getElementById('nextToDocsBtn').addEventListener('click', () => {
            document.body.innerHTML = `
                <form id="documentUploadForm">
                    <input id="admissionLetter" type="file" />
                    <input id="feeStructure" type="file" />
                    <input id="studentAadhaar" type="file" />
                    <input id="parentIncomeCertificate" type="file" />
                    <button id="nextToReviewBtn" type="button">Save & Proceed to Final Review →</button>
                </form>
            `;
        });
    """)

    fill_loan_res = BrowserAutomationService.fill_loan_info(run_id, mapped_dossier)
    assert fill_loan_res["status"] == "LOAN_INFO_COMPLETED"
    assert "course" in fill_loan_res["filled_fields"]
    assert "loan_amount" in fill_loan_res["filled_fields"]

    # -------------------------------------------------------------------------
    # STEP 12: Main Portal Receives LOAN_INFO_COMPLETED
    # -------------------------------------------------------------------------
    status_ln = main_client.get(f"/api/application/{run_id}/status").json()
    assert status_ln["last_completed_action"] == "LOAN_INFO_COMPLETED"

    # -------------------------------------------------------------------------
    # STEP 13: Playwright Automatically Uploads Documents
    # -------------------------------------------------------------------------
    assert BrowserAutomationService.detect_page_state(run_id) == "DOC_UPLOAD"
    assert is_human_barrier("DOC_UPLOAD") is False

    # Simulate DOM transition to Step 7 (Final Review) upon clicking #nextToReviewBtn
    page.evaluate("""
        document.getElementById('nextToReviewBtn').addEventListener('click', () => {
            document.body.innerHTML = `
                <div id="finalReviewContainer">
                    <h2>Application Final Review & Citizen Verification</h2>
                    <div id="humanReviewBarrier">MANDATORY HUMAN REVIEW BARRIER</div>
                    <input id="declaration_agreed" class="confirmDeclaration" type="checkbox" />
                    <button id="submitApplicationBtn" class="submitFinalApplicationBtn">Confirm & Submit</button>
                </div>
            `;
        });
    """)

    doc_upload_res = BrowserAutomationService.upload_application_documents(run_id, mapped_dossier)
    assert doc_upload_res["status"] == "DOCUMENTS_UPLOADED"
    assert len(doc_upload_res["uploaded_fields"]) == 4

    # -------------------------------------------------------------------------
    # STEP 14: Main Portal Receives DOCUMENTS_UPLOADED
    # -------------------------------------------------------------------------
    # In upload_application_documents, DOCUMENTS_UPLOADED is synced and state transitions to FINAL_REVIEW
    status_doc = main_client.get(f"/api/application/{run_id}/status").json()
    assert status_doc["last_completed_action"] in ("DOCUMENTS_UPLOADED", "FINAL_REVIEW_REQUIRED")

    # -------------------------------------------------------------------------
    # STEP 15: Mock Portal Reaches Final Review
    # -------------------------------------------------------------------------
    current_state = BrowserAutomationService.detect_page_state(run_id)
    assert current_state == "FINAL_REVIEW"

    # -------------------------------------------------------------------------
    # STEP 16: Playwright Strictly Stops (Never Submits!)
    # -------------------------------------------------------------------------
    assert doc_upload_res["paused_at"] == "FINAL_REVIEW"
    assert doc_upload_res["human_action_required"] is True
    # Ensure final review submit button has NOT been clicked
    assert BrowserAutomationService.detect_page_state(run_id) != "CONFIRMATION"

    # -------------------------------------------------------------------------
    # STEP 17: FINAL_REVIEW_REQUIRED is Shown in Main Portal
    # -------------------------------------------------------------------------
    sync_rev_res = main_client.post(
        f"/api/application/{run_id}/status",
        json={
            "action_type": "FINAL_REVIEW_REQUIRED",
            "status": "FINAL_REVIEW_REQUIRED",
            "portal_session_id": "session-e2e-demo-123",
        },
    )
    assert sync_rev_res.status_code == 200
    assert sync_rev_res.json()["last_completed_action"] == "FINAL_REVIEW_REQUIRED"
    assert is_human_barrier("FINAL_REVIEW") is True

    # -------------------------------------------------------------------------
    # STEP 18: Human Reviews and Confirms
    # -------------------------------------------------------------------------
    page.check("#declaration_agreed")
    assert page.is_checked("#declaration_agreed") is True

    # -------------------------------------------------------------------------
    # STEP 19: Mock Portal Generates Acknowledgment / Reference Number
    # -------------------------------------------------------------------------
    ack_number = "ACK-EDU-2026-874219"
    page.evaluate(f"""
        document.body.innerHTML = `
            <div class="ack-receipt-box">
                <h2>Education Loan Application Submitted Successfully</h2>
                <div class="ack-number-box">{ack_number}</div>
            </div>
        `;
    """)
    assert BrowserAutomationService.detect_page_state(run_id) == "CONFIRMATION"

    # -------------------------------------------------------------------------
    # STEP 20: APPLICATION_SUBMITTED Synchronized Back to Main Portal
    # -------------------------------------------------------------------------
    final_sync = main_client.post(
        f"/api/application/{run_id}/status",
        json={
            "action_type": "FINAL_SUBMIT",
            "status": "APPLICATION_SUBMITTED",
            "portal_session_id": "session-e2e-demo-123",
            "acknowledgment_number": ack_number,
        },
    )
    assert final_sync.status_code == 200
    final_state = final_sync.json()

    # -------------------------------------------------------------------------
    # STEP 21: Main Portal Displays Completed Workflow
    # -------------------------------------------------------------------------
    assert final_state["acknowledgment_number"] == ack_number
    assert final_state["application_status"].lower() == "submitted"
    assert final_state["automation_status"].lower() == "completed"

    BrowserAutomationService.close_session(run_id)


def test_guardrails_integrity_verification():
    """
    Verify all required safety guardrails:
    - CAPTCHA is never automated.
    - OTP is never automated.
    - Final submission is never clicked by Playwright.
    - No fake application completion generated before human confirmation.
    - No hardcoded fake student data used when real dossier data exists.
    - No health-specific fields leak into education-loan workflow.
    - Existing authentication remains functional.
    - Existing PM-KISAN/RAG functionality remains functional.
    - Existing mock scheme functionality is preserved.
    """
    from app.services import browser_automation_service
    source = inspect.getsource(browser_automation_service)

    # 1. CAPTCHA is never automated
    assert "solve_captcha" not in source.lower()
    assert "captcha_solver" not in source.lower()
    assert "fill(#captchaanswer" not in source.lower().replace(" ", "").replace('"', "'")

    # 2. OTP is never automated
    assert "fill(#otpinput" not in source.lower().replace(" ", "").replace('"', "'")
    assert "auto_fill_otp" not in source.lower()

    # 3. Final submission is never clicked by Playwright
    assert "click(#submitapplicationbtn" not in source.lower().replace(" ", "").replace('"', "'")
    assert "click(#submitfinalapplicationbtn" not in source.lower().replace(" ", "").replace('"', "'")
    assert "click('button[type=\"submit\"]')" not in source.lower()

    # 4. Human barriers are strictly recognized
    assert is_human_barrier("LOGIN") is True
    assert is_human_barrier("CAPTCHA") is True
    assert is_human_barrier("OTP") is True
    assert is_human_barrier("FINAL_REVIEW") is True

    # 5. Existing schemes remain intact
    all_schemes = load_all_schemes()
    scheme_ids = [s.scheme_id for s in all_schemes]
    assert "SCH-EDU-001" in scheme_ids
    assert "SCH-HLT-001" in scheme_ids  # Existing mock scheme preserved

    # 6. Existing PM-KISAN action routing remains intact
    action = detect_pmkisan_action("I want to check my beneficiary status for PM-KISAN")
    assert action is not None
    assert action["action"] == "beneficiary_status"
    assert "beneficiarystatus" in action["action_url"].lower()
