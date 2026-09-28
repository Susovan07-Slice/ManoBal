import os
import json
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from api.main import app
from db.base import Base
from db.session import get_db
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.telemetry import WearableTelemetry
from db.models.anomaly import WelfareAnomaly
from db.models.alert import WelfareAlert, WelfareIntervention
from db.models.recommendation import WelfareRecommendation
from db.models.user import User
from core.security import create_access_token
from services.welfare_recommendation_service import (
    WelfareRecommendationService,
    ANALYTICS_MIN_GROUP_SIZE,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase40.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def make_personnel(code, name="Cadet Test", battalion="1st Battalion", location="Srinagar", duty_hours=40.0, night_shifts=2, consecutive_days=3, leave_gap=30, deployment_days=60, exposure="Moderate"):
    return Personnel(
        personnel_code=code,
        name=name,
        age=28,
        gender="Male",
        department="Operations",
        battalion=battalion,
        job_role="Rifleman",
        location=location,
        experience_years=4.0,
        duty_hours_per_week=duty_hours,
        night_shifts_per_month=night_shifts,
        consecutive_duty_days=consecutive_days,
        transfer_frequency=1,
        training_load=2,
        leave_gap_days=leave_gap,
        deployment_days=deployment_days,
        remote_posting="No",
        operational_exposure=exposure
    )

def make_assessment(personnel_id, score, stress_level="Low", priority="Routine", days_ago=0, key_factors=None):
    ts = datetime.now(timezone.utc) - timedelta(days=days_ago)
    kf = json.dumps(key_factors) if key_factors is not None else json.dumps({
        "risk_category": stress_level,
        "top_risk_factors": ["Operational Routine"],
        "protective_factors": ["Adequate Rest"]
    })
    return StressAssessment(
        personnel_id=personnel_id,
        stress_level=stress_level,
        low_probability=0.7 if score < 35 else 0.1,
        medium_probability=0.2 if 35 <= score < 70 else 0.1,
        high_probability=0.8 if score >= 70 else 0.1,
        risk_score=score,
        risk_priority=priority,
        key_factors=kf,
        model_version="2.0.0-Phase34V2",
        assessment_timestamp=ts
    )

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_phase40.db"):
        try:
            os.remove("./test_phase40.db")
        except Exception:
            pass

@pytest.fixture(autouse=True)
def clean_session(db_session):
    yield
    db_session.rollback()

@pytest.fixture(scope="module")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestPhase40WelfareRecommendations:
    """
    Phase 40: Welfare Recommendation & Support Engine Test Suite.
    """

    # -------------------------------------------------------------------------
    # 1. Recommendation Generation Tests
    # -------------------------------------------------------------------------
    def test_01_recovery_review_generation(self, db_session):
        p = make_personnel("PF-P40-01", duty_hours=72.0, consecutive_days=14)
        db_session.add(p)
        db_session.commit()
        a = make_assessment(p.id, score=62.0, stress_level="Medium")
        db_session.add(a)
        db_session.commit()

        status_code, msg, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=a, persist=True
        )

        assert status_code == "GENERATED"
        rec_types = [r.recommendation_type for r in recs]
        assert "RECOVERY_REVIEW" in rec_types

        rec = next(r for r in recs if r.recommendation_type == "RECOVERY_REVIEW")
        assert rec.priority in ["HIGH", "MEDIUM"]
        assert "workload" in rec.recommendation_text.lower()
        assert rec.status == "SUGGESTED"
        assert rec.evidence_json is not None
        evidence = json.loads(rec.evidence_json)
        assert evidence["metrics"]["duty_hours_per_week"] == 72.0

    def test_02_duty_schedule_review_generation(self, db_session):
        p = make_personnel("PF-P40-02", duty_hours=48.0, night_shifts=8, consecutive_days=12)
        db_session.add(p)
        db_session.commit()
        a = make_assessment(p.id, score=50.0, stress_level="Medium")
        db_session.add(a)
        db_session.commit()

        status_code, msg, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=a, persist=True
        )

        assert status_code == "GENERATED"
        rec_types = [r.recommendation_type for r in recs]
        assert "DUTY_SCHEDULE_REVIEW" in rec_types

        rec = next(r for r in recs if r.recommendation_type == "DUTY_SCHEDULE_REVIEW")
        assert "duty schedule" in rec.recommendation_text.lower()
        evidence = json.loads(rec.evidence_json)
        assert evidence["metrics"]["night_shifts_per_month"] == 8

    def test_03_welfare_follow_up_generation(self, db_session):
        p = make_personnel("PF-P40-03")
        db_session.add(p)
        db_session.commit()
        # Create persistent elevated history (3+ assessments >= 55)
        for i in range(3, 0, -1):
            db_session.add(make_assessment(p.id, score=74.0, stress_level="High", days_ago=i * 2))
        latest = make_assessment(p.id, score=78.0, stress_level="High", days_ago=0)
        db_session.add(latest)
        db_session.commit()

        status_code, msg, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=latest, persist=True
        )

        rec_types = [r.recommendation_type for r in recs]
        assert "WELFARE_FOLLOW_UP" in rec_types
        rec = next(r for r in recs if r.recommendation_type == "WELFARE_FOLLOW_UP")
        assert rec.priority in ["HIGH", "URGENT"]
        assert "welfare follow-up" in rec.recommendation_text.lower()

    def test_04_voluntary_wellness_checkin_generation(self, db_session):
        p = make_personnel("PF-P40-04", duty_hours=42.0)
        db_session.add(p)
        db_session.commit()
        # Normal history, mild baseline shift
        db_session.add(make_assessment(p.id, score=25.0, days_ago=10))
        db_session.add(make_assessment(p.id, score=28.0, days_ago=5))
        latest = make_assessment(p.id, score=45.0, stress_level="Elevated", days_ago=0)
        db_session.add(latest)
        db_session.commit()

        status_code, msg, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=latest, persist=True
        )

        rec_types = [r.recommendation_type for r in recs]
        assert "VOLUNTARY_WELLNESS_CHECKIN" in rec_types
        rec = next(r for r in recs if r.recommendation_type == "VOLUNTARY_WELLNESS_CHECKIN")
        assert "voluntary" in rec.recommendation_text.lower()
        assert rec.priority == "MEDIUM"

    def test_05_support_resource_referral_generation(self, db_session):
        p = make_personnel("PF-P40-05", leave_gap=75, deployment_days=120, exposure="High")
        db_session.add(p)
        db_session.commit()
        a = make_assessment(p.id, score=38.0, stress_level="Low")
        db_session.add(a)
        db_session.commit()

        status_code, msg, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=a, persist=True
        )

        rec_types = [r.recommendation_type for r in recs]
        assert "SUPPORT_RESOURCE_REFERRAL" in rec_types
        rec = next(r for r in recs if r.recommendation_type == "SUPPORT_RESOURCE_REFERRAL")
        assert "available welfare" in rec.recommendation_text.lower()

    def test_06_follow_up_assessment_generation(self, db_session):
        p = make_personnel("PF-P40-06")
        db_session.add(p)
        db_session.commit()
        # History with rapidly accelerating slope
        db_session.add(make_assessment(p.id, score=25.0, days_ago=12))
        db_session.add(make_assessment(p.id, score=28.0, days_ago=8))
        db_session.add(make_assessment(p.id, score=45.0, days_ago=4))
        latest = make_assessment(p.id, score=68.0, days_ago=0)
        db_session.add(latest)
        db_session.commit()

        status_code, msg, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=latest, persist=True
        )

        rec_types = [r.recommendation_type for r in recs]
        assert "FOLLOW_UP_ASSESSMENT" in rec_types
        rec = next(r for r in recs if r.recommendation_type == "FOLLOW_UP_ASSESSMENT")
        assert "follow-up assessment" in rec.recommendation_text.lower()

    def test_07_continue_monitoring_for_stable_routine(self, db_session):
        p = make_personnel("PF-P40-07", duty_hours=38.0, night_shifts=1, consecutive_days=2, leave_gap=15)
        db_session.add(p)
        db_session.commit()
        a = make_assessment(p.id, score=22.0, stress_level="Low")
        db_session.add(a)
        db_session.commit()

        status_code, msg, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=a, persist=True
        )

        assert len(recs) == 1
        assert recs[0].recommendation_type == "CONTINUE_MONITORING"
        assert recs[0].priority == "LOW"
        assert "continue routine" in recs[0].recommendation_text.lower()

    def test_08_human_review_for_conflicting_signals(self, db_session):
        p = make_personnel("PF-P40-08", duty_hours=40.0)
        db_session.add(p)
        db_session.commit()
        # Add an urgent alert but low assessment score
        alert = WelfareAlert(
            personnel_id=p.id,
            alert_type="HIGH_CURRENT_RISK",
            severity="URGENT_REVIEW",
            trigger_reason="Simulated acute alert",
            status="OPEN"
        )
        db_session.add(alert)
        db_session.commit()

        a = make_assessment(p.id, score=24.0, stress_level="Low")
        db_session.add(a)
        db_session.commit()

        status_code, msg, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=a, persist=True
        )

        rec_types = [r.recommendation_type for r in recs]
        assert "HUMAN_REVIEW" in rec_types
        rec = next(r for r in recs if r.recommendation_type == "HUMAN_REVIEW")
        assert "human review" in rec.recommendation_text.lower()
        assert rec.priority == "HIGH"

    # -------------------------------------------------------------------------
    # 2. Explainability & Evidence Traceability Tests
    # -------------------------------------------------------------------------
    def test_09_explainability_and_evidence_traceability(self, db_session):
        p = make_personnel("PF-P40-09", duty_hours=68.0, night_shifts=7)
        db_session.add(p)
        db_session.commit()
        a = make_assessment(p.id, score=58.0, stress_level="Elevated")
        db_session.add(a)
        db_session.commit()

        status_code, msg, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=a, persist=True
        )

        for rec in recs:
            assert rec.reason is not None and len(rec.reason) > 5
            assert rec.title is not None and len(rec.title) > 3
            assert rec.recommendation_text is not None and len(rec.recommendation_text) > 5
            assert rec.evidence_json is not None
            ev = json.loads(rec.evidence_json)
            assert "trigger" in ev
            assert "metrics" in ev
            assert rec.source_signals_json is not None
            srcs = json.loads(rec.source_signals_json)
            assert len(srcs) >= 1

    # -------------------------------------------------------------------------
    # 3. Data Quality & Missing Value Tests
    # -------------------------------------------------------------------------
    def test_10_missing_and_invalid_data_handling(self, db_session):
        # Personnel with valid DB fields but missing optional telemetry/welfare factors
        p = make_personnel("PF-P40-10", duty_hours=40.0)
        p.night_shifts_per_month = None
        p.consecutive_duty_days = None
        p.leave_gap_days = None
        db_session.add(p)
        db_session.commit()

        # Assessment with valid DB constraints, then evaluated with NaN in-memory
        a = make_assessment(p.id, score=30.0, stress_level="Low", key_factors=None)
        db_session.add(a)
        db_session.commit()
        db_session.refresh(a)

        # Detach/expunge before modifying with in-memory NaN so DB session stays clean
        db_session.expunge(a)
        a.risk_score = float("nan")

        # Service should handle safely without throwing exceptions
        status_code, msg, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=a, persist=False
        )
        assert status_code in ["GENERATED", "NONE"]
        assert isinstance(recs, list)

    def test_10b_empty_history_data_sufficiency(self, db_session):
        p = make_personnel("PF-P40-10B")
        db_session.add(p)
        db_session.commit()

        status_code, msg, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=None, persist=True
        )
        assert status_code == "INSUFFICIENT_DATA"
        assert len(recs) == 0

    # -------------------------------------------------------------------------
    # 4. Deterministic Deduplication Tests
    # -------------------------------------------------------------------------
    def test_11_deterministic_deduplication(self, db_session):
        p = make_personnel("PF-P40-11", duty_hours=70.0)
        db_session.add(p)
        db_session.commit()
        a = make_assessment(p.id, score=65.0, stress_level="Elevated")
        db_session.add(a)
        db_session.commit()

        # First evaluation
        _, _, recs1 = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=a, persist=True
        )
        initial_count = db_session.query(WelfareRecommendation).filter(WelfareRecommendation.personnel_id == p.id).count()

        # Second evaluation with unchanged signals on same day
        _, _, recs2 = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=a, persist=True
        )
        second_count = db_session.query(WelfareRecommendation).filter(WelfareRecommendation.personnel_id == p.id).count()

        assert initial_count == second_count, "Unchanged repeated evaluations must deduplicate without creating new rows."

    # -------------------------------------------------------------------------
    # 5. Priority Independence Tests
    # -------------------------------------------------------------------------
    def test_12_priority_independent_from_risk_category(self, db_session):
        # A personnel with low continuous risk (32.0) but high consecutive duty days (14 days)
        # Recommendation priority should be HIGH for recovery review, even though risk score is low
        p = make_personnel("PF-P40-12", duty_hours=45.0, consecutive_days=14)
        db_session.add(p)
        db_session.commit()
        a = make_assessment(p.id, score=32.0, stress_level="Low")
        db_session.add(a)
        db_session.commit()

        _, _, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=a, persist=True
        )
        recovery_rec = next((r for r in recs if r.recommendation_type == "RECOVERY_REVIEW"), None)
        assert recovery_rec is not None
        assert recovery_rec.priority == "HIGH", "Recovery review priority should be HIGH due to 14 consecutive duty days independent of low risk category."

    # -------------------------------------------------------------------------
    # 6. Lifecycle & Phase 37 Intervention Linking Tests
    # -------------------------------------------------------------------------
    def test_13_lifecycle_acknowledge_and_action(self, db_session):
        reviewer = User(username="officer_rev1", hashed_password="pw", role="officer", battalion="1st Battalion", location="Srinagar", is_active=True)
        db_session.add(reviewer)
        db_session.commit()

        p = make_personnel("PF-P40-13")
        db_session.add(p)
        db_session.commit()
        a = make_assessment(p.id, score=55.0)
        db_session.add(a)
        db_session.commit()

        _, _, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(p, db_session, a, persist=True)
        rec = recs[0]
        assert rec.status == "SUGGESTED"

        # Acknowledge
        ack = WelfareRecommendationService.acknowledge_recommendation(db_session, rec.id, reviewer, notes="Reviewed during morning muster")
        assert ack.status == "ACKNOWLEDGED"
        assert ack.acknowledged_by == reviewer.id
        assert ack.acknowledged_at is not None

        # Action
        act = WelfareRecommendationService.action_recommendation(db_session, rec.id, reviewer, action_notes="Adjusted duty schedule with company commander")
        assert act.status == "ACTIONED"
        assert act.actioned_by == reviewer.id
        assert "Adjusted duty schedule" in act.action_notes

    def test_14_lifecycle_accept_and_phase37_intervention_linking(self, db_session):
        reviewer = User(username="officer_rev2", hashed_password="pw", role="officer", battalion="1st Battalion", location="Srinagar", is_active=True)
        db_session.add(reviewer)
        db_session.commit()

        p = make_personnel("PF-P40-14", duty_hours=75.0, consecutive_days=15)
        db_session.add(p)
        db_session.commit()
        a = make_assessment(p.id, score=70.0, stress_level="High")
        db_session.add(a)
        db_session.commit()

        _, _, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(p, db_session, a, persist=True)
        rec = recs[0]
        assert rec.linked_intervention_id is None, "No intervention must be automatically created upon recommendation generation."

        # Accept and initiate Phase 37 intervention
        scheduled_ts = datetime.now(timezone.utc) + timedelta(days=2)
        accepted_rec, intervention = WelfareRecommendationService.accept_recommendation(
            db=db_session,
            recommendation_id=rec.id,
            user=reviewer,
            create_intervention=True,
            intervention_type="MANDATORY_REST_INTERVAL",
            scheduled_date=scheduled_ts,
            notes="Scheduled 48-hour recovery interval"
        )

        assert accepted_rec.status == "ACCEPTED"
        assert accepted_rec.linked_intervention_id is not None
        assert intervention is not None
        assert intervention.id == accepted_rec.linked_intervention_id
        assert intervention.intervention_type == "MANDATORY_REST_INTERVAL"
        assert intervention.status == "PLANNED"

    def test_15_lifecycle_defer_and_dismiss(self, db_session):
        reviewer = User(username="officer_rev3", hashed_password="pw", role="officer", battalion="1st Battalion", location="Srinagar", is_active=True)
        db_session.add(reviewer)
        db_session.commit()

        p = make_personnel("PF-P40-15")
        db_session.add(p)
        db_session.commit()
        a = make_assessment(p.id, score=40.0)
        db_session.add(a)
        db_session.commit()

        _, _, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(p, db_session, a, persist=True)
        rec = recs[0]

        # Defer
        deferred = WelfareRecommendationService.defer_recommendation(db_session, rec.id, reviewer, defer_days=10, notes="Awaiting rotation cycle")
        assert deferred.status == "DEFERRED"
        assert "10 days" in deferred.recommended_review_window

        # Dismiss
        dismissed = WelfareRecommendationService.dismiss_recommendation(db_session, rec.id, reviewer, reason="Personnel currently on sanctioned annual leave")
        assert dismissed.status == "DISMISSED"
        assert "sanctioned annual leave" in dismissed.action_notes

    # -------------------------------------------------------------------------
    # 7. Security (RBAC / Anti-IDOR) API Tests
    # -------------------------------------------------------------------------
    def test_16_api_get_personnel_recommendations(self, client, db_session):
        p = make_personnel("PF-P40-16", battalion="1st Battalion", location="Srinagar")
        db_session.add(p)
        db_session.commit()

        u_officer = User(username="officer_api_1", hashed_password="pw", role="officer", battalion="1st Battalion", location="Srinagar", is_active=True)
        db_session.add(u_officer)
        db_session.commit()
        token = create_access_token({"sub": u_officer.username})

        a = make_assessment(p.id, score=50.0)
        db_session.add(a)
        db_session.commit()
        WelfareRecommendationService.evaluate_and_generate_recommendations(p, db_session, a, persist=True)

        resp = client.get(f"/api/recommendations/personnel/{p.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["personnel_id"] == p.id
        assert data["total_recommendations"] >= 1
        assert "recommendations" in data

    def test_17_security_rbac_anti_idor_jawan_protection(self, client, db_session):
        p1 = make_personnel("PF-P40-J1", battalion="1st Battalion", location="Srinagar")
        p2 = make_personnel("PF-P40-J2", battalion="1st Battalion", location="Srinagar")
        db_session.add_all([p1, p2])
        db_session.commit()

        u_jawan1 = User(username="jawan_p40_1", hashed_password="pw", role="personnel", personnel_id=p1.id, battalion="1st Battalion", location="Srinagar", is_active=True)
        db_session.add(u_jawan1)
        db_session.commit()
        token_j1 = create_access_token({"sub": u_jawan1.username})

        # Jawan 1 accesses own recommendations -> 200 OK
        resp_own = client.get(f"/api/recommendations/personnel/{p1.id}", headers={"Authorization": f"Bearer {token_j1}"})
        assert resp_own.status_code == 200

        # Jawan 1 attempts IDOR to access Jawan 2 recommendations -> 403 Forbidden
        resp_idor = client.get(f"/api/recommendations/personnel/{p2.id}", headers={"Authorization": f"Bearer {token_j1}"})
        assert resp_idor.status_code == 403
        assert "Access forbidden" in resp_idor.json()["detail"]

    def test_18_security_scope_isolation_battalion_and_location(self, client, db_session):
        p_other_bat = make_personnel("PF-P40-OB", battalion="9th Battalion", location="Jammu")
        p_other_loc = make_personnel("PF-P40-OL", battalion="1st Battalion", location="Leh")
        db_session.add_all([p_other_bat, p_other_loc])
        db_session.commit()

        u_officer = User(username="officer_scope_1", hashed_password="pw", role="officer", battalion="1st Battalion", location="Srinagar", is_active=True)
        db_session.add(u_officer)
        db_session.commit()
        token = create_access_token({"sub": u_officer.username})

        # Cross-battalion attempt -> 403
        resp_bat = client.get(f"/api/recommendations/personnel/{p_other_bat.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp_bat.status_code == 403
        assert "Assigned Battalion scope" in resp_bat.json()["detail"] or "battalion" in resp_bat.json()["detail"].lower()

        # Cross-location attempt -> 403
        resp_loc = client.get(f"/api/recommendations/personnel/{p_other_loc.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp_loc.status_code == 403
        assert "location" in resp_loc.json()["detail"].lower()

    # -------------------------------------------------------------------------
    # 8. Privacy (Small-Group Suppression) Tests
    # -------------------------------------------------------------------------
    def test_19_privacy_small_group_suppression(self, client, db_session):
        # Create a unit with only 2 personnel (< ANALYTICS_MIN_GROUP_SIZE = 5)
        p_small1 = make_personnel("PF-P40-S1", battalion="Small Battalion", location="Remote Outpost")
        p_small2 = make_personnel("PF-P40-S2", battalion="Small Battalion", location="Remote Outpost")
        db_session.add_all([p_small1, p_small2])
        db_session.commit()

        u_small_off = User(username="officer_small_unit", hashed_password="pw", role="officer", battalion="Small Battalion", location="Remote Outpost", is_active=True)
        db_session.add(u_small_off)
        db_session.commit()
        token = create_access_token({"sub": u_small_off.username})

        resp = client.get("/api/recommendations/commander", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["small_group_suppressed"] is True, "Small group (< 5) must trigger privacy suppression to protect re-identification."
        assert len(data["recommendations"]) == 0
        assert data["total_active_recommendations"] == 0

    # -------------------------------------------------------------------------
    # 9. Safety & Non-Coercive Semantics Tests
    # -------------------------------------------------------------------------
    def test_20_safety_and_non_coercive_language(self, db_session):
        p = make_personnel("PF-P40-20", duty_hours=75.0, consecutive_days=18)
        db_session.add(p)
        db_session.commit()
        a = make_assessment(p.id, score=88.0, stress_level="Critical")
        db_session.add(a)
        db_session.commit()

        _, _, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(p, db_session, a, persist=True)

        forbidden_terms = [
            "mental illness", "psychiatric disorder", "clinical depression", "punish",
            "disciplinary", "must be removed from duty", "forced leave", "compulsory treatment"
        ]

        for rec in recs:
            full_text = f"{rec.title} {rec.description} {rec.reason} {rec.recommendation_text}".lower()
            for forbidden in forbidden_terms:
                assert forbidden not in full_text, f"Forbidden coercive/clinical term '{forbidden}' detected in recommendation #{rec.id}."

            # Verify presence of supportive verbs
            assert any(verb in full_text for verb in ["consider", "review", "offer", "discuss", "monitor", "support", "reassess"])

    # -------------------------------------------------------------------------
    # 10. Determinism Tests
    # -------------------------------------------------------------------------
    def test_21_determinism(self, db_session):
        p = make_personnel("PF-P40-21", duty_hours=65.0, consecutive_days=11)
        db_session.add(p)
        db_session.commit()
        a = make_assessment(p.id, score=55.0, stress_level="Elevated")
        db_session.add(a)
        db_session.commit()

        ref_time = datetime(2026, 9, 28, 12, 0, 0, tzinfo=timezone.utc)
        _, _, run1 = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=a, reference_time=ref_time, persist=False
        )
        _, _, run2 = WelfareRecommendationService.evaluate_and_generate_recommendations(
            personnel=p, db=db_session, current_assessment=a, reference_time=ref_time, persist=False
        )

        assert len(run1) == len(run2)
        for r1, r2 in zip(run1, run2):
            assert r1.recommendation_type == r2.recommendation_type
            assert r1.priority == r2.priority
            assert r1.title == r2.title
            assert r1.recommendation_text == r2.recommendation_text
