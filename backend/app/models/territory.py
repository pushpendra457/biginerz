"""
Territory model – maps a unique sales zone to a rep, state, district and
a JSON list of tehsils.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
 
from app.database import Base
 
 
class Territory(Base):
    __tablename__ = "territories"
 
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    territory_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g. "TER_001"
    territory_name = Column(String(150), nullable=False)
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    tehsil_list = Column(JSONB, nullable=False, default=list)   # ["Tehsil A", "Tehsil B"]
 
    # Relationships
    reps = relationship("Rep", back_populates="territory")
    retailers = relationship("Retailer", back_populates="territory")
    visits = relationship("Visit", back_populates="territory")