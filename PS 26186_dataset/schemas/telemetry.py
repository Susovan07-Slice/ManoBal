from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class WearableTelemetryIngest(BaseModel):
    """
    Structured payload for simulated wearable biometric & recovery telemetry ingestion.
    Explicitly marked as simulated/mock IoT ingestion interface.
    """
    model_config = ConfigDict(from_attributes=True)

    personnel_id: int = Field(..., description="Target personnel database ID")
    recorded_at: datetime = Field(..., description="Timestamp of telemetry recording (UTC)")
    heart_rate: Optional[float] = Field(None, ge=30.0, le=240.0, description="Heart rate in beats per minute (30 - 240 bpm)")
    hrv_rmssd: Optional[float] = Field(None, ge=5.0, le=350.0, description="Heart rate variability RMSSD in milliseconds (5 - 350 ms)")
    sleep_duration_hours: Optional[float] = Field(None, ge=0.0, le=24.0, description="Recorded restorative sleep in hours (0.0 - 24.0 h)")
    sleep_quality_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Sleep quality score index (0.0 - 100.0)")
    step_count: Optional[int] = Field(None, ge=0, le=150000, description="Daily ambulatory step count (0 - 150,000 steps)")
    active_minutes: Optional[int] = Field(None, ge=0, le=1440, description="Moderate to vigorous physical activity minutes (0 - 1,440 min)")
    device_model: Optional[str] = Field("Simulated Band v1", max_length=64, description="Simulated device hardware identifier")

class WearableTelemetryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = "success"
    telemetry_id: int
    personnel_id: int
    recorded_at: datetime
    heart_rate: Optional[float]
    hrv_rmssd: Optional[float]
    sleep_duration_hours: Optional[float]
    sleep_quality_score: Optional[float]
    step_count: Optional[int]
    active_minutes: Optional[int]
    source: str = "simulated_wearable"
    created_at: datetime
    disclaimer: str = "Simulated wearable telemetry interface. Data represents simulated physiological signals, not real biometric device telemetry or medical diagnosis."
