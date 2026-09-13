from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.db.models import User
from app.schemas.citizen_profile_schema import (
    CitizenProfileCreate,
    CitizenProfileResponse,
)
from app.services import profile_service

router = APIRouter()


@router.post(
    "/profile",
    response_model=CitizenProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_citizen_profile(
    payload: CitizenProfileCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a citizen profile linked to the authenticated user."""
    profile = profile_service.create_profile(payload, user_id=current_user.id)
    return profile


@router.get(
    "/profile/me",
    response_model=CitizenProfileResponse,
)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Retrieve profile of the currently logged in user."""
    profile = profile_service.get_profile_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found for this user.",
        )
    return profile


@router.get(
    "/profile/{profile_id}",
    response_model=CitizenProfileResponse,
)
def get_citizen_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
):
    """Retrieve citizen profile, ensuring it belongs to the authenticated user."""
    profile = profile_service.get_profile(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with ID '{profile_id}' not found.",
        )

    # Scoping check: users can only view their own profile (or unassigned/test profiles)
    if profile.user_id not in (current_user.id, "anonymous"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: this profile belongs to another citizen.",
        )

    return profile
