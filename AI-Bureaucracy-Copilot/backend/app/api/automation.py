from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from pydantic import BaseModel
from app.core.dependencies import get_current_user, get_current_user_optional
from app.db.models import User
from app.schemas.automation_schema import (
    AutomationResumeRequest,
    AutomationStartRequest,
    AutomationStatusResponse,
    NotificationListResponse,
)
from app.services import automation_service, notification_service, profile_service
from app.schemas.application_state_schema import ApplicationStatusUpdateRequest, ApplicationState
from app.services import application_state_service

router = APIRouter()


def _verify_profile_ownership(profile_id: Optional[str], current_user: Optional[User]):
    # If unauthenticated server callback (e.g. mock portal notify_main_portal), permit state sync
    if current_user is None:
        return
    if not profile_id or profile_id in ("default", "anonymous"):
        return
    prof = profile_service.get_profile(profile_id)
    if prof and prof.user_id not in (current_user.id, "anonymous"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not have permission to access automation for this profile.",
        )


@router.post(
    "/automation/start",
    response_model=AutomationStatusResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_automation(
    payload: AutomationStartRequest,
    current_user: User = Depends(get_current_user),
):
    clean_scheme = payload.scheme_id.strip()
    clean_profile = payload.profile_id.strip()

    if not clean_scheme or not clean_profile:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fields 'scheme_id' and 'profile_id' cannot be empty.",
        )

    _verify_profile_ownership(clean_profile, current_user)

    run_state = automation_service.start_automation_run(
        scheme_id=clean_scheme, profile_id=clean_profile
    )
    
    # Initialize centralized state
    application_state_service.init_or_get_state(
        run_id=run_state["run_id"],
        scheme_id=clean_scheme,
        profile_id=clean_profile
    )

    return run_state


@router.get(
    "/automation/status",
    response_model=AutomationStatusResponse,
)
def get_automation_status(
    run_id: Optional[str] = Query(None, description="Automation run ID"),
    scheme_id: Optional[str] = Query(None, description="Scheme ID"),
    profile_id: Optional[str] = Query(None, description="Profile ID"),
    current_user: User = Depends(get_current_user),
):
    _verify_profile_ownership(profile_id, current_user)
    run_state = automation_service.get_automation_run_status(
        run_id=run_id, scheme_id=scheme_id, profile_id=profile_id
    )

    if not run_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation run state not found matching provided parameters.",
        )

    # Scoping check if run belongs to another profile
    run_pid = run_state.get("profile_id")
    _verify_profile_ownership(run_pid, current_user)

    return run_state


@router.post(
    "/automation/resume",
    response_model=AutomationStatusResponse,
)
def resume_automation(
    payload: AutomationResumeRequest,
    current_user: User = Depends(get_current_user),
):
    clean_run_id = payload.run_id.strip()
    clean_action = payload.action_type.strip()

    if not clean_run_id or not clean_action:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fields 'run_id' and 'action_type' cannot be empty.",
        )

    existing = automation_service.get_automation_run_status(run_id=clean_run_id)
    if existing:
        _verify_profile_ownership(existing.get("profile_id"), current_user)

    try:
        updated_state = automation_service.resume_automation_run(
            run_id=clean_run_id,
            action_type=clean_action,
            confirmation_data=payload.confirmation_data,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )

    return updated_state


@router.get(
    "/notifications",
    response_model=NotificationListResponse,
)
def get_notifications(
    profile_id: str = Query(..., min_length=1, description="Citizen profile ID"),
    current_user: User = Depends(get_current_user),
):
    clean_profile = profile_id.strip()
    _verify_profile_ownership(clean_profile, current_user)
    notifs = notification_service.get_notifications_for_profile(clean_profile)
    return {"notifications": notifs}


@router.get("/application/{application_id}/status", response_model=ApplicationState)
def get_application_status_endpoint(
    application_id: str = Path(..., description="Run ID / Application ID"),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    state = application_state_service.get_application_state(application_id)
    if not state:
        run_state = automation_service.get_automation_run_status(run_id=application_id)
        if run_state:
            state = application_state_service.init_or_get_state(
                run_id=application_id,
                scheme_id=run_state.get("scheme_id", "SCH-HLT-001"),
                profile_id=run_state.get("profile_id", "default"),
            )
            state["current_step_index"] = run_state.get("current_step_index", 0)
            state["automation_status"] = run_state.get("automation_status", "PENDING")
            state["acknowledgment_number"] = run_state.get("acknowledgment_number")
            application_state_service._save_states()
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application state not found")

    _verify_profile_ownership(state.get("profile_id"), current_user)
    return state


@router.post("/application/{application_id}/status", response_model=ApplicationState)
def update_application_status_endpoint(
    update_req: ApplicationStatusUpdateRequest,
    application_id: str = Path(..., description="Run ID / Application ID"),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    # Ensure state exists
    state = application_state_service.get_application_state(application_id)
    if not state:
        run_state = automation_service.get_automation_run_status(run_id=application_id)
        sid = run_state.get("scheme_id", "SCH-HLT-001") if run_state else "SCH-HLT-001"
        pid = run_state.get("profile_id", "default") if run_state else "default"
        state = application_state_service.init_or_get_state(application_id, sid, pid)

    _verify_profile_ownership(state.get("profile_id"), current_user)

    # Resume the automation agent to synchronize state!
    updated_run = None
    try:
        updated_run = automation_service.resume_automation_run(
            run_id=application_id,
            action_type=update_req.action_type,
            confirmation_data={
                "portal_session_id": update_req.portal_session_id,
                "acknowledgment_number": update_req.acknowledgment_number,
            },
        )
    except Exception:
        # Ignore if the run is not found or step differs
        pass

    state = application_state_service.update_application_status(application_id, update_req.model_dump())
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application state not found")

    if updated_run:
        state["current_step_index"] = updated_run.get("current_step_index", state["current_step_index"])
        state["automation_status"] = updated_run.get("automation_status", state["automation_status"])
        if updated_run.get("acknowledgment_number"):
            state["acknowledgment_number"] = updated_run["acknowledgment_number"]
        if updated_run.get("application_status"):
            state["application_status"] = updated_run["application_status"]
        application_state_service._save_states()

    return state


@router.post("/automation/{run_id}/browser/launch")
def launch_browser_endpoint(
    run_id: str = Path(..., description="Automation run ID"),
    headless: Optional[bool] = Query(None, description="Run headless or visible"),
    current_user: User = Depends(get_current_user),
):
    existing = automation_service.get_automation_run_status(run_id=run_id)
    if existing:
        _verify_profile_ownership(existing.get("profile_id"), current_user)

    result = automation_service.launch_browser_for_run(run_id, headless=headless)
    if result.get("status") == "ERROR":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to launch browser session"),
        )
    return result


@router.get("/automation/{run_id}/browser/status")
def get_browser_status_endpoint(
    run_id: str = Path(..., description="Automation run ID"),
    current_user: User = Depends(get_current_user),
):
    existing = automation_service.get_automation_run_status(run_id=run_id)
    if existing:
        _verify_profile_ownership(existing.get("profile_id"), current_user)

    from app.services.browser_automation_service import BrowserAutomationService
    info = BrowserAutomationService.get_session_info(run_id)
    if not info:
        return {"run_id": run_id, "is_open": False, "page_state": "CLOSED"}
    return info
