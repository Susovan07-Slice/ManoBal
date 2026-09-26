from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="personnel")  # admin, officer, welfare, personnel
    personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="SET NULL"), nullable=True)
    battalion = Column(String(64), nullable=True, index=True)
    location = Column(String(64), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    personnel = relationship("Personnel", back_populates="user", foreign_keys=[personnel_id])
