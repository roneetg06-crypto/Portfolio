from pydantic import BaseModel, Field, field_validator


class CitizenProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Citizen full name")
    age: int = Field(..., gt=0, description="Age must be a positive integer")
    gender: str = Field(..., min_length=1, description="Gender identity")
    state: str = Field(..., min_length=1, description="State of residence")
    district: str = Field(..., min_length=1, description="District of residence")

    @field_validator("name", "gender", "state", "district")
    @classmethod
    def not_empty_or_whitespace(cls, value: str) -> str:
        s = value.strip()
        if not s:
            raise ValueError("Field cannot be empty or blank whitespace")
        return s


class CitizenProfileResponse(BaseModel):
    profile_id: str
    name: str
    age: int
    gender: str
    state: str
    district: str
    user_id: str = "anonymous"
    created_at: str
