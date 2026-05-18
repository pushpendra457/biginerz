"""
WhatsAppMessageLog model – delivery and engagement tracking for WhatsApp
outreach messages sent to smartphone-owning growers.
"""
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class WhatsAppMessageLog(Base):
    __tablename__ = "whatsapp_message_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_row_id = Column(String(50), unique=True, nullable=False, index=True)  # "WAM_RABI25_#####"

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    grower_id = Column(
        Integer,
        ForeignKey("growers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Campaign Context ──────────────────────────────────────────────────────
    campaign_product = Column(String(150), nullable=False)
    campaign_crop = Column(String(50), nullable=False)

    # ── Delivery & Engagement ─────────────────────────────────────────────────
    message_sent_date = Column(Date, nullable=False, index=True)
    delivered_status = Column(Boolean, nullable=False, default=False)
    opened_status = Column(Boolean, nullable=False, default=False)
    clicked_status = Column(Boolean, nullable=False, default=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    grower = relationship("Grower", back_populates="whatsapp_messages")