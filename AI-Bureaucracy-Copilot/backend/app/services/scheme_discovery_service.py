import json
from pathlib import Path
from typing import List, Optional
from app.models.scheme import Scheme


def load_all_schemes() -> List[Scheme]:
    base_dir = Path(__file__).resolve().parent.parent.parent
    schemes_file = base_dir / "data" / "sample" / "schemes.json"

    if not schemes_file.exists():
        raise FileNotFoundError(f"Scheme dataset not found at {schemes_file}")

    with open(schemes_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [Scheme(**item) for item in data]


def discover_schemes(
    state: str,
    sector: Optional[str] = None,
    age: Optional[int] = None,
    gender: Optional[str] = None,
) -> List[Scheme]:
    """
    Deterministic, rule-based scheme discovery.
    Filters schemes by state (central vs state-specific), sector,
    and citizen demographic profile (age and gender).
    """
    all_schemes = load_all_schemes()
    target_state = state.strip().lower()
    target_sector = sector.strip().lower() if sector and sector.strip().lower() != "all" else None
    target_gender = gender.strip().lower() if gender and gender.strip() else None

    matching_schemes: List[Scheme] = []

    for scheme in all_schemes:
        # 1. Sector filtering
        if target_sector and scheme.sector.strip().lower() != target_sector:
            continue

        # 2. State & Jurisdiction level filtering
        scheme_level = scheme.level.strip().lower()
        if scheme_level == "central":
            state_match = True
        elif scheme_level == "state":
            applicable = [s.strip().lower() for s in scheme.applicable_states]
            state_match = target_state in applicable
        else:
            state_match = False

        if not state_match:
            continue

        # 3. Demographic: Gender filtering
        scheme_gender = scheme.applicable_gender.strip().lower() if hasattr(scheme, "applicable_gender") and scheme.applicable_gender else "all"
        if scheme_gender != "all" and target_gender:
            if scheme_gender != target_gender:
                continue

        # 4. Demographic: Age range filtering
        if age is not None:
            min_age = getattr(scheme, "applicable_age_min", 0)
            max_age = getattr(scheme, "applicable_age_max", 120)
            if not (min_age <= age <= max_age):
                continue

        matching_schemes.append(scheme)

    return matching_schemes
