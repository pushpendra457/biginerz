"""
Retailer request / response schemas.
Includes auth-related schemas for JWT login flow.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from app.schemas.common import OrmBase, UserRole


# ── Auth ──────────────────────────────────────────────────────────────────────

class RetailerLogin(BaseModel):
    """Used at POST /auth/retailer/login"""
    email: EmailStr
    password: str


class RetailerSetPassword(BaseModel):
    """Used at POST /auth/retailer/set-password"""
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
    retailer_id: str


# ── CRUD ──────────────────────────────────────────────────────────────────────

class RetailerCreate(BaseModel):
    retailer_id: str = Field(..., example="RET_0001")
    territory_id: Optional[int] = None
    state: str
    district: str
    tehsil: str
    shop_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.RETAILER


class RetailerUpdate(BaseModel):
    territory_id: Optional[int] = None
    state: Optional[str] = None
    district: Optional[str] = None
    tehsil: Optional[str] = None
    shop_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class RetailerResponse(OrmBase):
    id: int
    retailer_id: str
    territory_id: Optional[int] = None
    state: str
    district: str
    tehsil: str
    shop_name: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    role: UserRole


class RetailerSummary(OrmBase):
    id: int
    retailer_id: str
    state: str
    district: str
    tehsil: str