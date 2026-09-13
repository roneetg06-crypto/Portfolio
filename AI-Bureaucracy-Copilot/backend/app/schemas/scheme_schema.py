from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.scheme import RequiredDocumentItem, RequiredInfoField


class SchemeResponse(BaseModel):
    scheme_id: str
    name: str
    sector: str
    level: str
    applicable_states: List[str]
    issuing_authority: str
    short_description: str
    benefits: str
    official_link: str
    applicable_gender: str = "all"
    applicable_age_min: int = 0
    applicable_age_max: int = 120
    eligibility_criteria: Optional[Dict[str, Any]] = None
    required_info: List[RequiredInfoField] = Field(default_factory=list)
    required_documents: List[RequiredDocumentItem] = Field(default_factory=list)


class SchemeInfoRequirementsResponse(BaseModel):
    scheme_id: str
    scheme_name: str
    required_info: List[RequiredInfoField]


class SchemeInfoSubmissionRequest(BaseModel):
    profile_id: Optional[str] = None
    data: Dict[str, Any]


class SchemeInfoSubmissionResponse(BaseModel):
    status: str
    scheme_id: str
    profile_id: Optional[str] = None
    submitted_information: Dict[str, Any]
    missing_information: List[str] = Field(default_factory=list)


class SchemeRequiredDocumentsResponse(BaseModel):
    scheme_id: str
    scheme_name: str
    required_documents: List[RequiredDocumentItem]
