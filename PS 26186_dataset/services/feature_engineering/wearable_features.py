import statistics
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from db.models.telemetry import WearableTelemetry
from schemas.features import WearableWindowFeatureSet

def compute_wearable_window_features(
    personnel_id: int,
    window_days: int,
    db: Session,
    reference_time: Optional[datetime] = None
) -> WearableWindowFeatureSet:
    """
    Computes deterministic statistical aggregations over wearable telemetry within
    a specified window (e.g., 7 or 30 days) ending at reference_time.
    If observation_count is 0, metric values are set to None (never fabricated zeroes).
    """
    if reference_time is None:
        ref_time = datetime.now(timezone.utc)
    else:
        ref_time = reference_time if reference_time.tzinfo is not None else reference_time.replace(tzinfo=timezone.utc)

    window_start = ref_time - timedelta(days=window_days)

    records: List[WearableTelemetry] = (
        db.query(WearableTelemetry)
        .filter(
            WearableTelemetry.personnel_id == personnel_id,
            WearableTelemetry.recorded_at >= window_start,
            WearableTelemetry.recorded_at <= ref_time
        )
        .order_by(WearableTelemetry.recorded_at.desc())
        .all()
    )

    obs_count = len(records)
    if obs_count == 0:
        return WearableWindowFeatureSet(
            window_days=window_days,
            window_start=window_start,
            window_end=ref_time,
            observation_count=0,
            data_available=False,
            data_sufficiency="no_data",
            latest_recorded_at=None,
            source="simulated_wearable",
            is_simulated=True,
            mean_heart_rate=None,
            min_heart_rate=None,
            max_heart_rate=None,
            heart_rate_std=None,
            mean_hrv_rmssd=None,
            min_hrv_rmssd=None,
            hrv_rmssd_std=None,
            mean_sleep_duration=None,
            min_sleep_duration=None,
            sleep_duration_std=None,
            mean_sleep_quality=None,
            mean_step_count=None,
            mean_active_minutes=None,
        )

    # Filter non-null metrics
    hrs = [float(r.heart_rate) for r in records if r.heart_rate is not None]
    hrvs = [float(r.hrv_rmssd) for r in records if r.hrv_rmssd is not None]
    sleeps = [float(r.sleep_duration_hours) for r in records if r.sleep_duration_hours is not None]
    sleep_quals = [float(r.sleep_quality_score) for r in records if r.sleep_quality_score is not None]
    steps = [float(r.step_count) for r in records if r.step_count is not None]
    acts = [float(r.active_minutes) for r in records if r.active_minutes is not None]

    latest_ts = max(r.recorded_at for r in records)
    min_sufficient = 3 if window_days <= 7 else 10
    sufficiency = "sufficient" if obs_count >= min_sufficient else "partial"

    def _calc_std(data: List[float]) -> Optional[float]:
        if len(data) > 1:
            return round(float(statistics.stdev(data)), 3)
        elif len(data) == 1:
            return 0.0
        return None

    return WearableWindowFeatureSet(
        window_days=window_days,
        window_start=window_start,
        window_end=ref_time,
        observation_count=obs_count,
        data_available=True,
        data_sufficiency=sufficiency,
        latest_recorded_at=latest_ts,
        source="simulated_wearable",
        is_simulated=True,
        mean_heart_rate=round(float(statistics.mean(hrs)), 2) if hrs else None,
        min_heart_rate=round(float(min(hrs)), 2) if hrs else None,
        max_heart_rate=round(float(max(hrs)), 2) if hrs else None,
        heart_rate_std=_calc_std(hrs),
        mean_hrv_rmssd=round(float(statistics.mean(hrvs)), 2) if hrvs else None,
        min_hrv_rmssd=round(float(min(hrvs)), 2) if hrvs else None,
        hrv_rmssd_std=_calc_std(hrvs),
        mean_sleep_duration=round(float(statistics.mean(sleeps)), 2) if sleeps else None,
        min_sleep_duration=round(float(min(sleeps)), 2) if sleeps else None,
        sleep_duration_std=_calc_std(sleeps),
        mean_sleep_quality=round(float(statistics.mean(sleep_quals)), 2) if sleep_quals else None,
        mean_step_count=round(float(statistics.mean(steps)), 1) if steps else None,
        mean_active_minutes=round(float(statistics.mean(acts)), 1) if acts else None,
    )
