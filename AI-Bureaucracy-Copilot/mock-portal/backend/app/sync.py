import json
import logging
import urllib.request
from typing import Any, Dict, Optional

logger = logging.getLogger("mock_portal.sync")

MAIN_BACKEND_URL = "http://localhost:8000"


def notify_main_portal(
    run_id: Optional[str],
    action_type: str,
    status: str,
    portal_session_id: Optional[str] = None,
    acknowledgment_number: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """Send state synchronization event to the Main AI Bureaucracy Copilot backend."""
    if not run_id or not run_id.strip():
        return False

    payload = {
        "action_type": action_type,
        "status": status,
        "portal_session_id": portal_session_id,
        "acknowledgment_number": acknowledgment_number,
        "metadata": metadata or {},
    }

    url = f"{MAIN_BACKEND_URL}/api/application/{run_id.strip()}/status"
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            logger.info(
                f"[SYNC] Notified main backend for run '{run_id}', action '{action_type}': {resp.status}"
            )
            return resp.status in (200, 201)
    except Exception as e:
        logger.warning(
            f"[SYNC] Could not notify main backend for run '{run_id}': {e}"
        )
        return False
