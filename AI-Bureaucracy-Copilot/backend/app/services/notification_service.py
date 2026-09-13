import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Set

_notifications_store: Dict[str, List[Dict[str, Any]]] = {}
_subscribers: Dict[str, Set[asyncio.Queue]] = {}


def send_notification(
    profile_id: str,
    scheme_id: str,
    action_type: str,
    message: str,
    portal_url: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    pid = profile_id.strip() if profile_id else "default"
    notification_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    notif = {
        "notification_id": notification_id,
        "profile_id": pid,
        "scheme_id": scheme_id,
        "run_id": run_id,
        "action_type": action_type,
        "message": message,
        "portal_url": portal_url or f"https://mock-portal.gov.in/schemes/{scheme_id}",
        "status": "ACTION_REQUIRED",
        "created_at": now_iso,
    }

    if pid not in _notifications_store:
        _notifications_store[pid] = []

    _notifications_store[pid].append(notif)

    # Broadcast to active SSE subscribers
    targets = set()
    if pid in _subscribers:
        targets.update(_subscribers[pid])
    if "*" in _subscribers:
        targets.update(_subscribers["*"])

    for q in targets:
        try:
            q.put_nowait(notif)
        except Exception:
            pass

    return notif


def add_subscriber(profile_id: str) -> asyncio.Queue:
    pid = profile_id.strip() if profile_id else "default"
    q: asyncio.Queue = asyncio.Queue()
    if pid not in _subscribers:
        _subscribers[pid] = set()
    _subscribers[pid].add(q)
    return q


def remove_subscriber(profile_id: str, q: asyncio.Queue) -> None:
    pid = profile_id.strip() if profile_id else "default"
    if pid in _subscribers and q in _subscribers[pid]:
        _subscribers[pid].remove(q)
        if not _subscribers[pid]:
            del _subscribers[pid]


async def subscribe_notifications(profile_id: str) -> AsyncGenerator[Dict[str, Any], None]:
    pid = profile_id.strip() if profile_id else "default"
    q = add_subscriber(pid)
    try:
        while True:
            notif = await q.get()
            yield notif
    finally:
        remove_subscriber(pid, q)


def get_notifications_for_profile(profile_id: str) -> List[Dict[str, Any]]:
    pid = profile_id.strip() if profile_id else "default"
    return _notifications_store.get(pid, [])


def mark_notification_resolved(profile_id: str, notification_id: str) -> bool:
    pid = profile_id.strip() if profile_id else "default"
    user_notifs = _notifications_store.get(pid, [])

    for notif in user_notifs:
        if notif["notification_id"] == notification_id:
            notif["status"] = "RESOLVED"
            return True
    return False


def resolve_notifications_by_action(profile_id: str, run_id: str, action_type: str) -> bool:
    pid = profile_id.strip() if profile_id else "default"
    user_notifs = _notifications_store.get(pid, [])
    resolved = False

    for notif in user_notifs:
        if notif.get("run_id") == run_id and notif.get("action_type") == action_type:
            notif["status"] = "RESOLVED"
            resolved = True

    return resolved


def clear_notifications_for_testing():
    _notifications_store.clear()
    _subscribers.clear()

