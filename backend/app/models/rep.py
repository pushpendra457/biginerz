"""
Rep model – field representative with JWT-compatible login credentials.
Password is stored as a bcrypt hash; initialised empty ("") at seed time
and must be set before first login.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class Rep(Base):
    __tablename__ = "reps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rep_id = Column(String(50), unique=True, nullable=False, index=True)   # e.g. "REP_001"
    territory_id = Column(
        Integer,
        ForeignKey("territories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    full_name = Column(String(150), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)

    # ── Auth ──────────────────────────────────────────────────────────────────
    # Initialised as empty string at seed time; set via /auth/set-password
    hashed_password = Column(String(255), nullable=False, default="")
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String(50), nullable=False, default="rep")  # "rep" | "manager" | "admin"

    # ── Relationships ─────────────────────────────────────────────────────────
    territory = relationship("Territory", back_populates="reps")
    visits = relationship("Visit", back_populates="rep")