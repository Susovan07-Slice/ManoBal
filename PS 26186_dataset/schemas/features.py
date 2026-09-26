from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

class HrmsFeatureSet(BaseModel):
    """
    Structured feature set derived from HRMS records and personnel registry.
    Explicitly marked as simulated/mock data.
    """
    model_config = ConfigDict(from_attributes=True)

    has_hrms_record: bool = Field(..., description="Whether a dedicated HRMS service record is linked")
    source: str = Field("mock_hrms", description="Source identifier - synthetic mock HRMS")
    is_simulated: bool = Field(True, description="Strict synthetic data indicator")
    service_number: Optional[str] = Field(None, description="Official service / personnel identifier")
    years_of_service: Optional[float] = Field(None, description="Total active service experience in years")
    leave_balance_days: Optional[int] = Field(None, description="Sanctioned remaining leave balance")
    leaves_taken_past_year: Optional[int] = Field(None, description="Sanctioned leave days utilized in trailing year")
    duty_hours_per_week: Optional[float] = Field(None, description="Average operational duty hours per week")
    consecutive_days_on_duty: Optional[int] = Field(None, description="Continuous operational duty days without rest")
    deployment_history_raw: Optional[str] = Field(None, description="Raw deployment history text preserved without fabricated NLP parsing")
    transfer_history_raw: Optional[str] = Field(None, description="Raw transfer history text preserved without fabricated NLP parsing")
    training_history_raw: Optional[str] = Field(None, description="Raw training history text preserved without fabricated NLP parsing")
    transfer_count: Optional[int] = Field(None, description="Structured unit transfer count where reliably recorded")
    recent_transfer_indicator: Optional[bool] = Field(None, description="Boolean indicator of recent transfer activity")
    training_load: Optional[int] = Field(None, description="Active training intensity load score")
    synced_at: Optional[datetime] = Field(None, description="Timestamp of most recent HRMS synchronization")


class WearableWindowFeatureSet(BaseModel):
    """
    Aggregated physiological and activity feature window over wearable telemetry.
    Explicitly marked as simulated/mock data.
    """
    model_config = ConfigDict(from_attributes=True)

    window_days: int = Field(..., description="Duration of observation window in days (e.g., 7 or 30)")
    window_start: datetime = Field(..., description="Inclusive start boundary of aggregation window")
    window_end: datetime = Field(..., description="Inclusive reference time end boundary of aggregation window")
    observation_count: int = Field(..., description="Total telemetry observation records available in window")
    data_available: bool = Field(..., description="True if at least one valid observation exists in window")
    data_sufficiency: Literal["sufficient", "partial", "no_data"] = Field(
        ..., description="Data completeness status (sufficient, partial, or no_data)"
    )
    latest_recorded_at: Optional[datetime] = Field(None, description="Timestamp of latest observation in window")
    source: str = Field("simulated_wearable", description="Source identifier - simulated wearable signal")
    is_simulated: bool = Field(True, description="Strict synthetic data indicator")

    # Heart rate aggregates
    mean_heart_rate: Optional[float] = Field(None, description="Mean heart rate in bpm across window")
    min_heart_rate: Optional[float] = Field(None, description="Minimum heart rate in bpm across window")
    max_heart_rate: Optional[float] = Field(None, description="Maximum heart rate in bpm across window")
    heart_rate_std: Optional[float] = Field(None, description="Sample standard deviation of heart rate")

    # HRV aggregates (RMSSD)
    mean_hrv_rmssd: Optional[float] = Field(None, description="Mean HRV RMSSD in milliseconds across window")
    min_hrv_rmssd: Optional[float] = Field(None, description="Minimum HRV RMSSD in milliseconds across window")
    hrv_rmssd_std: Optional[float] = Field(None, description="Sample standard deviation of HRV RMSSD")

    # Sleep aggregates
    mean_sleep_duration: Optional[float] = Field(None, description="Mean daily sleep duration in hours")
    min_sleep_duration: Optional[float] = Field(None, description="Minimum single-night sleep duration in hours")
    sleep_duration_std: Optional[float] = Field(None, description="Sample standard deviation of sleep duration")
    mean_sleep_quality: Optional[float] = Field(None, description="Mean self-reported or device sleep quality score (0-100)")

    # Activity aggregates
    mean_step_count: Optional[float] = Field(None, description="Mean daily step count across window")
    mean_active_minutes: Optional[float] = Field(None, description="Mean daily active minutes across window")


class DataQualitySummary(BaseModel):
    """
    Summary of data sufficiency across HRMS and wearable data streams.
    """
    has_hrms: bool = Field(..., description="Whether service records exist")
    wearable_7d_observations: int = Field(..., description="Count of wearable records in 7-day window")
    wearable_30d_observations: int = Field(..., description="Count of wearable records in 30-day window")
    status: Literal["complete", "partial", "no_wearable_data", "no_data"] = Field(
        ..., description="Overall ingestion data completeness tier"
    )
    data_completeness: str = Field(..., description="Human-readable explanation of available signal streams")


class PersonnelFeatureSnapshotResponse(BaseModel):
    """
    Deterministic analytical feature snapshot for a single personnel record.
    Consolidates HRMS, 7-day wearable, and 30-day wearable signals.
    """
    model_config = ConfigDict(from_attributes=True)

    personnel_id: int = Field(..., description="Internal personnel identifier")
    personnel_code: Optional[str] = Field(None, description="Military personnel code / badge number")
    battalion: Optional[str] = Field(None, description="Assigned organizational unit / battalion")
    location: Optional[str] = Field(None, description="Duty posting base location")
    reference_time: datetime = Field(..., description="Reference UTC anchor timestamp used for window aggregation")
    hrms_features: HrmsFeatureSet = Field(..., description="Derived service and duty features")
    wearable_7d: WearableWindowFeatureSet = Field(..., description="7-day rolling telemetry aggregates")
    wearable_30d: WearableWindowFeatureSet = Field(..., description="30-day rolling telemetry aggregates")
    data_quality: DataQualitySummary = Field(..., description="Data quality and observation availability indicators")
    disclaimer: str = Field(
        default=(
            "Synthetic / Simulated Decision-Support Notice: All HRMS and wearable telemetry signals "
            "are simulated indicators. Derived features represent contextual operational indicators "
            "and are strictly NOT medical diagnoses, clinical assessments, or disciplinary criteria."
        ),
        description="Mandatory medical and operational safety notice"
    )
