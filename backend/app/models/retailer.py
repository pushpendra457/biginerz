"""
Retailer model – retail outlet with JWT-compatible login credentials.
Password is stored as a bcrypt hash; initialised empty ("") at seed time.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class Retailer(Base):
    __tablename__ = "retailers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    retailer_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g. "RET_0001"
    territory_id = Column(
        Integer,
        ForeignKey("territories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Geography ─────────────────────────────────────────────────────────────
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    tehsil = Column(String(100), nullable=False)

    # ── Auth ──────────────────────────────────────────────────────────────────
    shop_name = Column(String(200), nullable=True)
    email = Column(String(200), unique=True, nullable=True, index=True)  # nullable for legacy data
    hashed_password = Column(String(255), nullable=False, default="")
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String(50), nullable=False, default="retailer")

    # ── Relationships ─────────────────────────────────────────────────────────
    territory = relationship("Territory", back_populates="retailers")
    visits = relationship("Visit", back_populates="retailer")
    inventory_snapshots = relationship("RetailerInventoryWeekly", back_populates="retailer")
    pos_transactions = relationship("RetailerPOS", back_populates="retailer")