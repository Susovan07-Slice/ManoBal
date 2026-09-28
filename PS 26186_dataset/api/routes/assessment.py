import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.config import logger
from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.recommendation import WelfareRecommendation
from schemas.assessment import (
    AssessmentOverride,
    StressAssessmentOut,
    RecommendationOut,
    RecommendationStatusUpdate,
    AssessmentResponse,
    AssessmentScheduleStatus,
    LongitudinalTrendResponse
)
from api.deps import get_current_user, get_current_user_optional, require_roles, check_personnel_access
from services.prediction_service import get_prediction_service
from services.longitudinal_analytics_service import LongitudinalAnalyticsService
from services.welfare_alert_service import WelfareAlertService

router = APIRouter(tags=["Stress Assessments & Welfare Recommendations"])

def _format_assessment_out(
    a: StressAssessment,
    personnel: Optional[Personnel] = None,
    meta: Optional[dict] = None
) -> StressAssessmentOut:
    """Helper to convert StressAssessment ORM to Pydantic schema with parsed factors and recommendations."""
    key_factors_parsed = []
    if a.key_factors:
        try:
            parsed = json.loads(a.key_factors)
            if isinstance(parsed, list):
                key_factors_parsed = parsed
            elif isinstance(parsed, dict):
                key_factors_parsed = parsed.get("top_risk_factors", parsed.get("key_factors", []))
            else:
                key_factors_parsed = [str(parsed)]
        except Exception:
            key_factors_parsed = [a.key_factors]

    recs_out = [
        RecommendationOut(
            id=r.id,
            personnel_id=r.personnel_id,
            assessment_id=r.assessment_id,
            recommendation_type=r.recommendation_type,
            recommendation_text=r.recommendation_text,
            priority=r.priority,
            status=r.status,
            created_at=r.created_at
        ) for r in a.recommendations
    ]

    p_code = personnel.personnel_code if personnel else (a.personnel.personnel_code if a.personnel else None)
    p_name = personnel.name if personnel else (a.personnel.name if a.personnel else None)

    score_val = float(a.risk_score)
    conf_val = "Moderate"
    uncert_val = 0.0
    trend_val = "Stable"
    change_val = 0.0
    consec_val = 0
    prob_val = round(score_val / 100.0, 3)
    percentile_val = None
    ood_val = False
    ood_reasons = []

    if meta:
        score_val = float(meta.get("risk_score", score_val))
        conf_val = meta.get("confidence", conf_val)
        uncert_val = float(meta.get("uncertainty", uncert_val))
        trend_val = meta.get("risk_trend", trend_val)
        change_val = float(meta.get("risk_change", change_val))
        consec_val = int(meta.get("consecutive_high_risk", consec_val))
        prob_val = float(meta.get("risk_probability", prob_val))
        percentile_val = meta.get("risk_percentile", None)
        ood_val = meta.get("out_of_distribution", False)
        ood_reasons = meta.get("ood_reasons", [])

    return StressAssessmentOut(
        id=a.id,
        personnel_id=a.personnel_id,
        personnel_code=p_code,
        personnel_name=p_name,
        stress_level=a.stress_level,
        low_probability=a.low_probability,
        medium_probability=a.medium_probability,
        high_probability=a.high_probability,
        risk_score=score_val,
        risk_priority=a.risk_priority,
        confidence=conf_val,
        uncertainty=uncert_val,
        risk_trend=trend_val,
        risk_change=change_val,
        consecutive_high_risk=consec_val,
        risk_probability=prob_val,
        risk_percentile=percentile_val,
        out_of_distribution=ood_val,
        ood_reasons=ood_reasons,
        key_factors=key_factors_parsed,
        model_version=a.model_version,
        assessment_timestamp=a.assessment_timestamp,
        recommendations=recs_out
    )



