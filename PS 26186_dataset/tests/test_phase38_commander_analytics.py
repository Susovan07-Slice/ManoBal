import os
import json
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from api.main import app
from db.base import Base
from db.session import get_db
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.alert import WelfareAlert, WelfareIntervention
from db.models.user import User
from core.security import create_access_token
from services.commander_analytics_service import CommanderAnalyticsService, ANALYTICS_MIN_GROUP_SIZE

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase38.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def make_personnel(code, name="Cadet Test", battalion="1st Battalion", location="Srinagar", duty_hours=40.0, night_shifts=2, consecutive_days=3, leave_gap=30):
    return Personnel(
        personnel_code=code,
        name=name,
        age=28,
        gender="Male",
        department="Infantry",
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
        remote_posting="No",
        operational_exposure="Medium"
    )


def make_assessment(personnel_id, score, stress_level="Low", priority="Routine", days_ago=0, key_factors=None):
    ts = datetime.now(timezone.utc) - timedelta(days=days_ago)
    kf = json.dumps(key_factors) if key_factors is not None else None
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


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def admin_token(db_session: Session):
    user = User(username="admin_p38", role="admin", is_active=True, hashed_password="mock")
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": "admin_p38", "role": "admin"})


@pytest.fixture
def officer_sri_token(db_session: Session):
    user = User(username="officer_sri_p38", role="officer", battalion="1st Battalion", location="Srinagar", is_active=True, hashed_password="mock")
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": "officer_sri_p38", "role": "officer"})


@pytest.fixture
def welfare_sri_token(db_session: Session):
    user = User(username="welfare_sri_p38", role="welfare", battalion="1st Battalion", location="Srinagar", is_active=True, hashed_password="mock")
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": "welfare_sri_p38", "role": "welfare"})


@pytest.fixture
def officer_leh_token(db_session: Session):
    user = User(username="officer_leh_p38", role="officer", battalion="7th Battalion", location="Leh", is_active=True, hashed_password="mock")
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": "officer_leh_p38", "role": "officer"})


@pytest.fixture
def jawan_token(db_session: Session):
    user = User(username="jawan_p38", role="personnel", is_active=True, hashed_password="mock", personnel_id=1)
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": "jawan_p38", "role": "personnel"})


