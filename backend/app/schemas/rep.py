"""
Rep (field representative) request / response schemas.
Includes auth-related schemas for JWT login flow.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from app.schemas.common import OrmBase, UserRole


# ── Auth ──────────────────────────────────────────────────────────────────────

class RepLogin(BaseModel):
    """Used at POST /auth/rep/login"""
    email: EmailStr
    password: str


class RepSetPassword(BaseModel):
    """Used at POST /auth/rep/set-password (first-time or reset)"""
    email: EmailStr
    new_password: str = Field(..., min_length=8)
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class TokenResponse(BaseModel):
    """JWT response returned after successful login."""
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    rep_id: str


# ── CRUD ──────────────────────────────────────────────────────────────────────

class RepCreate(BaseModel):
    rep_id: str = Field(..., example="REP_001")
    territory_id: Optional[int] = None   # FK to territories.id
    full_name: str
    email: EmailStr
    role: UserRole = UserRole.REP


class RepUpdate(BaseModel):
    territory_id: Optional[int] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class RepResponse(OrmBase):
    id: int
    rep_id: str
    territory_id: Optional[int] = None
    full_name: str
    email: str
    is_active: bool
    role: UserRole


class RepSummary(OrmBase):
    id: int
    rep_id: str
    full_name: str
    email: str