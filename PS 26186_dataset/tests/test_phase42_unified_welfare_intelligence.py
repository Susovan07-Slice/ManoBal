import os
import json
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from api.main import app
from db.base import Base
from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.alert import WelfareAlert, WelfareIntervention
from db.models.anomaly import WelfareAnomaly
from db.models.recommendation import WelfareRecommendation
from db.models.welfare_followup import WelfareFollowup
from core.security import create_access_token
from services.unified_welfare_intelligence_service import (
    UnifiedWelfareIntelligenceService,
    ANALYTICS_MIN_GROUP_SIZE,
)

TEST_DB_URL = "sqlite:///./test_phase42.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def uid():
    return uuid.uuid4().hex[:6]

def make_personnel(code=None, battalion="1st Battalion", location="Srinagar"):
    c = code or f"PF-42-{uid()}"
    return Personnel(
        personnel_code=c,
        name=f"Cadet {c}",
        age=27,
        gender="Male",
        department="Infantry",
        battalion=battalion,
        location=location,
        job_role="Rifleman",
        experience_years=3.5,
        duty_hours_per_week=48.0,
        night_shifts_per_month=4,
        consecutive_duty_days=6,
        leave_gap_days=20,
        operational_exposure="Medium"
    )

def make_user(role="officer", battalion="1st Battalion", location="Srinagar", personnel_id=None):
    u_name = f"user_{role}_{uid()}"
    return User(
        username=u_name,
        hashed_password="fakehashedpassword",
        role=role,
        battalion=battalion,
        location=location,
        personnel_id=personnel_id,
        is_active=True
    )

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_phase42.db"):
        try:
            os.remove("./test_phase42.db")
        except Exception:
            pass

@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
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


