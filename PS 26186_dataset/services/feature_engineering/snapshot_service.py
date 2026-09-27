from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from schemas.features import (
    PersonnelFeatureSnapshotResponse,
    DataQualitySummary,
)
from services.feature_engineering.hrms_features import extract_hrms_features
from services.feature_engineering.wearable_features import compute_wearable_window_features

class FeatureSnapshotService:
    """
    Coordinates HRMS service data and rolling time-series wearable aggregations
    into deterministic analytical feature snapshots and risk contextual summaries.
    """

    @staticmethod
    def generate_snapshot(
        personnel: Personnel,
        db: Session,
        reference_time: Optional[datetime] = None
    ) -> PersonnelFeatureSnapshotResponse:
        """
        Builds a comprehensive, deterministic analytical feature snapshot for a given personnel.
        """
        if reference_time is None:
            ref_time = datetime.now(timezone.utc)
        else:
            ref_time = reference_time if reference_time.tzinfo is not None else reference_time.replace(tzinfo=timezone.utc)

        # 1. Derive HRMS indicators
        hrms_feat = extract_hrms_features(personnel)

        # 2. Derive rolling wearable indicators (7 days and 30 days)
        w7 = compute_wearable_window_features(
            personnel_id=personnel.id,
            window_days=7,
            db=db,
            reference_time=ref_time
        )
        w30 = compute_wearable_window_features(
            personnel_id=personnel.id,
            window_days=30,
            db=db,
            reference_time=ref_time
        )

        # 3. Assess overall multi-stream data quality
        has_hrms = hrms_feat.has_hrms_record
        if has_hrms and w7.data_available and w30.data_available:
            quality_status = "complete" if (w7.data_sufficiency == "sufficient") else "partial"
            quality_desc = f"HRMS synced. Wearable telemetry active ({w7.observation_count} obs/7d, {w30.observation_count} obs/30d)."
        elif has_hrms and not w7.data_available:
            quality_status = "no_wearable_data"
            quality_desc = "HRMS synced. No wearable telemetry recorded in trailing 7-30 days."
        elif not has_hrms and w7.data_available:
            quality_status = "partial"
            quality_desc = f"HRMS record absent. Wearable telemetry active ({w7.observation_count} obs/7d)."
        else:
            quality_status = "no_data"
            quality_desc = "Both HRMS service record and wearable telemetry are unpopulated for this personnel."

        data_quality = DataQualitySummary(
            has_hrms=has_hrms,
            wearable_7d_observations=w7.observation_count,
            wearable_30d_observations=w30.observation_count,
            status=quality_status,
            data_completeness=quality_desc
        )

        return PersonnelFeatureSnapshotResponse(
            personnel_id=personnel.id,
            personnel_code=personnel.personnel_code,
            battalion=personnel.battalion,
            location=personnel.location,
            reference_time=ref_time,
            hrms_features=hrms_feat,
            wearable_7d=w7,
            wearable_30d=w30,
            data_quality=data_quality
        )

    @staticmethod
    def get_contextual_risk_summary(
        personnel: Personnel,
        db: Session,
        reference_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Integrates current ML inference / latest assessment with the Phase 32
        derived HRMS and wearable feature layer.
        Preserves model prediction intact without arbitrary hand-weighted alterations.
        """
        snapshot = FeatureSnapshotService.generate_snapshot(personnel, db, reference_time=reference_time)

        # Retrieve latest recorded assessment if available
        latest_assessment = (
            db.query(StressAssessment)
            .filter(StressAssessment.personnel_id == personnel.id)
            .order_by(StressAssessment.assessment_timestamp.desc())
            .first()
        )

        assessment_summary = None
        if latest_assessment:
            assessment_summary = {
                "assessment_id": latest_assessment.id,
                "stress_level": latest_assessment.stress_level,
                "risk_score": float(latest_assessment.risk_score),
                "risk_priority": latest_assessment.risk_priority,
                "timestamp": latest_assessment.assessment_timestamp
            }

        return {
            "personnel_id": personnel.id,
            "personnel_code": personnel.personnel_code,
            "reference_time": snapshot.reference_time,
            "latest_ml_assessment": assessment_summary,
            "hrms_context": snapshot.hrms_features.model_dump(),
            "wearable_context_7d": snapshot.wearable_7d.model_dump(),
            "wearable_context_30d": snapshot.wearable_30d.model_dump(),
            "data_quality": snapshot.data_quality.model_dump(),
            "contextual_safety_notice": (
                "Operational contextual feature integration: Wearable signals (HR, HRV, sleep, activity) "
                "and HRMS indicators provide supplementary decision-support context alongside calibrated ML "
                "predictions. These features are non-diagnostic and do not alter the validated ML model artifact."
            )
        }
