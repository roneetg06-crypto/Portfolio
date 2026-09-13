import re
from typing import Any, Dict, List, Optional

# Controlled, immutable action mapping to official PM-KISAN government pages.
# LLMs must NOT invent or alter these URLs.
PM_KISAN_ACTION_ROUTES: Dict[str, Dict[str, Any]] = {
    "new_farmer_registration": {
        "action": "new_farmer_registration",
        "action_title": "PM-KISAN New Farmer Registration",
        "action_url": "https://pmkisan.gov.in/RegistrationFormnew.aspx",
        "description": "Official self-registration portal for eligible landholding farmer families.",
        "requires_human_verification": True,
    },
    "beneficiary_status": {
        "action": "beneficiary_status",
        "action_title": "Check PM-KISAN Beneficiary Status",
        "action_url": "https://pmkisan.gov.in/BeneficiaryStatus_New.aspx",
        "description": "Check installment payment status and DBT account transfer details.",
        "requires_human_verification": True,
    },
    "self_registered_farmer_status": {
        "action": "self_registered_farmer_status",
        "action_title": "Status of Self Registered Farmer",
        "action_url": "https://pmkisan.gov.in/FarmerStatus.aspx",
        "description": "Track approval and verification status of self-registration application via Aadhaar.",
        "requires_human_verification": True,
    },
}


def detect_pmkisan_action(
    question: str,
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
    explicit_scheme_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Deterministically detects if a user question contains an actionable PM-KISAN intent
    and returns the corresponding controlled action route object.
    
    Returns None for purely informational questions (e.g. "What is PM-KISAN?",
    "How much benefit does PM-KISAN provide?").
    """
    if not question:
        return None

    q_lower = question.lower().strip()

    # Check if context belongs to PM-KISAN or general farming
    is_pmkisan_context = (
        explicit_scheme_id == "PM-KISAN"
        or "pm-kisan" in q_lower
        or "pm kisan" in q_lower
        or "pmkisan" in q_lower
        or "farmer" in q_lower
        or "kisan" in q_lower
    )

    if not is_pmkisan_context and retrieved_chunks:
        # Check if retrieved chunks predominantly represent PM-KISAN
        pmkisan_count = sum(
            1 for c in retrieved_chunks
            if c.get("metadata", {}).get("scheme_id") == "PM-KISAN"
        )
        if pmkisan_count > 0 and pmkisan_count >= len(retrieved_chunks) / 2:
            is_pmkisan_context = True

    if not is_pmkisan_context:
        return None

    # Informational question patterns that should NOT trigger action routing
    informational_patterns = [
        r"^what is\b",
        r"^what are\b",
        r"^tell me about\b",
        r"^how much\b",
        r"^explain\b",
        r"\bwho is eligible\b",
        r"\beligibility criteria\b",
        r"\bbenefits\b",
        r"\bobjective\b",
    ]

    # Explicit check: If question is purely "what is pm-kisan" or "how much benefit...", return None
    is_purely_informational = any(re.search(pat, q_lower) for pat in informational_patterns)
    has_status_keyword = any(k in q_lower for k in ("status", "track", "check my", "installment status", "payment status"))
    has_register_keyword = any(k in q_lower for k in ("register", "registration", "apply", "enroll", "sign up"))

    if is_purely_informational and not (has_status_keyword or has_register_keyword):
        return None

    # 1. Self-registered farmer status check
    if any(k in q_lower for k in ("self registered", "self-registered", "csc farmer", "application status")):
        route = PM_KISAN_ACTION_ROUTES["self_registered_farmer_status"]
        return {
            "scheme_id": "PM-KISAN",
            "action": route["action"],
            "action_url": route["action_url"],
            "action_title": route["action_title"],
            "requires_human_verification": route["requires_human_verification"],
        }

    # 2. Beneficiary status check
    if has_status_keyword or "beneficiary status" in q_lower or "know your status" in q_lower:
        route = PM_KISAN_ACTION_ROUTES["beneficiary_status"]
        return {
            "scheme_id": "PM-KISAN",
            "action": route["action"],
            "action_url": route["action_url"],
            "action_title": route["action_title"],
            "requires_human_verification": route["requires_human_verification"],
        }

    # 3. New Farmer Registration
    if (
        "register" in q_lower
        or "registration" in q_lower
        or "apply as a farmer" in q_lower
        or "apply as farmer" in q_lower
        or "enroll as a farmer" in q_lower
        or "enroll as farmer" in q_lower
        or ("apply" in q_lower and ("kisan" in q_lower or "farmer" in q_lower))
    ):
        route = PM_KISAN_ACTION_ROUTES["new_farmer_registration"]
        return {
            "scheme_id": "PM-KISAN",
            "action": route["action"],
            "action_url": route["action_url"],
            "action_title": route["action_title"],
            "requires_human_verification": route["requires_human_verification"],
        }

    return None
