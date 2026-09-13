from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.agents.document_agent.graph import run_document_agent
from app.core.dependencies import get_current_user
from app.db.models import User
from app.schemas.scheme_schema import (
    SchemeInfoRequirementsResponse,
    SchemeInfoSubmissionRequest,
    SchemeInfoSubmissionResponse,
    SchemeRequiredDocumentsResponse,
    SchemeResponse,
)
from app.services.eligibility_service import evaluate_scheme_eligibility
from app.services import document_service, profile_service, scheme_discovery_service

router = APIRouter()


def _verify_profile_ownership(profile_id: Optional[str], current_user: User):
    """Ensure that if a profile_id is provided, it belongs to the current user."""
    if not profile_id or profile_id in ("default", "anonymous"):
        return
    prof = profile_service.get_profile(profile_id)
    if prof and prof.user_id not in (current_user.id, "anonymous"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not have permission to access data for this profile.",
        )


@router.get(
    "/schemes/discover",
    response_model=List[SchemeResponse],
)
def discover_schemes(
    state: str = Query(..., min_length=1, description="State of residence"),
    sector: Optional[str] = Query(None, description="Target sector"),
    age: Optional[int] = Query(None, description="Optional citizen age override"),
    gender: Optional[str] = Query(None, description="Optional citizen gender override"),
    current_user: User = Depends(get_current_user),
):
    clean_state = state.strip()
    if not clean_state:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query parameter 'state' cannot be empty or whitespace.",
        )

    # Automatically derive demographic attributes from user's linked citizen profile if not explicitly overridden
    user_age = age
    user_gender = gender

    if user_age is None or user_gender is None:
        user_profile = profile_service.get_profile_by_user_id(current_user.id)
        if user_profile:
            if user_age is None:
                user_age = user_profile.age
            if user_gender is None:
                user_gender = user_profile.gender

    return scheme_discovery_service.discover_schemes(
        state=clean_state,
        sector=sector,
        age=user_age,
        gender=user_gender,
    )


@router.get(
    "/schemes/{scheme_id}/information-requirements",
    response_model=SchemeInfoRequirementsResponse,
)
def get_scheme_information_requirements(
    scheme_id: str,
    current_user: User = Depends(get_current_user),
):
    scheme = document_service.get_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{scheme_id}' not found.",
        )

    return {
        "scheme_id": scheme.scheme_id,
        "scheme_name": scheme.name,
        "required_info": scheme.required_info,
    }


@router.post(
    "/schemes/{scheme_id}/evaluate-eligibility",
)
def evaluate_eligibility_endpoint(
    scheme_id: str,
    payload: SchemeInfoSubmissionRequest,
    current_user: User = Depends(get_current_user),
):
    _verify_profile_ownership(payload.profile_id, current_user)
    profile_data = {}
    if payload.profile_id:
        prof = profile_service.get_profile(payload.profile_id)
        if prof:
            profile_data = prof.dict() if hasattr(prof, "dict") else dict(prof)
    return evaluate_scheme_eligibility(
        scheme_id=scheme_id,
        profile_data=profile_data,
        form_data=payload.data,
    )


@router.post(
    "/schemes/{scheme_id}/information",
    response_model=SchemeInfoSubmissionResponse,
)
def submit_scheme_information(
    scheme_id: str,
    payload: SchemeInfoSubmissionRequest,
    current_user: User = Depends(get_current_user),
):
    _verify_profile_ownership(payload.profile_id, current_user)
    # Mandatory Eligibility Evaluation
    profile_data = {}
    if payload.profile_id:
        prof = profile_service.get_profile(payload.profile_id)
        if prof:
            profile_data = prof.dict() if hasattr(prof, "dict") else dict(prof)

    eligibility_result = evaluate_scheme_eligibility(
        scheme_id=scheme_id,
        profile_data=profile_data,
        form_data=payload.data,
    )
    if not eligibility_result.get("eligible", True):
        reasons_text = "; ".join(eligibility_result.get("reasons", []))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Eligibility criteria validation failed: {reasons_text}",
        )

    try:
        submitted_data, missing_fields = document_service.validate_and_save_information(
            scheme_id=scheme_id,
            profile_id=payload.profile_id,
            data=payload.data,
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        )

    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required fields: {', '.join(missing_fields)}",
        )

    return {
        "status": "saved",
        "scheme_id": scheme_id,
        "profile_id": payload.profile_id,
        "submitted_information": submitted_data,
        "missing_information": [],
    }


@router.get(
    "/schemes/{scheme_id}/information",
)
def get_scheme_information(
    scheme_id: str,
    profile_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    _verify_profile_ownership(profile_id, current_user)
    scheme = document_service.get_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{scheme_id}' not found.",
        )
    submitted_data = document_service.get_submitted_information(scheme_id, profile_id)
    return {
        "scheme_id": scheme_id,
        "profile_id": profile_id or "default",
        "submitted_information": submitted_data,
    }


@router.get(
    "/schemes/{scheme_id}/documents/required",
    response_model=SchemeRequiredDocumentsResponse,
)
def get_scheme_required_documents(
    scheme_id: str,
    profile_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    _verify_profile_ownership(profile_id, current_user)
    scheme = document_service.get_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{scheme_id}' not found.",
        )

    submitted_info = document_service.get_submitted_information(scheme_id, profile_id)
    agent_output = run_document_agent(
        scheme_id=scheme_id, submitted_information=submitted_info
    )

    return {
        "scheme_id": scheme.scheme_id,
        "scheme_name": scheme.name,
        "required_documents": agent_output.get("required_documents", []),
    }
