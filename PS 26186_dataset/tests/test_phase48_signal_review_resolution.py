import os
import json
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from api.main import app
from db.base import Base
from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from db.models.anomaly import WelfareAnomaly, WelfareAnomalyAudit
from db.models.welfare_notification import WelfareNotification, WelfareNotificationAudit
from core.security import hash_password, create_access_token

TEST_DB_URL = "sqlite:///./test_phase48.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def uid():
    return uuid.uuid4().hex[:6]


def make_personnel(code=None, battalion="7th Battalion", location="Srinagar"):
    c = code or f"PF-48-{uid()}"
    return Personnel(
        personnel_code=c,
        name=f"Jawan {c}",
        age=27,
        gender="Male",
        department="Infantry",
        battalion=battalion,
        location=location,
        job_role="Rifleman",
        experience_years=5.0,
        duty_hours_per_week=48.0,
    )


def make_user(role="personnel", battalion="7th Battalion", location="Srinagar", personnel_id=None):
    u_name = f"user_{role}_{uid()}"
    return User(
        username=u_name,
        hashed_password=hash_password("Password123!"),
        role=role,
        battalion=battalion,
        location=location,
        personnel_id=personnel_id,
        is_active=True,
    )


def make_anomaly(personnel_id, battalion="7th Battalion", location="Srinagar", anom_type="SLEEP_RECOVERY_ANOMALY"):
    return WelfareAnomaly(
        personnel_id=personnel_id,
        scope_type="INDIVIDUAL",
        scope_battalion=battalion,
        scope_location=location,
        anomaly_type=anom_type,
        severity="ATTENTION",
        status="DETECTED",
        confidence="MEDIUM",
        baseline_sample_count=8,
        detected_at=datetime.now(timezone.utc),
        dedup_hash=f"hash-{uid()}",
        evidence_json=json.dumps({
            "explanation": "Continuous high duty cycle detected with sleep deficit.",
            "baseline_value": 7.5,
            "current_value": 4.5,
            "delta": 3.0,
            "co_occurring_factors": ["High Temp", "Continuous Shifts"],
        }),
    )


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_phase48.db"):
        try:
            os.remove("./test_phase48.db")
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


def get_token(username: str, role: str, personnel_id: int = None, battalion: str = None, location: str = None) -> str:
    return create_access_token({
        "sub": username,
        "role": role,
        "personnel_id": personnel_id,
        "battalion": battalion,
        "location": location,
    })


# =============================================================================
# A. REVIEW WORKFLOW TESTS
# =============================================================================

