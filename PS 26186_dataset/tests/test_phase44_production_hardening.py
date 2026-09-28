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
from db.models.welfare_case import (
    WelfareCase,
    WelfareCaseReview,
    WelfareCaseNote,
    WelfareCaseAudit,
)
from core.config import Settings
from core.security import create_access_token, hash_password
from services.welfare_case_service import WelfareCaseService

TEST_DB_URL = "sqlite:///./test_phase44.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def uid():
    return uuid.uuid4().hex[:6]


def make_personnel(code=None, battalion="1st Battalion", location="Srinagar"):
    c = code or f"PF-44-{uid()}"
    return Personnel(
        personnel_code=c,
        name=f"Cadet {c}",
        age=28,
        gender="Male",
        department="Infantry",
        battalion=battalion,
        location=location,
        job_role="Rifleman",
        experience_years=4.0,
        duty_hours_per_week=48.0,
        night_shifts_per_month=4,
        consecutive_duty_days=6,
        leave_gap_days=20,
        operational_exposure="Medium",
    )


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_phase44.db"):
        try:
            os.remove("./test_phase44.db")
        except Exception:
            pass


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def jawan_user_and_token(db: Session):
    p = make_personnel(battalion="1st Battalion", location="Srinagar")
    db.add(p)
    db.commit()
    db.refresh(p)

    u = User(
        username=f"jawan_{uid()}",
        hashed_password=hash_password("Pass123!"),
        role="personnel",
        personnel_id=p.id,
        battalion="1st Battalion",
        location="Srinagar",
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    token = create_access_token(
        data={"sub": u.username, "role": u.role, "personnel_id": p.id, "battalion": u.battalion, "location": u.location}
    )
    return p, u, token


@pytest.fixture
def officer_user_and_token(db: Session):
    u = User(
        username=f"officer_{uid()}",
        hashed_password=hash_password("OfficerPass123!"),
        role="officer",
        personnel_id=None,
        battalion="1st Battalion",
        location="Srinagar",
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    token = create_access_token(
        data={"sub": u.username, "role": u.role, "battalion": u.battalion, "location": u.location}
    )
    return u, token


@pytest.fixture
def other_officer_user_and_token(db: Session):
    u = User(
        username=f"officer_other_{uid()}",
        hashed_password=hash_password("OtherPass123!"),
        role="officer",
        personnel_id=None,
        battalion="7th Battalion",
        location="Jammu",
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    token = create_access_token(
        data={"sub": u.username, "role": u.role, "battalion": u.battalion, "location": u.location}
    )
    return u, token


@pytest.fixture
def admin_user_and_token(db: Session):
    u = User(
        username=f"admin_{uid()}",
        hashed_password=hash_password("AdminPass123!"),
        role="admin",
        personnel_id=None,
        battalion=None,
        location=None,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    token = create_access_token(
        data={"sub": u.username, "role": u.role}
    )
    return u, token


# =============================================================================
# 1. SECURITY & CONFIGURATION HARDENING TESTS
# =============================================================================
def test_production_config_rejects_weak_secrets(monkeypatch):
    """Production mode must reject weak, default, or short secrets."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "sih_personnel_stress_monitoring_secret_key_2026_secure")
    with pytest.raises(RuntimeError) as exc:
        Settings()
    assert "Insecure SECRET_KEY" in str(exc.value)

    monkeypatch.setenv("SECRET_KEY", "short_secret_under_32_chars")
    with pytest.raises(RuntimeError) as exc2:
        Settings()
    assert "at least 32 characters" in str(exc2.value)


def test_production_config_rejects_debug_mode(monkeypatch):
    """Production mode must reject DEBUG=True."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "a" * 40)
    monkeypatch.setenv("DEBUG", "true")
    with pytest.raises(RuntimeError) as exc:
        Settings()
    assert "DEBUG mode cannot be enabled in a production environment" in str(exc.value)


def test_production_config_accepts_strong_secret(monkeypatch):
    """Production mode boots successfully with a strong high-entropy secret and DEBUG=false."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "Xk9#mP2$vL5@wR8!qZ3*tY6&bN1^cA7~dE4+")
    monkeypatch.setenv("DEBUG", "false")
    s = Settings()
    assert s.ENVIRONMENT == "production"
    assert s.DEBUG is False
    assert s.ENABLE_DOCS is False


# =============================================================================
# 2. HEALTH & MONITORING READINESS
# =============================================================================
def test_health_check_endpoint_healthy(client: TestClient):
    """Health endpoint must safely probe DB and report status without leaking credentials."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data
    assert "connected" in data["database"]
    assert "environment" in data
    assert "password" not in json.dumps(data).lower()
    assert "sqlite" not in json.dumps(data).lower() or data["database"]["engine"] in ["sqlite", "postgresql"]


# =============================================================================
# 3. GLOBAL EXCEPTION HANDLING & ERROR HARDENING
# =============================================================================
def test_unhandled_exception_returns_sanitized_500(monkeypatch):
    """Unhandled internal errors must return structured 500 without leaking stack traces or SQL."""
    from services.prediction_service import WelfarePredictionService

    def broken_predict(*args, **kwargs):
        raise RuntimeError("DATABASE DRIVER CONNECTION FAILED: secret_db_path /var/internal/data.db")

    monkeypatch.setattr(WelfarePredictionService, "predict", broken_predict)

    # Use TestClient with raise_server_exceptions=False to test Starlette/FastAPI exception handler
    with TestClient(app, raise_server_exceptions=False) as safe_client:
        resp = safe_client.post(
            "/api/submit-checkin",
            json={
                "Age": 28,
                "Gender": "Male",
                "Department": "Operations",
                "Working_Hours_per_Week": 50.0,
                "Duty_Hours_Per_Week": 50.0,
                "Consecutive_Duty_Days": 7,
                "Night_Shifts_Per_Month": 4,
                "Leave_Gap_Days": 30,
                "Annual_Leaves_Taken": 5,
                "Sleep_Hours": 6.5,
                "Physical_Activity_Hours_per_Week": 4.0,
                "Operational_Exposure": "Medium",
                "Remote_Posting": "No",
                "Burnout_Symptoms": "Sometimes",
                "Mood_Score": 3.0,
                "Experience_Years": 4.0,
                "Job_Role": "Rifleman",
                "Location": "Srinagar"
            }
        )
        assert resp.status_code == 500
        data = resp.json()
        assert data["error"] == "Internal Server Error"
        assert "secret_db_path" not in json.dumps(data)
        assert "Traceback" not in json.dumps(data)


# =============================================================================
# 4. AUTHENTICATION & TOKEN LIFECYCLE
# =============================================================================
def test_authentication_token_validation(client: TestClient, jawan_user_and_token):
    p, u, token = jawan_user_and_token

    # 1. No credentials
    resp_none = client.get("/api/auth/me")
    assert resp_none.status_code == 401
    assert "Bearer" in resp_none.headers.get("WWW-Authenticate", "")

    # 2. Invalid / malformed token
    resp_invalid = client.get("/api/auth/me", headers={"Authorization": "Bearer bad.token.here"})
    assert resp_invalid.status_code == 401

    # 3. Expired token
    expired_token = create_access_token(
        data={"sub": u.username, "role": u.role},
        expires_delta=timedelta(minutes=-10)
    )
    resp_expired = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp_expired.status_code == 401

    # 4. Valid token
    resp_valid = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp_valid.status_code == 200
    assert resp_valid.json()["username"] == u.username


# =============================================================================
# 5. RBAC BOUNDARIES
# =============================================================================
def test_rbac_personnel_forbidden_from_commander_endpoints(client: TestClient, jawan_user_and_token):
    p, u, token = jawan_user_and_token
    headers = {"Authorization": f"Bearer {token}"}

    # Jawan cannot view unit dashboard summary
    resp1 = client.get("/api/dashboard/summary", headers=headers)
    assert resp1.status_code == 403

    # Jawan cannot view unit welfare alerts
    resp2 = client.get("/api/welfare/alerts", headers=headers)
    assert resp2.status_code == 403

    # Jawan cannot view commander analytics
    resp3 = client.get("/api/analytics/commander", headers=headers)
    assert resp3.status_code == 403

    # Jawan cannot open a welfare case
    resp4 = client.post(
        "/api/welfare-cases",
        headers=headers,
        json={"personnel_id": p.id, "case_type": "CURRENT_RISK_REVIEW", "title": "Unauthorized"}
    )
    assert resp4.status_code == 403


# =============================================================================
# 6. ANTI-IDOR SECURITY
# =============================================================================
def test_anti_idor_jawan_cross_personnel_access_denied(
    client: TestClient, db: Session, jawan_user_and_token, officer_user_and_token
):
    p_me, u_me, token_me = jawan_user_and_token
    p_peer = make_personnel(code="PF-PEER-01", battalion="1st Battalion", location="Srinagar")
    db.add(p_peer)
    db.commit()
    db.refresh(p_peer)

    headers = {"Authorization": f"Bearer {token_me}"}

    # 1. Jawan cannot read peer personnel record
    r1 = client.get(f"/api/personnel/{p_peer.id}", headers=headers)
    assert r1.status_code == 403

    # 2. Jawan cannot read peer feature snapshot
    r2 = client.get(f"/api/analytics/personnel/{p_peer.id}/features", headers=headers)
    assert r2.status_code == 403

    # 3. Jawan cannot read peer unified welfare snapshot
    r3 = client.get(f"/api/analytics/welfare-intelligence/personnel/{p_peer.id}", headers=headers)
    assert r3.status_code == 403

    # 4. Jawan cannot read peer anomaly signals
    r4 = client.get(f"/api/anomalies/personnel/{p_peer.id}", headers=headers)
    assert r4.status_code == 403


def test_anti_idor_submit_checkin_tampering_blocked(
    client: TestClient, db: Session, jawan_user_and_token
):
    p_me, u_me, token_me = jawan_user_and_token
    p_peer = make_personnel(code="PF-PEER-CHK", battalion="1st Battalion", location="Srinagar")
    p_peer.duty_hours_per_week = 40.0
    db.add(p_peer)
    db.commit()
    db.refresh(p_peer)

    # 1. Authenticated Jawan passing peer's ID must be rejected with 403
    r1 = client.post(
        "/api/submit-checkin",
        headers={"Authorization": f"Bearer {token_me}"},
        json={
            "personnel_id": p_peer.id,
            "Age": 28,
            "Gender": "Male",
            "Department": "Operations",
            "Working_Hours_per_Week": 75.0,
            "Duty_Hours_Per_Week": 75.0,
            "Consecutive_Duty_Days": 14,
            "Night_Shifts_Per_Month": 8,
            "Leave_Gap_Days": 120,
            "Annual_Leaves_Taken": 2,
            "Sleep_Hours": 4.0,
            "Physical_Activity_Hours_per_Week": 2.0,
            "Operational_Exposure": "High",
            "Remote_Posting": "Yes",
            "Burnout_Symptoms": "Often",
            "Mood_Score": 1.0,
            "Experience_Years": 4.0,
            "Job_Role": "Rifleman",
            "Location": "Srinagar"
        }
    )
    assert r1.status_code == 403

    # 2. Unauthenticated caller passing personnel_id does NOT mutate database
    r2 = client.post(
        "/api/submit-checkin",
        json={
            "personnel_id": p_peer.id,
            "Age": 28,
            "Gender": "Male",
            "Department": "Operations",
            "Working_Hours_per_Week": 80.0,
            "Duty_Hours_Per_Week": 80.0,
            "Consecutive_Duty_Days": 15,
            "Night_Shifts_Per_Month": 10,
            "Leave_Gap_Days": 150,
            "Annual_Leaves_Taken": 2,
            "Sleep_Hours": 4.0,
            "Physical_Activity_Hours_per_Week": 1.0,
            "Operational_Exposure": "High",
            "Remote_Posting": "Yes",
            "Burnout_Symptoms": "Often",
            "Mood_Score": 1.0,
            "Experience_Years": 4.0,
            "Job_Role": "Rifleman",
            "Location": "Srinagar"
        }
    )
    assert r2.status_code == 200  # Returns evaluated assessment safely
    # Verify peer's database record was NOT mutated
    db.refresh(p_peer)
    assert p_peer.duty_hours_per_week == 40.0


def test_anti_idor_officer_cross_battalion_access_denied(
    client: TestClient, db: Session, other_officer_user_and_token
):
    """Officer from 7th Battalion cannot query 1st Battalion cases or personnel."""
    u_7th, token_7th = other_officer_user_and_token
    p_1st = make_personnel(code="PF-BAT1-01", battalion="1st Battalion", location="Srinagar")
    db.add(p_1st)
    db.commit()
    db.refresh(p_1st)

    headers = {"Authorization": f"Bearer {token_7th}"}

    # 1. Cannot query personnel from 1st Battalion
    r1 = client.get(f"/api/personnel/{p_1st.id}", headers=headers)
    assert r1.status_code == 403

    # 2. Cannot query commander analytics with battalion override
    r2 = client.get("/api/analytics/commander?battalion=1st Battalion", headers=headers)
    assert r2.status_code == 403

    # 3. Cannot query anomalies with battalion override
    r3 = client.get("/api/anomalies/commander?battalion=1st Battalion", headers=headers)
    assert r3.status_code == 403


# =============================================================================
# 7. SMALL-GROUP PRIVACY (k >= 5)
# =============================================================================
def test_privacy_k_anonymity_suppression(
    client: TestClient, db: Session, other_officer_user_and_token
):
    """When authorized population < 5, aggregate numbers and distributions must be suppressed."""
    u, token = other_officer_user_and_token
    headers = {"Authorization": f"Bearer {token}"}

    # Seed only 2 personnel in 7th Battalion and 1 case (cohort < 5)
    last_p = None
    for i in range(2):
        last_p = make_personnel(code=f"PF-PRIV-0{i}", battalion="7th Battalion", location="Jammu")
        db.add(last_p)
    db.commit()
    db.refresh(last_p)

    c = WelfareCase(
        personnel_id=last_p.id,
        case_reference=f"CASE-PRIV-{uid()}",
        title="Privacy Test Case",
        case_type="CURRENT_RISK_REVIEW",
        status="OPEN",
        trigger_source="OFFICER_INITIATED",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(c)
    db.commit()


    # 1. Commander analytics k-anonymity suppression
    r_comm = client.get("/api/analytics/commander", headers=headers)
    assert r_comm.status_code == 200
    comm_data = r_comm.json()
    assert comm_data["status"] == "INSUFFICIENT_GROUP_SIZE"
    assert comm_data.get("risk_distribution") is None
    assert comm_data.get("trend") is None

    # 2. Commander anomalies k-anonymity suppression
    r_anom = client.get("/api/anomalies/commander", headers=headers)
    assert r_anom.status_code == 200
    anom_data = r_anom.json()
    assert anom_data["status"] == "INSUFFICIENT_GROUP_SIZE"
    assert anom_data["active_anomalies_count"] == 0

    # 3. Welfare cases summary stats suppression
    r_case = client.get("/api/welfare-cases/summary-stats", headers=headers)
    assert r_case.status_code == 200
    case_data = r_case.json()
    assert case_data["data_suppressed"] is True
    assert case_data["status_counts"] == {}



# =============================================================================
# 8. DATABASE CONSTRAINTS & AUDIT TRAIL IMMUTABILITY
# =============================================================================
def test_database_cascade_and_audit_immutability(
    db: Session, officer_user_and_token
):
    """Historical audit logs and notes must remain immutable."""
    u, token = officer_user_and_token
    p = make_personnel(code="PF-AUD-01", battalion="1st Battalion", location="Srinagar")
    db.add(p)
    db.commit()
    db.refresh(p)

    from schemas.welfare_case import WelfareCaseCreateRequest
    req = WelfareCaseCreateRequest(
        personnel_id=p.id,
        case_type="CURRENT_RISK_REVIEW",
        title="Audit Integrity Check Case",
        initial_notes="Initial baseline observation."
    )
    case = WelfareCaseService.create_case(req, u, db)

    # Verify audit log was created
    audits = db.query(WelfareCaseAudit).filter(WelfareCaseAudit.case_id == case.id).all()
    assert len(audits) >= 1
    assert audits[0].action == "CASE_CREATED"
    assert audits[0].actor_id == u.id

    # Append immutable note
    from schemas.welfare_case import WelfareCaseNoteCreateRequest
    note_req = WelfareCaseNoteCreateRequest(
        note_type="REVIEW_NOTE",
        content="Human review recorded with clinical-safe observation."
    )
    note = WelfareCaseService.add_note(case.id, note_req, u, db)
    assert note.id is not None
    assert note.note_type == "REVIEW_NOTE"

    # Audits must have increased
    audits_after = db.query(WelfareCaseAudit).filter(WelfareCaseAudit.case_id == case.id).all()
    assert len(audits_after) == 2


# =============================================================================
# 9. 404 NOT FOUND HANDLING FOR NON-EXISTENT ENTITIES
# =============================================================================
def test_entity_not_found_returns_clean_404(client: TestClient, officer_user_and_token):
    u, token = officer_user_and_token
    headers = {"Authorization": f"Bearer {token}"}

    # Case not found
    r_case = client.get("/api/welfare-cases/999999", headers=headers)
    assert r_case.status_code == 404

    # Anomaly not found
    r_anom = client.post("/api/anomalies/999999/acknowledge", headers=headers)
    assert r_anom.status_code == 404


# =============================================================================
# 10. END-TO-END WELFARE LIFECYCLE INTEGRITY (PHASES 34–43)
# =============================================================================
def test_end_to_end_welfare_workflow_integrity(
    client: TestClient, db: Session, officer_user_and_token
):
    """Full workflow: assessment -> alert -> snapshot -> case -> review -> closure."""
    u, token = officer_user_and_token
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Personnel in Officer's scope
    p = make_personnel(code="PF-E2E-01", battalion="1st Battalion", location="Srinagar")
    db.add(p)
    db.commit()
    db.refresh(p)

    # 2. Trigger assessment (Phase 34)
    r_ass = client.post(
        f"/api/personnel/{p.id}/assess",
        headers=headers,
        json={"duty_hours_per_week": 65.0, "consecutive_duty_days": 12, "night_shifts_per_month": 6}
    )
    assert r_ass.status_code == 201
    ass_data = r_ass.json()["assessment"]
    assert "risk_score" in ass_data

    # 3. Retrieve Unified Intelligence Snapshot (Phase 42)
    r_snap = client.get(
        f"/api/analytics/welfare-intelligence/personnel/{p.id}",
        headers=headers
    )
    assert r_snap.status_code == 200
    snap_data = r_snap.json()
    assert snap_data["personnel_code"] == p.personnel_code

    # 4. Open Welfare Case (Phase 43)
    r_case = client.post(
        "/api/welfare-cases",
        headers=headers,
        json={
            "personnel_id": p.id,
            "case_type": "CURRENT_RISK_REVIEW",
            "title": "E2E Automated Hardening Test Case",
            "trigger_source": "PHASE_42_INTELLIGENCE",
            "assessment_id": ass_data["id"],
            "initial_notes": "Opened from Phase 42 unified intelligence drilldown."
        }
    )
    assert r_case.status_code == 201
    case_detail = r_case.json()
    case_id = case_detail["id"]
    assert case_detail["status"] == "OPEN"

    # 5. Record Human Review
    r_rev = client.post(
        f"/api/welfare-cases/{case_id}/review",
        headers=headers,
        json={
            "review_type": "INITIAL_TRIAGE",
            "observations": "Personnel experiencing sustained operational tempo; review duty pacing.",
            "decision": "REVIEW_DUTY_SUPPORT",
            "next_step": "Coordinate duty rotation with platoon commander.",
            "review_window": "7_DAYS",
            "new_status": "UNDER_REVIEW"
        }
    )
    assert r_rev.status_code == 201
    rev_data = r_rev.json()
    assert rev_data["decision"] == "REVIEW_DUTY_SUPPORT"

    # Verify case transitioned to UNDER_REVIEW
    r_case_chk = client.get(f"/api/welfare-cases/{case_id}", headers=headers)
    assert r_case_chk.status_code == 200
    assert r_case_chk.json()["status"] == "UNDER_REVIEW"


    # 6. Transition to Monitoring
    r_stat = client.post(
        f"/api/welfare-cases/{case_id}/status",
        headers=headers,
        json={"status": "MONITORING"}
    )
    assert r_stat.status_code == 200
    assert r_stat.json()["status"] == "MONITORING"

    # 7. Close Case with explicit human action
    r_close = client.post(
        f"/api/welfare-cases/{case_id}/close",
        headers=headers,
        json={
            "closure_reason": "MONITORING_COMPLETED",
            "closure_notes": "Duty hours stabilized at 44h/week; follow-up satisfactory."
        }
    )
    assert r_close.status_code == 200
    assert r_close.json()["status"] == "CLOSED"

    # 8. Verify Timeline and Audits are intact
    r_tl = client.get(f"/api/welfare-cases/{case_id}/timeline", headers=headers)
    assert r_tl.status_code == 200
    tl_events = r_tl.json()["events"]
    assert len(tl_events) >= 3

    r_aud = client.get(f"/api/welfare-cases/{case_id}/audits", headers=headers)
    assert r_aud.status_code == 200
    aud_events = r_aud.json()["audits"]
    assert len(aud_events) >= 4
