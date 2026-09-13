from typing import List, Optional
from pydantic import BaseModel, Field


class RequiredInfoField(BaseModel):
    name: str
    label: str
    type: str  # text, number, date, dropdown, radio, checkbox, boolean
    required: bool = True
    options: Optional[List[str]] = None
    help_text: Optional[str] = None


class RequiredDocumentItem(BaseModel):
    name: str
    label: str
    required: bool = True
    description: Optional[str] = None


class Scheme(BaseModel):
    scheme_id: str
    name: str
    sector: str
    level: str  # "central" | "state"
    applicable_states: List[str] = Field(default_factory=list)
    issuing_authority: str
    short_description: str
    benefits: str
    official_link: str
    applicable_gender: str = "all"  # "all" | "male" | "female" | "other"
    applicable_age_min: int = 0
    applicable_age_max: int = 120
    eligibility_criteria: Optional[dict] = None
    required_info: List[RequiredInfoField] = Field(default_factory=list)
    required_documents: List[RequiredDocumentItem] = Field(default_factory=list)

