"""
Visit model – retailer / grower visit log for field representatives.
"""
from datetime import date

from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base
from app.schemas.visit import VisitType, VisitOutcome


class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    rep_id = Column(
        Integer,
        ForeignKey("reps.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    territory_id = Column(
        Integer,
        ForeignKey("territories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    retailer_id = Column(
        Integer,
        ForeignKey("retailers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    grower_id = Column(
        Integer,
        ForeignKey("growers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Visit Data ────────────────────────────────────────────────────────────
    visit_date = Column(Date, default=date.today, nullable=False)
    visit_tehsil = Column(String(100), nullable=False)
    visit_type = Column(
        SQLEnum(VisitType, name="visittype", create_type=False),
        nullable=False,
    )
    outcome = Column(
        SQLEnum(VisitOutcome, name="visitoutcome", create_type=False),
        default=VisitOutcome.NOT_RECORDED,
        nullable=False,
    )
    product_recommended = Column(String(150), nullable=True)
    priority_score = Column(Float, default=0.0)
    priority_reasons = Column(JSONB, default=list)
    is_planned = Column(Boolean, default=False)
    notes = Column(String, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    rep = relationship("Rep", back_populates="visits")
    territory = relationship("Territory", back_populates="visits")
    retailer = relationship("Retailer", back_populates="visits")
    grower = relationship("Grower", back_populates="visits")