import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.automation_service import clear_automation_runs_for_testing
from app.services.document_service import clear_document_store_for_testing
from app.services.notification_service import clear_notifications_for_testing

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_stores():
    clear_automation_runs_for_testing()
    clear_document_store_for_testing()
    clear_notifications_for_testing()
    yield
    clear_automation_runs_for_testing()
    clear_document_store_for_testing()
    clear_notifications_for_testing()


def test_scenario_1_standard_automation_workflow_planning_and_pause():
    """Scenario 1: Automation agent plans steps, pauses at first human action (LOGIN), and fires notification."""
    start_payload = {
        "scheme_id": "SCH-HLT-001",
        "profile_id": "citizen-001",
    }
    start_res = client.post("/api/automation/start", json=start_payload)
    assert start_res.status_code == 201
    data = start_res.json()

    assert data["scheme_id"] == "SCH-HLT-001"
    assert data["profile_id"] == "citizen-001"
    assert data["automation_status"] == "AWAITING_HUMAN_ACTION"
    assert data["application_status"] == "PENDING_CITIZEN_ACTION"

    # Verify human_action_required payload
    human_req = data["human_action_required"]
    assert human_req is not None
    assert human_req["action_type"] == "LOGIN"
    assert "mock portal" in human_req["message"].lower()

    # Verify real notification fired
    notif_res = client.get("/api/notifications?profile_id=citizen-001")
    assert notif_res.status_code == 200
    notifs = notif_res.json()["notifications"]
    assert len(notifs) == 1
    assert notifs[0]["action_type"] == "LOGIN"
    assert notifs[0]["status"] == "ACTION_REQUIRED"


def test_scenario_2_data_gap_unverified_docs_planning():
    """Scenario 2: Agent identifies unverified/missing documents and includes a review step."""
    start_payload = {
        "scheme_id": "SCH-HLT-004",
        "profile_id": "citizen-002",
    }
    start_res = client.post("/api/automation/start", json=start_payload)
    assert start_res.status_code == 201
    data = start_res.json()

    step_ids = [s["step_id"] for s in data["planned_steps"]]
    assert "data_review" in step_ids


def test_scenario_3_human_confirmation_and_resume_to_completion():
    """Scenario 3: Resuming after human action resolves notification and advances workflow steps."""
    # Start automation run
    start_payload = {
        "scheme_id": "SCH-HLT-001",
        "profile_id": "citizen-003",
    }
    start_res = client.post("/api/automation/start", json=start_payload)
    run_id = start_res.json()["run_id"]
    current_status = start_res.json()

    # Loop resuming human action steps until completion
    max_steps = 10
    step_count = 0
    while current_status["automation_status"] == "AWAITING_HUMAN_ACTION" and step_count < max_steps:
        step_count += 1
        human_req = current_status["human_action_required"]
        assert human_req is not None

        action_type = human_req["action_type"]
        resume_payload = {
            "run_id": run_id,
            "action_type": action_type,
            "confirmation_data": {"user_confirmed": True},
        }
        resume_res = client.post("/api/automation/resume", json=resume_payload)
        assert resume_res.status_code == 200
        current_status = resume_res.json()

    assert current_status["automation_status"] == "COMPLETED"
    assert current_status["application_status"] == "SUBMITTED"

    # Check notification for citizen-003 is resolved
    notif_res = client.get("/api/notifications?profile_id=citizen-003")
    assert notif_res.status_code == 200
    notifs = notif_res.json()["notifications"]
    assert all(n["status"] == "RESOLVED" for n in notifs)
