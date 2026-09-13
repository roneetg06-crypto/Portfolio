from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class KnowledgeAskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question asked by citizen")
    state: Optional[str] = Field(None, description="Optional target state filter")
    sector: Optional[str] = Field(None, description="Optional target sector filter")
    scheme_id: Optional[str] = Field(None, description="Optional scheme ID filter")

    @field_validator("question")
    @classmethod
    def question_not_whitespace(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Question cannot be empty or whitespace.")
        return s


class SchemeSource(BaseModel):
    scheme_id: str
    scheme_name: str
    level: str


class KnowledgeAskResponse(BaseModel):
    answer: str
    sources: List[SchemeSource]
    grounded: bool
    scheme_id: Optional[str] = None
    action: Optional[str] = None
    action_url: Optional[str] = None
    action_title: Optional[str] = None
    requires_human_verification: Optional[bool] = False
