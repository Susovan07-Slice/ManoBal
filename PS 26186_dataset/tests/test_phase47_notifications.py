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
from db.models.welfare_notification import WelfareNotification, WelfareNotificationAudit
from db.models.recommendation import WelfareRecommendation
from db.models.welfare_followup import WelfareFollowup
from core.security import hash_password, create_access_token

TEST_DB_URL = "sqlite:///./test_phase47.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def uid():
    return uuid.uuid4().hex[:6]


def make_personnel(code=None, battalion="7th Battalion", location="Srinagar"):
    c = code or f"PF-47-{uid()}"
    return Personnel(
        personnel_code=c,
        name=f"Jawan {c}",
        age=26,
        gender="Male",
        department="Infantry",
        battalion=battalion,
        location=location,
        job_role="Rifleman",
        experience_years=4.0,
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


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_phase47.db"):
        try:
            os.remove("./test_phase47.db")
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


# -----------------------------------------------------------------------------
# 1. NOTIFICATION CREATION & DELIVERY TESTS
# -----------------------------------------------------------------------------
def test_commander_can_send_welfare_notification(client, db_session):
    p = make_personnel(battalion="7th Battalion", location="Srinagar")
    db_session.add(p)
    db_session.commit()

    officer = make_user(role="officer", battalion="7th Battalion", location="Srinagar")
    db_session.add(officer)
    db_session.commit()

    officer_token = get_token(officer.username, "officer", battalion="7th Battalion", location="Srinagar")
    res = client.post(
        "/api/notifications/send",
        headers={"Authorization": f"Bearer {officer_token}"},
        json={
            "recipient_personnel_id": p.id,
            "notification_type": "WELFARE_SUPPORT",
            "title": "Supportive Check-in",
            "message": "Routine check-in scheduled for unit readiness.",
            "priority": "STANDARD",
            "action_url": "/check-in",
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["recipient_personnel_id"] == p.id
    assert data["title"] == "Supportive Check-in"
    assert data["status"] == "UNREAD"
    assert data["creator_username"] == officer.username


def test_jawan_can_view_own_notifications(client, db_session):
    p = make_personnel(battalion="7th Battalion", location="Srinagar")
    db_session.add(p)
    db_session.commit()

    jawan_user = make_user(role="personnel", battalion="7th Battalion", location="Srinagar", personnel_id=p.id)
    db_session.add(jawan_user)
    db_session.commit()

    notif = WelfareNotification(
        recipient_personnel_id=p.id,
        notification_type="WELFARE_SUPPORT",
        title="Welcome Notice",
        message="Welcome to unit welfare support.",
        status="UNREAD",
    )
    db_session.add(notif)
    db_session.commit()

    jawan_token = get_token(jawan_user.username, "personnel", personnel_id=p.id, battalion="7th Battalion", location="Srinagar")
    res = client.get("/api/notifications", headers={"Authorization": f"Bearer {jawan_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["unread_count"] == 1
    assert data["notifications"][0]["recipient_personnel_id"] == p.id


def test_jawan_can_get_unread_count(client, db_session):
    p = make_personnel()
    db_session.add(p)
    db_session.commit()

    jawan_user = make_user(role="personnel", personnel_id=p.id)
    db_session.add(jawan_user)
    db_session.commit()

    notif = WelfareNotification(
        recipient_personnel_id=p.id,
        notification_type="FOLLOW_UP_REQUEST",
        title="Checkin Required",
        message="Please check in.",
        status="UNREAD",
    )
    db_session.add(notif)
    db_session.commit()

    jawan_token = get_token(jawan_user.username, "personnel", personnel_id=p.id)
    res = client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {jawan_token}"})
    assert res.status_code == 200
    assert res.json()["unread_count"] == 1


def test_jawan_can_mark_notification_as_read(client, db_session):
    p = make_personnel()
    db_session.add(p)
    db_session.commit()

    jawan_user = make_user(role="personnel", personnel_id=p.id)
    db_session.add(jawan_user)
    db_session.commit()

    notif = WelfareNotification(
        recipient_personnel_id=p.id,
        notification_type="WELFARE_SUPPORT",
        title="Notice",
        message="Notice content",
        status="UNREAD",
    )
    db_session.add(notif)
    db_session.commit()

    jawan_token = get_token(jawan_user.username, "personnel", personnel_id=p.id)
    read_res = client.post(f"/api/notifications/{notif.id}/read", headers={"Authorization": f"Bearer {jawan_token}"})
    assert read_res.status_code == 200
    assert read_res.json()["status"] == "READ"
    assert read_res.json()["read_at"] is not None

    count_res = client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {jawan_token}"})
    assert count_res.json()["unread_count"] == 0


def test_jawan_mark_all_as_read(client, db_session):
    p = make_personnel()
    db_session.add(p)
    db_session.commit()

    jawan_user = make_user(role="personnel", personnel_id=p.id)
    db_session.add(jawan_user)
    db_session.commit()

    for i in range(3):
        notif = WelfareNotification(
            recipient_personnel_id=p.id,
            notification_type="SUPPORT_RECOMMENDATION",
            title=f"Guidance #{i+1}",
            message="Support guidelines updated.",
            status="UNREAD",
        )
        db_session.add(notif)
    db_session.commit()

    jawan_token = get_token(jawan_user.username, "personnel", personnel_id=p.id)
    count_before = client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {jawan_token}"}).json()["unread_count"]
    assert count_before == 3

    all_res = client.post("/api/notifications/read-all", headers={"Authorization": f"Bearer {jawan_token}"})
    assert all_res.status_code == 200
    assert all_res.json()["unread_count"] == 0

    count_after = client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {jawan_token}"}).json()["unread_count"]
    assert count_after == 0


# -----------------------------------------------------------------------------
# 2. ANTI-IDOR & SECURITY TESTS
# -----------------------------------------------------------------------------
def test_jawan_cannot_access_another_jawans_notification(client, db_session):
    p1 = make_personnel(battalion="7th Battalion", location="Srinagar")
    p2 = make_personnel(battalion="7th Battalion", location="Srinagar")
    db_session.add_all([p1, p2])
    db_session.commit()

    j1 = make_user(role="personnel", personnel_id=p1.id)
    j2 = make_user(role="personnel", personnel_id=p2.id)
    db_session.add_all([j1, j2])
    db_session.commit()

    # Create private notification for Jawan 2
    notif2 = WelfareNotification(
        recipient_personnel_id=p2.id,
        notification_type="WELFARE_SUPPORT",
        title="Private for Jawan 2",
        message="Confidential guidance.",
        status="UNREAD",
    )
    db_session.add(notif2)
    db_session.commit()

    jawan1_token = get_token(j1.username, "personnel", personnel_id=p1.id)

    # 1. Jawan 1 attempts to GET Jawan 2 notification by ID -> MUST return 403
    get_res = client.get(f"/api/notifications/{notif2.id}", headers={"Authorization": f"Bearer {jawan1_token}"})
    assert get_res.status_code == 403
    assert "Access denied" in get_res.json()["detail"]

    # 2. Jawan 1 attempts to mark Jawan 2 notification read -> MUST return 403
    read_res = client.post(f"/api/notifications/{notif2.id}/read", headers={"Authorization": f"Bearer {jawan1_token}"})
    assert read_res.status_code == 403

    # 3. Jawan 1 attempts to query notifications of Personnel 2 via query param -> MUST return 403
    list_res = client.get(f"/api/notifications?personnel_id={p2.id}", headers={"Authorization": f"Bearer {jawan1_token}"})
    assert list_res.status_code == 403


def test_commander_cannot_send_notification_out_of_scope(client, db_session):
    p_other = make_personnel(battalion="9th Battalion", location="Jammu")
    db_session.add(p_other)
    db_session.commit()

    officer = make_user(role="officer", battalion="7th Battalion", location="Srinagar")
    db_session.add(officer)
    db_session.commit()

    officer_token = get_token(officer.username, "officer", battalion="7th Battalion", location="Srinagar")
    res = client.post(
        "/api/notifications/send",
        headers={"Authorization": f"Bearer {officer_token}"},
        json={
            "recipient_personnel_id": p_other.id,
            "notification_type": "WELFARE_SUPPORT",
            "title": "Out of scope communication",
            "message": "This should be denied by scope enforcement.",
        }
    )
    assert res.status_code == 403
    assert "outside your assigned Battalion" in res.json()["detail"]


# -----------------------------------------------------------------------------
# 3. CONTENT PRIVACY & SENSITIVE ML SANITIZATION TESTS
# -----------------------------------------------------------------------------
def test_sensitive_ml_jargon_is_sanitized_from_jawan_notifications(client, db_session):
    p = make_personnel(battalion="7th Battalion", location="Srinagar")
    db_session.add(p)
    db_session.commit()

    officer = make_user(role="officer", battalion="7th Battalion", location="Srinagar")
    db_session.add(officer)
    db_session.commit()

    officer_token = get_token(officer.username, "officer", battalion="7th Battalion", location="Srinagar")
    res = client.post(
        "/api/notifications/send",
        headers={"Authorization": f"Bearer {officer_token}"},
        json={
            "recipient_personnel_id": p.id,
            "notification_type": "WELFARE_SUPPORT",
            "title": "Anomaly score 2.8σ detected",
            "message": "Your Isolation Forest anomaly score is 2.8σ and risk score is 88.5.",
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert "Isolation Forest" not in data["message"]
    assert "2.8σ" not in data["title"]
    assert "2.8σ" not in data["message"]


# -----------------------------------------------------------------------------
# 4. AUTOMATIC WORKFLOW HOOKS TESTS
# -----------------------------------------------------------------------------
def test_automatic_notification_on_recommendation_accepted(client, db_session):
    p = make_personnel(battalion="7th Battalion", location="Srinagar")
    db_session.add(p)
    db_session.commit()

    officer = make_user(role="officer", battalion="7th Battalion", location="Srinagar")
    db_session.add(officer)
    db_session.commit()

    rec = WelfareRecommendation(
        personnel_id=p.id,
        recommendation_type="RECOVERY_REVIEW",
        recommendation_text="Structured rest interval suggested.",
        title="Rest Interval",
        priority="HIGH",
        status="SUGGESTED",
    )
    db_session.add(rec)
    db_session.commit()

    officer_token = get_token(officer.username, "officer", battalion="7th Battalion", location="Srinagar")
    accept_res = client.post(
        f"/api/recommendations/{rec.id}/accept",
        headers={"Authorization": f"Bearer {officer_token}"},
        json={"create_intervention": False}
    )
    assert accept_res.status_code == 200

    jawan_user = make_user(role="personnel", personnel_id=p.id)
    db_session.add(jawan_user)
    db_session.commit()

    jawan_token = get_token(jawan_user.username, "personnel", personnel_id=p.id)
    notifs = client.get("/api/notifications", headers={"Authorization": f"Bearer {jawan_token}"}).json()["notifications"]
    rec_notifs = [n for n in notifs if n["source_type"] == "RECOMMENDATION" and n["source_id"] == rec.id]
    assert len(rec_notifs) >= 1
    assert "Rest Interval" in rec_notifs[0]["message"]
    assert rec_notifs[0]["action_url"] == "/trends"


def test_automatic_notification_on_followup_scheduled(client, db_session):
    p = make_personnel(battalion="7th Battalion", location="Srinagar")
    db_session.add(p)
    db_session.commit()

    officer = make_user(role="officer", battalion="7th Battalion", location="Srinagar")
    db_session.add(officer)
    db_session.commit()

    followup = WelfareFollowup(
        personnel_id=p.id,
        followup_type="WELFARE_CHECKIN",
        status="PENDING",
    )
    db_session.add(followup)
    db_session.commit()

    officer_token = get_token(officer.username, "officer", battalion="7th Battalion", location="Srinagar")
    sched_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    sched_res = client.post(
        f"/api/followups/{followup.id}/schedule",
        headers={"Authorization": f"Bearer {officer_token}"},
        json={"scheduled_at": sched_date, "notes": "Checkin planned"}
    )
    assert sched_res.status_code == 200

    jawan_user = make_user(role="personnel", personnel_id=p.id)
    db_session.add(jawan_user)
    db_session.commit()

    jawan_token = get_token(jawan_user.username, "personnel", personnel_id=p.id)
    notifs = client.get("/api/notifications", headers={"Authorization": f"Bearer {jawan_token}"}).json()["notifications"]
    f_notifs = [n for n in notifs if n["source_type"] == "FOLLOWUP" and n["source_id"] == followup.id]
    assert len(f_notifs) >= 1
    assert "Welfare Follow-up Scheduled" in f_notifs[0]["title"]
    assert f_notifs[0]["action_url"] == "/check-in"


def test_audit_logs_exist_for_notification_events(client, db_session):
    p = make_personnel(battalion="7th Battalion", location="Srinagar")
    db_session.add(p)
    db_session.commit()

    officer = make_user(role="officer", battalion="7th Battalion", location="Srinagar")
    db_session.add(officer)
    db_session.commit()

    officer_token = get_token(officer.username, "officer", battalion="7th Battalion", location="Srinagar")
    send_res = client.post(
        "/api/notifications/send",
        headers={"Authorization": f"Bearer {officer_token}"},
        json={
            "recipient_personnel_id": p.id,
            "notification_type": "WELFARE_SUPPORT",
            "title": "Audited Notification",
            "message": "Audit trail testing.",
        }
    )
    assert send_res.status_code == 201
    notif_id = send_res.json()["id"]

    jawan_user = make_user(role="personnel", personnel_id=p.id)
    db_session.add(jawan_user)
    db_session.commit()

    jawan_token = get_token(jawan_user.username, "personnel", personnel_id=p.id)
    client.post(f"/api/notifications/{notif_id}/read", headers={"Authorization": f"Bearer {jawan_token}"})

    audits = db_session.query(WelfareNotificationAudit).filter(WelfareNotificationAudit.notification_id == notif_id).all()
    actions = [a.action for a in audits]
    assert "NOTIFICATION_CREATED" in actions
    assert "NOTIFICATION_READ" in actions