# =============================================================================
# 1. PERSONNEL WELFARE SNAPSHOT INTEGRATION TESTS
# =============================================================================
class TestPersonnelWelfareSnapshotIntegration:
    def test_full_snapshot_aggregation(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        now = datetime.now(timezone.utc)

        # 1. Phase 34 Assessments
        a1 = StressAssessment(
            personnel_id=p.id, stress_level="High", low_probability=0.1, medium_probability=0.2,
            high_probability=0.7, risk_score=78.5, risk_priority="Priority",
            key_factors=json.dumps(["Extended Duty Hours", "Sleep Deprivation"]),
            assessment_timestamp=now - timedelta(days=10)
        )
        a2 = StressAssessment(
            personnel_id=p.id, stress_level="Medium", low_probability=0.3, medium_probability=0.5,
            high_probability=0.2, risk_score=52.0, risk_priority="Preventive",
            key_factors=json.dumps(["Continuous Patrol Rotation"]),
            assessment_timestamp=now - timedelta(days=2)
        )
        db_session.add_all([a1, a2])

        # 2. Phase 37 Alert & Intervention
        al = WelfareAlert(
            personnel_id=p.id, alert_type="WORSENING_TREND", severity="ATTENTION",
            status="OPEN", trigger_reason="Delta +15 points in 7 days",
            created_at=now - timedelta(days=5)
        )
        db_session.add(al)
        db_session.commit()

        inv = WelfareIntervention(
            alert_id=al.id, personnel_id=p.id, intervention_type="REST_CYCLE_MANDATE",
            status="PLANNED", created_by=u.id, created_at=now - timedelta(days=4)
        )
        db_session.add(inv)

        # 3. Phase 39 Anomaly
        an = WelfareAnomaly(
            personnel_id=p.id, scope_type="INDIVIDUAL", scope_battalion=p.battalion,
            scope_location=p.location, anomaly_type="SLEEP_RECOVERY_ANOMALY",
            severity="ATTENTION", status="DETECTED", confidence="HIGH",
            evidence_json=json.dumps({"explanation": "Severe sleep recovery deficit detected"}),
            dedup_hash=f"hash_{uid()}", detected_at=now - timedelta(days=3)
        )
        db_session.add(an)

        # 4. Phase 40 Recommendation
        rc = WelfareRecommendation(
            personnel_id=p.id, assessment_id=a2.id, recommendation_type="RECOVERY_REVIEW",
            recommendation_text="Consider 48-hour recovery interval", priority="HIGH",
            status="SUGGESTED", recommended_review_window="Within 7 days",
            reason="High operational tempo fatigue", created_at=now - timedelta(days=2)
        )
        db_session.add(rc)

        # 5. Phase 41 Follow-up
        fu = WelfareFollowup(
            personnel_id=p.id, recommendation_id=rc.id, followup_type="WELFARE_CHECKIN",
            status="SCHEDULED", scheduled_at=now + timedelta(days=2), due_date=now + timedelta(days=5),
            outcome_status="INSUFFICIENT_DATA", created_at=now - timedelta(days=1)
        )
        db_session.add(fu)
        db_session.commit()

        # Run Phase 42 Service
        snapshot = UnifiedWelfareIntelligenceService.get_personnel_welfare_snapshot(
            db=db_session, current_user=u, personnel_id=p.id, reference_time=now
        )

        # Verify Core Identifiers
        assert snapshot["personnel_id"] == p.id
        assert snapshot["personnel_code"] == p.personnel_code

        # Verify Phase 34 Risk
        assert snapshot["current_risk"]["risk_score"] == 52.0
        assert snapshot["current_risk"]["stress_level"] == "Medium"
        assert snapshot["current_risk"]["risk_priority"] == "Preventive"
        assert snapshot["current_risk"]["data_sufficiency"] == "SUFFICIENT"
        assert "Continuous Patrol Rotation" in snapshot["current_risk"]["key_factors"]

        # Verify Phase 36 Trend
        assert snapshot["trend"]["trend_direction"] in ["IMPROVING", "STABLE", "WORSENING"]
        assert snapshot["trend"]["data_sufficiency"] == "LIMITED_HISTORY"

        # Verify Phase 37 Alerts & Interventions
        assert len(snapshot["alerts"]) == 1
        assert snapshot["alerts"][0]["alert_type"] == "WORSENING_TREND"
        assert len(snapshot["interventions"]) == 1
        assert snapshot["interventions"][0]["intervention_type"] == "REST_CYCLE_MANDATE"

        # Verify Phase 39 Anomalies
        assert len(snapshot["anomalies"]) == 1
        assert snapshot["anomalies"][0]["anomaly_type"] == "SLEEP_RECOVERY_ANOMALY"

        # Verify Phase 40 Recommendations
        assert len(snapshot["recommendations"]) == 1
        assert snapshot["recommendations"][0]["priority"] == "HIGH"
        assert snapshot["recommendations"][0]["is_system_suggestion"] is True

        # Verify Phase 41 Follow-up
        assert len(snapshot["followups"]) == 1
        assert snapshot["followups"][0]["status"] == "SCHEDULED"
        assert snapshot["followups"][0]["is_overdue"] is False

        # Verify Data Freshness
        assert snapshot["data_freshness"]["overall_freshness_status"] == "FRESH"
        assert snapshot["data_freshness"]["is_stale"] is False

        # Verify Human Review Indicator (MONITOR due to active alert/anomaly/recommendation)
        assert snapshot["human_review_indicator"]["review_level"] in ["REVIEW", "MONITOR"]
        assert len(snapshot["human_review_indicator"]["reasons"]) > 0

        # Verify Unified Chronological Timeline
        assert len(snapshot["timeline"]) >= 6
        # Strictly chronological
        timestamps = [item["timestamp"] for item in snapshot["timeline"]]
        assert timestamps == sorted(timestamps, reverse=True)


# =============================================================================
# 2. SEMANTIC INDEPENDENCE TESTS
# =============================================================================
class TestSemanticIndependence:
    def test_risk_and_anomaly_severity_coexist_independently(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        now = datetime.now(timezone.utc)

        # Risk is Low (Phase 34)
        a = StressAssessment(
            personnel_id=p.id, stress_level="Low", low_probability=0.85, medium_probability=0.1,
            high_probability=0.05, risk_score=22.0, risk_priority="Routine",
            assessment_timestamp=now - timedelta(days=1)
        )
        db_session.add(a)

        # Anomaly is URGENT_REVIEW (Phase 39)
        an = WelfareAnomaly(
            personnel_id=p.id, scope_type="INDIVIDUAL", scope_battalion=p.battalion,
            scope_location=p.location, anomaly_type="WORKLOAD_ANOMALY",
            severity="URGENT_REVIEW", status="DETECTED", confidence="HIGH",
            evidence_json=json.dumps({"explanation": "Severe shift spike"}),
            dedup_hash=f"hash_{uid()}", detected_at=now
        )
        db_session.add(an)
        db_session.commit()

        snapshot = UnifiedWelfareIntelligenceService.get_personnel_welfare_snapshot(
            db=db_session, current_user=u, personnel_id=p.id, reference_time=now
        )

        # Verify they are kept completely distinct
        assert snapshot["current_risk"]["stress_level"] == "Low"
        assert snapshot["current_risk"]["risk_score"] == 22.0
        assert snapshot["anomalies"][0]["severity"] == "URGENT_REVIEW"
        # Review indicator elevates to REVIEW without altering the Low risk score
        assert snapshot["human_review_indicator"]["review_level"] == "REVIEW"
        assert any("URGENT_REVIEW" in r for r in snapshot["human_review_indicator"]["reasons"])

    def test_missing_data_is_not_treated_as_low_risk(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        # No assessments added!
        snapshot = UnifiedWelfareIntelligenceService.get_personnel_welfare_snapshot(
            db=db_session, current_user=u, personnel_id=p.id
        )

        assert snapshot["current_risk"]["risk_score"] is None
        assert snapshot["current_risk"]["stress_level"] is None
        assert snapshot["current_risk"]["data_sufficiency"] == "INSUFFICIENT_DATA"
        assert snapshot["data_sufficiency"] == "INSUFFICIENT_DATA"
        assert snapshot["human_review_indicator"]["review_level"] == "INSUFFICIENT_DATA"


# =============================================================================
# 3. DATA FRESHNESS & STALE DATA TESTS
# =============================================================================
class TestDataFreshness:
    def test_stale_telemetry_detection(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        now = datetime.now(timezone.utc)
        # Assessment from 45 days ago (> 30 days is stale)
        a = StressAssessment(
            personnel_id=p.id, stress_level="Low", low_probability=0.8, medium_probability=0.15,
            high_probability=0.05, risk_score=25.0, risk_priority="Routine",
            assessment_timestamp=now - timedelta(days=45)
        )
        db_session.add(a)
        db_session.commit()

        snapshot = UnifiedWelfareIntelligenceService.get_personnel_welfare_snapshot(
            db=db_session, current_user=u, personnel_id=p.id, reference_time=now
        )

        assert snapshot["data_freshness"]["is_stale"] is True
        assert snapshot["data_freshness"]["overall_freshness_status"] == "STALE"
        assert "45 days ago" in snapshot["data_freshness"]["last_assessment_relative"]


# =============================================================================
# 4. SMALL-GROUP PRIVACY & UNIT-LEVEL INTELLIGENCE TESTS
# =============================================================================
class TestUnitIntelligencePrivacy:
    def test_privacy_suppression_when_below_threshold(self, db_session):
        bat = f"Bat_Small_{uid()}"
        # Create 3 personnel (< 5 threshold)
        p1 = make_personnel(battalion=bat)
        p2 = make_personnel(battalion=bat)
        p3 = make_personnel(battalion=bat)
        db_session.add_all([p1, p2, p3])
        db_session.commit()

        officer = make_user(role="officer", battalion=bat)
        db_session.add(officer)
        db_session.commit()

        unit_res = UnifiedWelfareIntelligenceService.get_unit_welfare_intelligence(
            db=db_session, current_user=officer, battalion=bat
        )

        assert unit_res["data_suppressed"] is True
        assert "Data suppressed to protect individual privacy" in unit_res["suppression_reason"]
        assert unit_res["total_personnel_in_scope"] == 3
        assert len(unit_res["personnel_cards"]) == 0
        assert unit_res["unit_overview"]["personnel_monitored"] == 0

    def test_unsuppressed_when_threshold_met(self, db_session):
        bat = f"Bat_Full_{uid()}"
        # Create 6 personnel (>= 5 threshold)
        personnel_group = [make_personnel(battalion=bat) for _ in range(6)]
        db_session.add_all(personnel_group)
        db_session.commit()

        officer = make_user(role="officer", battalion=bat)
        db_session.add(officer)
        db_session.commit()

        unit_res = UnifiedWelfareIntelligenceService.get_unit_welfare_intelligence(
            db=db_session, current_user=officer, battalion=bat
        )

        assert unit_res["data_suppressed"] is False
        assert unit_res["suppression_reason"] is None
        assert unit_res["total_personnel_in_scope"] == 6
        assert len(unit_res["personnel_cards"]) == 6
        assert unit_res["unit_overview"]["personnel_monitored"] == 6

    def test_no_personnel_ranking_attributes(self, db_session):
        bat = f"Bat_RankCheck_{uid()}"
        personnel_group = [make_personnel(battalion=bat) for _ in range(5)]
        db_session.add_all(personnel_group)
        db_session.commit()

        officer = make_user(role="officer", battalion=bat)
        db_session.add(officer)
        db_session.commit()

        unit_res = UnifiedWelfareIntelligenceService.get_unit_welfare_intelligence(
            db=db_session, current_user=officer, battalion=bat
        )

        # Ensure no ranking fields exist
        for card in unit_res["personnel_cards"]:
            assert "rank" not in card
            assert "top_risk" not in card
            assert "worst_score" not in card
            assert "performance_index" not in card


# =============================================================================
# 5. SECURITY, RBAC & ANTI-IDOR TESTS
# =============================================================================
class TestSecurityRBACAntiIDOR:
    def test_personnel_cannot_access_peer_snapshot(self, db_session):
        p1 = make_personnel()
        p2 = make_personnel()
        db_session.add_all([p1, p2])
        db_session.commit()

        jawan1 = make_user(role="personnel", personnel_id=p1.id)
        db_session.add(jawan1)
        db_session.commit()

        # Own snapshot -> OK
        snap = UnifiedWelfareIntelligenceService.get_personnel_welfare_snapshot(
            db=db_session, current_user=jawan1, personnel_id=p1.id
        )
        assert snap["personnel_id"] == p1.id

        # Peer snapshot -> 403 Forbidden (PermissionError)
        with pytest.raises(PermissionError, match="Personnel can only access their own welfare intelligence snapshot"):
            UnifiedWelfareIntelligenceService.get_personnel_welfare_snapshot(
                db=db_session, current_user=jawan1, personnel_id=p2.id
            )

    def test_officer_cross_battalion_access_rejected(self, db_session):
        p1 = make_personnel(battalion="1st Battalion")
        p2 = make_personnel(battalion="2nd Battalion")
        db_session.add_all([p1, p2])
        db_session.commit()

        officer = make_user(role="officer", battalion="1st Battalion")
        db_session.add(officer)
        db_session.commit()

        # Cross battalion snapshot -> PermissionError
        with pytest.raises(PermissionError, match="Cross-battalion access restricted"):
            UnifiedWelfareIntelligenceService.get_personnel_welfare_snapshot(
                db=db_session, current_user=officer, personnel_id=p2.id
            )

        # Cross battalion unit intelligence -> PermissionError
        with pytest.raises(PermissionError, match="Access denied: cannot query battalion"):
            UnifiedWelfareIntelligenceService.get_unit_welfare_intelligence(
                db=db_session, current_user=officer, battalion="2nd Battalion"
            )


# =============================================================================
# 6. DETERMINISM & PERFORMANCE TESTS
# =============================================================================
class TestDeterminismAndPerformance:
    def test_deterministic_identical_runs(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion)
        db_session.add(u)
        db_session.commit()

        now = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
        a = StressAssessment(
            personnel_id=p.id, stress_level="High", low_probability=0.1, medium_probability=0.2,
            high_probability=0.7, risk_score=75.0, risk_priority="Priority",
            assessment_timestamp=now
        )
        db_session.add(a)
        db_session.commit()

        run1 = UnifiedWelfareIntelligenceService.get_personnel_welfare_snapshot(
            db=db_session, current_user=u, personnel_id=p.id, reference_time=now
        )
        run2 = UnifiedWelfareIntelligenceService.get_personnel_welfare_snapshot(
            db=db_session, current_user=u, personnel_id=p.id, reference_time=now
        )

        assert run1["current_risk"]["risk_score"] == run2["current_risk"]["risk_score"]
        assert run1["human_review_indicator"]["review_level"] == run2["human_review_indicator"]["review_level"]

    def test_unit_query_performance_realistic_size(self, db_session):
        bat = f"Bat_Perf_{uid()}"
        # 15 personnel in unit
        group = [make_personnel(battalion=bat) for _ in range(15)]
        db_session.add_all(group)
        db_session.commit()

        officer = make_user(role="officer", battalion=bat)
        db_session.add(officer)
        db_session.commit()

        start = datetime.now()
        res = UnifiedWelfareIntelligenceService.get_unit_welfare_intelligence(
            db=db_session, current_user=officer, battalion=bat
        )
        duration_ms = (datetime.now() - start).total_seconds() * 1000

        assert res["total_personnel_in_scope"] == 15
        assert duration_ms < 500  # Must be fast and batched (sub-500ms)


# =============================================================================
# 7. FASTAPI API INTEGRATION TESTS
# =============================================================================
class TestAPIEndpoints:
    def test_api_unauthenticated_rejected(self, client):
        res = client.get("/api/analytics/welfare-intelligence/unit")
        assert res.status_code == 401

        res_p = client.get("/api/analytics/welfare-intelligence/personnel/1")
        assert res_p.status_code == 401

    def test_api_personnel_snapshot(self, client, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion)
        db_session.add(u)
        db_session.commit()

        token = create_access_token(data={"sub": u.username, "role": u.role})
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get(f"/api/analytics/welfare-intelligence/personnel/{p.id}", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["personnel_id"] == p.id
        assert "current_risk" in data
        assert "trend" in data
        assert "human_review_indicator" in data
        assert "timeline" in data

    def test_api_unit_intelligence(self, client, db_session):
        bat = f"Bat_API_{uid()}"
        group = [make_personnel(battalion=bat) for _ in range(6)]
        db_session.add_all(group)
        db_session.commit()
        u = make_user(role="officer", battalion=bat)
        db_session.add(u)
        db_session.commit()

        token = create_access_token(data={"sub": u.username, "role": u.role})
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/analytics/welfare-intelligence/unit", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total_personnel_in_scope"] == 6
        assert data["data_suppressed"] is False
        assert "unit_overview" in data
        assert "personnel_cards" in data
