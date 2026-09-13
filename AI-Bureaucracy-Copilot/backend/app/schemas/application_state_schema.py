from typing import Any, Dict, Optional
from pydantic import BaseModel

class ApplicationState(BaseModel):
    run_id: str
    scheme_id: str
    profile_id: str
    automation_status: str
    application_status: str
    current_step_index: int
    portal_session_id: Optional[str] = None
    acknowledgment_number: Optional[str] = None
    last_completed_action: Optional[str] = None
    last_updated: str

class ApplicationStatusUpdateRequest(BaseModel):
    action_type: str
    status: str
    portal_session_id: Optional[str] = None
    acknowledgment_number: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
