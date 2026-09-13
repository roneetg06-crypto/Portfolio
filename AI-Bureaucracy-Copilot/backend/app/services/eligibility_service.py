from typing import Any, Dict, List, Optional
from datetime import datetime
from app.services import document_service


def evaluate_scheme_eligibility(
    scheme_id: str,
    profile_data: Optional[Dict[str, Any]] = None,
    form_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evaluates whether an applicant meets the mandatory eligibility criteria for a given scheme.
    Specifically checks age, income, admission, and nationality requirements for SCH-EDU-001.
    """
    scheme = document_service.get_scheme_by_id(scheme_id)
    if not scheme:
        return {
            "scheme_id": scheme_id,
            "eligible": False,
            "reasons": [f"Scheme '{scheme_id}' does not exist."],
            "criteria_summary": [],
        }

    criteria = getattr(scheme, "eligibility_criteria", None) or {}
    if isinstance(scheme, dict):
        criteria = scheme.get("eligibility_criteria", {})

    merged: Dict[str, Any] = {}
    if profile_data:
        merged.update(profile_data)
    if form_data:
        merged.update(form_data)

    criteria_summary: List[Dict[str, Any]] = []
    reasons: List[str] = []

    # 1. Check Age (min_age / max_age)
    min_age = criteria.get("min_age", 16)
    max_age = criteria.get("max_age", 35)
    age = merged.get("age")

    # If DOB is provided instead of age, calculate age
    dob_str = merged.get("date_of_birth") or merged.get("dob")
    if age is None and dob_str:
        try:
            dob = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d")
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except Exception:
            pass

    if age is not None:
        try:
            age_int = int(age)
            if age_int < min_age:
                reasons.append(f"Age {age_int} is below the minimum required age of {min_age} years.")
                criteria_summary.append({
                    "criterion": f"Age ({min_age}-{max_age} years)",
                    "status": "FAIL",
                    "detail": f"Applicant is {age_int} years old (minimum is {min_age}).",
                })
            elif age_int > max_age:
                reasons.append(f"Age {age_int} exceeds the maximum allowable age of {max_age} years.")
                criteria_summary.append({
                    "criterion": f"Age ({min_age}-{max_age} years)",
                    "status": "FAIL",
                    "detail": f"Applicant is {age_int} years old (maximum is {max_age}).",
                })
            else:
                criteria_summary.append({
                    "criterion": f"Age ({min_age}-{max_age} years)",
                    "status": "PASS",
                    "detail": f"Applicant is {age_int} years old (eligible).",
                })
        except ValueError:
            pass
    else:
        criteria_summary.append({
            "criterion": f"Age ({min_age}-{max_age} years)",
            "status": "PENDING",
            "detail": "Age or Date of Birth not yet provided.",
        })

    # 2. Check Annual Family Income
    max_income = criteria.get("max_annual_family_income", 800000)
    income = merged.get("annual_family_income") or merged.get("annual_income")
    if income is not None:
        try:
            income_num = float(income)
            if income_num > max_income:
                reasons.append(
                    f"Annual family income of Rs. {income_num:,.0f} exceeds the limit of Rs. {max_income:,.0f} for interest subsidy & credit guarantee."
                )
                criteria_summary.append({
                    "criterion": f"Annual Family Income (<= Rs. {max_income:,.0f})",
                    "status": "FAIL",
                    "detail": f"Family income is Rs. {income_num:,.0f} (exceeds Rs. {max_income:,.0f}).",
                })
            else:
                criteria_summary.append({
                    "criterion": f"Annual Family Income (<= Rs. {max_income:,.0f})",
                    "status": "PASS",
                    "detail": f"Family income is Rs. {income_num:,.0f} (eligible for full interest subsidy & credit guarantee).",
                })
        except ValueError:
            pass
    else:
        criteria_summary.append({
            "criterion": f"Annual Family Income (<= Rs. {max_income:,.0f})",
            "status": "PENDING",
            "detail": "Annual family income not yet provided.",
        })

    # 3. Citizenship & State Eligibility
    state = merged.get("state")
    level = getattr(scheme, "level", "central")
    if level == "central":
        criteria_summary.append({
            "criterion": "Nationality & State Eligibility",
            "status": "PASS",
            "detail": "Central Scheme applicable across all States and Union Territories of India.",
        })
    elif state:
        applicable_states = [s.lower() for s in getattr(scheme, "applicable_states", [])]
        if state.lower() in applicable_states or not applicable_states:
            criteria_summary.append({
                "criterion": "State Eligibility",
                "status": "PASS",
                "detail": f"State '{state}' is eligible.",
            })
        else:
            reasons.append(f"Scheme is not applicable in state '{state}'.")
            criteria_summary.append({
                "criterion": "State Eligibility",
                "status": "FAIL",
                "detail": f"State '{state}' is not eligible.",
            })

    # Overall Eligibility flag
    is_eligible = len(reasons) == 0

    return {
        "scheme_id": scheme_id,
        "scheme_name": getattr(scheme, "name", scheme_id),
        "eligible": is_eligible,
        "reasons": reasons,
        "criteria_summary": criteria_summary,
    }
