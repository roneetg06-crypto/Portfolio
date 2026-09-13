import os
import uuid
from typing import Any, Dict, List, Optional

from app.agents.automation_agent.graph import run_automation_agent, resume_automation_agent
from app.services import document_service, notification_service, profile_service

_automation_runs_store: Dict[str, Dict[str, Any]] = {}


def start_automation_run(scheme_id: str, profile_id: str) -> Dict[str, Any]:
    pid = profile_id.strip() if profile_id else "default"
    sid = scheme_id.strip()

    # Retrieve citizen profile data
    profile_obj = profile_service.get_profile(pid)
    user_profile = (
        profile_obj.model_dump() if profile_obj else {"name": "Citizen", "state": "General"}
    )

    # Retrieve submitted dynamic info & uploaded documents status
    submitted_info = document_service.get_submitted_information(sid, pid)
    doc_status = document_service.get_all_document_statuses(sid, pid)
    uploaded_docs = doc_status.get("documents", [])

    run_id = str(uuid.uuid4())

    # Execute Automation Agent planning
    agent_state = run_automation_agent(
        run_id=run_id,
        scheme_id=sid,
        profile_id=pid,
        user_profile=user_profile,
        submitted_information=submitted_info,
        uploaded_documents=uploaded_docs,
        document_verification={"status": "CHECKED"},
    )

    # If human action is required at the first step, trigger notification
    human_req = agent_state.get("human_action_required")
    if human_req:
        notification_service.send_notification(
            profile_id=pid,
            scheme_id=sid,
            action_type=human_req["action_type"],
            message=human_req["message"],
            portal_url=human_req.get("portal_url"),
            run_id=run_id,
        )

    _automation_runs_store[run_id] = agent_state

    # Auto-launch Playwright browser session for interactive demo
    if os.environ.get("AUTO_LAUNCH_BROWSER", "true").lower() in ("true", "1", "yes"):
        try:
            from app.services.browser_automation_service import BrowserAutomationService, DEFAULT_HEADLESS
            if BrowserAutomationService.is_available():
                launch_browser_for_run(run_id=run_id, headless=DEFAULT_HEADLESS)
        except Exception as e:
            logger.debug(f"[AUTOMATION] Browser launch notice: {e}")

    return agent_state


def get_automation_run_status(
    run_id: Optional[str] = None,
    scheme_id: Optional[str] = None,
    profile_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    if run_id and run_id.strip() in _automation_runs_store:
        return _automation_runs_store[run_id.strip()]

    # Find latest run matching (scheme_id, profile_id)
    if scheme_id and profile_id:
        pid = profile_id.strip()
        sid = scheme_id.strip()
        matching = [
            run
            for run in _automation_runs_store.values()
            if run.get("scheme_id") == sid and run.get("profile_id") == pid
        ]
        if matching:
            return matching[-1]

    return None


def resume_automation_run(
    run_id: str, action_type: str, confirmation_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    rid = run_id.strip()
    if rid not in _automation_runs_store:
        raise ValueError(f"Automation run '{rid}' not found.")

    state = _automation_runs_store[rid]

    # Resolve notification for this step
    notification_service.resolve_notifications_by_action(
        profile_id=state.get("profile_id", "default"),
        run_id=rid,
        action_type=action_type,
    )

    # Resume Agent graph
    updated_state = resume_automation_agent(state, action_type, confirmation_data)

    # Check if next step also requires human action
    human_req = updated_state.get("human_action_required")
    if human_req and updated_state.get("automation_status") == "AWAITING_HUMAN_ACTION":
        notification_service.send_notification(
            profile_id=state.get("profile_id", "default"),
            scheme_id=state.get("scheme_id", ""),
            action_type=human_req["action_type"],
            message=human_req["message"],
            portal_url=human_req.get("portal_url"),
            run_id=rid,
        )

    _automation_runs_store[rid] = updated_state
    return updated_state


def launch_browser_for_run(run_id: str, headless: Optional[bool] = None) -> Dict[str, Any]:
    from app.services.browser_automation_service import BrowserAutomationService
    state = get_automation_run_status(run_id=run_id)
    if not state:
        return {"status": "ERROR", "error": f"Run '{run_id}' not found", "page_state": "ERROR"}
    sid = state.get("scheme_id", "SCH-HLT-001")
    pid = state.get("profile_id", "default")
    human_req = state.get("human_action_required")
    portal_url = human_req.get("portal_url") if human_req else None
    return BrowserAutomationService.start_session(
        run_id=run_id,
        scheme_id=sid,
        profile_id=pid,
        portal_url=portal_url,
        headless=headless,
    )


def clear_automation_runs_for_testing():
    from app.services.browser_automation_service import BrowserAutomationService
    BrowserAutomationService.close_all_sessions()
    _automation_runs_store.clear()

