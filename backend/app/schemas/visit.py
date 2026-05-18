"""
Visit request / response schemas.
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import date
from enum import Enum
from app.schemas.common import OrmBase


class VisitType(str, Enum):
    RETAILER_MEETING = "retailer meeting"
    GROWER_MEETING = "grower meeting"
    CAMPAIGN_CONDUCTED = "campaign_conducted"


class VisitOutcome(str, Enum):
    NOT_RECORDED = "not_recorded"
    SALE_MADE = "sale_made"
    ORDER_PLACED = "order_placed"
    NO_PURCHASE = "no_purchase"


class VisitCreate(BaseModel):
    retailer_id: Optional[int] = None
    grower_id: Optional[int] = None
    visit_tehsil: str
    visit_type: VisitType
    scheduled_date: date
    product_recommended: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("scheduled_date")
    @classmethod
    def validate_not_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Cannot schedule visits in the past")
        return v


class VisitUpdate(BaseModel):
    outcome: Optional[VisitOutcome] = None
    product_recommended: Optional[str] = None
    notes: Optional[str] = None


class VisitOutcomeRecord(BaseModel):
    outcome: VisitOutcome
    recommendations_accepted: list[str] = Field(default_factory=list)
    recommendations_rejected: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class VisitResponse(OrmBase):
    id: int
    rep_id: Optional[int] = None
    visit_date: date
    territory_id: Optional[int] = None
    visit_tehsil: str
    visit_type: VisitType
    product_recommended: Optional[str] = None
    retailer_id: Optional[int] = None
    grower_id: Optional[int] = None
    outcome: VisitOutcome = VisitOutcome.NOT_RECORDED
    priority_score: float = 0.0
    priority_reasons: list[str] = []
    is_planned: bool = False
    notes: Optional[str] = None


class VisitSummary(OrmBase):
    id: int
    visit_date: date
    visit_type: VisitType
    visit_tehsil: str
    outcome: VisitOutcome
    priority_score: float = 0.0