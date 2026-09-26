from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base

class WelfareRecommendation(Base):
    __tablename__ = "welfare_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(Integer, ForeignKey("stress_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_type = Column(String(64), nullable=False)  # workload, sleep, leave, medical, duty
    recommendation_text = Column(Text, nullable=False)
    priority = Column(String(16), nullable=False, index=True)  # Routine, Preventive, Priority
    status = Column(String(16), default="pending", index=True)  # pending, acknowledged, completed, dismissed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    personnel = relationship("Personnel", back_populates="recommendations")
    assessment = relationship("StressAssessment", back_populates="recommendations")
