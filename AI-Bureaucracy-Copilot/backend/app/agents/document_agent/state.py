from typing import Any, Dict, List, Optional, TypedDict


class DocumentWorkflowState(TypedDict):
    scheme_id: str
    missing_information: List[Dict[str, Any]]
    submitted_information: Dict[str, Any]
    required_documents: List[Dict[str, Any]]
    uploaded_documents: List[Dict[str, Any]]
    document_verification: Dict[str, Any]
