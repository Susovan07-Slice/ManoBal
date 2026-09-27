import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.recommendation import WelfareRecommendation
from db.models.welfare_request import WelfareRequest
from schemas.dashboard import (
    DashboardSummary,
    RiskDistributionResponse,
    StressDistributionResponse,
    DistributionItem,
    RecentAssessmentItem,
    HighRiskPersonnelItem
)
from api.deps import require_roles

router = APIRouter(prefix="/dashboard", tags=["Dashboard Aggregates & Analytics"])

def _get_latest_assessments_subquery(db: Session):
    """
    Subquery that returns the latest assessment ID for each personnel.
    """
    subq = (
        db.query(
            StressAssessment.personnel_id,
            func.max(StressAssessment.id).label("max_assessment_id")
        )
        .group_by(StressAssessment.personnel_id)
        .subquery()
    )
    return subq

def _apply_scope(query, model, current_user: User):
    """
    Applies organizational scope filter to a query joined with Personnel.
    """
    if current_user.role in ["officer", "welfare"]:
        user_battalion = (current_user.battalion or "").strip().lower()
        if user_battalion:
            query = query.filter(func.lower(Personnel.battalion) == user_battalion)
    return query


def _apply_scope_welfare_requests(query, current_user: User):
    if current_user.role in ["officer", "welfare"]:
        user_battalion = (current_user.battalion or "").strip().lower()
        if user_battalion:
            query = query.filter(
                func.lower(func.coalesce(WelfareRequest.battalion, Personnel.battalion)) == user_battalion
            )
    return query


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Get high-level operational stress & welfare summary metrics (Scope Enforced)"
)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    """
    Computes real-time aggregate statistics.
    For Officers and Welfare roles, metrics are strictly constrained to their
    assigned Battalion scope.
    """
    # 1. Total personnel in scope
    p_query = db.query(Personnel)
    if current_user.role in ["officer", "welfare"]:
        user_battalion = (current_user.battalion or "").strip().lower()
        if user_battalion:
            p_query = p_query.filter(func.lower(Personnel.battalion) == user_battalion)
    total_personnel = p_query.count()

    # 2. Latest assessment per personnel in scope
    latest_subq = _get_latest_assessments_subquery(db)
    ass_query = (
        db.query(StressAssessment)
        .join(latest_subq, StressAssessment.id == latest_subq.c.max_assessment_id)
        .join(Personnel, StressAssessment.personnel_id == Personnel.id)
    )
    ass_query = _apply_scope(ass_query, Personnel, current_user)
    latest_assessments = ass_query.all()

    assessed_count = len(latest_assessments)
    low_risk = sum(1 for a in latest_assessments if a.risk_priority.lower() == "routine")
    med_risk = sum(1 for a in latest_assessments if a.risk_priority.lower() == "preventive")
    high_risk = sum(1 for a in latest_assessments if a.risk_priority.lower() == "priority")

    # 3. Scope-filtered active recommendations and welfare requests
    ai_pending_query = (
        db.query(WelfareRecommendation)
        .join(Personnel, WelfareRecommendation.personnel_id == Personnel.id)
        .filter(WelfareRecommendation.status == "pending")
    )
    ai_pending_query = _apply_scope(ai_pending_query, Personnel, current_user)
    pending_ai_recs = ai_pending_query.count()

    jawan_pending_query = (
        db.query(WelfareRequest)
        .join(Personnel, WelfareRequest.personnel_id == Personnel.id)
        .filter(WelfareRequest.status == "pending")
    )
    jawan_pending_query = _apply_scope_welfare_requests(jawan_pending_query, current_user)
    pending_jawan_reqs = jawan_pending_query.count()

    pending_total = pending_ai_recs + pending_jawan_reqs

    ai_ack_query = (
        db.query(WelfareRecommendation)
        .join(Personnel, WelfareRecommendation.personnel_id == Personnel.id)
        .filter(WelfareRecommendation.status == "acknowledged")
    )
    ai_ack_query = _apply_scope(ai_ack_query, Personnel, current_user)
    ack_ai_recs = ai_ack_query.count()

    jawan_ack_query = (
        db.query(WelfareRequest)
        .join(Personnel, WelfareRequest.personnel_id == Personnel.id)
        .filter(WelfareRequest.status.in_(["acknowledged", "in_progress"]))
    )
    jawan_ack_query = _apply_scope_welfare_requests(jawan_ack_query, current_user)
    ack_jawan_reqs = jawan_ack_query.count()

    ack_total = ack_ai_recs + ack_jawan_reqs

    return DashboardSummary(
        total_personnel=total_personnel,
        assessed_personnel=assessed_count,
        low_risk=low_risk,
        medium_risk=med_risk,
        high_risk=high_risk,
        pending_recommendations=pending_total,
        acknowledged_recommendations=ack_total
    )


