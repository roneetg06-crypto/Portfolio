import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.schemas.application_state_schema import ApplicationState

_STATE_FILE = "data/application_states.json"
_states_store: Dict[str, Dict[str, Any]] = {}

def _load_states():
    global _states_store
    if os.path.exists(_STATE_FILE):
        try:
            with open(_STATE_FILE, "r") as f:
                _states_store = json.load(f)
        except Exception:
            _states_store = {}

def _save_states():
    os.makedirs(os.path.dirname(_STATE_FILE), exist_ok=True)
    with open(_STATE_FILE, "w") as f:
        json.dump(_states_store, f, indent=2)

_load_states()

def init_or_get_state(run_id: str, scheme_id: str, profile_id: str) -> Dict[str, Any]:
    if run_id not in _states_store:
        _states_store[run_id] = {
            "run_id": run_id,
            "scheme_id": scheme_id,
            "profile_id": profile_id,
            "automation_status": "in_progress",
            "application_status": "draft",
            "current_step_index": 0,
            "portal_session_id": None,
            "acknowledgment_number": None,
            "last_completed_action": None,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        _save_states()
    return _states_store[run_id]

def get_application_state(run_id: str) -> Optional[Dict[str, Any]]:
    return _states_store.get(run_id)

def get_latest_state(profile_id: str, scheme_id: str) -> Optional[Dict[str, Any]]:
    latest = None
    for state in _states_store.values():
        if state["profile_id"] == profile_id and state["scheme_id"] == scheme_id:
            if latest is None or state["last_updated"] > latest["last_updated"]:
                latest = state
    return latest

def update_application_status(run_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if run_id in _states_store:
        state = _states_store[run_id]
        if "status" in update_data:
            state["application_status"] = update_data["status"]
        if "action_type" in update_data:
            state["last_completed_action"] = update_data["action_type"]
        if "portal_session_id" in update_data and update_data["portal_session_id"]:
            state["portal_session_id"] = update_data["portal_session_id"]
        if "acknowledgment_number" in update_data and update_data["acknowledgment_number"]:
            state["acknowledgment_number"] = update_data["acknowledgment_number"]
            state["application_status"] = "submitted"
            state["automation_status"] = "completed"
        
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        _save_states()
        return state
    return None

def clear_states_for_testing():
    global _states_store
    _states_store.clear()
    if os.path.exists(_STATE_FILE):
        try:
            os.remove(_STATE_FILE)
        except Exception:
            pass

