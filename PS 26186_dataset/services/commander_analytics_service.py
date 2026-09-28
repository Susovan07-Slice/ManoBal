import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from core.config import logger
from db.models.user import User
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.alert import WelfareAlert, WelfareIntervention
from services.longitudinal_analytics_service import LongitudinalAnalyticsService
from schemas.commander_analytics import (
    CommanderAnalyticsResponse,
    ScopeInfo,
    RiskDistributionSection,
    RiskCategoryDistributionItem,
    TrendSection,
    TimelinePoint,
    AlertsSection,
    AlertTimelinePoint,
    WelfareFactorsSection,
    WelfareFactorItem,
    InterventionsSection,
    SummarySection,
    DateRangeInfo,
    DataQualitySection,
)

# Configurable minimum population size for privacy / small group protection (k-anonymity)
ANALYTICS_MIN_GROUP_SIZE = int(os.getenv("ANALYTICS_MIN_GROUP_SIZE", "5"))


class CommanderAnalyticsService:
    """
    Phase 38: Centralized Commander Analytics & Unit-Level Welfare Intelligence Service.
    Aggregates authoritative Phase 34 V2 assessments, Phase 36 longitudinal monitoring,
    and Phase 37 welfare alerts strictly within the authenticated user's authorized organizational scope.
    """

    @staticmethod
    def get_v2_category(score: float) -> str:
        """Authoritative Phase 34 V2 risk classification."""
        if score >= 85.0:
            return "Critical"
        elif score >= 70.0:
            return "High"
        elif score >= 55.0:
            return "Elevated"
        elif score >= 35.0:
            return "Moderate"
        else:
            return "Low"

    @classmethod
    def resolve_date_filter(
        cls,
        time_filter: str = "30d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        reference_time: Optional[datetime] = None
    ) -> Tuple[Optional[datetime], Optional[datetime], str]:
        """
        Parses time filter and returns (start_dt, end_dt, filter_type).
        """
        now = reference_time or datetime.now(timezone.utc)
        filter_type = time_filter.lower() if time_filter else "30d"

        if filter_type == "custom":
            start_dt = None
            end_dt = None
            if start_date:
                try:
                    s_clean = start_date.strip().replace(" ", "+")
                    if s_clean.endswith("Z") or s_clean.endswith("z"):
                        s_clean = s_clean[:-1] + "+00:00"
                    start_dt = datetime.fromisoformat(s_clean)
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=timezone.utc)
                except Exception:
                    start_dt = None
            if end_date:
                try:
                    e_clean = end_date.strip().replace(" ", "+")
                    if e_clean.endswith("Z") or e_clean.endswith("z"):
                        e_clean = e_clean[:-1] + "+00:00"
                    end_dt = datetime.fromisoformat(e_clean)
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=timezone.utc)
                except Exception:
                    end_dt = None
            return start_dt, end_dt, "custom"

        if filter_type == "7d":
            return now - timedelta(days=7), now, "7d"
        elif filter_type == "90d":
            return now - timedelta(days=90), now, "90d"
        elif filter_type == "all":
            return None, None, "all"
        else:  # default 30d
            return now - timedelta(days=30), now, "30d"

    @classmethod
    def get_scoped_personnel_query(cls, db: Session, current_user: User):
        """
        Builds a base Personnel query strictly bound to user's authorized scope.
        Officer / Welfare: restricted to current_user.battalion AND current_user.location (if configured).
        Admin: system-wide.
        Personnel role: blocked by caller (403).
        """
        p_query = db.query(Personnel)
        if current_user.role in ["officer", "welfare"]:
            user_battalion = (current_user.battalion or "").strip().lower()
            if user_battalion:
                p_query = p_query.filter(func.lower(Personnel.battalion) == user_battalion)
            user_location = (current_user.location or "").strip().lower()
            if user_location:
                p_query = p_query.filter(func.lower(Personnel.location) == user_location)
        return p_query

    @classmethod
    def compute_analytics(
        cls,
        db: Session,
        current_user: User,
        time_filter: str = "30d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        reference_time: Optional[datetime] = None
    ) -> CommanderAnalyticsResponse:
        """
        Executes end-to-end Commander analytics aggregation.
        """
        now = reference_time or datetime.now(timezone.utc)
        start_dt, end_dt, filter_type = cls.resolve_date_filter(time_filter, start_date, end_date, reference_time=now)
        date_range_info = DateRangeInfo(
            start_date=start_dt,
            end_date=end_dt,
            filter_type=filter_type
        )

        # 1. Scope Evaluation & Personnel Query
        p_query = cls.get_scoped_personnel_query(db, current_user)
        scoped_personnel = p_query.all()
        total_authorized_personnel = len(scoped_personnel)

        scope_info = ScopeInfo(
            role=current_user.role,
            battalion=current_user.battalion,
            location=current_user.location,
            total_authorized_personnel=total_authorized_personnel,
            min_group_size_threshold=ANALYTICS_MIN_GROUP_SIZE
        )

        data_quality_notes: List[str] = []

        # 2. PRIVACY / SMALL GROUP PROTECTION (k-anonymity)
        if total_authorized_personnel < ANALYTICS_MIN_GROUP_SIZE:
            logger.info(
                f"Commander analytics small-group protection triggered for user '{current_user.username}' "
                f"(scope personnel: {total_authorized_personnel} < threshold {ANALYTICS_MIN_GROUP_SIZE})"
            )
            return CommanderAnalyticsResponse(
                status="INSUFFICIENT_GROUP_SIZE",
                message=(
                    f"Aggregate analytics are unavailable for this population size. "
                    f"A minimum group size of {ANALYTICS_MIN_GROUP_SIZE} authorized personnel is required "
                    f"to protect individual privacy and prevent deductive re-identification."
                ),
                scope=scope_info,
                summary=None,
                risk_distribution=None,
                trend=None,
                alerts=None,
                welfare_factors=None,
                interventions=None,
                data_quality=DataQualitySection(
                    records_analyzed=0,
                    personnel_count=total_authorized_personnel,
                    latest_assessment_date=None,
                    date_range=date_range_info,
                    insufficient_data=True,
                    notes=["Population below privacy threshold. Individual risk metrics withheld."]
                )
            )

        scoped_personnel_ids = [p.id for p in scoped_personnel]
        scoped_personnel_map = {p.id: p for p in scoped_personnel}

        # 3. Assess Database Records within Scope
        all_assessments_query = (
            db.query(StressAssessment)
            .filter(StressAssessment.personnel_id.in_(scoped_personnel_ids))
            .order_by(StressAssessment.assessment_timestamp.asc(), StressAssessment.id.asc())
        )
        all_scoped_assessments = all_assessments_query.all()
        records_analyzed = len(all_scoped_assessments)

        # 4. Filter Assessments for Selected Time Window
        window_assessments: List[StressAssessment] = []
        for a in all_scoped_assessments:
            ts = a.assessment_timestamp
            if ts is not None and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if start_dt and ts and ts < start_dt:
                continue
            if end_dt and ts and ts > end_dt:
                continue
            window_assessments.append(a)

        latest_assessment_date = None
        if all_scoped_assessments:
            ts = all_scoped_assessments[-1].assessment_timestamp
            if ts is not None and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            latest_assessment_date = ts

        # 5. CURRENT RISK DISTRIBUTION (Latest Assessment per Personnel)
        # Group all scoped assessments by personnel_id to pick the authoritative latest assessment
        personnel_assessments_map: Dict[int, List[StressAssessment]] = {pid: [] for pid in scoped_personnel_ids}
        for a in all_scoped_assessments:
            personnel_assessments_map[a.personnel_id].append(a)

        latest_assessments: List[StressAssessment] = []
        for pid, p_list in personnel_assessments_map.items():
            if p_list:
                latest_assessments.append(p_list[-1])

        assessed_personnel_count = len(latest_assessments)
        if assessed_personnel_count == 0:
            data_quality_notes.append("No valid assessments recorded for authorized personnel.")

        unassessed_count = total_authorized_personnel - assessed_personnel_count
        if unassessed_count > 0:
            data_quality_notes.append(f"{unassessed_count} authorized personnel have no recorded assessments.")

        # Compute category distribution
        low_count = 0
        moderate_count = 0
        elevated_count = 0
        high_count = 0
        critical_count = 0

        valid_scores: List[float] = []
        for a in latest_assessments:
            score = a.risk_score
            if score is None:
                continue
            try:
                score_val = float(score)
                valid_scores.append(score_val)
                cat = cls.get_v2_category(score_val)
                if cat == "Critical":
                    critical_count += 1
                elif cat == "High":
                    high_count += 1
                elif cat == "Elevated":
                    elevated_count += 1
                elif cat == "Moderate":
                    moderate_count += 1
                else:
                    low_count += 1
            except (ValueError, TypeError):
                data_quality_notes.append(f"Assessment ID {a.id} has malformed risk_score: '{score}'")

        def calc_pct(c: int) -> float:
            return round((c / assessed_personnel_count) * 100.0, 1) if assessed_personnel_count > 0 else 0.0

        risk_dist_section = RiskDistributionSection(
            total_represented=assessed_personnel_count,
            categories=[
                RiskCategoryDistributionItem(label="Low", count=low_count, percentage=calc_pct(low_count)),
                RiskCategoryDistributionItem(label="Moderate", count=moderate_count, percentage=calc_pct(moderate_count)),
                RiskCategoryDistributionItem(label="Elevated", count=elevated_count, percentage=calc_pct(elevated_count)),
                RiskCategoryDistributionItem(label="High", count=high_count, percentage=calc_pct(high_count)),
                RiskCategoryDistributionItem(label="Critical", count=critical_count, percentage=calc_pct(critical_count)),
            ],
            low_count=low_count,
            low_pct=calc_pct(low_count),
            moderate_count=moderate_count,
            moderate_pct=calc_pct(moderate_count),
            elevated_count=elevated_count,
            elevated_pct=calc_pct(elevated_count),
            high_count=high_count,
            high_pct=calc_pct(high_count),
            critical_count=critical_count,
            critical_pct=calc_pct(critical_count),
        )

        # 6. LONGITUDINAL ORGANIZATIONAL TRENDS
        improving_count = 0
        stable_count = 0
        worsening_count = 0
        insufficient_history_count = 0
        persistent_elevated_population = 0

        for pid, p_list in personnel_assessments_map.items():
            if not p_list:
                continue
            if len(p_list) == 1:
                insufficient_history_count += 1
                continue

            # Analyze individual trajectory using Phase 36 service logic
            try:
                p_analysis = LongitudinalAnalyticsService.calculate_longitudinal_trend(
                    personnel_id=pid,
                    assessments=p_list,
                    reference_time=now
                )
                p_trend = p_analysis.get("trend", {}).get("direction", "INSUFFICIENT_DATA")
                if p_trend == "WORSENING":
                    worsening_count += 1
                elif p_trend == "IMPROVING":
                    improving_count += 1
                elif p_trend == "STABLE":
                    stable_count += 1
                else:
                    insufficient_history_count += 1

                if p_analysis.get("history", {}).get("persistent_elevated_risk", False):
                    persistent_elevated_population += 1
            except Exception as e:
                logger.warning(f"Error computing longitudinal trend for personnel {pid}: {e}")
                insufficient_history_count += 1

        improving_pct = calc_pct(improving_count)
        stable_pct = calc_pct(stable_count)
        worsening_pct = calc_pct(worsening_count)
        insufficient_pct = calc_pct(insufficient_history_count)
        persistent_pct = calc_pct(persistent_elevated_population)

        if assessed_personnel_count == 0:
            trend_direction = "INSUFFICIENT_DATA"
        elif insufficient_history_count == assessed_personnel_count:
            trend_direction = "LIMITED_HISTORY"
        elif worsening_pct >= 25.0:
            trend_direction = "WORSENING"
        elif improving_pct >= 25.0 and worsening_pct < 15.0:
            trend_direction = "IMPROVING"
        else:
            trend_direction = "STABLE"

        mean_risk_score = round(float(np.mean(valid_scores)), 1) if valid_scores else None
        median_risk_score = round(float(np.median(valid_scores)), 1) if valid_scores else None

        # Build timeline aggregated by date (using window assessments)
        date_buckets: Dict[str, List[float]] = {}
        target_assessments = window_assessments if window_assessments else all_scoped_assessments[-50:]
        for a in target_assessments:
            ts = a.assessment_timestamp
            if ts is None:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            d_str = ts.strftime("%Y-%m-%d")
            if d_str not in date_buckets:
                date_buckets[d_str] = []
            if a.risk_score is not None:
                date_buckets[d_str].append(float(a.risk_score))

        timeline_points: List[TimelinePoint] = []
        for d_str in sorted(date_buckets.keys()):
            scores = date_buckets[d_str]
            avg_s = round(float(np.mean(scores)), 1) if scores else None
            elev_count = sum(1 for s in scores if s >= 55.0)
            low_mod_count = sum(1 for s in scores if s < 55.0)
            timeline_points.append(
                TimelinePoint(
                    date=d_str,
                    average_risk_score=avg_s,
                    elevated_and_above_count=elev_count,
                    low_moderate_count=low_mod_count,
                    total_assessed=len(scores)
                )
            )

        trend_section = TrendSection(
            direction=trend_direction,
            improving_count=improving_count,
            improving_pct=improving_pct,
            stable_count=stable_count,
            stable_pct=stable_pct,
            worsening_count=worsening_count,
            worsening_pct=worsening_pct,
            insufficient_history_count=insufficient_history_count,
            insufficient_history_pct=insufficient_pct,
            mean_risk_score=mean_risk_score,
            median_risk_score=median_risk_score,
            persistent_elevated_population=persistent_elevated_population,
            persistent_elevated_pct=persistent_pct,
            timeline=timeline_points
        )

        # 7. ALERT ANALYTICS (Phase 37 integration)
        alert_query = (
            db.query(WelfareAlert)
            .filter(WelfareAlert.personnel_id.in_(scoped_personnel_ids))
        )
        if start_dt:
            alert_query = alert_query.filter(WelfareAlert.created_at >= start_dt)
        if end_dt:
            alert_query = alert_query.filter(WelfareAlert.created_at <= end_dt)

        scoped_alerts = alert_query.all()
        total_alerts = len(scoped_alerts)

        open_alerts = 0
        under_review_alerts = 0
        resolved_alerts = 0
        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        alert_date_buckets: Dict[str, Dict[str, int]] = {}

        for alt in scoped_alerts:
            st = (alt.status or "OPEN").upper()
            if st == "OPEN":
                open_alerts += 1
            elif st in ["UNDER_REVIEW", "ACKNOWLEDGED", "INTERVENTION_PLANNED", "FOLLOW_UP"]:
                under_review_alerts += 1
            elif st in ["RESOLVED", "DISMISSED"]:
                resolved_alerts += 1
            else:
                open_alerts += 1

            t_type = alt.alert_type or "GENERAL_ALERT"
            by_type[t_type] = by_type.get(t_type, 0) + 1

            sev = alt.severity or "ATTENTION"
            by_severity[sev] = by_severity.get(sev, 0) + 1

            # Timeline
            if alt.created_at:
                c_date = alt.created_at.strftime("%Y-%m-%d")
                if c_date not in alert_date_buckets:
                    alert_date_buckets[c_date] = {"created": 0, "resolved": 0}
                alert_date_buckets[c_date]["created"] += 1
            if alt.resolved_at:
                r_date = alt.resolved_at.strftime("%Y-%m-%d")
                if r_date not in alert_date_buckets:
                    alert_date_buckets[r_date] = {"created": 0, "resolved": 0}
                alert_date_buckets[r_date]["resolved"] += 1

        alert_timeline: List[AlertTimelinePoint] = []
        for d_str in sorted(alert_date_buckets.keys()):
            alert_timeline.append(
                AlertTimelinePoint(
                    date=d_str,
                    created_count=alert_date_buckets[d_str]["created"],
                    resolved_count=alert_date_buckets[d_str]["resolved"]
                )
            )

        alerts_section = AlertsSection(
            total_alerts=total_alerts,
            open_alerts=open_alerts,
            under_review_alerts=under_review_alerts,
            resolved_alerts=resolved_alerts,
            unresolved_alerts=open_alerts + under_review_alerts,
            by_type=by_type,
            by_severity=by_severity,
            timeline=alert_timeline
        )

        # 8. WELFARE INTERVENTIONS ANALYTICS
        alert_ids = [alt.id for alt in scoped_alerts]
        interventions: List[WelfareIntervention] = []
        if alert_ids:
            interventions = (
                db.query(WelfareIntervention)
                .filter(WelfareIntervention.alert_id.in_(alert_ids))
                .all()
            )
        elif scoped_personnel_ids:
            interventions = (
                db.query(WelfareIntervention)
                .filter(WelfareIntervention.personnel_id.in_(scoped_personnel_ids))
                .all()
            )

        planned_count = 0
        completed_count = 0
        follow_up_count = 0
        intervention_by_type: Dict[str, int] = {}

        for inv in interventions:
            st = (inv.status or "PLANNED").upper()
            if st == "PLANNED":
                planned_count += 1
            elif st == "COMPLETED":
                completed_count += 1

            if inv.follow_up_date is not None and inv.completed_at is None:
                follow_up_count += 1

            i_type = inv.intervention_type or "SUPPORTIVE_CHECK_IN"
            intervention_by_type[i_type] = intervention_by_type.get(i_type, 0) + 1

        interventions_section = InterventionsSection(
            total_interventions=len(interventions),
            planned=planned_count,
            completed=completed_count,
            follow_up_required=follow_up_count,
            by_type=intervention_by_type
        )

        # 9. WELFARE FACTOR ANALYTICS (Non-punitive aggregations)
        # Factor counts tracking unique personnel affected
        factor_personnel_map: Dict[str, set] = {
            "Elevated operational duty workload (> 50 hrs/week)": set(),
            "Restorative sleep deficit (< 5.5 hrs/night)": set(),
            "Frequent night-shift roster assignments": set(),
            "Prolonged duration without respite/leave": set(),
            "Continuous duty period without rest interval": set(),
            "Elevated perceived fatigue / burnout indicator": set(),
            "Recovery interval below baseline": set(),
        }

        # Check latest assessments key_factors JSON
        for a in latest_assessments:
            pid = a.personnel_id
            if not a.key_factors:
                continue
            raw_factors: List[str] = []
            try:
                parsed = json.loads(a.key_factors)
                if isinstance(parsed, list):
                    raw_factors = [str(x) for x in parsed]
                elif isinstance(parsed, dict):
                    raw_factors = parsed.get("top_risk_factors", parsed.get("key_factors", []))
                    if not isinstance(raw_factors, list):
                        raw_factors = [str(raw_factors)]
                else:
                    raw_factors = [str(parsed)]
            except Exception:
                raw_factors = [str(a.key_factors)]

            for rf in raw_factors:
                rf_lower = rf.lower()
                if "duty" in rf_lower or "workload" in rf_lower or "hours" in rf_lower:
                    factor_personnel_map["Elevated operational duty workload (> 50 hrs/week)"].add(pid)
                elif "sleep" in rf_lower:
                    factor_personnel_map["Restorative sleep deficit (< 5.5 hrs/night)"].add(pid)
                elif "night" in rf_lower or "shift" in rf_lower:
                    factor_personnel_map["Frequent night-shift roster assignments"].add(pid)
                elif "leave" in rf_lower or "respite" in rf_lower:
                    factor_personnel_map["Prolonged duration without respite/leave"].add(pid)
                elif "consecutive" in rf_lower or "continuous" in rf_lower:
                    factor_personnel_map["Continuous duty period without rest interval"].add(pid)
                elif "burnout" in rf_lower or "fatigue" in rf_lower:
                    factor_personnel_map["Elevated perceived fatigue / burnout indicator"].add(pid)
                else:
                    # Dynamically include any other specific factor cleanly
                    clean_rf = rf.strip().capitalize()
                    if clean_rf not in factor_personnel_map:
                        factor_personnel_map[clean_rf] = set()
                    factor_personnel_map[clean_rf].add(pid)

        # Also inspect structural Personnel indicators for any uncaptured cases
        for p in scoped_personnel:
            if p.duty_hours_per_week and p.duty_hours_per_week > 50.0:
                factor_personnel_map["Elevated operational duty workload (> 50 hrs/week)"].add(p.id)
            if p.night_shifts_per_month and p.night_shifts_per_month > 6:
                factor_personnel_map["Frequent night-shift roster assignments"].add(p.id)
            if p.leave_gap_days and p.leave_gap_days > 60:
                factor_personnel_map["Prolonged duration without respite/leave"].add(p.id)
            if p.consecutive_duty_days and p.consecutive_duty_days > 14:
                factor_personnel_map["Continuous duty period without rest interval"].add(p.id)

        welfare_factor_items: List[WelfareFactorItem] = []
        denom = assessed_personnel_count if assessed_personnel_count > 0 else total_authorized_personnel
        for factor_name, pids in factor_personnel_map.items():
            count = len(pids)
            if count > 0:
                pct = round((count / denom) * 100.0, 1)
                welfare_factor_items.append(
                    WelfareFactorItem(
                        factor=factor_name,
                        affected_count=count,
                        affected_pct=pct,
                        trend="STABLE"
                    )
                )

        welfare_factor_items.sort(key=lambda x: x.affected_count, reverse=True)
        welfare_factors_section = WelfareFactorsSection(
            factors=welfare_factor_items,
            total_records_analyzed=records_analyzed
        )

        # 10. SUMMARY SECTION
        coverage_pct = round((assessed_personnel_count / total_authorized_personnel) * 100.0, 1) if total_authorized_personnel > 0 else 0.0

        summary_section = SummarySection(
            total_authorized_personnel=total_authorized_personnel,
            assessed_personnel_count=assessed_personnel_count,
            assessment_coverage_pct=coverage_pct,
            open_alerts_count=open_alerts,
            worsening_trend_count=worsening_count,
            worsening_trend_pct=worsening_pct,
            persistent_elevated_count=persistent_elevated_population,
            persistent_elevated_pct=persistent_pct,
            average_risk_score=mean_risk_score
        )

        status_result = "SUCCESS"
        if assessed_personnel_count == 0:
            status_result = "INSUFFICIENT_DATA"

        return CommanderAnalyticsResponse(
            status=status_result,
            message=(
                f"Organizational welfare intelligence synthesized successfully for scope "
                f"'{current_user.battalion or 'System-wide'} - {current_user.location or 'All Locations'}'."
            ),
            scope=scope_info,
            summary=summary_section,
            risk_distribution=risk_dist_section,
            trend=trend_section,
            alerts=alerts_section,
            welfare_factors=welfare_factors_section,
            interventions=interventions_section,
            data_quality=DataQualitySection(
                records_analyzed=records_analyzed,
                personnel_count=total_authorized_personnel,
                latest_assessment_date=latest_assessment_date,
                date_range=date_range_info,
                insufficient_data=(assessed_personnel_count == 0),
                notes=data_quality_notes
            )
        )
