import json
import random
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from app.api.auth import get_session_or_404

router = APIRouter()


class SchemeApplicationPayload(BaseModel):
    session_id: str
    scheme_id: str = "SCH-EDU-001"
    applicant_name: Optional[str] = "Priya Sharma"
    student_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = 21
    gender: Optional[str] = "Female"
    state: Optional[str] = "Andhra Pradesh"
    district: Optional[str] = "Visakhapatnam"
    category: Optional[str] = "OBC"
    parent_name: Optional[str] = None
    parent_occupation: Optional[str] = None
    annual_family_income: Optional[float] = None
    annual_income: Optional[float] = None
    aadhaar_last_four: Optional[str] = "5821"
    course: Optional[str] = None
    college: Optional[str] = None
    loan_amount: Optional[float] = None
    tuition_fee: Optional[float] = None
    living_expenses: Optional[float] = None
    bank_preference: Optional[str] = None
    loan_tenure: Optional[str] = None
    documents: Optional[Dict[str, Any]] = None
    uploaded_documents: Optional[Dict[str, Any]] = None
    declaration_agreed: bool = False
    run_id: Optional[str] = None


class ApplicationMilestonePayload(BaseModel):
    session_id: str
    milestone: str  # STUDENT_INFO_COMPLETED | LOAN_INFO_COMPLETED | DOCUMENTS_UPLOADED | FINAL_REVIEW_REQUIRED | APPLICATION_SUBMITTED
    run_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ApplicationSubmitResponse(BaseModel):
    status: str
    acknowledgment_number: str
    session_id: str
    scheme_id: str
    applicant_name: str
    student_name: Optional[str] = None
    submitted_at: str
    message: str
    run_id: Optional[str] = None


