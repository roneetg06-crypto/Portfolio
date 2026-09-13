import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.agents.document_agent.graph import run_document_agent
from app.models.scheme import Scheme
from app.services import profile_service
from app.services.scheme_discovery_service import load_all_schemes

# Upload configuration
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

# In-memory storage for submitted dynamic information: (profile_id, scheme_id) -> Dict[str, Any]
_submitted_info_store: Dict[Tuple[str, str], Dict[str, Any]] = {}

# In-memory storage for document records: (profile_id, scheme_id, doc_name) -> Dict[str, Any]
_documents_store: Dict[Tuple[str, str, str], Dict[str, Any]] = {}


def get_uploads_dir() -> Path:
    base_dir = Path(__file__).resolve().parent.parent.parent
    uploads_dir = base_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    return uploads_dir


def get_scheme_by_id(scheme_id: str) -> Optional[Scheme]:
    all_schemes = load_all_schemes()
    return next((s for s in all_schemes if s.scheme_id == scheme_id.strip()), None)


def validate_and_save_information(
    scheme_id: str, profile_id: Optional[str], data: Dict[str, Any]
) -> Tuple[Dict[str, Any], List[str]]:
    scheme = get_scheme_by_id(scheme_id)
    if not scheme:
        raise ValueError(f"Scheme '{scheme_id}' not found.")

    missing_fields: List[str] = []

    for field in scheme.required_info:
        val = data.get(field.name)

        if field.required:
            if val is None or (isinstance(val, str) and not val.strip()):
                missing_fields.append(field.label)
                continue
            if field.type == "checkbox" and val is not True:
                missing_fields.append(field.label)
                continue

        # Basic type checking if value is supplied
        if val is not None and val != "":
            if field.type == "number":
                try:
                    float(val)
                except (ValueError, TypeError):
                    raise ValueError(f"Field '{field.label}' must be a valid number.")

            elif field.type == "date":
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(val).strip()):
                    raise ValueError(f"Field '{field.label}' must be a valid date in YYYY-MM-DD format.")

            elif field.type in ("dropdown", "radio") and field.options:
                if str(val) not in field.options:
                    raise ValueError(f"Selected option for '{field.label}' must be one of {field.options}.")

    if missing_fields:
        return data, missing_fields

    pid = (profile_id or "default").strip()
    _submitted_info_store[(pid, scheme_id)] = data
    return data, []


def get_submitted_information(scheme_id: str, profile_id: Optional[str]) -> Dict[str, Any]:
    pid = (profile_id or "default").strip()
    return _submitted_info_store.get((pid, scheme_id), {})


def _extract_text_preview(file_path: Path, ext: str) -> str:
    """Safely extracts text preview from document without external binaries."""
    text_content = ""
    try:
        if ext == ".pdf":
            # Scan for standard text stream blocks in PDF
            with open(file_path, "rb") as f:
                content = f.read(100000)
                # Find plain text strings in PDF stream objects
                matches = re.findall(rb"\(([^\(\)]+)\)\s*Tj", content)
                if matches:
                    text_content = " ".join(
                        m.decode("latin1", errors="ignore") for m in matches
                    )
                else:
                    # Generic string extraction
                    strings = re.findall(rb"[A-Za-z0-9\s]{4,}", content)
                    text_content = " ".join(
                        s.decode("latin1", errors="ignore") for s in strings[:50]
                    )
        else:
            # Image or binary file: read byte header/strings
            with open(file_path, "rb") as f:
                content = f.read(4096)
                strings = re.findall(rb"[A-Za-z0-9\s]{4,}", content)
                text_content = " ".join(
                    s.decode("latin1", errors="ignore") for s in strings[:20]
                )
    except Exception:
        text_content = ""

    return text_content.strip()


