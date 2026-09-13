import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.automation_service import clear_automation_runs_for_testing
from app.services.application_state_service import clear_states_for_testing
from app.services.document_service import clear_document_store_for_testing
from app.services.notification_service import clear_notifications_for_testing

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_stores():
    clear_automation_runs_for_testing()
    clear_states_for_testing()
    clear_document_store_for_testing()
    clear_notifications_for_testing()
    yield
    clear_automation_runs_for_testing()
    clear_states_for_testing()
    clear_document_store_for_testing()
    clear_notifications_for_testing()


def test_scenario_1_state_initialization_on_automation_start():
    """Scenario 1: Starting an automation run creates centralized application state."""
    start_res = client.post(
        "/api/automation/start",
        json={"scheme_id": "SCH-HLT-001", "profile_id": "citizen-sync-01"},
    )
    assert start_res.status_code == 201
    run_id = start_res.json()["run_id"]

    # Verify centralized application status endpoint
    status_res = client.get(f"/api/application/{run_id}/status")
    assert status_res.status_code == 200
    state = status_res.json()
    assert state["run_id"] == run_id
    assert state["scheme_id"] == "SCH-HLT-001"
    assert state["profile_id"] == "citizen-sync-01"
    assert state["application_status"] == "draft"


def test_scenario_2_get_unknown_application_status_404():
    """Scenario 2: Querying non-existent application returns 404."""
    status_res = client.get("/api/application/non-existent-run-id/status")
    assert status_res.status_code == 404


def test_scenario_3_sync_login_event_advances_agent():
    """Scenario 3: Mock portal login callback automatically advances agent from LOGIN to CAPTCHA."""
    start_res = client.post(
        "/api/automation/start",
        json={"scheme_id": "SCH-HLT-001", "profile_id": "citizen-sync-02"},
    )
    run_id = start_res.json()["run_id"]
    assert start_res.json()["human_action_required"]["action_type"] == "LOGIN"

    # Mock portal completes login and notifies main backend
    sync_res = client.post(
        f"/api/application/{run_id}/status",
        json={
            "action_type": "LOGIN",
            "status": "LOGIN_COMPLETED",
            "portal_session_id": "portal-session-999",
        },
    )
    assert sync_res.status_code == 200
    state = sync_res.json()
    assert state["portal_session_id"] == "portal-session-999"
    assert state["last_completed_action"] == "LOGIN"

    # Verify automation status is now awaiting CAPTCHA without manual button click
    auto_status = client.get(f"/api/automation/status?run_id={run_id}").json()
    assert auto_status["human_action_required"]["action_type"] == "CAPTCHA"


def test_scenario_4_sync_captcha_event_advances_to_data_review_and_otp():
    """Scenario 4: Mock portal CAPTCHA callback advances workflow to DATA_REVIEW, and subsequent action advances through form mapping to OTP."""
    start_res = client.post(
        "/api/automation/start",
        json={"scheme_id": "SCH-HLT-001", "profile_id": "citizen-sync-03"},
    )
    run_id = start_res.json()["run_id"]

    # 1. Login callback
    client.post(
        f"/api/application/{run_id}/status",
        json={"action_type": "LOGIN", "status": "LOGIN_COMPLETED"},
    )

    # 2. CAPTCHA callback
    sync_res = client.post(
        f"/api/application/{run_id}/status",
        json={"action_type": "CAPTCHA", "status": "CAPTCHA_COMPLETED"},
    )
    assert sync_res.status_code == 200

    # Pauses at DATA_REVIEW due to unverified docs
    auto_status = client.get(f"/api/automation/status?run_id={run_id}").json()
    assert auto_status["human_action_required"]["action_type"] == "DATA_REVIEW"

    # 3. Completing DATA_REVIEW advances through automated form_mapping to OTP
    review_res = client.post(
        f"/api/application/{run_id}/status",
        json={"action_type": "DATA_REVIEW", "status": "DATA_REVIEW_COMPLETED"},
    )
    assert review_res.status_code == 200

    auto_status_after = client.get(f"/api/automation/status?run_id={run_id}").json()
    assert auto_status_after["human_action_required"]["action_type"] == "OTP"



