"""Request/response contracts for the auth module (public API surface)."""
import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    college: str | None = Field(default=None, max_length=150)
    graduation_year: int | None = Field(default=None, ge=1990, le=2100)
    target_role: str | None = Field(default=None, max_length=100)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        # Security requirement SR-2: at least one letter and one digit.
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("password must contain at least one letter and one digit")
        return v

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("name too short")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    college: str | None = None
    graduation_year: int | None = None
    target_role: str | None = None
    created_at: datetime


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    college: str | None = Field(default=None, max_length=150)
    graduation_year: int | None = Field(default=None, ge=1990, le=2100)
    target_role: str | None = Field(default=None, max_length=100)


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return RegisterRequest.strong_password(v)


TokenResponse.model_rebuild()