@router.get("/application/prefill")
def get_application_prefill(
    run_id: Optional[str] = Query(None, description="Copilot automation run ID"),
    profile_id: Optional[str] = Query(None, description="Citizen profile ID"),
    scheme_id: Optional[str] = Query(None, description="Selected scheme ID"),
):
    """Retrieve prefilled citizen application attributes from Copilot Phase 2/4/5B."""
    sid_target = scheme_id or "SCH-EDU-001"
    result = {
        "scheme_id": sid_target,
        "student_name": "Priya Sharma",
        "applicant_name": "Priya Sharma",
        "date_of_birth": "2003-05-15",
        "age": 21,
        "gender": "Female",
        "state": "Andhra Pradesh",
        "district": "Visakhapatnam",
        "category": "OBC",
        "parent_name": "Ramesh Sharma",
        "parent_occupation": "Salaried / Private",
        "annual_family_income": 350000.0,
        "annual_income": 350000.0,
        "aadhaar_last_four": "5821",
        "course": "B.Tech Computer Science and Engineering",
        "college": "National Institute of Technology",
        "loan_amount": 750000.0,
        "tuition_fee": 500000.0,
        "living_expenses": 250000.0,
        "bank_preference": "State Bank of India",
        "loan_tenure": "10 Years",
        "documents": {
            "admission_letter": "NIT_Admission_Offer_Letter.pdf",
            "fee_structure": "Academic_Fee_Structure_2026.pdf",
            "student_aadhaar": "Student_Aadhaar_Card.pdf",
            "parent_income_certificate": "Revenue_Income_Certificate.pdf",
        },
        "source": "mock_default",
    }

    resolved_pid = profile_id.strip() if profile_id else None
    resolved_sid = sid_target

    if run_id:
        try:
            url = f"http://localhost:8000/api/automation/status?run_id={run_id.strip()}"
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    status_data = json.loads(resp.read().decode())
                    resolved_sid = status_data.get("scheme_id") or resolved_sid
                    resolved_pid = status_data.get("profile_id") or resolved_pid
                    mapped = status_data.get("mapped_form_data")
                    if mapped:
                        st_name = mapped.get("student_name") or mapped.get("applicant_name") or result["student_name"]
                        result.update({
                            "scheme_id": resolved_sid,
                            "student_name": st_name,
                            "applicant_name": st_name,
                            "date_of_birth": mapped.get("date_of_birth") or result["date_of_birth"],
                            "age": mapped.get("age") or result["age"],
                            "gender": mapped.get("gender") or result["gender"],
                            "state": mapped.get("state") or result["state"],
                            "district": mapped.get("district") or result["district"],
                            "category": mapped.get("category") or result["category"],
                            "parent_name": mapped.get("parent_name") or result["parent_name"],
                            "parent_occupation": mapped.get("parent_occupation") or result["parent_occupation"],
                            "annual_family_income": mapped.get("annual_family_income") or mapped.get("annual_income") or result["annual_family_income"],
                            "annual_income": mapped.get("annual_income") or mapped.get("annual_family_income") or result["annual_income"],
                            "aadhaar_last_four": mapped.get("aadhaar_last_four") or result["aadhaar_last_four"],
                            "course": mapped.get("course") or result["course"],
                            "college": mapped.get("college") or result["college"],
                            "loan_amount": mapped.get("loan_amount") or result["loan_amount"],
                            "tuition_fee": mapped.get("tuition_fee") or result["tuition_fee"],
                            "living_expenses": mapped.get("living_expenses") or result["living_expenses"],
                            "bank_preference": mapped.get("bank_preference") or result["bank_preference"],
                            "loan_tenure": mapped.get("loan_tenure") or result["loan_tenure"],
                            "source": "copilot_automation_agent",
                        })
                        if mapped.get("documents"):
                            if isinstance(mapped["documents"], dict):
                                result["documents"].update(mapped["documents"])
                            elif isinstance(mapped["documents"], list):
                                for doc in mapped["documents"]:
                                    if isinstance(doc, dict) and doc.get("name"):
                                        result["documents"][doc["name"]] = doc.get("original_filename") or f"{doc['name']}.pdf"
        except Exception:
            pass

    if resolved_pid:
        try:
            # Query submitted info if not already retrieved via run_id
            if result.get("source") == "mock_default":
                url = f"http://localhost:8000/api/schemes/{resolved_sid}/information?profile_id={resolved_pid}"
                req = urllib.request.Request(url, headers={"Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    if resp.status == 200:
                        info_resp = json.loads(resp.read().decode())
                        s_info = info_resp.get("submitted_information") or {}
                        if s_info:
                            st_name = s_info.get("student_name") or result["student_name"]
                            result.update({
                                "student_name": st_name,
                                "applicant_name": st_name,
                                "date_of_birth": s_info.get("date_of_birth") or result["date_of_birth"],
                                "gender": s_info.get("gender") or result["gender"],
                                "state": s_info.get("state") or result["state"],
                                "district": s_info.get("district") or result["district"],
                                "category": s_info.get("category") or result["category"],
                                "parent_name": s_info.get("parent_name") or result["parent_name"],
                                "parent_occupation": s_info.get("parent_occupation") or result["parent_occupation"],
                                "annual_family_income": s_info.get("annual_family_income") or result["annual_family_income"],
                                "aadhaar_last_four": s_info.get("aadhaar_last_four") or result["aadhaar_last_four"],
                                "course": s_info.get("course") or result["course"],
                                "college": s_info.get("college") or result["college"],
                                "loan_amount": s_info.get("loan_amount") or result["loan_amount"],
                                "tuition_fee": s_info.get("tuition_fee") or result["tuition_fee"],
                                "living_expenses": s_info.get("living_expenses") or result["living_expenses"],
                                "bank_preference": s_info.get("bank_preference") or result["bank_preference"],
                                "loan_tenure": s_info.get("loan_tenure") or result["loan_tenure"],
                                "source": "copilot_submitted_info",
                            })

            # Check profile data
            url = f"http://localhost:8000/api/profile/{resolved_pid}"
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    prof_data = json.loads(resp.read().decode())
                    p_name = prof_data.get("name") or result["student_name"]
                    result.update({
                        "student_name": p_name,
                        "applicant_name": p_name,
                        "age": prof_data.get("age") or result["age"],
                        "gender": prof_data.get("gender") or result["gender"],
                        "state": prof_data.get("state") or result["state"],
                        "district": prof_data.get("district") or result["district"],
                    })

            # Check document status
            doc_url = f"http://localhost:8000/api/documents/status?scheme_id={resolved_sid}&profile_id={resolved_pid}"
            doc_req = urllib.request.Request(doc_url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(doc_req, timeout=1.0) as resp:
                if resp.status == 200:
                    doc_res = json.loads(resp.read().decode())
                    for d in doc_res.get("documents", []):
                        if d.get("status") not in ("MISSING", None):
                            d_name = d.get("name")
                            if d_name:
                                result["documents"][d_name] = d.get("original_filename") or f"{d_name}.pdf"
        except Exception:
            pass

    return result


@router.post("/application/milestone")
def record_application_milestone(payload: ApplicationMilestonePayload):
    """Synchronize workflow milestones back to the Main Copilot backend."""
    session = get_session_or_404(payload.session_id)
    active_run_id = payload.run_id or session.get("run_id")

    step_mapping = {
        "STUDENT_INFO_COMPLETED": "LOAN_INFO",
        "LOAN_INFO_COMPLETED": "DOC_UPLOAD",
        "DOCUMENTS_UPLOADED": "FINAL_REVIEW",
        "FINAL_REVIEW_REQUIRED": "FINAL_REVIEW",
        "APPLICATION_SUBMITTED": "CONFIRMED",
    }
    if payload.milestone in step_mapping:
        session["step"] = step_mapping[payload.milestone]

    if payload.data:
        if not session.get("application_data"):
            session["application_data"] = {}
        session["application_data"].update(payload.data)

    if active_run_id:
        session["run_id"] = active_run_id
        from app.sync import notify_main_portal
        notify_main_portal(
            run_id=active_run_id,
            action_type=payload.milestone,
            status=payload.milestone,
            portal_session_id=payload.session_id,
            metadata=payload.data or {},
        )

    return {
        "status": "SUCCESS",
        "milestone": payload.milestone,
        "session_id": payload.session_id,
        "run_id": active_run_id,
        "current_step": session["step"],
    }


@router.get("/application/session")
def get_session_status(session_id: str = Query(..., description="Portal session ID")):
    session = get_session_or_404(session_id)
    return {
        "session_id": session["session_id"],
        "username": session["username"],
        "current_step": session["step"],
        "created_at": session["created_at"],
        "run_id": session.get("run_id"),
    }


@router.post(
    "/application/submit",
    response_model=ApplicationSubmitResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_application(payload: SchemeApplicationPayload):
    session = get_session_or_404(payload.session_id)

    valid_submission_steps = (
        "APPLICATION_FORM",
        "STUDENT_PARENT_INFO",
        "LOAN_INFO",
        "DOC_UPLOAD",
        "FINAL_REVIEW",
    )
    if session["step"] not in valid_submission_steps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit application at step '{session['step']}'. Must complete Login, CAPTCHA, and OTP first.",
        )

    if not payload.declaration_agreed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="You must agree to the citizen declaration before submitting.",
        )

    display_name = (payload.student_name or payload.applicant_name or "").strip()
    if not display_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Student / applicant name cannot be empty.",
        )

    prefix = "ACK-EDU-2026-" if "EDU" in payload.scheme_id else "ACK-GOV-2026-"
    ack_number = f"{prefix}{random.randint(100000, 999999)}"
    now_iso = datetime.now(timezone.utc).isoformat()

    session["step"] = "CONFIRMED"
    session["run_id"] = payload.run_id or session.get("run_id")
    active_run_id = session.get("run_id")
    session["application_data"] = {
        "acknowledgment_number": ack_number,
        "scheme_id": payload.scheme_id,
        "student_name": display_name,
        "applicant_name": display_name,
        "date_of_birth": payload.date_of_birth,
        "age": payload.age,
        "gender": payload.gender,
        "state": payload.state,
        "district": payload.district,
        "category": payload.category,
        "parent_name": payload.parent_name,
        "parent_occupation": payload.parent_occupation,
        "annual_family_income": payload.annual_family_income or payload.annual_income,
        "aadhaar_last_four": payload.aadhaar_last_four,
        "course": payload.course,
        "college": payload.college,
        "loan_amount": payload.loan_amount,
        "tuition_fee": payload.tuition_fee,
        "living_expenses": payload.living_expenses,
        "bank_preference": payload.bank_preference,
        "loan_tenure": payload.loan_tenure,
        "documents": payload.documents or payload.uploaded_documents or {},
        "submitted_at": now_iso,
        "run_id": active_run_id,
    }

    # Synchronize final submission with main Copilot backend
    if active_run_id:
        from app.sync import notify_main_portal
        notify_main_portal(
            run_id=active_run_id,
            action_type="FINAL_SUBMIT",
            status="APPLICATION_SUBMITTED",
            portal_session_id=payload.session_id,
            acknowledgment_number=ack_number,
            metadata={"scheme_id": payload.scheme_id, "student_name": display_name},
        )

    return ApplicationSubmitResponse(
        status="SUBMITTED",
        acknowledgment_number=ack_number,
        session_id=payload.session_id,
        scheme_id=payload.scheme_id,
        applicant_name=display_name,
        student_name=display_name,
        submitted_at=now_iso,
        run_id=active_run_id,
        message="Education Loan application successfully submitted. Please save your acknowledgment reference.",
    )



@router.post("/application/document/upload")
def upload_mock_document(
    session_id: str = Query(..., description="Active session ID"),
    document_type: str = Query(..., description="Document type name e.g. aadhaar_card"),
):
    session = get_session_or_404(session_id)
    doc_id = f"MOCK-DOC-{uuid.uuid4().hex[:8].upper()}"
    return {
        "status": "UPLOADED",
        "document_id": doc_id,
        "document_type": document_type,
        "session_id": session_id,
        "message": f"Document '{document_type}' uploaded successfully to mock portal.",
    }