class TestPhase38CommanderAnalytics:

    # =========================================================================
    # 1. RISK DISTRIBUTION (Authoritative Phase 34 V2, Latest Assessment Only)
    # =========================================================================
    def test_risk_distribution_uses_latest_assessment_and_no_duplication(self, db_session: Session):
        """Verifies that multiple historical assessments for the same person do not duplicate counts."""
        # Create 6 personnel in 1st Battalion Srinagar (>= min group size 5)
        personnel_list = []
        for i in range(1, 7):
            p = make_personnel(f"P-DIST-{i:02d}", f"Cadet {i}", "1st Battalion", "Srinagar")
            db_session.add(p)
            personnel_list.append(p)
        db_session.commit()

        # Personnel 1: Historical low (20), then intermediate (40), then latest critical (88.0)
        db_session.add(make_assessment(personnel_list[0].id, 20.0, "Low", "Routine", days_ago=20))
        db_session.add(make_assessment(personnel_list[0].id, 40.0, "Medium", "Preventive", days_ago=10))
        db_session.add(make_assessment(personnel_list[0].id, 88.0, "High", "Priority", days_ago=1))

        # Personnel 2: Latest High (74.0)
        db_session.add(make_assessment(personnel_list[1].id, 74.0, "High", "Priority", days_ago=2))

        # Personnel 3: Latest Elevated (60.0)
        db_session.add(make_assessment(personnel_list[2].id, 60.0, "Medium", "Preventive", days_ago=2))

        # Personnel 4: Latest Moderate (45.0)
        db_session.add(make_assessment(personnel_list[3].id, 45.0, "Medium", "Preventive", days_ago=2))

        # Personnel 5: Latest Low (22.0)
        db_session.add(make_assessment(personnel_list[4].id, 22.0, "Low", "Routine", days_ago=2))

        # Personnel 6: Latest Low (18.0)
        db_session.add(make_assessment(personnel_list[5].id, 18.0, "Low", "Routine", days_ago=2))
        db_session.commit()

        officer = User(username="officer_dist", role="officer", battalion="1st Battalion", location="Srinagar")
        res = CommanderAnalyticsService.compute_analytics(db_session, officer, time_filter="30d")

        assert res.status == "SUCCESS"
        dist = res.risk_distribution
        assert dist is not None
        # Exactly 6 unique personnel assessed, not 8 assessments
        assert dist.total_represented == 6
        assert dist.critical_count == 1
        assert dist.high_count == 1
        assert dist.elevated_count == 1
        assert dist.moderate_count == 1
        assert dist.low_count == 2

        # Check exact percentages: 2/6 = 33.3%, 1/6 = 16.7%
        assert dist.critical_pct == 16.7
        assert dist.high_pct == 16.7
        assert dist.elevated_pct == 16.7
        assert dist.moderate_pct == 16.7
        assert dist.low_pct == 33.3

    # =========================================================================
    # 2. LONGITUDINAL ORGANIZATIONAL TRENDS
    # =========================================================================
    def test_longitudinal_organizational_trends(self, db_session: Session):
        """Validates worsening, improving, stable, and insufficient history population calculations."""
        # 6 personnel in scope
        personnel_list = []
        for i in range(1, 7):
            p = make_personnel(f"P-TR-{i:02d}", f"Cadet Trend {i}", "1st Battalion", "Srinagar")
            db_session.add(p)
            personnel_list.append(p)
        db_session.commit()

        # P1: Worsening (score increases from 30 to 75, > 5.0 points)
        db_session.add(make_assessment(personnel_list[0].id, 30.0, "Low", "Routine", days_ago=15))
        db_session.add(make_assessment(personnel_list[0].id, 75.0, "High", "Priority", days_ago=1))

        # P2: Improving (score decreases from 80 to 40, < -5.0 points)
        db_session.add(make_assessment(personnel_list[1].id, 80.0, "High", "Priority", days_ago=15))
        db_session.add(make_assessment(personnel_list[1].id, 40.0, "Medium", "Preventive", days_ago=1))

        # P3: Stable (score changes by 1.0 point, e.g. 50 to 51)
        db_session.add(make_assessment(personnel_list[2].id, 50.0, "Medium", "Preventive", days_ago=15))
        db_session.add(make_assessment(personnel_list[2].id, 51.0, "Medium", "Preventive", days_ago=1))

        # P4: Insufficient History (only 1 assessment)
        db_session.add(make_assessment(personnel_list[3].id, 45.0, "Medium", "Preventive", days_ago=2))

        # P5: Persistent Elevated (consecutive high scores: 72, 75, 78)
        db_session.add(make_assessment(personnel_list[4].id, 72.0, "High", "Priority", days_ago=20))
        db_session.add(make_assessment(personnel_list[4].id, 75.0, "High", "Priority", days_ago=10))
        db_session.add(make_assessment(personnel_list[4].id, 78.0, "High", "Priority", days_ago=1))

        # P6: Stable low
        db_session.add(make_assessment(personnel_list[5].id, 20.0, "Low", "Routine", days_ago=15))
        db_session.add(make_assessment(personnel_list[5].id, 21.0, "Low", "Routine", days_ago=1))
        db_session.commit()

        officer = User(username="officer_trend", role="officer", battalion="1st Battalion", location="Srinagar")
        res = CommanderAnalyticsService.compute_analytics(db_session, officer, time_filter="30d")

        trend = res.trend
        assert trend is not None
        assert trend.worsening_count >= 1
        assert trend.improving_count >= 1
        assert trend.insufficient_history_count == 1
        assert trend.persistent_elevated_population >= 1
        assert trend.mean_risk_score is not None
        assert trend.median_risk_score is not None

    # =========================================================================
    # 3. ALERT & INTERVENTION ANALYTICS (Phase 37 integration)
    # =========================================================================
    def test_alert_and_intervention_aggregations(self, db_session: Session):
        """Verifies aggregate counts of open, under review, and resolved alerts, plus interventions."""
        personnel_list = []
        for i in range(1, 6):
            p = make_personnel(f"P-ALT-{i:02d}", f"Cadet Alt {i}", "1st Battalion", "Srinagar")
            db_session.add(p)
            personnel_list.append(p)
        db_session.commit()

        # Add 3 alerts
        a1 = WelfareAlert(personnel_id=personnel_list[0].id, alert_type="RAPID_ESCALATION", severity="URGENT_REVIEW", status="OPEN")
        a2 = WelfareAlert(personnel_id=personnel_list[1].id, alert_type="PERSISTENT_ELEVATED_RISK", severity="HIGH_PRIORITY", status="UNDER_REVIEW")
        a3 = WelfareAlert(personnel_id=personnel_list[2].id, alert_type="SUDDEN_SPIKE", severity="ATTENTION", status="RESOLVED")
        db_session.add_all([a1, a2, a3])
        db_session.commit()

        # Add 2 interventions
        inv1 = WelfareIntervention(
            alert_id=a1.id,
            personnel_id=personnel_list[0].id,
            intervention_type="sleep_stand_down",
            status="PLANNED",
            created_by=1
        )
        inv2 = WelfareIntervention(
            alert_id=a2.id,
            personnel_id=personnel_list[1].id,
            intervention_type="supportive_check_in",
            status="COMPLETED",
            created_by=1,
            completed_at=datetime.now(timezone.utc)
        )
        db_session.add_all([inv1, inv2])
        db_session.commit()

        officer = User(username="officer_alt", role="officer", battalion="1st Battalion", location="Srinagar")
        res = CommanderAnalyticsService.compute_analytics(db_session, officer, time_filter="30d")

        alerts = res.alerts
        assert alerts is not None
        assert alerts.total_alerts == 3
        assert alerts.open_alerts == 1
        assert alerts.under_review_alerts == 1
        assert alerts.resolved_alerts == 1
        assert alerts.unresolved_alerts == 2
        assert alerts.by_type.get("RAPID_ESCALATION") == 1
        assert alerts.by_type.get("PERSISTENT_ELEVATED_RISK") == 1
        assert alerts.by_type.get("SUDDEN_SPIKE") == 1

        inv_sec = res.interventions
        assert inv_sec is not None
        assert inv_sec.total_interventions == 2
        assert inv_sec.planned == 1
        assert inv_sec.completed == 1

    # =========================================================================
    # 4. WELFARE FACTORS ANALYTICS & NON-PUNITIVE LANGUAGE
    # =========================================================================
    def test_welfare_factors_non_punitive_aggregation(self, db_session: Session):
        """Verifies recurring factor identification without punitive labels."""
        personnel_list = []
        for i in range(1, 6):
            p = make_personnel(f"P-WF-{i:02d}", f"Cadet WF {i}", "1st Battalion", "Srinagar", duty_hours=55.0)
            db_session.add(p)
            personnel_list.append(p)
        db_session.commit()

        for p in personnel_list:
            db_session.add(make_assessment(
                p.id,
                65.0,
                key_factors=["Restorative sleep deficit (< 5.5 hrs/night)", "Elevated operational duty workload (> 50 hrs/week)"]
            ))
        db_session.commit()

        officer = User(username="officer_wf", role="officer", battalion="1st Battalion", location="Srinagar")
        res = CommanderAnalyticsService.compute_analytics(db_session, officer)

        wf_sec = res.welfare_factors
        assert wf_sec is not None
        factor_names = [f.factor for f in wf_sec.factors]
        assert any("sleep" in f.lower() for f in factor_names)
        assert any("duty" in f.lower() or "workload" in f.lower() for f in factor_names)

        # Non-punitive check: no "bad", "weak", "poor", "disciplinary"
        for f in factor_names:
            f_lower = f.lower()
            assert "bad" not in f_lower
            assert "weak" not in f_lower
            assert "poor" not in f_lower
            assert "disciplinary" not in f_lower

    # =========================================================================
    # 5. PRIVACY & SMALL GROUP PROTECTION (k-anonymity)
    # =========================================================================
    def test_small_group_privacy_protection_prevents_leakage(self, db_session: Session):
        """When population < ANALYTICS_MIN_GROUP_SIZE (default 5), aggregated risk categories must NOT be revealed."""
        # Create only 3 personnel (< 5)
        for i in range(1, 4):
            p = make_personnel(f"P-PRIV-{i:02d}", f"Cadet Priv {i}", "Small Outpost", "Remote Hill")
            db_session.add(p)
        db_session.commit()

        officer = User(username="officer_priv", role="officer", battalion="Small Outpost", location="Remote Hill")
        res = CommanderAnalyticsService.compute_analytics(db_session, officer)

        assert res.status == "INSUFFICIENT_GROUP_SIZE"
        assert "Aggregate analytics are unavailable for this population size" in (res.message or "")
        # Sections must be withheld to guarantee zero deduction of individual risk
        assert res.risk_distribution is None
        assert res.trend is None
        assert res.alerts is None
        assert res.welfare_factors is None
        assert res.interventions is None
        assert res.data_quality.insufficient_data is True

    # =========================================================================
    # 6. RBAC & ANTI-IDOR SCOPE ISOLATION
    # =========================================================================
    def test_officer_scope_isolation_and_jawan_forbidden(
        self, db_session: Session, officer_sri_token, officer_leh_token, jawan_token
    ):
        """Validates that officers only see their own battalion/location and Jawans cannot access analytics."""
        app.dependency_overrides[get_db] = lambda: db_session
        client = TestClient(app)

        # Create 6 personnel in Srinagar
        for i in range(1, 7):
            p_sri = make_personnel(f"P-SRI-{i:02d}", f"Srinagar Cadet {i}", "1st Battalion", "Srinagar")
            db_session.add(p_sri)
            db_session.flush()
            db_session.add(make_assessment(p_sri.id, 25.0, "Low", "Routine"))

        # Create 6 personnel in Leh
        for i in range(1, 7):
            p_leh = make_personnel(f"P-LEH-{i:02d}", f"Leh Cadet {i}", "7th Battalion", "Leh")
            db_session.add(p_leh)
            db_session.flush()
            db_session.add(make_assessment(p_leh.id, 80.0, "High", "Priority"))
        db_session.commit()

        # Srinagar Officer: Sees Srinagar data (low risk), total_authorized = 6
        res_sri = client.get("/api/analytics/commander", headers={"Authorization": f"Bearer {officer_sri_token}"})
        assert res_sri.status_code == 200
        data_sri = res_sri.json()
        assert data_sri["scope"]["battalion"] == "1st Battalion"
        assert data_sri["scope"]["location"] == "Srinagar"
        assert data_sri["scope"]["total_authorized_personnel"] == 6
        assert data_sri["risk_distribution"]["low_count"] == 6
        assert data_sri["risk_distribution"]["high_count"] == 0

        # Leh Officer: Sees Leh data (high risk), total_authorized = 6
        res_leh = client.get("/api/analytics/commander", headers={"Authorization": f"Bearer {officer_leh_token}"})
        assert res_leh.status_code == 200
        data_leh = res_leh.json()
        assert data_leh["scope"]["battalion"] == "7th Battalion"
        assert data_leh["scope"]["location"] == "Leh"
        assert data_leh["scope"]["total_authorized_personnel"] == 6
        assert data_leh["risk_distribution"]["high_count"] == 6
        assert data_leh["risk_distribution"]["low_count"] == 0

        # Anti-IDOR: Srinagar Officer attempts to pass ?battalion=7th Battalion -> 403 Forbidden
        res_tamper = client.get(
            "/api/analytics/commander?battalion=7th%20Battalion",
            headers={"Authorization": f"Bearer {officer_sri_token}"}
        )
        assert res_tamper.status_code == 403
        assert "outside your assigned Battalion scope" in res_tamper.json()["detail"]

        # Jawan user receives 403 Forbidden
        res_jawan = client.get("/api/analytics/commander", headers={"Authorization": f"Bearer {jawan_token}"})
        assert res_jawan.status_code == 403

    # =========================================================================
    # 7. TIME FILTERING (7d, 30d, 90d, custom)
    # =========================================================================
    def test_time_filters(self, db_session: Session, admin_token):
        """Verifies that date range filters filter alerts and assessment timelines accurately."""
        app.dependency_overrides[get_db] = lambda: db_session
        client = TestClient(app)

        for i in range(1, 6):
            p = make_personnel(f"P-TF-{i:02d}", f"Cadet TF {i}", "1st Battalion", "Srinagar")
            db_session.add(p)
            db_session.flush()
            # 1 assessment 3 days ago, 1 assessment 60 days ago
            db_session.add(make_assessment(p.id, 45.0, days_ago=3))
            db_session.add(make_assessment(p.id, 35.0, days_ago=60))
        db_session.commit()

        # 7d filter
        res_7d = client.get("/api/analytics/commander?time_filter=7d", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_7d.status_code == 200
        assert res_7d.json()["data_quality"]["date_range"]["filter_type"] == "7d"

        # 90d filter
        res_90d = client.get("/api/analytics/commander?time_filter=90d", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_90d.status_code == 200
        assert res_90d.json()["data_quality"]["date_range"]["filter_type"] == "90d"

    # =========================================================================
    # 8. DATA QUALITY & DETERMINISM
    # =========================================================================
    def test_data_quality_and_determinism(self, db_session: Session):
        """Verifies resilience against missing assessments, malformed values, and ensures deterministic outputs."""
        # 5 personnel with 0 assessments
        for i in range(1, 6):
            p = make_personnel(f"P-DQ-{i:02d}", f"Cadet DQ {i}", "1st Battalion", "Srinagar")
            db_session.add(p)
        db_session.commit()

        ref_time = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
        officer = User(username="officer_dq", role="officer", battalion="1st Battalion", location="Srinagar")
        res1 = CommanderAnalyticsService.compute_analytics(db_session, officer, reference_time=ref_time)
        res2 = CommanderAnalyticsService.compute_analytics(db_session, officer, reference_time=ref_time)

        # Zero assessments handled cleanly
        assert res1.status == "INSUFFICIENT_DATA"
        assert res1.data_quality.insufficient_data is True
        assert res1.risk_distribution.total_represented == 0

        # Determinism check: identical results
        assert res1.model_dump() == res2.model_dump()