def test_scenario_5_sync_otp_event_advances_to_final_submit():
    """Scenario 5: Mock portal OTP verification callback advances to FINAL_SUBMIT."""
    start_res = client.post(
        "/api/automation/start",
        json={"scheme_id": "SCH-HLT-001", "profile_id": "citizen-sync-04"},
    )
    run_id = start_res.json()["run_id"]

    # Advance Login and Captcha
    client.post(f"/api/application/{run_id}/status", json={"action_type": "LOGIN", "status": "LOGIN_COMPLETED"})
    client.post(f"/api/application/{run_id}/status", json={"action_type": "CAPTCHA", "status": "CAPTCHA_COMPLETED"})

    # OTP callback
    sync_res = client.post(
        f"/api/application/{run_id}/status",
        json={"action_type": "OTP", "status": "OTP_COMPLETED"},
    )
    assert sync_res.status_code == 200

    auto_status = client.get(f"/api/automation/status?run_id={run_id}").json()
    assert auto_status["human_action_required"]["action_type"] == "FINAL_SUBMIT"


def test_scenario_6_sync_final_submit_completes_workflow():
    """Scenario 6: Mock portal final submission completes the entire workflow and records acknowledgment."""
    start_res = client.post(
        "/api/automation/start",
        json={"scheme_id": "SCH-HLT-001", "profile_id": "citizen-sync-05"},
    )
    run_id = start_res.json()["run_id"]

    # Progress through all steps
    client.post(f"/api/application/{run_id}/status", json={"action_type": "LOGIN", "status": "LOGIN_COMPLETED"})
    client.post(f"/api/application/{run_id}/status", json={"action_type": "CAPTCHA", "status": "CAPTCHA_COMPLETED"})
    client.post(f"/api/application/{run_id}/status", json={"action_type": "OTP", "status": "OTP_COMPLETED"})

    # Final Submit callback
    ack_ref = "ACK-GOV-2026-987654"
    sync_res = client.post(
        f"/api/application/{run_id}/status",
        json={
            "action_type": "FINAL_SUBMIT",
            "status": "APPLICATION_SUBMITTED",
            "acknowledgment_number": ack_ref,
        },
    )
    assert sync_res.status_code == 200
    state = sync_res.json()
    assert state["acknowledgment_number"] == ack_ref
    assert state["application_status"] == "SUBMITTED" or state["application_status"] == "submitted"
    assert state["automation_status"].lower() == "completed"

    # Verify agent state
    auto_status = client.get(f"/api/automation/status?run_id={run_id}").json()
    assert auto_status["automation_status"] == "COMPLETED"
    assert auto_status["human_action_required"] is None
    assert auto_status["acknowledgment_number"] == ack_ref


def test_scenario_7_notifications_resolved_on_sync():
    """Scenario 7: When mock portal synchronizes a step, the corresponding notification is resolved."""
    start_res = client.post(
        "/api/automation/start",
        json={"scheme_id": "SCH-HLT-001", "profile_id": "citizen-sync-06"},
    )
    run_id = start_res.json()["run_id"]

    # Initial notification should be ACTION_REQUIRED
    notifs = client.get("/api/notifications?profile_id=citizen-sync-06").json()["notifications"]
    assert len(notifs) == 1
    assert notifs[0]["action_type"] == "LOGIN"
    assert notifs[0]["status"] == "ACTION_REQUIRED"

    # Mock portal syncs LOGIN
    client.post(f"/api/application/{run_id}/status", json={"action_type": "LOGIN", "status": "LOGIN_COMPLETED"})

    # Check notification status updated to RESOLVED
    notifs = client.get("/api/notifications?profile_id=citizen-sync-06").json()["notifications"]
    login_notif = next(n for n in notifs if n["action_type"] == "LOGIN")
    assert login_notif["status"] == "RESOLVED"


def test_scenario_8_application_state_persistence_and_retrieval():
    """Scenario 8: Centralized application state persists, records updates, and is queryable."""
    from app.services.application_state_service import get_latest_state

    start_res = client.post(
        "/api/automation/start",
        json={"scheme_id": "SCH-HLT-001", "profile_id": "citizen-sync-08"},
    )
    run_id = start_res.json()["run_id"]

    # Post an update with custom metadata
    update_res = client.post(
        f"/api/application/{run_id}/status",
        json={
            "action_type": "LOGIN",
            "status": "LOGIN_COMPLETED",
            "portal_session_id": "sess-persist-test",
            "metadata": {"browser": "Chrome", "mode": "sync"},
        },
    )
    assert update_res.status_code == 200

    # Retrieve via API
    get_res = client.get(f"/api/application/{run_id}/status")
    assert get_res.status_code == 200
    state = get_res.json()
    assert state["portal_session_id"] == "sess-persist-test"
    assert state["last_completed_action"] == "LOGIN"
    assert state["last_updated"] is not None

    # Retrieve via service helper
    latest = get_latest_state(profile_id="citizen-sync-08", scheme_id="SCH-HLT-001")
    assert latest is not None
    assert latest["run_id"] == run_id
    assert latest["portal_session_id"] == "sess-persist-test"


