from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from app.core.dependencies import get_current_user
from app.db.models import User
from app.services import document_service, profile_service

router = APIRouter()


def _verify_profile_ownership(profile_id: Optional[str], current_user: User):
    if not profile_id or profile_id in ("default", "anonymous"):
        return
    prof = profile_service.get_profile(profile_id)
    if prof and prof.user_id not in (current_user.id, "anonymous"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not have permission to access documents for this profile.",
        )


@router.post("/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_name: str = Form(..., description="Document type identifier"),
    scheme_id: str = Form(..., description="Target scheme identifier"),
    profile_id: Optional[str] = Form(None, description="Citizen profile ID"),
    current_user: User = Depends(get_current_user),
):
    _verify_profile_ownership(profile_id, current_user)
    clean_doc_name = document_name.strip()
    clean_scheme_id = scheme_id.strip()

    if not clean_doc_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Field 'document_name' cannot be empty.",
        )
    if not clean_scheme_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Field 'scheme_id' cannot be empty.",
        )

    # Read uploaded file content
    try:
        file_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(exc)}",
        )

    try:
        record = document_service.save_and_verify_document(
            file_bytes=file_bytes,
            original_filename=file.filename or "uploaded_file",
            document_name=clean_doc_name,
            scheme_id=clean_scheme_id,
            profile_id=profile_id or "default",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )

    return {
        "status": "success",
        "document_id": record["document_id"],
        "document_name": record["document_name"],
        "original_filename": record["original_filename"],
        "verification_status": record["status"],
        "verification_message": record["verification_message"],
        "size_bytes": record["size_bytes"],
        "uploaded_at": record["uploaded_at"],
    }


@router.get("/documents/status")
def get_documents_status(
    scheme_id: str = Query(..., description="Scheme identifier"),
    profile_id: Optional[str] = Query(None, description="Citizen profile ID"),
    current_user: User = Depends(get_current_user),
):
    _verify_profile_ownership(profile_id, current_user)
    clean_scheme_id = scheme_id.strip()
    if not clean_scheme_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query parameter 'scheme_id' cannot be empty.",
        )

    return document_service.get_all_document_statuses(
        scheme_id=clean_scheme_id, profile_id=profile_id
    )
