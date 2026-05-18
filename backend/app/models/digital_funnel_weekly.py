"""
DigitalFunnelWeekly model – weekly campaign performance funnel metrics.
"""
from sqlalchemy import Column, Integer, String, Date, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class DigitalFunnelWeekly(Base):
    __tablename__ = "digital_funnel_weekly"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    campaign_id = Column(String(50), nullable=False, index=True)   # e.g. "CMP_RABI25_001"
    week_start_date = Column(Date, nullable=False, index=True)      # Monday ISO date

    # ── Funnel Metrics ────────────────────────────────────────────────────────
    social_post_impression = Column(Integer, nullable=False, default=0)
    landing_page_visits = Column(Integer, nullable=False, default=0)   # ≤ impressions
    lead_form_submission = Column(Integer, nullable=False, default=0)  # ≤ visits

    # ── Campaign Meta ─────────────────────────────────────────────────────────
    campaign_crop = Column(String(50), nullable=False)       # wheat | mustard | chickpea | potato
    campaign_product = Column(String(150), nullable=False)   # aligned product name

    __table_args__ = (
        UniqueConstraint("campaign_id", "week_start_date", name="uq_funnel_campaign_week"),
    )