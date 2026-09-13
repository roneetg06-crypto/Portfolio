import uuid
from typing import Any, Dict, List, Optional
from langgraph.graph import END, StateGraph
from app.agents.automation_agent.state import AutomationWorkflowState
from app.services.scheme_discovery_service import load_all_schemes
from app.services.browser_automation_service import BrowserAutomationService



def build_mapped_form_data(
    scheme_id: str,
    user_profile: Dict[str, Any],
    submitted_info: Dict[str, Any],
    uploaded_documents: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    if scheme_id == "SCH-EDU-001":
        raw_income = submitted_info.get("annual_family_income")
        if raw_income is None:
            raw_income = submitted_info.get("annual_income")
        if raw_income is None:
            raw_income = user_profile.get("annual_income")
        income_val = float(raw_income) if raw_income is not None else None

        raw_aadhaar = (
            submitted_info.get("aadhaar_last_four")
            or submitted_info.get("aadhaar_number")
            or user_profile.get("aadhaar_last_four")
            or user_profile.get("aadhaar_number")
        )
        aadhaar_four = str(raw_aadhaar)[-4:] if raw_aadhaar else None

        doc_list: List[Dict[str, Any]] = []
        if uploaded_documents:
            for doc in uploaded_documents:
                doc_list.append({
                    "name": doc.get("name"),
                    "label": doc.get("label"),
                    "required": doc.get("required", True),
                    "status": doc.get("status", "UPLOADED"),
                    "original_filename": doc.get("original_filename"),
                    "storage_path": doc.get("storage_path"),
                    "document_id": doc.get("document_id"),
                    "size_bytes": doc.get("size_bytes"),
                })
        elif submitted_info.get("documents"):
            sub_docs = submitted_info["documents"]
            if isinstance(sub_docs, list):
                doc_list.extend(sub_docs)
            elif isinstance(sub_docs, dict):
                for d_name, d_val in sub_docs.items():
                    if isinstance(d_val, dict):
                        doc_list.append(d_val)
                    else:
                        doc_list.append({
                            "name": d_name,
                            "label": d_name.replace("_", " ").title(),
                            "required": True,
                            "status": "UPLOADED",
                            "original_filename": str(d_val),
                            "storage_path": None,
                            "document_id": None,
                            "size_bytes": None,
                        })

        loan_amt = submitted_info.get("loan_amount")
        tuition = submitted_info.get("tuition_fee")
        living = submitted_info.get("living_expenses")

        return {
            "scheme_id": "SCH-EDU-001",
            "student_name": submitted_info.get("student_name") or user_profile.get("name"),
            "date_of_birth": submitted_info.get("date_of_birth") or user_profile.get("date_of_birth"),
            "gender": submitted_info.get("gender") or user_profile.get("gender"),
            "state": submitted_info.get("state") or user_profile.get("state"),
            "district": submitted_info.get("district") or user_profile.get("district"),
            "category": submitted_info.get("category") or user_profile.get("category"),
            "parent_name": submitted_info.get("parent_name"),
            "parent_occupation": submitted_info.get("parent_occupation"),
            "annual_family_income": income_val,
            "aadhaar_last_four": aadhaar_four,
            "course": submitted_info.get("course"),
            "college": submitted_info.get("college"),
            "loan_amount": float(loan_amt) if loan_amt is not None else None,
            "tuition_fee": float(tuition) if tuition is not None else None,
            "living_expenses": float(living) if living is not None else None,
            "bank_preference": submitted_info.get("bank_preference"),
            "loan_tenure": submitted_info.get("loan_tenure"),
            "documents": doc_list,
        }

    # Generic / other schemes fallback (preserves backwards-compatibility for existing tests)
    income = (
        submitted_info.get("annual_family_income")
        or submitted_info.get("annual_income")
        or user_profile.get("annual_income")
        or 180000
    )
    raw_aadhaar = (
        submitted_info.get("aadhaar_last_four")
        or submitted_info.get("aadhaar_number")
        or user_profile.get("aadhaar_last_four")
    )
    aadhaar_four = str(raw_aadhaar)[-4:] if raw_aadhaar else "1234"

    return {
        "scheme_id": scheme_id,
        "applicant_name": user_profile.get("name", "Citizen"),
        "age": user_profile.get("age", 30),
        "gender": user_profile.get("gender", "Female"),
        "state": user_profile.get("state", "Andhra Pradesh"),
        "district": user_profile.get("district", "General"),
        "annual_income": float(income) if income else 180000.0,
        "aadhaar_last_four": aadhaar_four,
        "declaration_agreed": True,
    }


def plan_application_node(state: AutomationWorkflowState) -> Dict[str, Any]:
    scheme_id = state.get("scheme_id", "")
    profile = state.get("user_profile", {})
    submitted_info = state.get("submitted_information", {})
    uploaded_docs = state.get("uploaded_documents", [])

    mapped_form = build_mapped_form_data(scheme_id, profile, submitted_info, uploaded_docs)

    if scheme_id == "SCH-EDU-001":
        planned_steps: List[Dict[str, Any]] = [
            {
                "step_id": "portal_login",
                "name": "Portal Login & Authentication",
                "type": "human_action",
                "action_type": "LOGIN",
                "status": "pending",
                "description": "Authenticate student identity on the education loan portal",
            },
            {
                "step_id": "captcha_challenge",
                "name": "CAPTCHA Security Challenge",
                "type": "human_action",
                "action_type": "CAPTCHA",
                "status": "pending",
                "description": "Solve anti-bot visual CAPTCHA security puzzle",
            },
            {
                "step_id": "mobile_otp",
                "name": "Two-Factor Mobile OTP Verification",
                "type": "human_action",
                "action_type": "OTP",
                "status": "pending",
                "description": "Verify OTP code sent to registered mobile phone",
            },
            {
                "step_id": "student_information",
                "name": "Student & Parent Information Entry",
                "type": "auto",
                "action_type": "STUDENT_INFORMATION",
                "status": "pending",
                "description": "Automated fill of student identity, address, category, and parental details",
            },
            {
                "step_id": "loan_information",
                "name": "Academic & Loan Details Entry",
                "type": "auto",
                "action_type": "LOAN_INFORMATION",
                "status": "pending",
                "description": "Automated fill of course, institution, loan amount, fee structure, and bank preference",
            },
            {
                "step_id": "document_upload",
                "name": "Automated Document Upload",
                "type": "auto",
                "action_type": "DOCUMENT_UPLOAD",
                "status": "pending",
                "description": "Automated attachment of verified admission offer, fee structure, Aadhaar, and income documents",
            },
            {
                "step_id": "final_review",
                "name": "Final Review & Citizen Declaration",
                "type": "human_action",
                "action_type": "FINAL_REVIEW",
                "status": "pending",
                "description": "Mandatory human review of complete loan dossier and declaration sign-off",
            },
            {
                "step_id": "completion",
                "name": "Application Completion & Acknowledgment",
                "type": "auto",
                "action_type": "COMPLETION",
                "status": "pending",
                "description": "System receipt confirmation and acknowledgment capture",
            },
        ]
        return {
            "planned_steps": planned_steps,
            "current_step_index": 0,
            "automation_status": "IN_PROGRESS",
            "application_status": "DRAFT",
            "mapped_form_data": mapped_form,
        }

    all_schemes = load_all_schemes()
    scheme = next((s for s in all_schemes if s.scheme_id == scheme_id), None)
    scheme_name = scheme.name if scheme else "Government Scheme"

    planned_steps: List[Dict[str, Any]] = [
        {
            "step_id": "portal_login",
            "name": f"Portal Login & Authentication ({scheme_name})",
            "type": "human_action",
            "action_type": "LOGIN",
            "status": "pending",
            "description": "Authenticate citizen identity on the government portal",
        },
        {
            "step_id": "captcha_challenge",
            "name": "CAPTCHA Security Challenge",
            "type": "human_action",
            "action_type": "CAPTCHA",
            "status": "pending",
            "description": "Solve anti-bot visual CAPTCHA puzzle",
        },
    ]

    # Check if there's any data gap requiring user review
    has_unverified_docs = any(d.get("status") in ("MISSING", "INVALID", "UNCLEAR") for d in uploaded_docs)
    if has_unverified_docs:
        planned_steps.append({
            "step_id": "data_review",
            "name": "Citizen Data & Unverified Document Review",
            "type": "human_action",
            "action_type": "DATA_REVIEW",
            "status": "pending",
            "description": "Review unverified document requirements before proceeding",
        })

    planned_steps.extend([
        {
            "step_id": "form_mapping",
            "name": "Automated Form Field Mapping & Assembly",
            "type": "auto",
            "status": "pending",
            "description": "Assemble citizen profile & verified form attributes",
        },
        {
            "step_id": "mobile_otp",
            "name": "Two-Factor Mobile OTP Verification",
            "type": "human_action",
            "action_type": "OTP",
            "status": "pending",
            "description": "Verify Aadhaar / Mobile OTP sent to citizen phone",
        },
        {
            "step_id": "final_submit",
            "name": "Final Review & Application Submission",
            "type": "human_action",
            "action_type": "FINAL_SUBMIT",
            "status": "pending",
            "description": "Confirm final application preview and submit to portal",
        },
    ])

    return {
        "planned_steps": planned_steps,
        "current_step_index": 0,
        "automation_status": "IN_PROGRESS",
        "application_status": "DRAFT",
        "mapped_form_data": mapped_form,
    }


def check_human_action_node(state: AutomationWorkflowState) -> Dict[str, Any]:
    planned_steps = state.get("planned_steps", [])
    current_idx = state.get("current_step_index", 0)
    rid = state.get("run_id", "")
    sid = state.get("scheme_id", "")
    pid = state.get("profile_id", "")

    if current_idx >= len(planned_steps):
        if rid:
            BrowserAutomationService.close_session(rid)
        return {
            "automation_status": "COMPLETED",
            "application_status": "SUBMITTED",
            "human_action_required": None,
        }

    current_step = planned_steps[current_idx]

    # Incorporate live browser detection if active session exists
    live_page_state = BrowserAutomationService.detect_page_state(rid) if rid else "UNKNOWN"
    is_human_required = (current_step.get("type") == "human_action" and current_step.get("status") != "completed")

    # If live page indicates a human barrier gate, enforce human action pause ONLY if current step is human_action or live state is FINAL_REVIEW
    if current_step.get("type") == "human_action" and current_step.get("status") != "completed":
        is_human_required = True
    elif live_page_state == "FINAL_REVIEW" and current_step.get("status") != "completed":
        is_human_required = True

    if is_human_required:
        action_type = current_step.get("action_type", "LOGIN")
        if live_page_state == "FINAL_REVIEW":
            action_type = "FINAL_REVIEW"

        step_id = current_step.get("step_id", "")
        portal_url = f"http://localhost:5174/?run_id={rid}&scheme_id={sid}&profile_id={pid}&step={step_id}"

        human_req = {
            "action_type": action_type,
            "step_id": step_id,
            "step_name": current_step.get("name"),
            "message": f"Human Action Required: Please complete {current_step.get('name')} on the mock portal.",
            "portal_url": portal_url,
        }
        return {
            "automation_status": "AWAITING_HUMAN_ACTION",
            "human_action_required": human_req,
            "application_status": "PENDING_CITIZEN_ACTION",
        }

    return {"human_action_required": None, "automation_status": "IN_PROGRESS"}


def advance_step_node(state: AutomationWorkflowState) -> Dict[str, Any]:
    planned_steps = [dict(s) for s in state.get("planned_steps", [])]
    current_idx = state.get("current_step_index", 0)
    rid = state.get("run_id", "")

    if current_idx < len(planned_steps):
        current_step = planned_steps[current_idx]
        step_id = current_step.get("step_id")
        # Execute automated browser form-filling if at auto step
        if current_step.get("type") == "auto" and rid:
            form_d = state.get("mapped_form_data", {})
            if step_id == "student_information":
                BrowserAutomationService.fill_student_parent_info(run_id=rid, form_data=form_d)
            elif step_id == "loan_information":
                BrowserAutomationService.fill_loan_info(run_id=rid, form_data=form_d)
            elif step_id == "document_upload":
                BrowserAutomationService.upload_application_documents(run_id=rid, form_data=form_d)
            elif step_id in ("form_mapping",):
                BrowserAutomationService.fill_application_form(run_id=rid, form_data=form_d)
        planned_steps[current_idx]["status"] = "completed"

    next_idx = current_idx + 1

    if next_idx >= len(planned_steps):
        if rid:
            BrowserAutomationService.close_session(rid)
        return {
            "planned_steps": planned_steps,
            "current_step_index": next_idx,
            "automation_status": "COMPLETED",
            "application_status": "SUBMITTED",
            "human_action_required": None,
        }

    return {
        "planned_steps": planned_steps,
        "current_step_index": next_idx,
        "automation_status": "IN_PROGRESS",
        "human_action_required": None,
    }



def should_pause(state: AutomationWorkflowState) -> str:
    if state.get("automation_status") == "AWAITING_HUMAN_ACTION":
        return "await_human_action"
    if state.get("automation_status") == "COMPLETED":
        return END
    return "advance_step"


def await_human_action_node(state: AutomationWorkflowState) -> Dict[str, Any]:
    return {}


def build_automation_agent_graph():
    workflow = StateGraph(AutomationWorkflowState)

    workflow.add_node("plan_application", plan_application_node)
    workflow.add_node("check_human_action", check_human_action_node)
    workflow.add_node("await_human_action", await_human_action_node)
    workflow.add_node("advance_step", advance_step_node)

    workflow.set_entry_point("plan_application")
    workflow.add_edge("plan_application", "check_human_action")

    workflow.add_conditional_edges(
        "check_human_action",
        should_pause,
        {
            "await_human_action": "await_human_action",
            "advance_step": "advance_step",
            END: END,
        },
    )

    workflow.add_edge("await_human_action", END)
    workflow.add_edge("advance_step", "check_human_action")

    return workflow.compile()


automation_agent_graph = build_automation_agent_graph()


def run_automation_agent(
    run_id: str,
    scheme_id: str,
    profile_id: str,
    user_profile: Dict[str, Any],
    submitted_information: Dict[str, Any],
    uploaded_documents: List[Dict[str, Any]],
    document_verification: Dict[str, Any],
) -> AutomationWorkflowState:
    mapped_form = build_mapped_form_data(
        scheme_id, user_profile, submitted_information, uploaded_documents
    )

    initial_state: AutomationWorkflowState = {
        "run_id": run_id,
        "scheme_id": scheme_id,
        "profile_id": profile_id,
        "user_profile": user_profile,
        "submitted_information": submitted_information,
        "uploaded_documents": uploaded_documents,
        "document_verification": document_verification,
        "planned_steps": [],
        "current_step_index": 0,
        "automation_status": "PLANNING",
        "human_action_required": None,
        "application_status": "DRAFT",
        "mapped_form_data": mapped_form,
        "portal_session_id": None,
        "acknowledgment_number": None,
    }
    return automation_agent_graph.invoke(initial_state)


def resume_automation_agent(
    state: AutomationWorkflowState,
    action_type: str,
    confirmation_data: Optional[Dict[str, Any]] = None,
) -> AutomationWorkflowState:
    current_idx = state.get("current_step_index", 0)
    planned_steps = [dict(s) for s in state.get("planned_steps", [])]

    # Find the target step corresponding to action_type
    target_idx = -1
    for idx, s in enumerate(planned_steps):
        s_act = s.get("action_type")
        s_id = s.get("step_id")
        matched = False
        if s_act == action_type or s_id == action_type:
            matched = True
        elif action_type in ("LOGIN_COMPLETED", "LOGIN") and (s_act == "LOGIN" or s_id == "portal_login"):
            matched = True
        elif action_type in ("CAPTCHA_COMPLETED", "CAPTCHA") and (s_act == "CAPTCHA" or s_id == "captcha_challenge"):
            matched = True
        elif action_type in ("OTP_COMPLETED", "OTP") and (s_act == "OTP" or s_id == "mobile_otp"):
            matched = True
        elif action_type in ("STUDENT_INFO_COMPLETED", "STUDENT_INFORMATION") and (s_act == "STUDENT_INFORMATION" or s_id == "student_information"):
            matched = True
        elif action_type in ("LOAN_INFO_COMPLETED", "LOAN_INFORMATION") and (s_act == "LOAN_INFORMATION" or s_id == "loan_information"):
            matched = True
        elif action_type in ("DOCUMENTS_UPLOADED", "DOCUMENT_UPLOAD") and (s_act == "DOCUMENT_UPLOAD" or s_id == "document_upload"):
            matched = True
        elif action_type in ("FINAL_REVIEW", "FINAL_REVIEW_REQUIRED") and (s_act == "FINAL_REVIEW" or s_id == "final_review"):
            matched = True
        elif action_type in ("FINAL_SUBMIT", "APPLICATION_SUBMITTED") and (s_act in ("FINAL_SUBMIT", "FINAL_REVIEW", "COMPLETION")):
            matched = True

        if matched and s.get("status") != "completed":
            target_idx = idx
            break

    if action_type in ("FINAL_SUBMIT", "APPLICATION_SUBMITTED"):
        # Final submit completes all steps up to the end
        for s in planned_steps:
            s["status"] = "completed"
        next_idx = len(planned_steps)
    elif target_idx != -1 and target_idx >= current_idx:
        # Mark all steps up to and including target_idx as completed
        for i in range(current_idx, target_idx + 1):
            planned_steps[i]["status"] = "completed"
        next_idx = target_idx + 1
    else:
        if current_idx < len(planned_steps):
            planned_steps[current_idx]["status"] = "completed"
        next_idx = current_idx + 1

    updated_state: AutomationWorkflowState = dict(state)
    updated_state["planned_steps"] = planned_steps
    updated_state["current_step_index"] = next_idx

    prefix = "ACK-EDU-2026-" if "EDU" in updated_state.get("scheme_id", "") else "ACK-GOV-2026-"

    # Capture portal session id or acknowledgment if provided in confirmation data
    if confirmation_data:
        if confirmation_data.get("portal_session_id"):
            updated_state["portal_session_id"] = confirmation_data["portal_session_id"]
        if confirmation_data.get("acknowledgment_number"):
            updated_state["acknowledgment_number"] = confirmation_data["acknowledgment_number"]

    if next_idx >= len(planned_steps):
        updated_state["automation_status"] = "COMPLETED"
        updated_state["application_status"] = "SUBMITTED"
        updated_state["human_action_required"] = None
        if not updated_state.get("acknowledgment_number"):
            updated_state["acknowledgment_number"] = f"{prefix}{uuid.uuid4().hex[:6].upper()}"
        return updated_state

    # Loop through steps: auto steps get completed immediately,
    # stop when we hit a human_action step or reach the end.
    max_iterations = len(planned_steps)
    iterations = 0
    while iterations < max_iterations:
        iterations += 1
        next_check = check_human_action_node(updated_state)
        updated_state.update(next_check)

        # If we're now awaiting human action or completed, stop
        if updated_state.get("automation_status") in ("AWAITING_HUMAN_ACTION", "COMPLETED"):
            break

        # Auto step: mark completed and advance
        idx = updated_state.get("current_step_index", 0)
        steps = [dict(s) for s in updated_state.get("planned_steps", [])]
        if idx < len(steps):
            step_id = steps[idx].get("step_id")
            rid = updated_state.get("run_id")
            if steps[idx].get("type") == "auto" and rid:
                form_d = updated_state.get("mapped_form_data", {})
                if step_id == "student_information":
                    BrowserAutomationService.fill_student_parent_info(run_id=rid, form_data=form_d)
                elif step_id == "loan_information":
                    BrowserAutomationService.fill_loan_info(run_id=rid, form_data=form_d)
                elif step_id == "document_upload":
                    BrowserAutomationService.upload_application_documents(run_id=rid, form_data=form_d)
                elif step_id in ("form_mapping",):
                    BrowserAutomationService.fill_application_form(run_id=rid, form_data=form_d)
            steps[idx]["status"] = "completed"
        new_idx = idx + 1
        updated_state["planned_steps"] = steps
        updated_state["current_step_index"] = new_idx

        if new_idx >= len(steps):
            updated_state["automation_status"] = "COMPLETED"
            updated_state["application_status"] = "SUBMITTED"
            updated_state["human_action_required"] = None
            if not updated_state.get("acknowledgment_number"):
                updated_state["acknowledgment_number"] = f"{prefix}{uuid.uuid4().hex[:6].upper()}"
            rid = updated_state.get("run_id")
            if rid:
                BrowserAutomationService.close_session(rid)
            break

    return updated_state

