import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserSignupRequest(BaseModel):
    email: str = Field(..., description="Citizen email or official ID")
    password: str = Field(..., min_length=6, description="Password (at least 6 characters)")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        # Basic email format check
        email_regex = r"^[\w\.\+\-]+@[\w\.\-]+\.\w+$"
        if not re.match(email_regex, clean):
            raise ValueError("Invalid email format.")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.strip()) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        return v


class UserLoginRequest(BaseModel):
    email: str = Field(..., description="Citizen email or official ID")
    password: str = Field(..., description="Password")

    @field_validator("email")
    @classmethod
    def clean_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
