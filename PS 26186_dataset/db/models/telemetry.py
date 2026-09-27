from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from db.base import Base

class WearableTelemetry(Base):
    """
    Dedicated time-series telemetry entity for simulated wearable device signals.
    Explicitly marked with source="simulated_wearable" to maintain synthetic-data disclosures.
    """
    __tablename__ = "wearable_telemetry"

    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=False, index=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)
    heart_rate = Column(Float, nullable=True)           # BPM (beats per minute)
    hrv_rmssd = Column(Float, nullable=True)            # Root Mean Square of Successive Differences (ms)
    sleep_duration_hours = Column(Float, nullable=True) # Restorative sleep hours
    sleep_quality_score = Column(Float, nullable=True)  # Quality index (0 - 100)
    step_count = Column(Integer, nullable=True)         # Daily ambulatory activity count
    active_minutes = Column(Integer, nullable=True)     # Moderate-to-vigorous physical activity minutes
    source = Column(String(32), default="simulated_wearable", nullable=False)
    device_model = Column(String(64), nullable=True, default="Simulated Band v1")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    personnel = relationship("Personnel", back_populates="wearable_telemetry")

    __table_args__ = (
        Index("ix_wearable_telemetry_personnel_recorded", "personnel_id", "recorded_at"),
    )