def test_scenario_9_education_loan_workflow_milestone_synchronization():
    """Scenario 9: Education loan full workflow syncs all 5 milestones back to main copilot state."""
    profile_id = "student-sync-09"
    scheme_id = "SCH-EDU-001"

    # 1. Citizen submits dynamic info
    info_payload = {
        "profile_id": profile_id,
        "data": {
            "student_name": "Priya Sharma",
            "date_of_birth": "2003-05-15",
            "gender": "Female",
            "state": "Andhra Pradesh",
            "district": "Visakhapatnam",
            "category": "OBC",
            "parent_name": "Ramesh Sharma",
            "parent_occupation": "Salaried / Private",
            "annual_family_income": 350000.0,
            "aadhaar_last_four": "5821",
            "course": "B.Tech Computer Science and Engineering",
            "college": "National Institute of Technology",
            "loan_amount": 750000.0,
            "tuition_fee": 500000.0,
            "living_expenses": 250000.0,
            "bank_preference": "State Bank of India",
            "loan_tenure": "10 Years",
            "declaration_agreed": True,
        }
    }
    client.post(f"/api/schemes/{scheme_id}/information", json=info_payload)

    # 2. Start automation run
    start_res = client.post(
        "/api/automation/start",
        json={"scheme_id": scheme_id, "profile_id": profile_id},
    )
    assert start_res.status_code == 201
    run_id = start_res.json()["run_id"]

    # 3. Verify mapped_form_data delivers complete dossier
    auto_status = client.get(f"/api/automation/status?run_id={run_id}").json()
    mapped = auto_status["mapped_form_data"]
    assert mapped is not None
    assert mapped["student_name"] == "Priya Sharma"
    assert mapped["course"] == "B.Tech Computer Science and Engineering"
    assert mapped["loan_amount"] == 750000.0
    assert "documents" in mapped

    # 4. Milestone 1: STUDENT_INFO_COMPLETED
    m1 = client.post(
        f"/api/application/{run_id}/status",
        json={
            "action_type": "STUDENT_INFO_COMPLETED",
            "status": "STUDENT_INFO_COMPLETED",
            "portal_session_id": "sess-edu-101",
            "metadata": {"student_name": "Priya Sharma"},
        },
    )
    assert m1.status_code == 200
    assert m1.json()["last_completed_action"] == "STUDENT_INFO_COMPLETED"
    assert m1.json()["portal_session_id"] == "sess-edu-101"

    # 5. Milestone 2: LOAN_INFO_COMPLETED
    m2 = client.post(
        f"/api/application/{run_id}/status",
        json={
            "action_type": "LOAN_INFO_COMPLETED",
            "status": "LOAN_INFO_COMPLETED",
            "portal_session_id": "sess-edu-101",
            "metadata": {"loan_amount": 750000.0},
        },
    )
    assert m2.status_code == 200
    assert m2.json()["last_completed_action"] == "LOAN_INFO_COMPLETED"

    # 6. Milestone 3: DOCUMENTS_UPLOADED
    m3 = client.post(
        f"/api/application/{run_id}/status",
        json={
            "action_type": "DOCUMENTS_UPLOADED",
            "status": "DOCUMENTS_UPLOADED",
            "portal_session_id": "sess-edu-101",
        },
    )
    assert m3.status_code == 200
    assert m3.json()["last_completed_action"] == "DOCUMENTS_UPLOADED"

    # 7. Milestone 4: FINAL_REVIEW_REQUIRED
    m4 = client.post(
        f"/api/application/{run_id}/status",
        json={
            "action_type": "FINAL_REVIEW_REQUIRED",
            "status": "FINAL_REVIEW_REQUIRED",
            "portal_session_id": "sess-edu-101",
        },
    )
    assert m4.status_code == 200
    assert m4.json()["last_completed_action"] == "FINAL_REVIEW_REQUIRED"

    # 8. Milestone 5: APPLICATION_SUBMITTED
    ack_edu = "ACK-EDU-2026-654321"
    m5 = client.post(
        f"/api/application/{run_id}/status",
        json={
            "action_type": "FINAL_SUBMIT",
            "status": "APPLICATION_SUBMITTED",
            "portal_session_id": "sess-edu-101",
            "acknowledgment_number": ack_edu,
        },
    )
    assert m5.status_code == 200
    final_state = m5.json()
    assert final_state["acknowledgment_number"] == ack_edu
    assert final_state["application_status"].lower() == "submitted"
    assert final_state["automation_status"].lower() == "completed"


