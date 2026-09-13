from datetime import datetime, timezone
from pydantic import BaseModel, Field


class CitizenProfile(BaseModel):
    profile_id: str
    name: str
    age: int
    gender: str
    state: str
    district: str
    user_id: str = "anonymous"
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
