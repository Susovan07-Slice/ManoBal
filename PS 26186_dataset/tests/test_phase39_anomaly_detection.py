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
from db.models.telemetry import WearableTelemetry
from db.models.anomaly import WelfareAnomaly
from db.models.alert import WelfareAlert
from db.models.user import User
from core.security import create_access_token
from services.welfare_anomaly_service import (
    WelfareAnomalyService,
    MIN_PERSONAL_ASSESSMENTS_FOR_ANOMALY,
    ANALYTICS_MIN_GROUP_SIZE,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase39.db"
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


def make_telemetry(personnel_id, sleep_hours, days_ago):
    ts = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return WearableTelemetry(
        personnel_id=personnel_id,
        recorded_at=ts,
        heart_rate=68.0,
        hrv_rmssd=45.0,
        sleep_duration_hours=sleep_hours,
        sleep_quality_score=75.0,
        step_count=9000,
        active_minutes=45,
        source="simulated_wearable"
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
    user = User(username="admin_p39", role="admin", is_active=True, hashed_password="mock")
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": "admin_p39", "role": "admin"})


@pytest.fixture
def officer_sri_token(db_session: Session):
    user = User(username="officer_sri_p39", role="officer", battalion="1st Battalion", location="Srinagar", is_active=True, hashed_password="mock")
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": "officer_sri_p39", "role": "officer"})


@pytest.fixture
def officer_leh_token(db_session: Session):
    user = User(username="officer_leh_p39", role="officer", battalion="7th Battalion", location="Leh", is_active=True, hashed_password="mock")
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": "officer_leh_p39", "role": "officer"})


@pytest.fixture
def jawan_token(db_session: Session):
    user = User(username="jawan_p39", role="personnel", is_active=True, hashed_password="mock", personnel_id=1)
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": "jawan_p39", "role": "personnel"})


class TestPhase39WelfareAnomalyDetection:

    # =========================================================================
    # 1. PERSONAL ANOMALIES: RAPID RISK CHANGE & ACCELERATION
    # =========================================================================
    def test_rapid_risk_change_and_acceleration_detection(self, db_session: Session):
        """Verifies rapid risk change and acceleration anomaly detection."""
        p = make_personnel("P-ANOM-01", "Cadet Rapid", "1st Battalion", "Srinagar")
        db_session.add(p)
        db_session.commit()

        # Baseline: 3 assessments (scores 25, 27, 28)
        db_session.add(make_assessment(p.id, 25.0, days_ago=30))
        db_session.add(make_assessment(p.id, 27.0, days_ago=20))
        db_session.add(make_assessment(p.id, 28.0, days_ago=10))
        # Acute jump to 58.0 (+30 pts change!)
        db_session.add(make_assessment(p.id, 58.0, days_ago=1))
        db_session.commit()

        status_code, msg, anomalies, base_summary = WelfareAnomalyService.detect_personal_anomalies(p, db_session)

        assert status_code == "DETECTED"
        types = [a.anomaly_type for a in anomalies]
        assert "RAPID_RISK_CHANGE" in types

        # Check explainability of the anomaly
        rapid_anom = next(a for a in anomalies if a.anomaly_type == "RAPID_RISK_CHANGE")
        evidence = json.loads(rapid_anom.evidence_json)
        assert evidence["delta"] == 30.0
        assert evidence["baseline_value"] == 26.7
        assert "Current risk score (58.0) increased substantially" in evidence["explanation"]
        assert rapid_anom.severity in ["ATTENTION", "URGENT_REVIEW"]

    # =========================================================================
    # 2. WORKLOAD, SLEEP/RECOVERY, AND NIGHT SHIFT ANOMALIES
    # =========================================================================
    def test_workload_sleep_and_night_shift_anomalies(self, db_session: Session):
        """Validates detection of acute workload surges, sleep deficit departures, and night shifts."""
        p = make_personnel(
            "P-ANOM-02",
            "Cadet Strained",
            "1st Battalion",
            "Srinagar",
            duty_hours=72.0,  # Acute workload surge
            night_shifts=9,   # High night shifts
            consecutive_days=15 # Prolonged continuous duty
        )
        db_session.add(p)
        db_session.commit()

        # Add 3 baseline assessments so data sufficiency is satisfied
        for i, days in enumerate([30, 20, 10]):
            db_session.add(make_assessment(p.id, 30.0 + i, days_ago=days))

        # Add 6 wearable telemetry records: past 4 records typical sleep (7.5 hrs), recent 2 records acute drop (4.2 hrs)
        for d in [10, 8, 6, 4]:
            db_session.add(make_telemetry(p.id, 7.5, days_ago=d))
        for d in [2, 1]:
            db_session.add(make_telemetry(p.id, 4.2, days_ago=d))
        db_session.commit()

        status_code, msg, anomalies, base_summary = WelfareAnomalyService.detect_personal_anomalies(p, db_session)

        assert status_code == "DETECTED"
        types = [a.anomaly_type for a in anomalies]
        assert "WORKLOAD_ANOMALY" in types
        assert "SLEEP_RECOVERY_ANOMALY" in types
        assert "NIGHT_SHIFT_PATTERN_CHANGE" in types

        # Check sleep recovery explanation is non-medical
        sleep_anom = next(a for a in anomalies if a.anomaly_type == "SLEEP_RECOVERY_ANOMALY")
        ev = json.loads(sleep_anom.evidence_json)
        assert "Recent recovery pattern differs substantially from the person's historical baseline" in ev["explanation"]
        assert "medically unfit" not in ev["explanation"]

    # =========================================================================
    # 3. WELFARE FACTOR CLUSTERING
    # =========================================================================
    def test_welfare_factor_cluster_detection(self, db_session: Session):
        """Verifies multi-factor strain cluster anomaly."""
        p = make_personnel(
            "P-CLUSTER-01",
            "Cadet Cluster",
            "1st Battalion",
            "Srinagar",
            duty_hours=60.0,
            night_shifts=8,
            consecutive_days=14,
            leave_gap=75
        )
        db_session.add(p)
        db_session.commit()

        # Assessments showing worsening trajectory (25 -> 40 -> 60)
        db_session.add(make_assessment(p.id, 25.0, days_ago=25))
        db_session.add(make_assessment(p.id, 40.0, days_ago=15))
        db_session.add(make_assessment(p.id, 65.0, days_ago=1))
        db_session.commit()

        status_code, msg, anomalies, base_summary = WelfareAnomalyService.detect_personal_anomalies(p, db_session)
        assert status_code == "DETECTED"
        types = [a.anomaly_type for a in anomalies]
        assert "WELFARE_FACTOR_CLUSTER" in types

        cluster_anom = next(a for a in anomalies if a.anomaly_type == "WELFARE_FACTOR_CLUSTER")
        ev = json.loads(cluster_anom.evidence_json)
        assert len(ev["co_occurring_factors"]) >= 3
        assert cluster_anom.severity in ["ATTENTION", "URGENT_REVIEW"]

    # =========================================================================
    # 4. BASELINE SUFFICIENCY & FALSE-POSITIVE CONTROLS
    # =========================================================================
    def test_insufficient_baseline_and_normal_variation_controls(self, db_session: Session):
        """Verifies that insufficient history returns INSUFFICIENT_BASELINE and normal variation generates NO_ANOMALY."""
        # Personnel with only 1 assessment (< 3 required)
        p_insufficient = make_personnel("P-INSUFF-01", "Cadet Insuff", "1st Battalion", "Srinagar")
        db_session.add(p_insufficient)
        db_session.commit()
        db_session.add(make_assessment(p_insufficient.id, 45.0, days_ago=2))
        db_session.commit()

        status_code, msg, anomalies, _ = WelfareAnomalyService.detect_personal_anomalies(p_insufficient, db_session)
        assert status_code == "INSUFFICIENT_BASELINE"
        assert len(anomalies) == 0

        # Personnel with 3 assessments exhibiting normal, stable variation (20, 22, 21)
        p_stable = make_personnel("P-STABLE-01", "Cadet Stable", "1st Battalion", "Srinagar", duty_hours=40.0, night_shifts=2)
        db_session.add(p_stable)
        db_session.commit()
        db_session.add(make_assessment(p_stable.id, 20.0, days_ago=20))
        db_session.add(make_assessment(p_stable.id, 22.0, days_ago=10))
        db_session.add(make_assessment(p_stable.id, 21.0, days_ago=1))
        db_session.commit()

        status_code, msg, anomalies, _ = WelfareAnomalyService.detect_personal_anomalies(p_stable, db_session)
        assert status_code == "NO_ANOMALY"
        assert len(anomalies) == 0

    # =========================================================================
    # 5. DEDUPLICATION: REPEATED EVALUATIONS DO NOT CREATE DUPLICATE ROWS
    # =========================================================================
    def test_anomaly_deduplication(self, db_session: Session):
        """Running detection multiple times on unchanged data must NOT produce duplicate active anomalies."""
        p = make_personnel("P-DEDUP-01", "Cadet Dedup", "1st Battalion", "Srinagar", duty_hours=70.0)
        db_session.add(p)
        db_session.commit()

        db_session.add(make_assessment(p.id, 20.0, days_ago=20))
        db_session.add(make_assessment(p.id, 22.0, days_ago=10))
        db_session.add(make_assessment(p.id, 65.0, days_ago=1))  # Rapid change
        db_session.commit()

        # Run 1
        WelfareAnomalyService.detect_personal_anomalies(p, db_session, persist=True)
        count_1 = db_session.query(WelfareAnomaly).filter(WelfareAnomaly.personnel_id == p.id).count()
        assert count_1 > 0

        # Run 2, 3, 4 (identical data)
        for _ in range(3):
            WelfareAnomalyService.detect_personal_anomalies(p, db_session, persist=True)

        count_final = db_session.query(WelfareAnomaly).filter(WelfareAnomaly.personnel_id == p.id).count()
        assert count_final == count_1, "Repeated evaluations must not generate duplicate active anomaly records."

    # =========================================================================
    # 6. LIFECYCLE MANAGEMENT: ACKNOWLEDGE, REVIEW, RESOLVE
    # =========================================================================
    def test_anomaly_lifecycle_and_invalid_transitions(self, db_session: Session):
        """Validates DETECTED -> ACKNOWLEDGED -> UNDER_REVIEW -> RESOLVED and rejects invalid terminal transitions."""
        officer = User(username="officer_life", role="officer", battalion="1st Battalion", location="Srinagar", is_active=True, hashed_password="mock")
        db_session.add(officer)
        db_session.commit()

        p = make_personnel("P-LIFE-01", "Cadet Life", "1st Battalion", "Srinagar")
        db_session.add(p)
        db_session.commit()

        anom = WelfareAnomaly(
            personnel_id=p.id,
            scope_type="INDIVIDUAL",
            scope_battalion="1st Battalion",
            scope_location="Srinagar",
            anomaly_type="WORKLOAD_ANOMALY",
            severity="ATTENTION",
            status="DETECTED",
            confidence="HIGH",
            evidence_json=json.dumps({"reason": "Test"}),
            dedup_hash="test_life"
        )
        db_session.add(anom)
        db_session.commit()

        # Step 1: Acknowledge
        ack_anom = WelfareAnomalyService.acknowledge_anomaly(anom.id, officer, db_session)
        assert ack_anom.status == "ACKNOWLEDGED"
        assert ack_anom.acknowledged_by == officer.id

        # Step 2: Review
        rev_anom = WelfareAnomalyService.review_anomaly(anom.id, officer, db_session)
        assert rev_anom.status == "UNDER_REVIEW"

        # Step 3: Resolve (requires notes)
        with pytest.raises(ValueError):
            WelfareAnomalyService.resolve_anomaly(anom.id, "", officer, db_session)

        res_anom = WelfareAnomalyService.resolve_anomaly(anom.id, "Adjusted duty rota and granted 48h respite.", officer, db_session)
        assert res_anom.status == "RESOLVED"
        assert res_anom.resolved_by == officer.id

        # Terminal state: Cannot acknowledge a resolved anomaly
        with pytest.raises(ValueError):
            WelfareAnomalyService.acknowledge_anomaly(anom.id, officer, db_session)

    # =========================================================================
    # 7. UNIT-LEVEL ANOMALY DETECTION
    # =========================================================================
    def test_unit_level_anomaly_detection(self, db_session: Session):
        """Verifies detection of sudden unit-wide surges in elevated risk proportion."""
        # Create 6 personnel in Srinagar
        personnel_list = []
        for i in range(1, 7):
            p = make_personnel(f"P-UNIT-{i:02d}", f"Cadet Unit {i}", "1st Battalion", "Srinagar")
            db_session.add(p)
            personnel_list.append(p)
        db_session.commit()

        # Baseline period (30 days ago): All low risk (score 20.0) -> High/Crit = 0%
        for p in personnel_list:
            db_session.add(make_assessment(p.id, 20.0, days_ago=35))

        # Recent period (3 days ago): 4 of 6 personnel jump to High/Critical (scores 75-85) -> High/Crit = 66.7%!
        for p in personnel_list[:4]:
            db_session.add(make_assessment(p.id, 78.0, days_ago=3))
        for p in personnel_list[4:]:
            db_session.add(make_assessment(p.id, 25.0, days_ago=3))
        db_session.commit()

        officer = User(username="officer_unit", role="officer", battalion="1st Battalion", location="Srinagar")
        u_stat, u_msg, unit_anomalies, dq = WelfareAnomalyService.detect_unit_anomalies(db_session, officer)

        assert u_stat == "DETECTED"
        assert len(unit_anomalies) >= 1
        anom = unit_anomalies[0]
        assert anom.anomaly_type == "UNIT_LEVEL_ANOMALY"
        ev = json.loads(anom.evidence_json)
        assert ev["delta"] >= 15.0
        assert "An unusual increase in unit welfare indicators" in ev["explanation"]

    # =========================================================================
    # 8. RBAC, ANTI-IDOR, AND SMALL-GROUP PRIVACY PROTECTION
    # =========================================================================
    def test_rbac_anti_idor_and_small_group_privacy(
        self, db_session: Session, officer_sri_token, officer_leh_token, jawan_token
    ):
        """Validates RBAC barriers, prevents cross-battalion access, anti-IDOR, and enforces small group k-anonymity."""
        app.dependency_overrides[get_db] = lambda: db_session
        client = TestClient(app)

        # 6 personnel in Srinagar
        p_sri_list = []
        for i in range(1, 7):
            p = make_personnel(f"P-RBA-S{i:02d}", f"Sri Cadet {i}", "1st Battalion", "Srinagar", duty_hours=68.0)
            db_session.add(p)
            p_sri_list.append(p)
            db_session.flush()
            for d in [30, 20, 10, 1]:
                db_session.add(make_assessment(p.id, 30.0 if d > 1 else 65.0, days_ago=d))

        # 6 personnel in Leh
        for i in range(1, 7):
            p_leh = make_personnel(f"P-RBA-L{i:02d}", f"Leh Cadet {i}", "7th Battalion", "Leh")
            db_session.add(p_leh)
        db_session.commit()

        # Authorized Srinagar Officer can view Srinagar commander anomalies
        res_sri = client.get("/api/anomalies/commander", headers={"Authorization": f"Bearer {officer_sri_token}"})
        assert res_sri.status_code == 200
        assert res_sri.json()["status"] == "SUCCESS"
        assert res_sri.json()["scope"]["battalion"] == "1st Battalion"

        # Anti-IDOR: Srinagar Officer attempts to pass ?battalion=7th Battalion -> 403 Forbidden
        res_tamper = client.get(
            "/api/anomalies/commander?battalion=7th%20Battalion",
            headers={"Authorization": f"Bearer {officer_sri_token}"}
        )
        assert res_tamper.status_code == 403
        assert "outside your assigned Battalion scope" in res_tamper.json()["detail"]

        # Jawan user receives 403 Forbidden on commander anomalies endpoint
        res_jawan_cmd = client.get("/api/anomalies/commander", headers={"Authorization": f"Bearer {jawan_token}"})
        assert res_jawan_cmd.status_code == 403

        # Jawan cannot view other personnel anomalies
        res_jawan_other = client.get(f"/api/anomalies/personnel/{p_sri_list[1].id}", headers={"Authorization": f"Bearer {jawan_token}"})
        assert res_jawan_other.status_code == 403

        # Small Group Privacy: Remote outpost with only 3 personnel (< 5)
        user_small = User(username="officer_small", role="officer", battalion="Small Outpost", location="Border", is_active=True, hashed_password="mock")
        db_session.add(user_small)
        for i in range(1, 4):
            p_small = make_personnel(f"P-SM-{i:02d}", f"Small Cadet {i}", "Small Outpost", "Border")
            db_session.add(p_small)
        db_session.commit()
        token_small = create_access_token({"sub": "officer_small", "role": "officer"})

        res_priv = client.get("/api/anomalies/commander", headers={"Authorization": f"Bearer {token_small}"})
        assert res_priv.status_code == 200
        assert res_priv.json()["status"] == "INSUFFICIENT_GROUP_SIZE"
        assert len(res_priv.json()["anomalies"]) == 0