def process_document_verification(
    doc_record: Dict[str, Any], profile_id: str
) -> Tuple[str, str]:
    """
    Evaluates uploaded document consistency.
    Non-authoritative: clearly distinguishes extracted information from official government validation.
    """
    file_path = Path(doc_record["storage_path"])
    ext = doc_record["extension"].lower()

    if not file_path.exists():
        return "INVALID", "File could not be found on storage system."

    # Validate file size
    if doc_record["size_bytes"] > MAX_FILE_SIZE_BYTES:
        return "INVALID", "File exceeds maximum size limit of 5MB."

    # Extract text preview
    extracted_text = _extract_text_preview(file_path, ext)
    profile = profile_service.get_profile(profile_id) if profile_id else None

    if profile and profile.name and extracted_text:
        # Check if citizen's name appears in extracted text
        name_parts = [p.lower() for p in profile.name.split() if len(p) > 2]
        matches = [p for p in name_parts if p in extracted_text.lower()]

        if matches:
            return (
                "VERIFIED",
                f"Information extracted: matching name '{profile.name}' found in document text. "
                "Preliminary consistency check only; not official government verification.",
            )
        else:
            return (
                "MANUAL_VERIFICATION_REQUIRED",
                "Text extracted but citizen name was not automatically identified. "
                "Marked for human review. Note: Not official government verification.",
            )

    # Standard fallback for valid image/PDF where automated OCR is unavailable
    return (
        "MANUAL_VERIFICATION_REQUIRED",
        "Document uploaded and format verified. Automated OCR engine is unavailable on this host system — "
        "marked for manual officer verification. Note: Not official government verification.",
    )


def save_and_verify_document(
    file_bytes: bytes,
    original_filename: str,
    document_name: str,
    scheme_id: str,
    profile_id: str,
) -> Dict[str, Any]:
    # 1. Validate file extension
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    # 2. Validate file size
    size_bytes = len(file_bytes)
    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File size exceeds maximum permitted limit of 5MB.")

    if size_bytes == 0:
        raise ValueError("Cannot upload an empty file.")

    # 3. Store file with sanitized UUID filename outside web root
    uploads_dir = get_uploads_dir()
    safe_filename = f"{uuid.uuid4()}{ext}"
    target_path = uploads_dir / safe_filename

    with open(target_path, "wb") as f:
        f.write(file_bytes)

    doc_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    doc_record = {
        "document_id": doc_id,
        "document_name": document_name.strip(),
        "original_filename": Path(original_filename).name,
        "storage_path": str(target_path),
        "extension": ext,
        "size_bytes": size_bytes,
        "scheme_id": scheme_id.strip(),
        "profile_id": (profile_id or "default").strip(),
        "uploaded_at": now_iso,
    }

    # 4. Perform document verification
    status, message = process_document_verification(doc_record, profile_id)
    doc_record["status"] = status
    doc_record["verification_message"] = message

    # 5. Persist record in memory store
    key = ((profile_id or "default").strip(), scheme_id.strip(), document_name.strip())
    _documents_store[key] = doc_record

    return doc_record


def get_all_document_statuses(
    scheme_id: str, profile_id: Optional[str]
) -> Dict[str, Any]:
    pid = (profile_id or "default").strip()

    # Determine required documents from Document Agent LangGraph node
    submitted_info = get_submitted_information(scheme_id, profile_id)
    agent_output = run_document_agent(
        scheme_id=scheme_id,
        submitted_information=submitted_info,
    )
    required_docs = agent_output.get("required_documents", [])

    results: List[Dict[str, Any]] = []

    for req in required_docs:
        doc_name = req["name"]
        key = (pid, scheme_id, doc_name)
        record = _documents_store.get(key)

        if record:
            results.append({
                "name": doc_name,
                "label": req["label"],
                "required": req["required"],
                "status": record["status"],
                "verification_message": record["verification_message"],
                "document_id": record["document_id"],
                "uploaded_at": record["uploaded_at"],
                "original_filename": record["original_filename"],
                "storage_path": record.get("storage_path"),
                "size_bytes": record["size_bytes"],
            })
        else:
            results.append({
                "name": doc_name,
                "label": req["label"],
                "required": req["required"],
                "status": "MISSING",
                "verification_message": "Document has not been uploaded yet.",
                "document_id": None,
                "uploaded_at": None,
                "original_filename": None,
                "storage_path": None,
                "size_bytes": None,
            })

    return {
        "scheme_id": scheme_id,
        "profile_id": pid,
        "documents": results,
    }


def clear_document_store_for_testing():
    """Helper for resetting test data between unit test runs."""
    _submitted_info_store.clear()
    _documents_store.clear()
