"""
RetailerPOS model – point-of-sale transaction line items.
"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class RetailerPOS(Base):
    __tablename__ = "retailer_pos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    retailer_id = Column(
        Integer,
        ForeignKey("retailers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Transaction ───────────────────────────────────────────────────────────
    transaction_id = Column(String(100), nullable=False, index=True)  # line-item unique ID
    sku_id = Column(String(50), nullable=False, index=True)
    sku_name = Column(String(150), nullable=False)
    sku_qty = Column(Float, nullable=False)
    sku_price = Column(Float, nullable=False)                         # standardised currency
    transaction_date = Column(Date, nullable=False, index=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    retailer = relationship("Retailer", back_populates="pos_transactions")