@router.get(
    "/stress-distribution",
    response_model=StressDistributionResponse,
    summary="Get categorical stress level breakdown (Low, Medium, High) (Scope Enforced)"
)
def get_stress_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    """
    Returns breakdown and percentages of personnel by their latest predicted stress level within scope.
    """
    latest_subq = _get_latest_assessments_subquery(db)
    query = (
        db.query(StressAssessment)
        .join(latest_subq, StressAssessment.id == latest_subq.c.max_assessment_id)
        .join(Personnel, StressAssessment.personnel_id == Personnel.id)
    )
    query = _apply_scope(query, Personnel, current_user)
    latest_assessments = query.all()

    total = len(latest_assessments)
    counts = {"Low": 0, "Medium": 0, "High": 0}
    for a in latest_assessments:
        tier = a.stress_level.capitalize()
        if tier in counts:
            counts[tier] += 1
        else:
            counts[tier] = 1

    distribution = []
    for label in ["Low", "Medium", "High"]:
        cnt = counts.get(label, 0)
        pct = round((cnt / total * 100.0), 1) if total > 0 else 0.0
        distribution.append(DistributionItem(label=label, count=cnt, percentage=pct))

    return StressDistributionResponse(total_assessed=total, distribution=distribution)


@router.get(
    "/risk-distribution",
    response_model=RiskDistributionResponse,
    summary="Get welfare intervention priority distribution (Scope Enforced)"
)
def get_risk_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    """
    Returns breakdown and percentages of personnel by operational welfare priority within scope.
    """
    latest_subq = _get_latest_assessments_subquery(db)
    query = (
        db.query(StressAssessment)
        .join(latest_subq, StressAssessment.id == latest_subq.c.max_assessment_id)
        .join(Personnel, StressAssessment.personnel_id == Personnel.id)
    )
    query = _apply_scope(query, Personnel, current_user)
    latest_assessments = query.all()

    total = len(latest_assessments)
    counts = {"Routine": 0, "Preventive": 0, "Priority": 0}
    for a in latest_assessments:
        priority = a.risk_priority.capitalize()
        if priority in counts:
            counts[priority] += 1
        else:
            counts[priority] = 1

    distribution = []
    for label in ["Routine", "Preventive", "Priority"]:
        cnt = counts.get(label, 0)
        pct = round((cnt / total * 100.0), 1) if total > 0 else 0.0
        distribution.append(DistributionItem(label=label, count=cnt, percentage=pct))

    return RiskDistributionResponse(total_assessed=total, distribution=distribution)


@router.get(
    "/recent-assessments",
    response_model=List[RecentAssessmentItem],
    summary="Retrieve most recent stress assessments within scope"
)
def get_recent_assessments(
    limit: int = Query(10, ge=1, le=50, description="Max recent assessments to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    """
    Returns the latest chronological assessments with associated personnel metadata in scope.
    """
    query = (
        db.query(StressAssessment)
        .join(Personnel, StressAssessment.personnel_id == Personnel.id)
    )
    query = _apply_scope(query, Personnel, current_user)
    assessments = query.order_by(desc(StressAssessment.assessment_timestamp)).limit(limit).all()

    results = []
    for a in assessments:
        results.append(RecentAssessmentItem(
            id=a.id,
            personnel_id=a.personnel_id,
            personnel_code=a.personnel.personnel_code,
            personnel_name=a.personnel.name,
            department=a.personnel.department,
            battalion=a.personnel.battalion,
            location=a.personnel.location,
            stress_level=a.stress_level,
            risk_score=a.risk_score,
            risk_priority=a.risk_priority,
            assessment_timestamp=a.assessment_timestamp
        ))
    return results


@router.get(
    "/high-risk",
    response_model=List[HighRiskPersonnelItem],
    summary="List personnel flagged with Priority risk or high stress within scope"
)
def get_high_risk_personnel(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    """
    Retrieves all personnel within the commander's assigned battalion and location scope
    whose latest assessment indicates 'Priority' status or elevated risk scores.
    """
    latest_subq = _get_latest_assessments_subquery(db)
    query = (
        db.query(StressAssessment)
        .join(latest_subq, StressAssessment.id == latest_subq.c.max_assessment_id)
        .join(Personnel, StressAssessment.personnel_id == Personnel.id)
        .filter((StressAssessment.risk_priority == "Priority") | (StressAssessment.risk_score >= 60))
    )
    query = _apply_scope(query, Personnel, current_user)
    high_risk_assessments = query.order_by(desc(StressAssessment.risk_score)).all()

    results = []
    for a in high_risk_assessments:
        p = a.personnel
        key_factors = []
        if a.key_factors:
            try:
                key_factors = json.loads(a.key_factors)
            except Exception:
                key_factors = [a.key_factors]

        pending_recs = db.query(WelfareRecommendation).filter(
            WelfareRecommendation.personnel_id == p.id,
            WelfareRecommendation.status == "pending"
        ).count()

        results.append(HighRiskPersonnelItem(
            id=a.id,
            personnel_id=p.id,
            personnel_code=p.personnel_code,
            personnel_name=p.name,
            department=p.department,
            battalion=p.battalion,
            job_role=p.job_role,
            location=p.location,
            risk_score=a.risk_score,
            stress_level=a.stress_level,
            risk_priority=a.risk_priority,
            duty_hours_per_week=p.duty_hours_per_week,
            night_shifts_per_month=p.night_shifts_per_month,
            consecutive_duty_days=p.consecutive_duty_days,
            leave_gap_days=p.leave_gap_days,
            key_factors=key_factors,
            pending_recommendations_count=pending_recs,
            latest_assessment_date=a.assessment_timestamp
        ))

    return results
