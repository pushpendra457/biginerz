"""
Grower model – farmer profile including demographics, engagement, and
crop calendar.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base
from app.schemas.grower import DeviceType, Gender


class Grower(Base):
    __tablename__ = "growers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    grower_id = Column(String(50), unique=True, nullable=False, index=True)  # "GRW_00001"

    # ── Geography ─────────────────────────────────────────────────────────────
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    tehsil = Column(String(100), nullable=False)

    # ── Demographics ──────────────────────────────────────────────────────────
    language = Column(String(50), nullable=True)
    device_type = Column(
        SQLEnum(DeviceType, name="devicetype", create_type=False),
        nullable=False,
        default=DeviceType.UNKNOWN,
    )
    grower_age = Column(Integer, nullable=True)
    gender = Column(
        SQLEnum(Gender, name="gender", create_type=False),
        nullable=True,
    )
    grower_farm_size = Column(Float, nullable=True)  # acres

    # ── Crop & Product ────────────────────────────────────────────────────────
    grower_crop_calendar = Column(JSONB, nullable=True)   # {crop, stages: [...]}
    product_scan = Column(Boolean, default=False, nullable=False)
    product_name = Column(String(150), nullable=True)
    product_scan_datetime = Column(DateTime(timezone=True), nullable=True)

    # ── Offline Engagement ────────────────────────────────────────────────────
    offline_campaign_attended = Column(Boolean, default=False, nullable=False)
    campaign_attendance_date = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    visits = relationship("Visit", back_populates="grower")
    whatsapp_messages = relationship("WhatsAppMessageLog", back_populates="grower")