from typing import Any, Dict, List, Optional
from langgraph.graph import END, StateGraph
from app.agents.document_agent.state import DocumentWorkflowState
from app.services.scheme_discovery_service import load_all_schemes


def determine_required_documents_node(state: DocumentWorkflowState) -> Dict[str, Any]:
    scheme_id = state.get("scheme_id", "").strip()
    submitted_info = state.get("submitted_information", {})

    all_schemes = load_all_schemes()
    target_scheme = next((s for s in all_schemes if s.scheme_id == scheme_id), None)

    if not target_scheme:
        return {"required_documents": []}

    docs: List[Dict[str, Any]] = []
    for doc in target_scheme.required_documents:
        docs.append({
            "name": doc.name,
            "label": doc.label,
            "required": doc.required,
            "description": doc.description or "",
        })

    return {"required_documents": docs}


def build_document_agent_graph():
    workflow = StateGraph(DocumentWorkflowState)
    workflow.add_node("determine_required_documents", determine_required_documents_node)
    workflow.set_entry_point("determine_required_documents")
    workflow.add_edge("determine_required_documents", END)
    return workflow.compile()


document_agent_graph = build_document_agent_graph()


def run_document_agent(
    scheme_id: str,
    submitted_information: Optional[Dict[str, Any]] = None,
    missing_information: Optional[List[Dict[str, Any]]] = None,
    uploaded_documents: Optional[List[Dict[str, Any]]] = None,
    document_verification: Optional[Dict[str, Any]] = None,
) -> DocumentWorkflowState:
    initial_state: DocumentWorkflowState = {
        "scheme_id": scheme_id,
        "missing_information": missing_information or [],
        "submitted_information": submitted_information or {},
        "required_documents": [],
        "uploaded_documents": uploaded_documents or [],
        "document_verification": document_verification or {},
    }
    result = document_agent_graph.invoke(initial_state)
    return result
