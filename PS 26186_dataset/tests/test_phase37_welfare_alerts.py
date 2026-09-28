import pytest
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from api.main import app
from db.models.alert import WelfareAlert, WelfareIntervention, WelfareAlertAudit
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.user import User
from core.security import create_access_token

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.base import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase37.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def make_personnel(code, name="Test Cadet", battalion="1st Battalion", location="Srinagar"):
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
        duty_hours_per_week=44.0,
        night_shifts_per_month=4,
        consecutive_duty_days=3,
        transfer_frequency=1,
        training_load=2,
        leave_gap_days=30,
        remote_posting="No",
        operational_exposure="Medium"
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
    user = User(username="admin_test", role="admin", is_active=True, hashed_password="mock")
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": "admin_test", "role": "admin"})

@pytest.fixture
def officer_srinagar_token(db_session: Session):
    user = User(username="officer_sri", role="officer", battalion="1st Battalion", location="Srinagar", is_active=True, hashed_password="mock")
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": "officer_sri", "role": "officer"})

@pytest.fixture
def officer_leh_token(db_session: Session):
    user = User(username="officer_leh", role="officer", battalion="7th Battalion", location="Leh", is_active=True, hashed_password="mock")
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": "officer_leh", "role": "officer"})

@pytest.fixture
def jawan_token(db_session: Session):
    user = User(username="jawan_test", role="personnel", is_active=True, hashed_password="mock", personnel_id=1)
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": "jawan_test", "role": "personnel"})


