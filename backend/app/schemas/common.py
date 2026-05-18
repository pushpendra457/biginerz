"""
Common reusable Pydantic models, enums, and mixins shared across schemas.
"""
from pydantic import BaseModel, ConfigDict
from enum import Enum


class OrmBase(BaseModel):
    """Enables SQLAlchemy ORM → Pydantic model conversion for all response schemas."""
    model_config = ConfigDict(from_attributes=True)


class UserRole(str, Enum):
    REP = "rep"
    RETAILER = "retailer"
    MANAGER = "manager"
    ADMIN = "admin"