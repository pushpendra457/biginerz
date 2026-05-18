"""
RetailerInventoryWeekly model – weekly stock snapshot per SKU per retailer.
"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class RetailerInventoryWeekly(Base):
    __tablename__ = "retailer_inventory_weekly"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    retailer_id = Column(
        Integer,
        ForeignKey("retailers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── SKU ───────────────────────────────────────────────────────────────────
    sku_id = Column(String(50), nullable=False, index=True)   # e.g. "SKU_001"
    sku_name = Column(String(150), nullable=False)
    sku_qty = Column(Float, nullable=False, default=0.0)       # 0 = Out of Stock
    week_end_date = Column(Date, nullable=False, index=True)   # Sunday closing the week

    # One row per (retailer × SKU × week)
    __table_args__ = (
        UniqueConstraint("retailer_id", "sku_id", "week_end_date", name="uq_inventory_retailer_sku_week"),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    retailer = relationship("Retailer", back_populates="inventory_snapshots")