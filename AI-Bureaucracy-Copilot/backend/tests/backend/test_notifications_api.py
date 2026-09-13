import asyncio
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import notification_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_notifications():
    notification_service.clear_notifications_for_testing()
    yield
    notification_service.clear_notifications_for_testing()


def test_notification_test_trigger_endpoint():
    """Verify test-trigger endpoint dispatches action-required notification."""
    payload = {
        "profile_id": "test-citizen-01",
        "scheme_id": "SCH-HLT-001",
        "action_type": "CAPTCHA",
        "message": "Please solve CAPTCHA challenge on the portal.",
        "portal_url": "http://localhost:5174",
    }
    res = client.post("/api/notifications/test-trigger", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "DISPATCHED"
    notif = data["notification"]
    assert notif["profile_id"] == "test-citizen-01"
    assert notif["action_type"] == "CAPTCHA"
    assert notif["status"] == "ACTION_REQUIRED"

    # Verify notification appears in profile notifications list
    list_res = client.get("/api/notifications?profile_id=test-citizen-01")
    assert list_res.status_code == 200
    items = list_res.json()["notifications"]
    assert len(items) == 1
    assert items[0]["notification_id"] == notif["notification_id"]


def test_notification_resolve_endpoint():
    """Verify resolution of an active notification."""
    # Create notification
    notif = notification_service.send_notification(
        profile_id="test-citizen-02",
        scheme_id="SCH-HLT-001",
        action_type="OTP",
        message="Enter OTP",
    )
    nid = notif["notification_id"]

    # Resolve notification
    res = client.post(f"/api/notifications/{nid}/resolve?profile_id=test-citizen-02")
    assert res.status_code == 200
    assert res.json()["status"] == "RESOLVED"

    # Confirm status is updated
    items = notification_service.get_notifications_for_profile("test-citizen-02")
    assert items[0]["status"] == "RESOLVED"


def test_notification_resolve_not_found():
    """Resolving non-existent notification returns 404."""
    res = client.post("/api/notifications/non-existent-id/resolve?profile_id=test-citizen-03")
    assert res.status_code == 404
    assert "not found" in res.json()["error"].lower()


@pytest.mark.anyio
async def test_notification_pubsub_realtime():
    """Verify async subscriber receives published notification."""
    profile_id = "test-citizen-async"

    # Register subscriber queue directly
    q = notification_service.add_subscriber(profile_id)

    try:
        # Fire notification
        notification_service.send_notification(
            profile_id=profile_id,
            scheme_id="SCH-HLT-001",
            action_type="LOGIN",
            message="Please log in to continue.",
        )

        # Receive from queue with timeout
        received = await asyncio.wait_for(q.get(), timeout=2.0)
        assert received["profile_id"] == profile_id
        assert received["action_type"] == "LOGIN"
        assert received["status"] == "ACTION_REQUIRED"
    finally:
        notification_service.remove_subscriber(profile_id, q)
