from typing import Any, Dict, List, Optional, TypedDict


class AutomationWorkflowState(TypedDict):
    run_id: str
    scheme_id: str
    profile_id: str
    user_profile: Dict[str, Any]
    submitted_information: Dict[str, Any]
    uploaded_documents: List[Dict[str, Any]]
    document_verification: Dict[str, Any]
    planned_steps: List[Dict[str, Any]]
    current_step_index: int
    automation_status: str  # NOT_STARTED | PLANNING | IN_PROGRESS | AWAITING_HUMAN_ACTION | PAUSED | COMPLETED | FAILED
    human_action_required: Optional[Dict[str, Any]]
    application_status: str  # DRAFT | PENDING_CITIZEN_ACTION | SUBMITTED
    mapped_form_data: Optional[Dict[str, Any]]
    portal_session_id: Optional[str]
    acknowledgment_number: Optional[str]