class TestPhase37WelfareAlertsHardening:

    # =========================================================================
    # 1. Authoritative V2 Category Alignment (No Competing Scoring)
    # =========================================================================
    def test_v2_category_alignment_and_non_competing_threshold(self, db_session: Session):
        """Verifies Phase 37 strictly adopts Phase 34 V2 outputs without calculating independent risk."""
        from services.welfare_alert_service import WelfareAlertService

        p = make_personnel("P-V2-01", "Cadet V2", "1st Battalion", "Srinagar")
        db_session.add(p)
        db_session.commit()

        # V2 Critical (Score 88.0, risk_category='Critical') -> URGENT_REVIEW
        ass_crit = StressAssessment(
            personnel_id=p.id,
            stress_level="High",
            low_probability=0.05,
            medium_probability=0.10,
            high_probability=0.85,
            risk_score=88.0,
            risk_priority="Priority",
            key_factors=json.dumps({"risk_category": "Critical", "top_risk_factors": ["Severe night duty"]}),
            model_version="risk_engine_v2",
            assessment_timestamp=datetime.now(timezone.utc)
        )
        db_session.add(ass_crit)
        db_session.commit()

        alerts = WelfareAlertService.evaluate_and_generate_alerts(db_session, p.id, ass_crit)
        high_alert = next((a for a in alerts if a.alert_type == "HIGH_CURRENT_RISK"), None)
        assert high_alert is not None
        assert high_alert.severity == "URGENT_REVIEW"
        assert "Critical" in high_alert.trigger_reason
        assert "88.0" in high_alert.trigger_reason

    # =========================================================================
    # 2. Alert Deduplication Scenarios A through E
    # =========================================================================
    def test_alert_deduplication_scenarios_a_to_e(self, db_session: Session):
        """Validates all five deduplication scenarios required by specification."""
        from services.welfare_alert_service import WelfareAlertService

        p = make_personnel("P-DEDUP-01", "Cadet Dedup", "1st Battalion", "Srinagar")
        db_session.add(p)
        db_session.commit()

        # --- Scenario A: Assessment completed once -> exactly 1 alert ---
        ass1 = StressAssessment(
            personnel_id=p.id,
            stress_level="High",
            low_probability=0.1,
            medium_probability=0.1,
            high_probability=0.8,
            risk_score=75.0,
            risk_priority="Priority",
            key_factors=json.dumps({"risk_category": "High"}),
            model_version="risk_engine_v2",
            assessment_timestamp=datetime.now(timezone.utc)
        )
        db_session.add(ass1)
        db_session.commit()

        alerts_a = WelfareAlertService.evaluate_and_generate_alerts(db_session, p.id, ass1)
        assert len([a for a in alerts_a if a.alert_type == "HIGH_CURRENT_RISK"]) == 1

        # --- Scenario B: Same assessment endpoint called repeatedly -> No duplicate alert ---
        alerts_b = WelfareAlertService.evaluate_and_generate_alerts(db_session, p.id, ass1)
        assert len(alerts_b) == 0

        # --- Scenario C: New assessment with same underlying condition -> Unresolved alert remains, No duplicate ---
        ass2 = StressAssessment(
            personnel_id=p.id,
            stress_level="High",
            low_probability=0.1,
            medium_probability=0.1,
            high_probability=0.8,
            risk_score=78.0,
            risk_priority="Priority",
            key_factors=json.dumps({"risk_category": "High"}),
            model_version="risk_engine_v2",
            assessment_timestamp=datetime.now(timezone.utc)
        )
        db_session.add(ass2)
        db_session.commit()

        alerts_c = WelfareAlertService.evaluate_and_generate_alerts(db_session, p.id, ass2)
        assert len([a for a in alerts_c if a.alert_type == "HIGH_CURRENT_RISK"]) == 0

        # --- Scenario D: Old alert resolved -> New assessment creates genuinely new alert ---
        existing_alert = db_session.query(WelfareAlert).filter(WelfareAlert.personnel_id == p.id, WelfareAlert.alert_type == "HIGH_CURRENT_RISK").first()
        WelfareAlertService.resolve_alert(db_session, existing_alert.id, user_id=1, resolution_reason="Welfare stand-down complete")

        ass3 = StressAssessment(
            personnel_id=p.id,
            stress_level="High",
            low_probability=0.1,
            medium_probability=0.1,
            high_probability=0.8,
            risk_score=82.0,
            risk_priority="Priority",
            key_factors=json.dumps({"risk_category": "High"}),
            model_version="risk_engine_v2",
            assessment_timestamp=datetime.now(timezone.utc)
        )
        db_session.add(ass3)
        db_session.commit()

        alerts_d = WelfareAlertService.evaluate_and_generate_alerts(db_session, p.id, ass3)
        assert len([a for a in alerts_d if a.alert_type == "HIGH_CURRENT_RISK"]) == 1

        # --- Scenario E: Multiple alert types triggered by one assessment -> Separate legitimate alert types, no accidental duplication ---
        # Add history records to also trigger persistent elevated risk and worsening trend
        for i in range(4):
            hist_ass = StressAssessment(
                personnel_id=p.id,
                stress_level="High",
                low_probability=0.1,
                medium_probability=0.1,
                high_probability=0.8,
                risk_score=60.0 + (i * 5.0),
                risk_priority="Priority",
                key_factors=json.dumps({"risk_category": "Elevated", "top_risk_factors": ["High duty hours"]}),
                model_version="risk_engine_v2",
                assessment_timestamp=datetime.now(timezone.utc)
            )
            db_session.add(hist_ass)
        db_session.commit()

        # Resolve the previous alert so fresh triggers can fire
        for a in db_session.query(WelfareAlert).filter(WelfareAlert.personnel_id == p.id).all():
            if a.status != "RESOLVED":
                a.status = "RESOLVED"
        db_session.commit()

        multi_ass = StressAssessment(
            personnel_id=p.id,
            stress_level="High",
            low_probability=0.05,
            medium_probability=0.1,
            high_probability=0.85,
            risk_score=85.0,
            risk_priority="Priority",
            key_factors=json.dumps({"risk_category": "Critical", "top_risk_factors": ["High duty hours"]}),
            model_version="risk_engine_v2",
            assessment_timestamp=datetime.now(timezone.utc)
        )
        db_session.add(multi_ass)
        db_session.commit()

        alerts_e = WelfareAlertService.evaluate_and_generate_alerts(db_session, p.id, multi_ass)
        types_e = [a.alert_type for a in alerts_e]
        assert len(types_e) == len(set(types_e)), "All triggered alert types must be distinct without duplicate types!"
        assert "HIGH_CURRENT_RISK" in types_e

    # =========================================================================
    # 3. Complete State Machine Lifecycle & Invalid Transitions
    # =========================================================================
    def test_complete_lifecycle_and_invalid_transitions(self, db_session: Session, admin_token):
        """Validates OPEN -> ACKNOWLEDGED -> UNDER_REVIEW -> INTERVENTION_PLANNED -> FOLLOW_UP -> RESOLVED and rejects invalid transitions."""
        from db.session import get_db
        app.dependency_overrides[get_db] = lambda: db_session
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {admin_token}"}

        p = make_personnel("P-LIFE-01", "Cadet Lifecycle", "1st Battalion", "Srinagar")
        db_session.add(p)
        db_session.commit()

        alert = WelfareAlert(personnel_id=p.id, alert_type="HIGH_CURRENT_RISK", severity="HIGH_PRIORITY", status="OPEN")
        db_session.add(alert)
        db_session.commit()

        # Valid: Acknowledge
        res_ack = client.post(f"/api/welfare/alerts/{alert.id}/acknowledge", headers=headers)
        assert res_ack.status_code == 200
        assert res_ack.json()["status"] == "ACKNOWLEDGED"

        # Invalid: cannot acknowledge already acknowledged alert
        res_dup_ack = client.post(f"/api/welfare/alerts/{alert.id}/acknowledge", headers=headers)
        assert res_dup_ack.status_code == 400

        # Valid: Start review
        res_rev = client.post(f"/api/welfare/alerts/{alert.id}/review", headers=headers)
        assert res_rev.status_code == 200
        assert res_rev.json()["status"] == "UNDER_REVIEW"

        # Valid: Create intervention
        res_int = client.post(f"/api/welfare/alerts/{alert.id}/intervention", json={"intervention_type": "sleep_stand_down", "notes": "48h rest"}, headers=headers)
        assert res_int.status_code == 200
        intervention_id = res_int.json()["id"]

        # Valid: Schedule follow-up
        res_fol = client.post(f"/api/welfare/interventions/{intervention_id}/follow-up", json={"follow_up_date": datetime.now(timezone.utc).isoformat(), "notes": "Followup in 48h"}, headers=headers)
        assert res_fol.status_code == 200
        assert res_fol.json()["follow_up_date"] is not None

        # Valid: Complete follow-up intervention
        res_comp = client.post(f"/api/welfare/interventions/{intervention_id}/complete", json={"notes": "Followup completed successfully"}, headers=headers)
        assert res_comp.status_code == 200
        assert res_comp.json()["status"] == "COMPLETED"

        # Valid: Resolve alert
        res_res = client.post(f"/api/welfare/alerts/{alert.id}/resolve", json={"resolution_reason": "Welfare restored"}, headers=headers)
        assert res_res.status_code == 200
        assert res_res.json()["status"] == "RESOLVED"

        # Invalid: cannot acknowledge resolved alert
        res_bad_ack = client.post(f"/api/welfare/alerts/{alert.id}/acknowledge", headers=headers)
        assert res_bad_ack.status_code == 400

        # Invalid: cannot review resolved alert
        res_bad_rev = client.post(f"/api/welfare/alerts/{alert.id}/review", headers=headers)
        assert res_bad_rev.status_code == 400

        # Invalid: cannot create intervention for resolved alert
        res_bad_int = client.post(f"/api/welfare/alerts/{alert.id}/intervention", json={"intervention_type": "welfare_check"}, headers=headers)
        assert res_bad_int.status_code == 400

        # Invalid: cannot resolve already resolved alert
        res_bad_res = client.post(f"/api/welfare/alerts/{alert.id}/resolve", json={"resolution_reason": "Again"}, headers=headers)
        assert res_bad_res.status_code == 400

    # =========================================================================
    # 4. Intervention Management (Creation, Follow-Up, Completion, Cancellation)
    # =========================================================================
    def test_intervention_completion_and_cancellation(self, db_session: Session, admin_token):
        """Tests that interventions can be scheduled, completed, and cancelled with appropriate audits."""
        from db.session import get_db
        app.dependency_overrides[get_db] = lambda: db_session
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {admin_token}"}

        p = make_personnel("P-INT-01", "Cadet Intervene", "1st Battalion", "Srinagar")
        db_session.add(p)
        db_session.commit()

        alert = WelfareAlert(personnel_id=p.id, alert_type="WORSENING_TREND", severity="ATTENTION", status="UNDER_REVIEW")
        db_session.add(alert)
        db_session.commit()

        # Create intervention
        res_int = client.post(f"/api/welfare/alerts/{alert.id}/intervention", json={"intervention_type": "counseling", "notes": "Peer support meeting"}, headers=headers)
        int_id = res_int.json()["id"]

        # Cancel intervention
        res_cancel = client.post(f"/api/welfare/interventions/{int_id}/cancel", json={"reason": "Replaced by medical consultation"}, headers=headers)
        assert res_cancel.status_code == 200
        assert res_cancel.json()["status"] == "CANCELLED"

        # Attempting to cancel again should fail
        res_dup_cancel = client.post(f"/api/welfare/interventions/{int_id}/cancel", json={"reason": "Again"}, headers=headers)
        assert res_dup_cancel.status_code == 400

    # =========================================================================
    # 5. Audit Trail Verification
    # =========================================================================
    def test_audit_trail_completeness(self, db_session: Session, admin_token):
        """Verifies complete audit trail recording across all state changes."""
        from db.session import get_db
        app.dependency_overrides[get_db] = lambda: db_session
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {admin_token}"}

        p = make_personnel("P-AUD-01", "Cadet Audit", "1st Battalion", "Srinagar")
        db_session.add(p)
        db_session.commit()

        alert = WelfareAlert(personnel_id=p.id, alert_type="PERSISTENT_ELEVATED_RISK", severity="HIGH_PRIORITY", status="OPEN")
        db_session.add(alert)
        db_session.commit()

        # Log initial creation audit
        from services.welfare_alert_service import WelfareAlertService
        WelfareAlertService._create_audit_log(db_session, alert.id, "ALERT_CREATED", actor_id=None, new_status="OPEN")
        db_session.commit()

        client.post(f"/api/welfare/alerts/{alert.id}/acknowledge", headers=headers)
        client.post(f"/api/welfare/alerts/{alert.id}/review", headers=headers)
        res_i = client.post(f"/api/welfare/alerts/{alert.id}/intervention", json={"intervention_type": "workload_cap"}, headers=headers)
        int_id = res_i.json()["id"]
        client.post(f"/api/welfare/interventions/{int_id}/follow-up", json={"follow_up_date": datetime.now(timezone.utc).isoformat()}, headers=headers)
        client.post(f"/api/welfare/interventions/{int_id}/complete", json={"notes": "All done"}, headers=headers)
        client.post(f"/api/welfare/alerts/{alert.id}/resolve", json={"resolution_reason": "Welfare indicators stabilized"}, headers=headers)

        audits = db_session.query(WelfareAlertAudit).filter(WelfareAlertAudit.alert_id == alert.id).order_by(WelfareAlertAudit.id).all()
        actions = [a.action for a in audits]

        assert "ALERT_CREATED" in actions
        assert "ALERT_ACKNOWLEDGED" in actions
        assert "REVIEW_STARTED" in actions
        assert "INTERVENTION_CREATED" in actions
        assert "FOLLOWUP_SCHEDULED" in actions
        assert "FOLLOWUP_COMPLETED" in actions
        assert "ALERT_RESOLVED" in actions

        for audit in audits:
            assert audit.timestamp is not None
            assert audit.alert_id == alert.id

    # =========================================================================
    # 6. RBAC & Cross-Personnel Scope Isolation (Security & IDOR)
    # =========================================================================
    def test_rbac_and_scope_isolation(self, db_session: Session, admin_token, officer_srinagar_token, officer_leh_token, jawan_token):
        """Verifies that Jawans receive 403, and Officers can only view/manipulate alerts within their battalion scope."""
        from db.session import get_db
        app.dependency_overrides[get_db] = lambda: db_session
        client = TestClient(app)

        # Personnel 1 in 1st Battalion (Srinagar)
        p1 = make_personnel("P-SRI-01", "Sepoy Srinagar", "1st Battalion", "Srinagar")
        # Personnel 2 in 7th Battalion (Leh)
        p2 = make_personnel("P-LEH-01", "Sepoy Leh", "7th Battalion", "Leh")
        db_session.add_all([p1, p2])
        db_session.commit()

        alert_sri = WelfareAlert(personnel_id=p1.id, alert_type="HIGH_CURRENT_RISK", severity="HIGH_PRIORITY", status="OPEN")
        alert_leh = WelfareAlert(personnel_id=p2.id, alert_type="HIGH_CURRENT_RISK", severity="URGENT_REVIEW", status="OPEN")
        db_session.add_all([alert_sri, alert_leh])
        db_session.commit()

        # 1. Jawan receives 403 Forbidden on alerts endpoints
        res_jwn = client.get("/api/welfare/alerts", headers={"Authorization": f"Bearer {jawan_token}"})
        assert res_jwn.status_code == 403

        # 2. Officer Srinagar only sees alerts for 1st Battalion
        res_sri = client.get("/api/welfare/alerts", headers={"Authorization": f"Bearer {officer_srinagar_token}"})
        assert res_sri.status_code == 200
        sri_alerts = res_sri.json()
        assert any(a["id"] == alert_sri.id for a in sri_alerts)
        assert not any(a["id"] == alert_leh.id for a in sri_alerts)

        # 3. Officer Leh only sees alerts for 7th Battalion
        res_leh = client.get("/api/welfare/alerts", headers={"Authorization": f"Bearer {officer_leh_token}"})
        assert res_leh.status_code == 200
        leh_alerts = res_leh.json()
        assert any(a["id"] == alert_leh.id for a in leh_alerts)
        assert not any(a["id"] == alert_sri.id for a in leh_alerts)

        # 4. Cross-battalion manipulation: Officer Srinagar attempting to acknowledge Officer Leh's alert is 403 Forbidden!
        res_cross = client.post(f"/api/welfare/alerts/{alert_leh.id}/acknowledge", headers={"Authorization": f"Bearer {officer_srinagar_token}"})
        assert res_cross.status_code == 403
        assert "scope" in res_cross.json().get("detail", "").lower()

        # 5. Admin has system-wide access to all battalions
        res_adm = client.get("/api/welfare/alerts", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_adm.status_code == 200
        adm_ids = [a["id"] for a in res_adm.json()]
        assert alert_sri.id in adm_ids
        assert alert_leh.id in adm_ids
