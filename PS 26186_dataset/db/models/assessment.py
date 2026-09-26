from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from db.base import Base

class StressAssessment(Base):
    __tablename__ = "stress_assessments"

    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=False, index=True)
    stress_level = Column(String(16), nullable=False, index=True)  # Low, Medium, High
    low_probability = Column(Float, nullable=False)
    medium_probability = Column(Float, nullable=False)
    high_probability = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False, index=True)  # 0.0 - 100.0 continuous

    risk_priority = Column(String(16), nullable=False, index=True)  # Routine, Preventive, Priority
    key_factors = Column(Text, nullable=True)  # JSON-encoded array of factor strings
    model_version = Column(String(32), default="1.0.0-LightGBM")
    assessment_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    personnel = relationship("Personnel", back_populates="assessments")
    recommendations = relationship("WelfareRecommendation", back_populates="assessment", cascade="all, delete-orphan")
