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
from core.security import create_access_token
from services.welfare_case_service import (
    WelfareCaseService,
    VALID_STATUS_TRANSITIONS,
)

TEST_DB_URL = "sqlite:///./test_phase43.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def uid():
    return uuid.uuid4().hex[:6]


def make_personnel(code=None, battalion="1st Battalion", location="Srinagar"):
    c = code or f"PF-43-{uid()}"
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


def make_user(role="officer", battalion="1st Battalion", location="Srinagar", personnel_id=None):
    u_name = f"user_{role}_{uid()}"
    return User(
        username=u_name,
        hashed_password="fakehashedpassword",
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
    if os.path.exists("./test_phase43.db"):
        try:
            os.remove("./test_phase43.db")
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
# 1. CASE CREATION & VALIDATION TESTS
# =============================================================================
class TestCaseCreation:
    def test_create_valid_case_by_officer(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        officer = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(officer)
        db_session.commit()

        from schemas.welfare_case import WelfareCaseCreateRequest
        payload = WelfareCaseCreateRequest(
            personnel_id=p.id,
            case_type="CURRENT_RISK_REVIEW",
            title="Operational Review for High Stress Alert",
            summary="Review triggered following elevated stress telemetry.",
            trigger_source="PHASE_34_RISK",
        )

        case = WelfareCaseService.create_case(payload, officer, db_session)
        assert case.id is not None
        assert case.personnel_id == p.id
        assert case.status == "OPEN"
        assert case.case_reference.startswith("WC-")
        assert case.opened_by == officer.id

        # Verify audit record created
        audits = db_session.query(WelfareCaseAudit).filter(WelfareCaseAudit.case_id == case.id).all()
        assert len(audits) == 1
        assert audits[0].action == "CASE_CREATED"
        assert audits[0].actor_id == officer.id
        assert audits[0].new_status == "OPEN"

    def test_jawan_cannot_create_case(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        jawan = make_user(role="personnel", personnel_id=p.id)
        db_session.add(jawan)
        db_session.commit()

        from schemas.welfare_case import WelfareCaseCreateRequest
        payload = WelfareCaseCreateRequest(
            personnel_id=p.id,
            case_type="CURRENT_RISK_REVIEW",
        )
        with pytest.raises(PermissionError, match="Jawans are not authorized to create welfare cases"):
            WelfareCaseService.create_case(payload, jawan, db_session)

    def test_create_case_invalid_personnel(self, db_session):
        admin = make_user(role="admin")
        db_session.add(admin)
        db_session.commit()

        from schemas.welfare_case import WelfareCaseCreateRequest
        payload = WelfareCaseCreateRequest(
            personnel_id=999999,
            case_type="CURRENT_RISK_REVIEW",
        )
        with pytest.raises(LookupError, match="does not exist"):
            WelfareCaseService.create_case(payload, admin, db_session)

    def test_create_case_invalid_case_type(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        admin = make_user(role="admin")
        db_session.add(admin)
        db_session.commit()

        from schemas.welfare_case import WelfareCaseCreateRequest
        payload = WelfareCaseCreateRequest(
            personnel_id=p.id,
            case_type="NON_EXISTENT_TYPE",
        )
        with pytest.raises(ValueError, match="Invalid case_type"):
            WelfareCaseService.create_case(payload, admin, db_session)


# =============================================================================
# 2. CONTROLLED STATE MACHINE TESTS
# =============================================================================
class TestControlledStateMachine:
    def test_valid_lifecycle_transitions(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        officer = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(officer)
        db_session.commit()

        from schemas.welfare_case import (
            WelfareCaseCreateRequest,
            WelfareCaseStatusUpdateRequest,
            WelfareCaseCloseRequest,
            WelfareCaseReopenRequest,
        )

        # 1. Create -> OPEN
        case = WelfareCaseService.create_case(
            WelfareCaseCreateRequest(personnel_id=p.id, case_type="ACTIVE_ALERT"),
            officer,
            db_session,
        )
        assert case.status == "OPEN"

        # 2. OPEN -> UNDER_REVIEW
        case = WelfareCaseService.update_status(
            case.id,
            WelfareCaseStatusUpdateRequest(status="UNDER_REVIEW", reason="Initiated formal interview"),
            officer,
            db_session,
        )
        assert case.status == "UNDER_REVIEW"

        # 3. UNDER_REVIEW -> SUPPORT_IN_PROGRESS
        case = WelfareCaseService.update_status(
            case.id,
            WelfareCaseStatusUpdateRequest(status="SUPPORT_IN_PROGRESS", reason="Support intervention started"),
            officer,
            db_session,
        )
        assert case.status == "SUPPORT_IN_PROGRESS"

        # 4. SUPPORT_IN_PROGRESS -> AWAITING_FOLLOW_UP
        case = WelfareCaseService.update_status(
            case.id,
            WelfareCaseStatusUpdateRequest(status="AWAITING_FOLLOW_UP", reason="Session completed, awaiting follow-up"),
            officer,
            db_session,
        )
        assert case.status == "AWAITING_FOLLOW_UP"

        # 5. AWAITING_FOLLOW_UP -> MONITORING
        case = WelfareCaseService.update_status(
            case.id,
            WelfareCaseStatusUpdateRequest(status="MONITORING", reason="Check-in favorable; continuing monitoring"),
            officer,
            db_session,
        )
        assert case.status == "MONITORING"

        # 6. MONITORING -> RESOLVED
        case = WelfareCaseService.update_status(
            case.id,
            WelfareCaseStatusUpdateRequest(status="RESOLVED", reason="Welfare indicators stabilized"),
            officer,
            db_session,
        )
        assert case.status == "RESOLVED"

        # 7. RESOLVED -> CLOSED
        case = WelfareCaseService.close_case(
            case.id,
            WelfareCaseCloseRequest(closure_reason="RESOLVED", closure_notes="Personnel recovered; regular monitoring resumed"),
            officer,
            db_session,
        )
        assert case.status == "CLOSED"
        assert case.closed_by == officer.id
        assert case.closure_reason == "RESOLVED"

        # 8. Reopen: CLOSED -> OPEN
        case = WelfareCaseService.reopen_case(
            case.id,
            WelfareCaseReopenRequest(reopen_reason="Recurrence of operational fatigue reported by company commander"),
            officer,
            db_session,
        )
        assert case.status == "OPEN"
        assert case.reopened_by == officer.id
        assert case.reopen_reason is not None

    def test_invalid_transitions_rejected(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        admin = make_user(role="admin")
        db_session.add(admin)
        db_session.commit()

        from schemas.welfare_case import WelfareCaseCreateRequest, WelfareCaseStatusUpdateRequest

        case = WelfareCaseService.create_case(
            WelfareCaseCreateRequest(personnel_id=p.id, case_type="WORSENING_TREND"),
            admin,
            db_session,
        )
        assert case.status == "OPEN"

        # Direct leap OPEN -> RESOLVED is forbidden
        with pytest.raises(ValueError, match="not permitted"):
            WelfareCaseService.update_status(
                case.id,
                WelfareCaseStatusUpdateRequest(status="RESOLVED"),
                admin,
                db_session,
            )

    def test_terminal_closed_protection(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        admin = make_user(role="admin")
        db_session.add(admin)
        db_session.commit()

        from schemas.welfare_case import (
            WelfareCaseCreateRequest,
            WelfareCaseCloseRequest,
            WelfareCaseStatusUpdateRequest,
        )

        case = WelfareCaseService.create_case(
            WelfareCaseCreateRequest(personnel_id=p.id, case_type="ACTIVE_ALERT"),
            admin,
            db_session,
        )
        WelfareCaseService.close_case(
            case.id,
            WelfareCaseCloseRequest(closure_reason="DUPLICATE"),
            admin,
            db_session,
        )

        # Attempt to transition closed case to UNDER_REVIEW directly without reopen
        with pytest.raises(ValueError, match="Case is CLOSED"):
            WelfareCaseService.update_status(
                case.id,
                WelfareCaseStatusUpdateRequest(status="UNDER_REVIEW"),
                admin,
                db_session,
            )


# =============================================================================
# 3. HUMAN REVIEW & DECISION RECORDING TESTS
# =============================================================================
class TestHumanReview:
    def test_record_review_and_decision(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        officer = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(officer)
        db_session.commit()

        from schemas.welfare_case import WelfareCaseCreateRequest, WelfareCaseReviewRequest

        case = WelfareCaseService.create_case(
            WelfareCaseCreateRequest(personnel_id=p.id, case_type="CURRENT_RISK_REVIEW"),
            officer,
            db_session,
        )

        rev_payload = WelfareCaseReviewRequest(
            review_type="INITIAL_TRIAGE",
            observations="Discussed operational schedule with unit subedar. Jawan reports fatigue from night shifts.",
            decision="REVIEW_DUTY_SUPPORT",
            next_step="Coordinate with company commander for rotation out of consecutive night duties.",
            review_window="Within 7 days",
            notes="Recommendation accepted in principle; human review confirmed duty adjustment needed.",
            new_status="UNDER_REVIEW",
        )

        review = WelfareCaseService.record_review(case.id, rev_payload, officer, db_session)
        assert review.id is not None
        assert review.reviewer_id == officer.id
        assert review.decision == "REVIEW_DUTY_SUPPORT"
        assert review.review_type == "INITIAL_TRIAGE"

        # Case updated
        db_session.refresh(case)
        assert case.status == "UNDER_REVIEW"
        assert case.last_reviewed_by == officer.id
        assert case.last_reviewed_at is not None

        # Audits contain both STATUS_CHANGED and CASE_REVIEWED
        audits = db_session.query(WelfareCaseAudit).filter(WelfareCaseAudit.case_id == case.id).all()
        actions = [a.action for a in audits]
        assert "CASE_REVIEWED" in actions
        assert "STATUS_CHANGED" in actions

    def test_invalid_decision_rejected(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        admin = make_user(role="admin")
        db_session.add(admin)
        db_session.commit()

        from schemas.welfare_case import WelfareCaseCreateRequest, WelfareCaseReviewRequest

        case = WelfareCaseService.create_case(
            WelfareCaseCreateRequest(personnel_id=p.id, case_type="CURRENT_RISK_REVIEW"),
            admin,
            db_session,
        )

        with pytest.raises(ValueError, match="Invalid decision"):
            WelfareCaseService.record_review(
                case.id,
                WelfareCaseReviewRequest(
                    observations="Invalid test decision",
                    decision="DISCIPLINARY_PUNISHMENT",  # Explicitly forbidden
                ),
                admin,
                db_session,
            )


# =============================================================================
# 4. IMMUTABLE CASE NOTES TESTS
# =============================================================================
class TestImmutableCaseNotes:
    def test_add_case_notes_history(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        officer = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(officer)
        db_session.commit()

        from schemas.welfare_case import WelfareCaseCreateRequest, WelfareCaseNoteCreateRequest

        case = WelfareCaseService.create_case(
            WelfareCaseCreateRequest(personnel_id=p.id, case_type="SUPPORT_FOLLOW_UP"),
            officer,
            db_session,
        )

        note1 = WelfareCaseService.add_note(
            case.id,
            WelfareCaseNoteCreateRequest(note_type="REVIEW_NOTE", content="First observation note."),
            officer,
            db_session,
        )
        note2 = WelfareCaseService.add_note(
            case.id,
            WelfareCaseNoteCreateRequest(note_type="SUPPORT_NOTE", content="Second support note."),
            officer,
            db_session,
        )

        assert note1.id is not None
        assert note2.id is not None
        assert note1.id != note2.id

        # Verify notes are preserved chronologically
        notes = db_session.query(WelfareCaseNote).filter(WelfareCaseNote.case_id == case.id).order_by(WelfareCaseNote.created_at.asc()).all()
        assert len(notes) == 2
        assert notes[0].content == "First observation note."
        assert notes[1].content == "Second support note."


# =============================================================================
# 5. MULTI-PHASE INTEGRATION & EVIDENCE CONSOLIDATION
# =============================================================================
class TestMultiPhaseIntegration:
    def test_case_evidence_links_existing_phases_without_new_score(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        now = datetime.now(timezone.utc)

        # 1. Phase 34 Risk Assessment
        ass = StressAssessment(
            personnel_id=p.id,
            assessment_timestamp=now - timedelta(days=2),
            risk_score=68.5,
            stress_level="Medium",
            risk_priority="Preventive",
            low_probability=0.15,
            medium_probability=0.70,
            high_probability=0.15,
            key_factors=json.dumps(["duty_hours", "night_shifts"]),
        )
        db_session.add(ass)

        # 2. Phase 37 Alert
        alert = WelfareAlert(
            personnel_id=p.id,
            alert_type="TREND_WORSENING",
            severity="HIGH",
            status="OPEN",
            trigger_reason="Consistent elevation in reported stress scores",
            created_at=now - timedelta(days=1),
        )
        db_session.add(alert)

        # 3. Phase 39 Anomaly
        anom = WelfareAnomaly(
            personnel_id=p.id,
            anomaly_type="WORKLOAD_ANOMALY",
            severity="ATTENTION",
            status="DETECTED",
            confidence="HIGH",
            evidence_json=json.dumps({"explanation": "Sudden surge in resting pulse telemetry"}),
            dedup_hash=f"hash-{uid()}",
            detected_at=now - timedelta(hours=12),
        )
        db_session.add(anom)

        # 4. Phase 40 Recommendation
        rec = WelfareRecommendation(
            personnel_id=p.id,
            recommendation_type="PEER_SUPPORT",
            recommendation_text="Assign peer support buddy for informal check-in",
            title="Peer Buddy Check-in",
            priority="MEDIUM",
            status="SUGGESTED",
            description="Assign peer support buddy for informal check-in",
            evidence_json=json.dumps({"risk_score": 68.5}),
            created_at=now - timedelta(hours=6),
        )
        db_session.add(rec)
        db_session.commit()

        admin = make_user(role="admin")
        db_session.add(admin)
        db_session.commit()

        from schemas.welfare_case import WelfareCaseCreateRequest
        case = WelfareCaseService.create_case(
            WelfareCaseCreateRequest(
                personnel_id=p.id,
                case_type="ACTIVE_ALERT",
                assessment_id=ass.id,
                alert_id=alert.id,
                anomaly_id=anom.id,
                recommendation_id=rec.id,
            ),
            admin,
            db_session,
        )

        detail = WelfareCaseService.get_case_detail(case.id, admin, db_session)
        assert detail.evidence is not None
        assert detail.evidence.current_risk.get("risk_score") == 68.5
        assert detail.evidence.current_risk.get("stress_level") == "Medium"
        assert detail.evidence.active_alert is not None
        assert detail.evidence.active_anomaly is not None
        assert detail.evidence.open_recommendation is not None

        # Verify NO new composite score exists
        assert not hasattr(detail, "case_score")
        assert not hasattr(detail, "case_priority_score")
        assert not hasattr(detail, "case_severity_score")


# =============================================================================
# 6. SECURITY, RBAC & ANTI-IDOR TESTS
# =============================================================================
class TestSecurityAndAntiIDOR:
    def test_jawan_can_view_own_case_only(self, db_session):
        p1 = make_personnel(code="PF-43-JAWAN1")
        p2 = make_personnel(code="PF-43-JAWAN2")
        db_session.add_all([p1, p2])
        db_session.commit()

        jawan1 = make_user(role="personnel", personnel_id=p1.id)
        jawan2 = make_user(role="personnel", personnel_id=p2.id)
        admin = make_user(role="admin")
        db_session.add_all([jawan1, jawan2, admin])
        db_session.commit()

        from schemas.welfare_case import WelfareCaseCreateRequest

        # Admin creates case for Jawan 1 and case for Jawan 2
        case1 = WelfareCaseService.create_case(
            WelfareCaseCreateRequest(personnel_id=p1.id, case_type="CURRENT_RISK_REVIEW"),
            admin,
            db_session,
        )
        case2 = WelfareCaseService.create_case(
            WelfareCaseCreateRequest(personnel_id=p2.id, case_type="CURRENT_RISK_REVIEW"),
            admin,
            db_session,
        )

        # Jawan 1 can view own case
        detail1 = WelfareCaseService.get_case_detail(case1.id, jawan1, db_session)
        assert detail1.id == case1.id

        # Jawan 1 attempting to view Jawan 2 case is rejected (Anti-IDOR)
        with pytest.raises(PermissionError, match="Access denied"):
            WelfareCaseService.get_case_detail(case2.id, jawan1, db_session)

    def test_officer_battalion_scope_isolation(self, db_session):
        p_bat1 = make_personnel(battalion="1st Battalion", location="Srinagar")
        p_bat2 = make_personnel(battalion="2nd Battalion", location="Jammu")
        db_session.add_all([p_bat1, p_bat2])
        db_session.commit()

        officer_bat1 = make_user(role="officer", battalion="1st Battalion", location="Srinagar")
        admin = make_user(role="admin")
        db_session.add_all([officer_bat1, admin])
        db_session.commit()

        from schemas.welfare_case import WelfareCaseCreateRequest

        case2 = WelfareCaseService.create_case(
            WelfareCaseCreateRequest(personnel_id=p_bat2.id, case_type="CURRENT_RISK_REVIEW"),
            admin,
            db_session,
        )

        # Officer of 1st Battalion cannot access case of 2nd Battalion
        with pytest.raises(PermissionError, match="outside your assigned Battalion scope"):
            WelfareCaseService.get_case_detail(case2.id, officer_bat1, db_session)


# =============================================================================
# 7. SMALL-GROUP PRIVACY (k >= 5) TESTS
# =============================================================================
class TestSmallGroupPrivacy:
    def test_summary_stats_suppression_when_under_5(self, db_session):
        p = make_personnel(battalion="Isolated Post Battalion")
        db_session.add(p)
        db_session.commit()

        admin = make_user(role="admin")
        db_session.add(admin)
        db_session.commit()

        from schemas.welfare_case import WelfareCaseCreateRequest

        # Create only 2 cases in this battalion
        WelfareCaseService.create_case(
            WelfareCaseCreateRequest(personnel_id=p.id, case_type="CURRENT_RISK_REVIEW"),
            admin,
            db_session,
        )
        WelfareCaseService.create_case(
            WelfareCaseCreateRequest(personnel_id=p.id, case_type="WORSENING_TREND"),
            admin,
            db_session,
        )

        stats = WelfareCaseService.get_case_summary_stats(
            db=db_session,
            current_user=admin,
            battalion="Isolated Post Battalion",
        )
        assert stats.total_cases == 2
        assert stats.data_suppressed is True
        assert stats.open_cases == 0
        assert "privacy threshold" in stats.suppression_reason.lower()


# =============================================================================
# 8. API ENDPOINT INTEGRATION TESTS (FASTAPI)
# =============================================================================
class TestAPIEndpoints:
    def test_api_unauthenticated_rejected(self, client):
        r = client.get("/api/welfare-cases")
        assert r.status_code == 401

    def test_api_full_case_workflow(self, client, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        officer = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(officer)
        db_session.commit()

        token = create_access_token(data={"sub": officer.username, "role": officer.role})
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Open Case
        res_open = client.post(
            "/api/welfare-cases",
            json={
                "personnel_id": p.id,
                "case_type": "CURRENT_RISK_REVIEW",
                "title": "API Operational Case",
                "summary": "Opened via API test",
            },
            headers=headers,
        )
        assert res_open.status_code == 201
        case_data = res_open.json()
        case_id = case_data["id"]
        assert case_data["status"] == "OPEN"

        # 2. Add Note
        res_note = client.post(
            f"/api/welfare-cases/{case_id}/notes",
            json={"note_type": "REVIEW_NOTE", "content": "Initial API case note."},
            headers=headers,
        )
        assert res_note.status_code == 201

        # 3. Record Review
        res_rev = client.post(
            f"/api/welfare-cases/{case_id}/review",
            json={
                "review_type": "INITIAL_TRIAGE",
                "observations": "Reviewer confirmed stress indicators via API.",
                "decision": "CONTINUE_MONITORING",
                "next_step": "Review next check-in.",
                "new_status": "MONITORING",
            },
            headers=headers,
        )
        assert res_rev.status_code == 201
        assert res_rev.json()["decision"] == "CONTINUE_MONITORING"

        # 4. Get Timeline
        res_time = client.get(f"/api/welfare-cases/{case_id}/timeline", headers=headers)
        assert res_time.status_code == 200
        events = res_time.json()["events"]
        assert len(events) >= 2
        # Check explicit labeling of HUMAN_ACTION
        action_events = [e for e in events if e["event_type"] == "HUMAN_ACTION"]
        assert len(action_events) >= 2

        # 5. Close Case
        res_close = client.post(
            f"/api/welfare-cases/{case_id}/close",
            json={"closure_reason": "MONITORING_COMPLETED", "closure_notes": "All checks passed."},
            headers=headers,
        )
        assert res_close.status_code == 200
        assert res_close.json()["status"] == "CLOSED"

        # 6. Reopen Case
        res_reopen = client.post(
            f"/api/welfare-cases/{case_id}/reopen",
            json={"reopen_reason": "Follow-up check required after new patrol."},
            headers=headers,
        )
        assert res_reopen.status_code == 200
        assert res_reopen.json()["status"] == "OPEN"

        # 7. Audits
        res_aud = client.get(f"/api/welfare-cases/{case_id}/audits", headers=headers)
        assert res_aud.status_code == 200
        audits = res_aud.json()["audits"]
        actions = [a["action"] for a in audits]
        assert "CASE_CREATED" in actions
        assert "CASE_CLOSED" in actions
        assert "CASE_REOPENED" in actions
