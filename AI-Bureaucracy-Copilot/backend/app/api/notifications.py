import asyncio
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.core.dependencies import get_current_user
from app.db.models import User
from app.services import notification_service, profile_service

router = APIRouter()


def _verify_profile_ownership(profile_id: Optional[str], current_user: User):
    if not profile_id or profile_id in ("default", "anonymous"):
        return
    prof = profile_service.get_profile(profile_id)
    if prof and prof.user_id not in (current_user.id, "anonymous"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not have permission to access notifications for this profile.",
        )


class NotificationTestTriggerPayload(BaseModel):
    profile_id: str = "default"
    scheme_id: str = "SCH-HLT-001"
    action_type: str = "CAPTCHA"
    message: str = "Action Required: Please solve the CAPTCHA puzzle on the portal."
    portal_url: Optional[str] = "http://localhost:5174"
    run_id: Optional[str] = None


@router.get("/notifications/stream")
async def stream_notifications(
    profile_id: str = Query("default", description="Citizen profile ID to stream notifications for")
):
    """Server-Sent Events (SSE) stream for real-time notification push to citizen frontend."""
    pid = profile_id.strip() if profile_id else "default"

    async def event_generator():
        yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'profile_id': pid})}\n\n"

        async for notif in notification_service.subscribe_notifications(pid):
            data_str = json.dumps(notif)
            yield f"event: notification\ndata: {data_str}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/notifications/test-trigger",
    status_code=status.HTTP_201_CREATED,
)
def trigger_test_notification(
    payload: NotificationTestTriggerPayload,
    current_user: User = Depends(get_current_user),
):
    """Test endpoint to trigger a simulated action-required notification event."""
    _verify_profile_ownership(payload.profile_id, current_user)
    notif = notification_service.send_notification(
        profile_id=payload.profile_id,
        scheme_id=payload.scheme_id,
        action_type=payload.action_type,
        message=payload.message,
        portal_url=payload.portal_url,
        run_id=payload.run_id,
    )
    return {
        "status": "DISPATCHED",
        "notification": notif,
    }


@router.post("/notifications/{notification_id}/resolve")
def resolve_notification(
    notification_id: str,
    profile_id: str = Query("default", description="Citizen profile ID"),
    current_user: User = Depends(get_current_user),
):
    pid = profile_id.strip() if profile_id else "default"
    nid = notification_id.strip()

    _verify_profile_ownership(pid, current_user)

    resolved = notification_service.mark_notification_resolved(pid, nid)
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification '{nid}' not found for profile '{pid}'.",
        )

    return {"status": "RESOLVED", "notification_id": nid}
