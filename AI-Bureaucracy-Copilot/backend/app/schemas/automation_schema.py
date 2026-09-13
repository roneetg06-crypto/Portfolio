from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AutomationStartRequest(BaseModel):
    scheme_id: str
    profile_id: str


class PlannedStepItem(BaseModel):
    step_id: str
    name: str
    type: str  # human_action | auto
    action_type: Optional[str] = None
    status: str  # pending | completed
    description: Optional[str] = None


class HumanActionRequiredDetail(BaseModel):
    action_type: str
    step_id: str
    step_name: Optional[str] = None
    message: str
    portal_url: Optional[str] = None


class AutomationStatusResponse(BaseModel):
    run_id: str
    scheme_id: str
    profile_id: str
    automation_status: str
    application_status: str
    current_step_index: int
    planned_steps: List[PlannedStepItem]
    human_action_required: Optional[HumanActionRequiredDetail] = None
    mapped_form_data: Optional[Dict[str, Any]] = None
    portal_session_id: Optional[str] = None
    acknowledgment_number: Optional[str] = None


class AutomationResumeRequest(BaseModel):
    run_id: str
    action_type: str
    confirmation_data: Optional[Dict[str, Any]] = None


class NotificationItem(BaseModel):
    notification_id: str
    profile_id: str
    scheme_id: str
    run_id: Optional[str] = None
    action_type: str
    message: str
    portal_url: Optional[str] = None
    status: str
    created_at: str


class NotificationListResponse(BaseModel):
    notifications: List[NotificationItem]
