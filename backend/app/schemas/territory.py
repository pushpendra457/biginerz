"""
Territory request / response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.common import OrmBase


class TerritoryCreate(BaseModel):
    territory_id: str = Field(..., example="TER_001")
    territory_name: str
    state: str
    district: str
    tehsil_list: list[str] = Field(default_factory=list)


class TerritoryUpdate(BaseModel):
    territory_name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    tehsil_list: Optional[list[str]] = None


class TerritoryResponse(OrmBase):
    id: int
    territory_id: str
    territory_name: str
    state: str
    district: str
    tehsil_list: list[str]


class TerritorySummary(OrmBase):
    id: int
    territory_id: str
    territory_name: str
    state: str
    district: str