@router.post(
    "/personnel/{personnel_id}/assess",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger ML stress risk assessment & welfare recommendations for personnel"
)
def run_personnel_assessment(
    personnel_id: int,
    override_telemetry: Optional[AssessmentOverride] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Executes the finalized ML prediction pipeline on the personnel record,
    computes calibrated 0-100 risk score, extracts contributing factors,
    generates supportive non-punitive welfare recommendations, and persists
    the results into the database.
    """
    personnel = check_personnel_access(current_user, personnel_id, db)

    # Update personnel telemetry attributes if provided in override
    if override_telemetry:
        if override_telemetry.duty_hours_per_week is not None:
            personnel.duty_hours_per_week = override_telemetry.duty_hours_per_week
        if override_telemetry.night_shifts_per_month is not None:
            personnel.night_shifts_per_month = override_telemetry.night_shifts_per_month
        if override_telemetry.consecutive_duty_days is not None:
            personnel.consecutive_duty_days = override_telemetry.consecutive_duty_days
        if override_telemetry.leave_gap_days is not None:
            personnel.leave_gap_days = override_telemetry.leave_gap_days
        if override_telemetry.operational_exposure is not None:
            personnel.operational_exposure = override_telemetry.operational_exposure
        if override_telemetry.remote_posting is not None:
            personnel.remote_posting = override_telemetry.remote_posting

    # 1. Prepare feature dictionary for the ML inference pipeline
    duty_hours = (
        override_telemetry.duty_hours_per_week
        if override_telemetry and override_telemetry.duty_hours_per_week is not None
        else personnel.duty_hours_per_week
    )
    night_shifts = (
        override_telemetry.night_shifts_per_month
        if override_telemetry and override_telemetry.night_shifts_per_month is not None
        else personnel.night_shifts_per_month
    )
    consec_days = (
        override_telemetry.consecutive_duty_days
        if override_telemetry and override_telemetry.consecutive_duty_days is not None
        else personnel.consecutive_duty_days
    )
    leave_gap = (
        override_telemetry.leave_gap_days
        if override_telemetry and override_telemetry.leave_gap_days is not None
        else personnel.leave_gap_days
    )
    sleep = (
        override_telemetry.sleep_hours
        if override_telemetry and override_telemetry.sleep_hours is not None
        else max(4.0, 7.5 - (night_shifts * 0.12))
    )
    phys_act = (
        override_telemetry.physical_activity_hours_per_week
        if override_telemetry and override_telemetry.physical_activity_hours_per_week is not None
        else 5.0
    )
    op_exposure = (
        override_telemetry.operational_exposure
        if override_telemetry and override_telemetry.operational_exposure is not None
        else personnel.operational_exposure
    )
    remote = (
        override_telemetry.remote_posting
        if override_telemetry and override_telemetry.remote_posting is not None
        else personnel.remote_posting
    )

    burnout_val = (
        override_telemetry.burnout_symptoms
        if override_telemetry and override_telemetry.burnout_symptoms is not None
        else ('Often' if (consec_days > 14 or leave_gap > 180) else ('Sometimes' if consec_days > 7 else 'Rarely'))
    )

    satisfaction_val = (
        int(override_telemetry.mood_score)
        if override_telemetry and override_telemetry.mood_score is not None
        else 3
    )

    # Map to domain features expected by the preprocessor pipeline
    feature_dict = {
        'Age': personnel.age,
        'Gender': personnel.gender,
        'Marital_Status': 'Married' if personnel.age >= 26 else 'Single',
        'Location': personnel.location,
        'Job_Role': personnel.job_role,
        'Experience_Years': personnel.experience_years,
        'Monthly_Salary_INR': 45000.0 + (personnel.experience_years * 3200.0),
        'Company_Size': 'Large',
        'Department': personnel.department if personnel.department in ['Engineering', 'Operations', 'HR', 'Marketing'] else 'Operations',
        'Working_Hours_per_Week': duty_hours,
        'Duty_Hours_Per_Week': duty_hours,
        'Commute_Time_Hours': 0.5,
        'Remote_Work': 'No',
        'Annual_Leaves_Taken': max(0, min(30, int(personnel.experience_years * 2))),
        'Team_Size': 30,
        'Health_Issues': '',
        'Sleep_Hours': sleep,
        'Physical_Activity_Hours_per_Week': phys_act,
        'Mental_Health_Leave_Taken': 'No',
        'Burnout_Symptoms': burnout_val,
        'BusinessTravel': 'Travel_Rarely',
        'DistanceFromHome': 15.0,
        'JobLevel': min(5, max(1, int(personnel.experience_years / 5) + 1)),
        'JobSatisfaction': satisfaction_val,
        'NumCompaniesWorked': 1,
        'OverTime': 'Yes' if duty_hours > 50 else 'No',
        'PerformanceRating': 3,
        'RelationshipSatisfaction': satisfaction_val,
        'TrainingTimesLastYear': personnel.training_load,
        'WorkLifeBalance': 2 if duty_hours > 55 else 3,
        'YearsAtCompany': personnel.experience_years,
        'YearsInCurrentRole': min(personnel.experience_years, 3.0),
        'YearsSinceLastPromotion': 2.0,
        'YearsWithCurrManager': 2.0,
        'Deployment_Days': personnel.deployment_days,
        'Night_Shifts_Per_Month': night_shifts,
        'Consecutive_Duty_Days': consec_days,
        'Transfer_Frequency': personnel.transfer_frequency,
        'Training_Load': personnel.training_load,
        'Leave_Gap_Days': leave_gap,
        'Remote_Posting': remote,
        'Operational_Exposure': op_exposure,
        'physical_fatigue': override_telemetry.physical_fatigue if override_telemetry else None,
        'interest_score': override_telemetry.interest_score if override_telemetry else None,
        'discouraged_score': override_telemetry.discouraged_score if override_telemetry else None,
        'concentration_score': override_telemetry.concentration_score if override_telemetry else None,
        'mood_score': satisfaction_val
    }

    # 2. Invoke the in-memory ML inference service
    try:
        service = get_prediction_service()
        # Query preceding historical assessments for temporal signals without future leakage
        past_records = (
            db.query(StressAssessment)
            .filter(StressAssessment.personnel_id == personnel.id)
            .order_by(desc(StressAssessment.assessment_timestamp))
            .limit(10)
            .all()
        )
        past_list = [
            {
                "risk_score": p.risk_score,
                "stress_level": p.stress_level,
                "risk_priority": p.risk_priority,
                "assessment_timestamp": p.assessment_timestamp,
            }
            for p in past_records
        ]
        result = service.predictor.assess_personnel(feature_dict, past_assessments=past_list)
    except Exception as e:
        logger.error(f"Inference failure during assessment of personnel {personnel_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference pipeline execution error: {str(e)}"
        )

    # 3. Persist StressAssessment to Database
    probas = result.get("probabilities", {})
    low_p = probas.get("low", probas.get("Low", 0.0))
    med_p = probas.get("moderate", probas.get("Medium", probas.get("medium", 0.0)))
    high_p = probas.get("high", probas.get("High", 0.0)) + probas.get("critical", probas.get("Critical", 0.0))
    
    key_factors_dump = json.dumps({
        "top_risk_factors": result.get("top_risk_factors", result.get("key_factors", [])),
        "protective_factors": result.get("protective_factors", []),
        "risk_category": result.get("risk_category", "Moderate"),
        "probabilities": probas,
        "confidence": result.get("confidence", 0.85),
        "uncertainty": result.get("uncertainty", 0.15),
        "assessment_completeness": result.get("assessment_completeness", 1.0)
    })

    new_assessment = StressAssessment(
        personnel_id=personnel.id,
        stress_level=result.get("stress_level", "Medium"),
        low_probability=float(low_p),
        medium_probability=float(med_p),
        high_probability=float(high_p),
        risk_score=float(result["risk_score"]),
        risk_priority=result.get("risk_priority", "Routine"),
        key_factors=key_factors_dump,
        model_version=str(result.get("model_version", "risk_engine_v2"))[:32],
        assessment_timestamp=datetime.now(timezone.utc)
    )
    db.add(new_assessment)
    db.flush()  # Populates new_assessment.id

    # 4. Persist WelfareRecommendations to Database
    for rec in result.get("recommendations", []):
        if isinstance(rec, dict):
            rec_type = rec.get("type", "General Welfare")
            rec_text = rec.get("action", "")
            rec_priority = rec.get("priority", result["risk_priority"])
        else:
            rec_text = str(rec)
            rec_lower = rec_text.lower()
            if any(k in rec_lower for k in ["workload", "duty", "hours", "pacing"]):
                rec_type = "Workload Optimization"
            elif any(k in rec_lower for k in ["sleep", "rest", "circadian"]):
                rec_type = "Sleep & Recovery"
            elif any(k in rec_lower for k in ["leave", "block", "sanctioned"]):
                rec_type = "Restorative Leave"
            elif any(k in rec_lower for k in ["medical", "clinical", "health"]):
                rec_type = "Medical Consultation"
            elif any(k in rec_lower for k in ["interview", "counselor", "peer-support", "welfare"]):
                rec_type = "Welfare Support"
            else:
                rec_type = "Operational Adjustment"
            rec_priority = result["risk_priority"]

        welfare_rec = WelfareRecommendation(
            personnel_id=personnel.id,
            assessment_id=new_assessment.id,
            recommendation_type=rec_type,
            recommendation_text=rec_text,
            priority=rec_priority,
            status="pending",
            created_at=datetime.now(timezone.utc)
        )
        db.add(welfare_rec)

    db.commit()
    db.refresh(new_assessment)

    logger.info(
        f"Assessment recorded for {personnel.personnel_code}: Level={new_assessment.stress_level}, "
        f"Continuous Risk Score={result['risk_score']} ({new_assessment.risk_priority})"
    )

    # Trigger Welfare Alerts evaluation safely without blocking assessment response
    try:
        WelfareAlertService.evaluate_and_generate_alerts(db, personnel.id, new_assessment)
    except Exception as e:
        logger.error(f"Non-critical failure evaluating welfare alerts for personnel {personnel.id}: {e}", exc_info=True)

    # Trigger Phase 40 Welfare Recommendations evaluation safely
    try:
        from services.welfare_recommendation_service import WelfareRecommendationService
        WelfareRecommendationService.evaluate_and_generate_recommendations(personnel, db, new_assessment, persist=True)
    except Exception as re_err:
        logger.error(f"Non-critical failure evaluating welfare recommendations for personnel {personnel.id}: {re_err}", exc_info=True)

    assessment_out = _format_assessment_out(new_assessment, personnel, meta=result)
    return AssessmentResponse(
        message="Stress risk assessment and welfare recommendations successfully generated and persisted.",
        assessment=assessment_out
    )


@router.get(
    "/personnel/{personnel_id}/assessment-status",
    response_model=AssessmentScheduleStatus,
    summary="Get 24-hour assessment schedule status for personnel"
)
def get_assessment_schedule_status(
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Evaluates whether an assessment is currently due based on the authoritative
    server-side timestamp of the last completed assessment (>= 24 hours).
    New jawans with no assessment return assessment_due=True.
    """
    personnel = check_personnel_access(current_user, personnel_id, db)

    latest_assessment = (
        db.query(StressAssessment)
        .filter(StressAssessment.personnel_id == personnel_id)
        .order_by(desc(StressAssessment.assessment_timestamp))
        .first()
    )

    if not latest_assessment:
        return AssessmentScheduleStatus(
            personnel_id=personnel_id,
            has_assessment=False,
            last_assessment_at=None,
            assessment_due=True,
            hours_since_last_assessment=None,
            next_assessment_due_at=None,
            latest_stress_level=None,
            latest_risk_score=None,
            latest_priority=None,
            message="No previous assessment found on record. Initial assessment is immediately due."
        )

    now = datetime.now(timezone.utc)
    ts = latest_assessment.assessment_timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    hours_elapsed = (now - ts).total_seconds() / 3600.0
    assessment_due = hours_elapsed >= 24.0
    next_due_at = ts + timedelta(hours=24)

    msg = (
        f"Daily assessment is due ({hours_elapsed:.1f} hours elapsed since last assessment)."
        if assessment_due
        else f"Assessment completed ({hours_elapsed:.1f} hours ago; next assessment due in {max(0.0, 24.0 - hours_elapsed):.1f}h)."
    )

    return AssessmentScheduleStatus(
        personnel_id=personnel_id,
        has_assessment=True,
        last_assessment_at=ts,
        assessment_due=assessment_due,
        hours_since_last_assessment=round(hours_elapsed, 2),
        next_assessment_due_at=next_due_at,
        latest_stress_level=latest_assessment.stress_level,
        latest_risk_score=float(latest_assessment.risk_score) if latest_assessment.risk_score is not None else None,
        latest_priority=latest_assessment.risk_priority,
        message=msg
    )


@router.get(
    "/assessment/status",
    response_model=AssessmentScheduleStatus,
    summary="Get current authenticated user's 24-hour assessment schedule status"
)
def get_current_user_assessment_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Convenience endpoint returning the authoritative 24-hour assessment schedule status
    for the currently logged in Jawan. For administrative/officer accounts without a linked
    personnel profile, returns a graceful informational status.
    """
    if not current_user.personnel_id:
        return AssessmentScheduleStatus(
            personnel_id=0,
            has_assessment=False,
            last_assessment_at=None,
            assessment_due=False,
            hours_since_last_assessment=None,
            next_assessment_due_at=None,
            latest_stress_level=None,
            latest_risk_score=None,
            latest_priority=None,
            message="Assessment schedule is only applicable to personnel accounts."
        )
    return get_assessment_schedule_status(current_user.personnel_id, db, current_user)



@router.get(
    "/personnel/{personnel_id}/assessments",
    response_model=List[StressAssessmentOut],
    summary="Get assessment history for specific personnel record"
)
def get_personnel_assessments(
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the historical timeline of stress assessments for a given personnel.
    Protected by RBAC (Personnel can only access their own history).
    """
    personnel = check_personnel_access(current_user, personnel_id, db)

    assessments = (
        db.query(StressAssessment)
        .filter(StressAssessment.personnel_id == personnel_id)
        .order_by(desc(StressAssessment.assessment_timestamp))
        .all()
    )

    return [_format_assessment_out(a, personnel) for a in assessments]


@router.get(
    "/personnel/{personnel_id}/trend",
    response_model=LongitudinalTrendResponse,
    summary="Get longitudinal welfare trend intelligence for personnel"
)
def get_personnel_trend(
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves longitudinal trend analytics for a given personnel.
    Protected by RBAC.
    """
    personnel = check_personnel_access(current_user, personnel_id, db)

    # Fetch all past assessments for the personnel
    assessments = (
        db.query(StressAssessment)
        .filter(StressAssessment.personnel_id == personnel_id)
        .order_by(desc(StressAssessment.assessment_timestamp))
        .all()
    )

    return LongitudinalAnalyticsService.calculate_longitudinal_trend(
        personnel_id=personnel_id,
        assessments=assessments
    )

@router.get(
    "/assessments/{assessment_id}",
    response_model=StressAssessmentOut,
    summary="Retrieve individual assessment details by ID"
)
def get_assessment_by_id(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a single assessment by ID with its key factors and recommendations.
    Enforces RBAC verification.
    """
    assessment = db.query(StressAssessment).filter(StressAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment ID {assessment_id} not found."
        )

    check_personnel_access(current_user, assessment.personnel_id, db)
    return _format_assessment_out(assessment)


@router.patch(
    "/recommendations/{recommendation_id}/status",
    response_model=RecommendationOut,
    summary="Update welfare recommendation status (Welfare / Officer / Admin / Personnel)"
)
def update_recommendation_status(
    recommendation_id: int,
    status_update: RecommendationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare", "personnel"))
):
    """
    Updates the lifecycle status of a welfare recommendation.
    Restricted to Welfare Counselor, Officer, Admin, or the assigned Personnel themselves.
    """
    rec = db.query(WelfareRecommendation).filter(WelfareRecommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Welfare recommendation ID {recommendation_id} not found."
        )

    # Anti-IDOR check for personnel role
    if current_user.role == "personnel":
        if current_user.personnel_id != rec.personnel_id:
            logger.warning(
                f"IDOR Violation: Personnel '{current_user.username}' attempted to update recommendation #{recommendation_id} belonging to personnel #{rec.personnel_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only update recommendations assigned to your own record."
            )

    # Organizational scope verification for officers/welfare
    if current_user.role in ["officer", "welfare"]:
        user_battalion = (current_user.battalion or "").strip().lower()
        p_battalion = (rec.personnel.battalion or "").strip().lower()
        if user_battalion and p_battalion and user_battalion != p_battalion:
            logger.warning(
                f"Scope Violation: User '{current_user.username}' attempted to update out-of-scope recommendation ID {recommendation_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Linked personnel is outside your assigned Battalion scope."
            )

    rec.status = status_update.status
    db.commit()
    db.refresh(rec)
    logger.info(f"Recommendation ID {recommendation_id} status changed to '{rec.status}' by {current_user.username}")
    return rec


@router.post(
    "/welfare/assessment",
    status_code=status.HTTP_200_OK,
    summary="Personnel Welfare Risk Engine V2 assessment endpoint (Section 24)"
)
def welfare_assessment_endpoint(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Direct probabilistic welfare inference conforming to Section 24 specification:
    Combines Jawan assessment with available personnel telemetry and persists the record.
    """
    raw_assessment = payload.get("assessment", payload)
    personnel_id = payload.get("personnel_id")
    personnel = None
    if personnel_id:
        if current_user:
            # Anti-IDOR & Scope enforcement: validates Jawan ownership or Officer battalion scope
            personnel = check_personnel_access(current_user, personnel_id, db)
        else:
            # Unauthenticated requests cannot bind and persist assessments to arbitrary personnel profiles
            personnel = None
    elif current_user and getattr(current_user, "personnel_id", None):
        personnel = db.query(Personnel).filter(Personnel.id == current_user.personnel_id).first()

    eval_record = dict(raw_assessment)
    past_list = []
    if personnel:
        for k, v in {
            "Age": personnel.age,
            "Gender": personnel.gender,
            "duty_hours_per_week": personnel.duty_hours_per_week,
            "consecutive_duty_days": personnel.consecutive_duty_days,
            "night_shifts_per_month": personnel.night_shifts_per_month,
            "operational_exposure": personnel.operational_exposure,
            "leave_gap_days": personnel.leave_gap_days,
            "remote_posting": personnel.remote_posting
        }.items():
            if eval_record.get(k) is None:
                eval_record[k] = v

        past_records = (
            db.query(StressAssessment)
            .filter(StressAssessment.personnel_id == personnel.id)
            .order_by(desc(StressAssessment.assessment_timestamp))
            .limit(10)
            .all()
        )
        past_list = [{"risk_score": p.risk_score, "stress_level": p.stress_level} for p in past_records]

    service = get_prediction_service()
    res = service.predictor.assess_personnel(eval_record, past_assessments=past_list)

    if res.get("risk_score") is None and res.get("error"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": res["error"],
                "validation_errors": res.get("validation_errors", [res["error"]]),
                "risk_category": res.get("risk_category", "Invalid Input")
            }
        )

    if personnel and res.get("risk_score") is not None:
        try:
            probas = res.get("probabilities", {})
            low_p = probas.get("low", probas.get("Low", 0.0))
            med_p = probas.get("moderate", probas.get("Medium", 0.0))
            high_p = probas.get("high", 0.0) + probas.get("critical", 0.0)
            new_ass = StressAssessment(
                personnel_id=personnel.id,
                stress_level=res.get("stress_level", "Medium"),
                low_probability=float(low_p),
                medium_probability=float(med_p),
                high_probability=float(high_p),
                risk_score=float(res["risk_score"]),
                risk_priority=res.get("risk_priority", "Routine"),
                key_factors=json.dumps({
                    "top_risk_factors": res.get("top_risk_factors", []),
                    "protective_factors": res.get("protective_factors", []),
                    "risk_category": res.get("risk_category", "Moderate"),
                    "probabilities": probas,
                    "confidence": res.get("confidence", 0.85),
                    "uncertainty": res.get("uncertainty", 0.15)
                }),
                model_version="risk_engine_v2",
                assessment_timestamp=datetime.now(timezone.utc)
            )
            db.add(new_ass)
            db.commit()
            db.refresh(new_ass)
            
            # Trigger Welfare Alerts evaluation
            WelfareAlertService.evaluate_and_generate_alerts(db, personnel.id, new_ass)

            # Trigger Phase 40 Welfare Recommendations evaluation
            try:
                from services.welfare_recommendation_service import WelfareRecommendationService
                WelfareRecommendationService.evaluate_and_generate_recommendations(personnel, db, new_ass, persist=True)
            except Exception as re_err:
                logger.warning(f"Could not generate welfare recommendations: {re_err}")
            
        except Exception as e:
            db.rollback()
            logger.warning(f"Could not persist welfare assessment: {e}")

    return {
        "risk_score": res.get("risk_score"),
        "risk_category": res.get("risk_category", "Moderate"),
        "probabilities": res.get("probabilities"),
        "confidence": res.get("confidence", 0.85),
        "uncertainty": res.get("uncertainty", 0.15),
        "assessment_completeness": res.get("assessment_completeness", 1.0),
        "top_risk_factors": res.get("top_risk_factors", []),
        "protective_factors": res.get("protective_factors", []),
        "model_version": "risk_engine_v2",
        "recommendations": res.get("recommendations", [])
    }

