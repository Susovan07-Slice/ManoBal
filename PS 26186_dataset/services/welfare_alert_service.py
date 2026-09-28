import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from db.models.alert import WelfareAlert, WelfareIntervention, WelfareAlertAudit
from db.models.assessment import StressAssessment
from db.models.personnel import Personnel
from services.longitudinal_analytics_service import LongitudinalAnalyticsService

class WelfareAlertService:
    """
    Centralized service for generating and managing non-punitive welfare alerts and interventions.
    """

    @staticmethod
    def _create_audit_log(db: Session, alert_id: int, action: str, actor_id: Optional[int] = None, previous_status: Optional[str] = None, new_status: Optional[str] = None, metadata: Optional[Dict] = None):
        audit = WelfareAlertAudit(
            alert_id=alert_id,
            action=action,
            actor_id=actor_id,
            previous_status=previous_status,
            new_status=new_status,
            timestamp=datetime.now(timezone.utc),
            metadata_json=json.dumps(metadata) if metadata else None
        )
        db.add(audit)
        db.flush()

    @staticmethod
    def evaluate_and_generate_alerts(db: Session, personnel_id: int, current_assessment: StressAssessment) -> List[WelfareAlert]:
        """
        Evaluates current risk and longitudinal history to generate deduplicated welfare alerts.
        """
        # Fetch history and get longitudinal trend
        past_records = (
            db.query(StressAssessment)
            .filter(StressAssessment.personnel_id == personnel_id)
            .order_by(desc(StressAssessment.assessment_timestamp))
            .limit(20)  # Enough for trend/baseline
            .all()
        )
        
        trend_data = LongitudinalAnalyticsService.calculate_longitudinal_trend(personnel_id, past_records)
        
        generated_alerts = []

        # Helper to deduplicate and insert
        def create_alert_if_new(alert_type: str, severity: str, reason: str):
            # Check if an unresolved alert of same type exists for this personnel
            existing = (
                db.query(WelfareAlert)
                .filter(
                    WelfareAlert.personnel_id == personnel_id,
                    WelfareAlert.alert_type == alert_type,
                    WelfareAlert.status.in_(["OPEN", "ACKNOWLEDGED", "UNDER_REVIEW", "INTERVENTION_PLANNED", "FOLLOW_UP"])
                )
                .first()
            )
            
            if not existing:
                new_alert = WelfareAlert(
                    personnel_id=personnel_id,
                    alert_type=alert_type,
                    severity=severity,
                    trigger_assessment_id=current_assessment.id,
                    trigger_reason=reason,
                    status="OPEN"
                )
                db.add(new_alert)
                db.flush()
                WelfareAlertService._create_audit_log(db, new_alert.id, "ALERT_CREATED", actor_id=None, new_status="OPEN", metadata={"reason": reason})
                generated_alerts.append(new_alert)

        # 1. High Current Risk
        # Rely entirely on the authoritative Phase 34 V2 engine's risk_category & stress_level mapping 
        # rather than inventing independent thresholds or recalculating risk scores.
        risk_category = None
        if current_assessment.key_factors:
            try:
                kf_data = json.loads(current_assessment.key_factors)
                if isinstance(kf_data, dict):
                    risk_category = kf_data.get("risk_category")
            except Exception:
                pass
        if not risk_category:
            risk_category = current_assessment.stress_level

        if (
            risk_category in ["Critical", "High"]
            or current_assessment.stress_level in ["Critical", "High"]
            or current_assessment.risk_priority == "Priority"
        ):
            severity = "URGENT_REVIEW" if (risk_category == "Critical" or current_assessment.stress_level == "Critical") else "HIGH_PRIORITY"
            create_alert_if_new(
                "HIGH_CURRENT_RISK", 
                severity, 
                f"Authoritative Risk Category: {risk_category} (Score: {current_assessment.risk_score})"
            )
            
        # 2. Persistent Elevated Risk
        if trend_data.get("history", {}).get("persistent_elevated_risk"):
            create_alert_if_new(
                "PERSISTENT_ELEVATED_RISK", 
                "HIGH_PRIORITY", 
                f"{trend_data['history']['consecutive_elevated_assessments']} consecutive elevated assessments."
            )
            
        # 3. Worsening Trend
        if trend_data.get("trend", {}).get("direction") == "WORSENING":
            create_alert_if_new(
                "WORSENING_TREND", 
                "ATTENTION", 
                f"Recent score change: +{trend_data['trend']['score_change']} points."
            )
            
        # 4. Rapid Risk Increase (Acceleration)
        if trend_data.get("trend", {}).get("acceleration") == "INCREASING":
            create_alert_if_new(
                "RAPID_RISK_INCREASE", 
                "ATTENTION", 
                "Risk acceleration detected in recent history compared to older history."
            )
            
        # 5. Repeated Welfare Factor
        repeated_factors = trend_data.get("repeated_factors", [])
        for factor in repeated_factors:
            if factor["type"] == "risk":
                create_alert_if_new(
                    "REPEATED_WELFARE_FACTOR", 
                    "INFO", 
                    f"Repeated risk factor: {factor['factor']} ({factor['frequency']} times)"
                )
                # Only flag the top repeated risk factor to avoid alert fatigue
                break

        db.commit()
        return generated_alerts

    @staticmethod
    def acknowledge_alert(db: Session, alert_id: int, user_id: int) -> WelfareAlert:
        alert = db.query(WelfareAlert).filter(WelfareAlert.id == alert_id).first()
        if not alert:
            raise ValueError("Alert not found")
        
        if alert.status not in ["OPEN"]:
            raise ValueError(f"Cannot acknowledge alert in state {alert.status}")
            
        prev = alert.status
        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.acknowledged_by = user_id
        
        db.flush()
        WelfareAlertService._create_audit_log(db, alert.id, "ALERT_ACKNOWLEDGED", actor_id=user_id, previous_status=prev, new_status="ACKNOWLEDGED")
        db.commit()
        return alert

    @staticmethod
    def start_review(db: Session, alert_id: int, user_id: int) -> WelfareAlert:
        alert = db.query(WelfareAlert).filter(WelfareAlert.id == alert_id).first()
        if not alert:
            raise ValueError("Alert not found")
            
        if alert.status not in ["OPEN", "ACKNOWLEDGED", "FOLLOW_UP"]:
            raise ValueError(f"Cannot start review from state {alert.status}")
            
        prev = alert.status
        alert.status = "UNDER_REVIEW"
        
        db.flush()
        WelfareAlertService._create_audit_log(db, alert.id, "REVIEW_STARTED", actor_id=user_id, previous_status=prev, new_status="UNDER_REVIEW")
        db.commit()
        return alert

    @staticmethod
    def create_intervention(db: Session, alert_id: int, user_id: int, intervention_type: str, planned_date: Optional[datetime], notes: Optional[str]) -> WelfareIntervention:
        alert = db.query(WelfareAlert).filter(WelfareAlert.id == alert_id).first()
        if not alert:
            raise ValueError("Alert not found")
        
        if alert.status in ["RESOLVED", "DISMISSED"]:
            raise ValueError(f"Cannot create intervention for {alert.status} alert")
            
        intervention = WelfareIntervention(
            alert_id=alert.id,
            personnel_id=alert.personnel_id,
            intervention_type=intervention_type,
            created_by=user_id,
            planned_date=planned_date,
            notes=notes
        )
        db.add(intervention)
        
        prev = alert.status
        if alert.status in ["OPEN", "ACKNOWLEDGED", "UNDER_REVIEW"]:
            alert.status = "INTERVENTION_PLANNED"
            
        db.flush()
        WelfareAlertService._create_audit_log(db, alert.id, "INTERVENTION_CREATED", actor_id=user_id, previous_status=prev, new_status=alert.status, metadata={"intervention_type": intervention_type})
        db.commit()
        db.refresh(intervention)
        return intervention

    @staticmethod
    def schedule_followup(db: Session, intervention_id: int, user_id: int, follow_up_date: datetime, notes: Optional[str]) -> WelfareIntervention:
        intervention = db.query(WelfareIntervention).filter(WelfareIntervention.id == intervention_id).first()
        if not intervention:
            raise ValueError("Intervention not found")
            
        alert = intervention.alert
        if alert.status in ["RESOLVED", "DISMISSED"]:
            raise ValueError(f"Cannot schedule follow-up on intervention for {alert.status} alert")

        intervention.follow_up_date = follow_up_date
        
        if notes:
            intervention.notes = (intervention.notes + "\n" + notes) if intervention.notes else notes
            
        prev = alert.status
        alert.status = "FOLLOW_UP"
        
        db.flush()
        WelfareAlertService._create_audit_log(db, alert.id, "FOLLOWUP_SCHEDULED", actor_id=user_id, previous_status=prev, new_status="FOLLOW_UP", metadata={"follow_up_date": follow_up_date.isoformat()})
        db.commit()
        db.refresh(intervention)
        return intervention

    @staticmethod
    def complete_intervention(db: Session, intervention_id: int, user_id: int, notes: Optional[str] = None) -> WelfareIntervention:
        intervention = db.query(WelfareIntervention).filter(WelfareIntervention.id == intervention_id).first()
        if not intervention:
            raise ValueError("Intervention not found")
        if intervention.status in ["COMPLETED", "CANCELLED"]:
            raise ValueError(f"Intervention is already {intervention.status}")

        intervention.status = "COMPLETED"
        intervention.completed_at = datetime.now(timezone.utc)
        if notes:
            intervention.notes = (intervention.notes + "\n" + notes) if intervention.notes else notes

        alert = intervention.alert
        action = "FOLLOWUP_COMPLETED" if intervention.follow_up_date else "INTERVENTION_COMPLETED"
        db.flush()
        WelfareAlertService._create_audit_log(db, alert.id, action, actor_id=user_id, previous_status=alert.status, new_status=alert.status, metadata={"intervention_id": intervention.id})
        db.commit()
        db.refresh(intervention)
        return intervention

    @staticmethod
    def cancel_intervention(db: Session, intervention_id: int, user_id: int, reason: Optional[str] = None) -> WelfareIntervention:
        intervention = db.query(WelfareIntervention).filter(WelfareIntervention.id == intervention_id).first()
        if not intervention:
            raise ValueError("Intervention not found")
        if intervention.status in ["COMPLETED", "CANCELLED"]:
            raise ValueError(f"Intervention is already {intervention.status}")

        intervention.status = "CANCELLED"
        if reason:
            intervention.notes = (intervention.notes + f"\n[Cancelled: {reason}]") if intervention.notes else f"[Cancelled: {reason}]"

        alert = intervention.alert
        db.flush()
        WelfareAlertService._create_audit_log(db, alert.id, "INTERVENTION_CANCELLED", actor_id=user_id, previous_status=alert.status, new_status=alert.status, metadata={"intervention_id": intervention.id, "reason": reason})
        db.commit()
        db.refresh(intervention)
        return intervention

    @staticmethod
    def resolve_alert(db: Session, alert_id: int, user_id: int, resolution_reason: str, dismiss: bool = False) -> WelfareAlert:
        alert = db.query(WelfareAlert).filter(WelfareAlert.id == alert_id).first()
        if not alert:
            raise ValueError("Alert not found")
        if alert.status in ["RESOLVED", "DISMISSED"]:
            raise ValueError(f"Alert is already {alert.status}")
            
        prev = alert.status
        alert.status = "DISMISSED" if dismiss else "RESOLVED"
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolved_by = user_id
        alert.resolution_reason = resolution_reason
        
        db.flush()
        WelfareAlertService._create_audit_log(db, alert.id, "ALERT_DISMISSED" if dismiss else "ALERT_RESOLVED", actor_id=user_id, previous_status=prev, new_status=alert.status, metadata={"reason": resolution_reason})
        db.commit()
        return alert

