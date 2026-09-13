import uuid
from typing import Dict, Optional
from app.models.citizen_profile import CitizenProfile
from app.schemas.citizen_profile_schema import CitizenProfileCreate

_profiles_db: Dict[str, CitizenProfile] = {}


def create_profile(payload: CitizenProfileCreate, user_id: str = "anonymous") -> CitizenProfile:
    profile_id = str(uuid.uuid4())
    profile = CitizenProfile(
        profile_id=profile_id,
        name=payload.name,
        age=payload.age,
        gender=payload.gender,
        state=payload.state,
        district=payload.district,
        user_id=user_id,
    )
    _profiles_db[profile_id] = profile
    return profile


def get_profile(profile_id: str) -> Optional[CitizenProfile]:
    return _profiles_db.get(profile_id)


def get_profile_by_user_id(user_id: str) -> Optional[CitizenProfile]:
    """Retrieve profile associated with a specific user_id."""
    for profile in _profiles_db.values():
        if profile.user_id == user_id:
            return profile
    return None


def clear_profiles_for_testing():
    """Reset in-memory profile storage for unit tests."""
    _profiles_db.clear()