def test_commander_can_review_anomaly_with_decision_and_notes(client, db_session):
    p = make_personnel(battalion="7th Battalion", location="Srinagar")
    db_session.add(p)
    db_session.commit()

    anom = make_anomaly(p.id, battalion="7th Battalion", location="Srinagar")
    db_session.add(anom)
    db_session.commit()

    officer = make_user(role="officer", battalion="7th Battalion", location="Srinagar")
    db_session.add(officer)
    db_session.commit()

    token = get_token(officer.username, "officer", battalion="7th Battalion", location="Srinagar")

    res = client.post(
        f"/api/anomalies/{anom.id}/review",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "decision": "OFFER_WELFARE_SUPPORT",
            "notes": "Conducted initial review. Recommended 24h recuperative rest and sleep hygiene protocol.",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "UNDER_REVIEW"
    assert data["review_decision"] == "OFFER_WELFARE_SUPPORT"
    assert "recuperative rest" in data["review_notes"]
    assert data["reviewed_by"] == officer.id
    assert data["reviewed_at"] is not None

    # Verify audit record created
    audit = db_session.query(WelfareAnomalyAudit).filter(
        WelfareAnomalyAudit.anomaly_id == anom.id,
        WelfareAnomalyAudit.action == "ANOMALY_REVIEWED",
    ).first()
    assert audit is not None
    assert audit.actor_id == officer.id
    assert audit.new_status == "UNDER_REVIEW"
    details = json.loads(audit.details)
    assert details["decision"] == "OFFER_WELFARE_SUPPORT"


def test_get_anomaly_audits_endpoint(client, db_session):
    p = make_personnel(battalion="7th Battalion", location="Srinagar")
    db_session.add(p)
    db_session.commit()

    anom = make_anomaly(p.id, battalion="7th Battalion", location="Srinagar")
    db_session.add(anom)
    db_session.commit()

    officer = make_user(role="officer", battalion="7th Battalion", location="Srinagar")
    db_session.add(officer)
    db_session.commit()

    token = get_token(officer.username, "officer", battalion="7th Battalion", location="Srinagar")

    # Review signal
    client.post(
        f"/api/anomalies/{anom.id}/review",
        headers={"Authorization": f"Bearer {token}"},
        json={"decision": "CONTINUE_MONITORING", "notes": "Baseline stable."},
    )

    # Fetch audits
    res = client.get(
        f"/api/anomalies/{anom.id}/audits",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    audits = res.json()
    assert len(audits) >= 1
    assert audits[0]["action"] == "ANOMALY_REVIEWED"
    assert audits[0]["actor_username"] == officer.username


# =============================================================================
# B. RESOLVE + JAWAN NOTIFICATION TESTS
# =============================================================================

def test_commander_can_resolve_anomaly_and_notify_jawan(client, db_session):
    p = make_personnel(battalion="7th Battalion", location="Srinagar")
    db_session.add(p)
    db_session.commit()

    anom = make_anomaly(p.id, battalion="7th Battalion", location="Srinagar")
    db_session.add(anom)
    db_session.commit()

    officer = make_user(role="officer", battalion="7th Battalion", location="Srinagar")
    db_session.add(officer)
    db_session.commit()

    token = get_token(officer.username, "officer", battalion="7th Battalion", location="Srinagar")

    res = client.post(
        f"/api/anomalies/{anom.id}/resolve",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "resolution_notes": "Conducted 1-on-1 supportive check-in, arranged 48h recovery period, and reallocated roster shifts.",
            "notify_personnel": True,
            "custom_message": "Your recent duty/recovery concern has been reviewed and resolved. Please ensure adequate rest and reach out to your welfare officer if needed.",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "RESOLVED"
    assert data["resolved_at"] is not None
    assert data["resolved_by"] == officer.id
    assert "48h recovery" in data["resolution_notes"]

    # Verify Anomaly Audit
    audit = db_session.query(WelfareAnomalyAudit).filter(
        WelfareAnomalyAudit.anomaly_id == anom.id,
        WelfareAnomalyAudit.action == "ANOMALY_RESOLVED",
    ).first()
    assert audit is not None
    assert audit.new_status == "RESOLVED"

    # Verify Welfare Notification created for the Jawan
    notif = db_session.query(WelfareNotification).filter(
        WelfareNotification.recipient_personnel_id == p.id,
        WelfareNotification.source_type == "ANOMALY",
        WelfareNotification.source_id == anom.id,
    ).first()
    assert notif is not None
    assert notif.title == "Welfare Signal Resolved"
    assert "duty/recovery concern has been reviewed" in notif.message
    assert notif.status == "UNREAD"
    assert notif.created_by == officer.id


# =============================================================================
# C. JAWAN PORTAL NOTIFICATION CONSUMPTION
# =============================================================================

def test_jawan_receives_and_reads_resolution_notification(client, db_session):
    p = make_personnel(battalion="7th Battalion", location="Srinagar")
    db_session.add(p)
    db_session.commit()

    jawan_user = make_user(role="personnel", battalion="7th Battalion", location="Srinagar", personnel_id=p.id)
    db_session.add(jawan_user)
    db_session.commit()

    anom = make_anomaly(p.id, battalion="7th Battalion", location="Srinagar")
    db_session.add(anom)
    db_session.commit()

    officer = make_user(role="officer", battalion="7th Battalion", location="Srinagar")
    db_session.add(officer)
    db_session.commit()

    officer_token = get_token(officer.username, "officer", battalion="7th Battalion", location="Srinagar")

    # Officer resolves and notifies
    client.post(
        f"/api/anomalies/{anom.id}/resolve",
        headers={"Authorization": f"Bearer {officer_token}"},
        json={
            "resolution_notes": "Roster adjusted; supportive check-in concluded.",
            "notify_personnel": True,
            "custom_message": "Welfare signal resolved. Rest days confirmed.",
        },
    )

    # Jawan logs in
    jawan_token = get_token(
        jawan_user.username,
        "personnel",
        personnel_id=p.id,
        battalion="7th Battalion",
        location="Srinagar",
    )

    # Jawan fetches notifications
    res = client.get("/api/notifications", headers={"Authorization": f"Bearer {jawan_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["unread_count"] >= 1
    matching = [n for n in data["notifications"] if n["source_type"] == "ANOMALY" and n["source_id"] == anom.id]
    assert len(matching) == 1
    notif_id = matching[0]["id"]
    assert "Rest days confirmed" in matching[0]["message"]

    # Jawan marks as read
    read_res = client.post(
        f"/api/notifications/{notif_id}/read",
        headers={"Authorization": f"Bearer {jawan_token}"},
    )
    assert read_res.status_code == 200
    assert read_res.json()["status"] == "READ"

    # Unread count decreases
    count_res = client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {jawan_token}"})
    assert count_res.status_code == 200
    assert count_res.json()["unread_count"] == 0


# =============================================================================
# D. SECURITY & SCOPE ENFORCEMENT (RBAC & ANTI-IDOR)
# =============================================================================

def test_jawan_cannot_review_or_resolve_anomaly(client, db_session):
    p = make_personnel(battalion="7th Battalion", location="Srinagar")
    db_session.add(p)
    db_session.commit()

    jawan_user = make_user(role="personnel", battalion="7th Battalion", location="Srinagar", personnel_id=p.id)
    db_session.add(jawan_user)
    db_session.commit()

    anom = make_anomaly(p.id, battalion="7th Battalion", location="Srinagar")
    db_session.add(anom)
    db_session.commit()

    jawan_token = get_token(
        jawan_user.username,
        "personnel",
        personnel_id=p.id,
        battalion="7th Battalion",
        location="Srinagar",
    )

    # Review attempt by Jawan -> 403
    res_review = client.post(
        f"/api/anomalies/{anom.id}/review",
        headers={"Authorization": f"Bearer {jawan_token}"},
        json={"decision": "RESOLVE_SIGNAL", "notes": "Trying to self-resolve."},
    )
    assert res_review.status_code == 403

    # Resolve attempt by Jawan -> 403
    res_resolve = client.post(
        f"/api/anomalies/{anom.id}/resolve",
        headers={"Authorization": f"Bearer {jawan_token}"},
        json={"resolution_notes": "Trying to resolve."},
    )
    assert res_resolve.status_code == 403


def test_officer_cannot_review_or_resolve_outside_battalion_scope(client, db_session):
    p_unit9 = make_personnel(battalion="9th Battalion", location="Ladakh")
    db_session.add(p_unit9)
    db_session.commit()

    anom_unit9 = make_anomaly(p_unit9.id, battalion="9th Battalion", location="Ladakh")
    db_session.add(anom_unit9)
    db_session.commit()

    officer_unit7 = make_user(role="officer", battalion="7th Battalion", location="Srinagar")
    db_session.add(officer_unit7)
    db_session.commit()

    token_unit7 = get_token(officer_unit7.username, "officer", battalion="7th Battalion", location="Srinagar")

    # Out of scope review -> 403
    res_review = client.post(
        f"/api/anomalies/{anom_unit9.id}/review",
        headers={"Authorization": f"Bearer {token_unit7}"},
        json={"decision": "CONTINUE_MONITORING", "notes": "Unauthorized review."},
    )
    assert res_review.status_code == 403

    # Out of scope resolve -> 403
    res_resolve = client.post(
        f"/api/anomalies/{anom_unit9.id}/resolve",
        headers={"Authorization": f"Bearer {token_unit7}"},
        json={"resolution_notes": "Unauthorized resolve."},
    )
    assert res_resolve.status_code == 403


def test_another_jawan_cannot_access_or_read_resolution_notification(client, db_session):
    p1 = make_personnel(battalion="7th Battalion", location="Srinagar")
    p2 = make_personnel(battalion="7th Battalion", location="Srinagar")
    db_session.add_all([p1, p2])
    db_session.commit()

    jawan2 = make_user(role="personnel", battalion="7th Battalion", location="Srinagar", personnel_id=p2.id)
    officer = make_user(role="officer", battalion="7th Battalion", location="Srinagar")
    db_session.add_all([jawan2, officer])
    db_session.commit()

    anom1 = make_anomaly(p1.id, battalion="7th Battalion", location="Srinagar")
    db_session.add(anom1)
    db_session.commit()

    officer_token = get_token(officer.username, "officer", battalion="7th Battalion", location="Srinagar")

    # Resolve and notify p1
    client.post(
        f"/api/anomalies/{anom1.id}/resolve",
        headers={"Authorization": f"Bearer {officer_token}"},
        json={"resolution_notes": "Resolved for p1", "notify_personnel": True},
    )

    notif = db_session.query(WelfareNotification).filter(WelfareNotification.recipient_personnel_id == p1.id).first()
    assert notif is not None

    # Jawan 2 tries to read Jawan 1's notification -> 403
    jawan2_token = get_token(jawan2.username, "personnel", personnel_id=p2.id, battalion="7th Battalion", location="Srinagar")
    res = client.post(
        f"/api/notifications/{notif.id}/read",
        headers={"Authorization": f"Bearer {jawan2_token}"},
    )
    assert res.status_code == 403


# =============================================================================
# E. DUPLICATION & TERMINAL STATE PREVENTION
# =============================================================================

def test_duplicate_resolution_prevented(client, db_session):
    p = make_personnel(battalion="7th Battalion", location="Srinagar")
    db_session.add(p)
    db_session.commit()

    anom = make_anomaly(p.id, battalion="7th Battalion", location="Srinagar")
    db_session.add(anom)
    db_session.commit()

    officer = make_user(role="officer", battalion="7th Battalion", location="Srinagar")
    db_session.add(officer)
    db_session.commit()

    token = get_token(officer.username, "officer", battalion="7th Battalion", location="Srinagar")

    # First resolution -> 200
    res1 = client.post(
        f"/api/anomalies/{anom.id}/resolve",
        headers={"Authorization": f"Bearer {token}"},
        json={"resolution_notes": "First resolution note.", "notify_personnel": True},
    )
    assert res1.status_code == 200

    notifs_count_1 = db_session.query(WelfareNotification).filter(WelfareNotification.recipient_personnel_id == p.id).count()
    assert notifs_count_1 == 1

    # Second resolution attempt -> 400 Bad Request
    res2 = client.post(
        f"/api/anomalies/{anom.id}/resolve",
        headers={"Authorization": f"Bearer {token}"},
        json={"resolution_notes": "Second resolution attempt.", "notify_personnel": True},
    )
    assert res2.status_code == 400
    assert "already in terminal status" in res2.json()["detail"]

    # Verify no duplicate notification was created
    notifs_count_2 = db_session.query(WelfareNotification).filter(WelfareNotification.recipient_personnel_id == p.id).count()
    assert notifs_count_2 == 1


def test_review_on_resolved_anomaly_rejected(client, db_session):
    p = make_personnel(battalion="7th Battalion", location="Srinagar")
    db_session.add(p)
    db_session.commit()

    anom = make_anomaly(p.id, battalion="7th Battalion", location="Srinagar")
    anom.status = "RESOLVED"
    db_session.add(anom)
    db_session.commit()

    officer = make_user(role="officer", battalion="7th Battalion", location="Srinagar")
    db_session.add(officer)
    db_session.commit()

    token = get_token(officer.username, "officer", battalion="7th Battalion", location="Srinagar")

    res = client.post(
        f"/api/anomalies/{anom.id}/review",
        headers={"Authorization": f"Bearer {token}"},
        json={"decision": "CONTINUE_MONITORING", "notes": "Attempting review on resolved."},
    )
    assert res.status_code == 400
    assert "terminal status" in res.json()["detail"]
