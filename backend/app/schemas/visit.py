"""
Visit-related request/response schemas modified for PostgreSQL.
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import date
from enum import Enum

# Assuming these enums are defined using Python's standard enum.Enum
class VisitType(str, Enum):
    ROUTINE = "routine"
    ADVISORY = "advisory"
    PROMOTION = "promotion"

class VisitOutcome(str, Enum):
    NOT_RECORDED = "not_recorded"
    SALE_MADE = "sale_made"
    ORDER_PLACED = "order_placed"
    NO_PURCHASE = "no_purchase"


class VisitCreate(BaseModel):
    """Schema for creating/scheduling a new visit."""
    retailer_id: Optional[int] = None   # Changed str -> int for Postgres Foreign Keys
    grower_id: Optional[str] = None     # Keeping str if farmer IDs look like 'GRW_00006'
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
    """Schema for updating a visit (e.g. completing it)."""
    outcome: Optional[VisitOutcome] = None
    product_recommended: Optional[str] = None
    notes: Optional[str] = None


class VisitOutcomeRecord(BaseModel):
    """Schema for recording visit outcome with feedback."""
    outcome: VisitOutcome
    # Postgres handles arrays natively; Pydantic handles lists natively
    recommendations_accepted: list[str] = Field(default_factory=list)
    recommendations_rejected: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class VisitResponse(BaseModel):
    """Full visit response."""
    model_config = ConfigDict(from_attributes=True) # Pydantic v2 compatibility with SQLAlchemy

    id: int                              # Changed str -> int for PostgreSQL primary key
    rep_id: int                          # Changed str -> int for User foreign key
    visit_date: date
    territory_id: int                    # Changed str -> int for Territory foreign key
    visit_tehsil: str
    visit_type: VisitType
    product_recommended: Optional[str] = None
    retailer_id: Optional[int] = None    # Changed str -> int
    grower_id: Optional[str] = None     # Matches 'GRW_00006' format
    outcome: VisitOutcome = VisitOutcome.NOT_RECORDED
    priority_score: float = 0.0
    priority_reasons: list[str] = []    # Mapped to a JSONB or ARRAY column in Postgres
    is_planned: bool = False
    notes: Optional[str] = None


class VisitSummary(BaseModel):
    """Minimal visit info."""
    id: int                              # Changed str -> int
    visit_date: date
    visit_type: VisitType
    visit_tehsil: str
    outcome: VisitOutcome
    priority_score: float = 0.0