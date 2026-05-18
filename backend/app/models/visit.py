from datetime import date
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base
from app.schemas.visit import VisitType, VisitOutcome

class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rep_id = Column(Integer, nullable=False, index=True) # Linked to your User model later
    territory_id = Column(Integer, nullable=False, index=True)
    visit_date = Column(Date, default=date.today, nullable=False)
    visit_tehsil = Column(String(100), nullable=False)
    
    # Store Enums safely as strings in the database
    visit_type = Column(SQLEnum(VisitType, name="visittype", create_type=False), nullable=False)
    outcome = Column(SQLEnum(VisitOutcome, name="visitoutcome", create_type=False), default=VisitOutcome.NOT_RECORDED, nullable=False)
    
    product_recommended = Column(String(150), nullable=True)
    retailer_id = Column(Integer, nullable=True, index=True)
    grower_id = Column(String(50), nullable=True, index=True) # For formats like 'GRW_00006'
    
    priority_score = Column(Float, default=0.0)
    priority_reasons = Column(JSONB, default=list) # Stores your list["str"] natively
    
    is_planned = Column(Boolean, default=False)
    notes = Column(String, nullable=True)