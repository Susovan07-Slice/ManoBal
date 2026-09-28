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
from db.models.recommendation import WelfareRecommendation
from db.models.welfare_followup import WelfareFollowup, WelfareFollowupAudit
from core.security import create_access_token
from services.welfare_outcome_service import WelfareOutcomeService, ANALYTICS_MIN_GROUP_SIZE

TEST_DB_URL = "sqlite:///./test_phase41.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def uid():
    return uuid.uuid4().hex[:6]

def make_personnel(code=None, battalion="1st Battalion", location="Srinagar", duty_hours=45.0, consecutive_days=5):
    c = code or f"PF-41-{uid()}"
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
        duty_hours_per_week=duty_hours,
        night_shifts_per_month=4,
        consecutive_duty_days=consecutive_days,
        leave_gap_days=25,
        operational_exposure="Medium"
    )

def make_assessment(personnel_id, score, stress_level="Low", priority="Routine", days_ago=0):
    ts = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return StressAssessment(
        personnel_id=personnel_id,
        stress_level=stress_level,
        low_probability=0.7 if score < 35 else 0.1,
        medium_probability=0.2 if 35 <= score < 70 else 0.1,
        high_probability=0.8 if score >= 70 else 0.1,
        risk_score=score,
        risk_priority=priority,
        key_factors=json.dumps({"risk_category": stress_level}),
        assessment_timestamp=ts
    )

def make_user(username=None, role="officer", battalion="1st Battalion", location="Srinagar", personnel_id=None):
    u = username or f"usr_{uid()}"
    return User(
        username=u,
        hashed_password="pwd",
        role=role,
        battalion=battalion,
        location=location,
        personnel_id=personnel_id,
        is_active=True
    )

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_phase41.db"):
        try:
            os.remove("./test_phase41.db")
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


# =============================================================================
# 1. FOLLOW-UP CREATION TESTS
# =============================================================================
class TestFollowupCreation:
    def test_create_recommendation_linked_followup(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        ass = make_assessment(p.id, score=78.5, stress_level="High", days_ago=2)
        db_session.add(ass)
        db_session.commit()

        rec = WelfareRecommendation(
            personnel_id=p.id,
            assessment_id=ass.id,
            recommendation_type="WELFARE_FOLLOW_UP",
            recommendation_text="Consider a welfare follow-up check-in.",
            title="Supportive Welfare Follow-Up",
            priority="HIGH",
            status="SUGGESTED",
            confidence="HIGH",
            recommended_review_window="Within 7 days",
            created_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db_session.add(rec)
        db_session.commit()

        followup = WelfareOutcomeService.create_followup(
            db=db_session,
            user=u,
            personnel_id=p.id,
            followup_type="WELFARE_CHECKIN",
            recommendation_id=rec.id,
            review_window="Within 7 days",
            notes="Initial review scheduled per Phase 40 suggestion.",
        )

        assert followup.id is not None
        assert followup.personnel_id == p.id
        assert followup.recommendation_id == rec.id
        assert followup.status == "PENDING"
        assert followup.outcome_status == "INSUFFICIENT_DATA"
        assert followup.baseline_assessment_id == ass.id
        assert followup.baseline_source == "PRE_RECOMMENDATION_ASSESSMENT"
        assert followup.due_date is not None
        assert followup.review_window == "Within 7 days"

    def test_create_intervention_linked_followup(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        alert = WelfareAlert(
            personnel_id=p.id,
            alert_type="HIGH_CURRENT_RISK",
            severity="HIGH_PRIORITY",
            status="INTERVENTION_PLANNED",
            created_at=datetime.now(timezone.utc) - timedelta(days=3),
        )
        db_session.add(alert)
        db_session.flush()

        interv = WelfareIntervention(
            alert_id=alert.id,
            personnel_id=p.id,
            intervention_type="COUNSELING_SESSION",
            status="COMPLETED",
            created_by=u.id,
            created_at=datetime.now(timezone.utc) - timedelta(days=2),
            completed_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db_session.add(interv)
        db_session.commit()

        followup = WelfareOutcomeService.create_followup(
            db=db_session,
            user=u,
            personnel_id=p.id,
            followup_type="INTERVENTION_REVIEW",
            intervention_id=interv.id,
            alert_id=alert.id,
            review_window="Within 14 days",
            notes="Post-counseling review.",
        )

        assert followup.id is not None
        assert followup.intervention_id == interv.id
        assert followup.alert_id == alert.id
        assert followup.followup_type == "INTERVENTION_REVIEW"

    def test_invalid_followup_type_rejected(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        with pytest.raises(ValueError, match="Invalid follow-up type"):
            WelfareOutcomeService.create_followup(
                db=db_session,
                user=u,
                personnel_id=p.id,
                followup_type="NON_EXISTENT_TYPE",
            )

    def test_nonexistent_personnel_rejected(self, db_session):
        u = make_user(role="admin")
        db_session.add(u)
        db_session.commit()

        with pytest.raises(LookupError, match="Personnel #999999 not found"):
            WelfareOutcomeService.create_followup(
                db=db_session,
                user=u,
                personnel_id=999999,
                followup_type="WELFARE_CHECKIN",
            )


# =============================================================================
# 2. LIFECYCLE & STATE MACHINE TESTS
# =============================================================================
class TestLifecycleStateMachine:
    def test_valid_lifecycle_transitions(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        followup = WelfareOutcomeService.create_followup(
            db=db_session,
            user=u,
            personnel_id=p.id,
            followup_type="RECOVERY_REVIEW",
            review_window="Within 7 days",
        )
        assert followup.status == "PENDING"

        # 1. PENDING -> SCHEDULED
        sched_time = datetime.now(timezone.utc) + timedelta(days=2)
        followup = WelfareOutcomeService.schedule_followup(
            db=db_session,
            followup_id=followup.id,
            user=u,
            scheduled_at=sched_time,
            notes="Scheduled with unit welfare officer",
        )
        assert followup.status == "SCHEDULED"
        assert followup.scheduled_at is not None


        # 2. SCHEDULED -> DEFERRED
        followup = WelfareOutcomeService.defer_followup(
            db=db_session,
            followup_id=followup.id,
            user=u,
            defer_days=5,
            notes="Personnel away on operational assignment",
        )
        assert followup.status == "DEFERRED"

        # 3. DEFERRED -> SCHEDULED
        new_sched = datetime.now(timezone.utc) + timedelta(days=4)
        followup = WelfareOutcomeService.schedule_followup(
            db=db_session,
            followup_id=followup.id,
            user=u,
            scheduled_at=new_sched,
        )
        assert followup.status == "SCHEDULED"

        # 4. SCHEDULED -> COMPLETED
        followup = WelfareOutcomeService.complete_followup(
            db=db_session,
            followup_id=followup.id,
            user=u,
            notes="Completed interview and recorded observations.",
        )
        assert followup.status == "COMPLETED"
        assert followup.completed_at is not None
        assert followup.completed_by == u.id

    def test_invalid_lifecycle_transition_from_completed(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        followup = WelfareOutcomeService.create_followup(
            db=db_session,
            user=u,
            personnel_id=p.id,
            followup_type="DUTY_SCHEDULE_REVIEW",
        )
        followup = WelfareOutcomeService.complete_followup(
            db=db_session,
            followup_id=followup.id,
            user=u,
        )
        assert followup.status == "COMPLETED"

        # Transitioning away from COMPLETED must raise ValueError
        with pytest.raises(ValueError, match="Cannot schedule follow-up from current status 'COMPLETED'"):
            WelfareOutcomeService.schedule_followup(
                db=db_session,
                followup_id=followup.id,
                user=u,
                scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            )

    def test_cancellation(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        followup = WelfareOutcomeService.create_followup(
            db=db_session,
            user=u,
            personnel_id=p.id,
            followup_type="SUPPORT_RESOURCE_FOLLOWUP",
        )
        followup = WelfareOutcomeService.cancel_followup(
            db=db_session,
            followup_id=followup.id,
            user=u,
            reason="Personnel transferred to different unit headquarters",
        )
        assert followup.status == "CANCELLED"
        assert "Cancelled:" in followup.notes

    def test_expired_transition_and_rejection(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        followup = WelfareOutcomeService.create_followup(
            db=db_session,
            user=u,
            personnel_id=p.id,
            followup_type="WELFARE_CHECKIN",
        )
        assert followup.status == "PENDING"

        # PENDING -> EXPIRED
        followup = WelfareOutcomeService.expire_followup(
            db=db_session,
            followup_id=followup.id,
            user=u,
            reason="Review window elapsed",
        )
        assert followup.status == "EXPIRED"

        # EXPIRED -> SCHEDULED must fail
        with pytest.raises(ValueError, match="Cannot schedule follow-up from current status 'EXPIRED'"):
            WelfareOutcomeService.schedule_followup(
                db=db_session,
                followup_id=followup.id,
                user=u,
                scheduled_at=datetime.now(timezone.utc) + timedelta(days=2),
            )

    def test_cancelled_cannot_transition_to_completed(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        followup = WelfareOutcomeService.create_followup(
            db=db_session,
            user=u,
            personnel_id=p.id,
            followup_type="WELFARE_CHECKIN",
        )
        followup = WelfareOutcomeService.cancel_followup(
            db=db_session,
            followup_id=followup.id,
            user=u,
            reason="Duplicate request",
        )
        assert followup.status == "CANCELLED"

        # CANCELLED -> COMPLETED must fail
        with pytest.raises(ValueError, match="Cannot complete follow-up from current status 'CANCELLED'"):
            WelfareOutcomeService.complete_followup(
                db=db_session,
                followup_id=followup.id,
                user=u,
            )

    def test_completed_cannot_transition_to_pending(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        followup = WelfareOutcomeService.create_followup(
            db=db_session,
            user=u,
            personnel_id=p.id,
            followup_type="WELFARE_CHECKIN",
        )
        followup = WelfareOutcomeService.complete_followup(
            db=db_session,
            followup_id=followup.id,
            user=u,
        )
        assert followup.status == "COMPLETED"

        # Deferring or rescheduling from COMPLETED must fail
        with pytest.raises(ValueError, match="Cannot defer follow-up from current status 'COMPLETED'"):
            WelfareOutcomeService.defer_followup(
                db=db_session,
                followup_id=followup.id,
                user=u,
                defer_days=7,
            )



# =============================================================================
# 3. TEMPORAL INTEGRITY & BASELINE SELECTION TESTS
# =============================================================================
class TestTemporalIntegrity:
    def test_baseline_selection_strictly_precedes_followup(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        t0 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc)

        ass0 = StressAssessment(
            personnel_id=p.id,
            stress_level="Medium",
            low_probability=0.2,
            medium_probability=0.6,
            high_probability=0.2,
            risk_score=50.0,
            risk_priority="Preventive",
            assessment_timestamp=t0,
        )
        db_session.add(ass0)
        db_session.commit()

        followup = WelfareOutcomeService.create_followup(
            db=db_session,
            user=u,
            personnel_id=p.id,
            followup_type="REASSESSMENT",
        )
        assert followup.baseline_assessment_id == ass0.id

        ass1 = StressAssessment(
            personnel_id=p.id,
            stress_level="Low",
            low_probability=0.8,
            medium_probability=0.15,
            high_probability=0.05,
            risk_score=25.0,
            risk_priority="Routine",
            assessment_timestamp=t1,
        )
        db_session.add(ass1)
        db_session.commit()

        completed = WelfareOutcomeService.complete_followup(
            db=db_session,
            followup_id=followup.id,
            user=u,
            followup_assessment_id=ass1.id,
        )
        assert completed.followup_assessment_id == ass1.id
        assert completed.outcome_status == "IMPROVED"

    def test_reject_out_of_order_followup_assessment(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        t_base = datetime(2026, 9, 10, 10, 0, tzinfo=timezone.utc)
        t_prior = datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc)

        ass_base = StressAssessment(
            personnel_id=p.id,
            stress_level="High",
            low_probability=0.1,
            medium_probability=0.2,
            high_probability=0.7,
            risk_score=75.0,
            risk_priority="Priority",
            assessment_timestamp=t_base,
        )
        ass_prior = StressAssessment(
            personnel_id=p.id,
            stress_level="Medium",
            low_probability=0.2,
            medium_probability=0.6,
            high_probability=0.2,
            risk_score=50.0,
            risk_priority="Preventive",
            assessment_timestamp=t_prior,
        )
        db_session.add_all([ass_base, ass_prior])
        db_session.commit()

        followup = WelfareOutcomeService.create_followup(
            db=db_session,
            user=u,
            personnel_id=p.id,
            followup_type="WELFARE_CHECKIN",
        )
        followup.baseline_assessment_id = ass_base.id
        db_session.commit()

        with pytest.raises(ValueError, match="Temporal integrity violation"):
            WelfareOutcomeService.complete_followup(
                db=db_session,
                followup_id=followup.id,
                user=u,
                followup_assessment_id=ass_prior.id,
            )

    def test_evaluate_outcome_reversed_timestamps(self, db_session):
        p = make_personnel()
        b = StressAssessment(
            id=201, personnel_id=p.id, stress_level="High", low_probability=0.1, medium_probability=0.2,
            high_probability=0.7, risk_score=75.0, risk_priority="Priority",
            assessment_timestamp=datetime(2026, 9, 20, tzinfo=timezone.utc)
        )
        f = StressAssessment(
            id=202, personnel_id=p.id, stress_level="Low", low_probability=0.8, medium_probability=0.15,
            high_probability=0.05, risk_score=25.0, risk_priority="Routine",
            assessment_timestamp=datetime(2026, 9, 10, tzinfo=timezone.utc)  # Reversed!
        )
        outcome, ev = WelfareOutcomeService.evaluate_outcome(db_session, p.id, b, f)
        assert outcome == "INSUFFICIENT_DATA"
        assert "chronological integrity violated" in ev["explanation"]

    def test_evaluate_outcome_identical_timestamps(self, db_session):
        p = make_personnel()
        ts = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)
        b = StressAssessment(
            id=203, personnel_id=p.id, stress_level="High", low_probability=0.1, medium_probability=0.2,
            high_probability=0.7, risk_score=75.0, risk_priority="Priority",
            assessment_timestamp=ts
        )
        f = StressAssessment(
            id=203, personnel_id=p.id, stress_level="Low", low_probability=0.8, medium_probability=0.15,
            high_probability=0.05, risk_score=25.0, risk_priority="Routine",
            assessment_timestamp=ts  # Identical!
        )
        outcome, ev = WelfareOutcomeService.evaluate_outcome(db_session, p.id, b, f)
        assert outcome == "INSUFFICIENT_DATA"
        assert "chronological integrity violated" in ev["explanation"]

    def test_evaluate_outcome_missing_timestamps(self, db_session):
        p = make_personnel()
        b = StressAssessment(
            id=204, personnel_id=p.id, stress_level="High", low_probability=0.1, medium_probability=0.2,
            high_probability=0.7, risk_score=75.0, risk_priority="Priority",
            assessment_timestamp=None  # Missing timestamp
        )
        f = StressAssessment(
            id=205, personnel_id=p.id, stress_level="Low", low_probability=0.8, medium_probability=0.15,
            high_probability=0.05, risk_score=25.0, risk_priority="Routine",
            assessment_timestamp=None  # Missing timestamp
        )
        outcome, ev = WelfareOutcomeService.evaluate_outcome(db_session, p.id, b, f)
        assert outcome == "INSUFFICIENT_DATA"



# =============================================================================
# 4. DETERMINISTIC OUTCOME CLASSIFICATION TESTS
# =============================================================================
class TestOutcomeClassification:
    def test_outcome_improved(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        b = StressAssessment(
            personnel_id=p.id, stress_level="High", low_probability=0.1, medium_probability=0.2,
            high_probability=0.7, risk_score=75.0, risk_priority="Priority",
            assessment_timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc)
        )
        f = StressAssessment(
            personnel_id=p.id, stress_level="Moderate", low_probability=0.5, medium_probability=0.4,
            high_probability=0.1, risk_score=45.0, risk_priority="Preventive",
            assessment_timestamp=datetime(2026, 9, 10, tzinfo=timezone.utc)
        )
        db_session.add_all([b, f])
        db_session.commit()

        outcome, ev = WelfareOutcomeService.evaluate_outcome(db_session, p.id, b, f)
        assert outcome == "IMPROVED"
        assert ev["score_delta"] == -30.0
        assert ev["data_sufficiency"] == "SUFFICIENT"

    def test_outcome_worsening(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        b = StressAssessment(
            personnel_id=p.id, stress_level="Low", low_probability=0.8, medium_probability=0.15,
            high_probability=0.05, risk_score=20.0, risk_priority="Routine",
            assessment_timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc)
        )
        f = StressAssessment(
            personnel_id=p.id, stress_level="Medium", low_probability=0.2, medium_probability=0.5,
            high_probability=0.3, risk_score=52.0, risk_priority="Preventive",
            assessment_timestamp=datetime(2026, 9, 10, tzinfo=timezone.utc)
        )
        db_session.add_all([b, f])
        db_session.commit()

        outcome, ev = WelfareOutcomeService.evaluate_outcome(db_session, p.id, b, f)
        assert outcome == "WORSENING"
        assert ev["score_delta"] == 32.0

    def test_outcome_persistent_concern(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        b = StressAssessment(
            personnel_id=p.id, stress_level="High", low_probability=0.1, medium_probability=0.2,
            high_probability=0.7, risk_score=72.0, risk_priority="Priority",
            assessment_timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc)
        )
        f = StressAssessment(
            personnel_id=p.id, stress_level="High", low_probability=0.1, medium_probability=0.2,
            high_probability=0.7, risk_score=71.5, risk_priority="Priority",
            assessment_timestamp=datetime(2026, 9, 10, tzinfo=timezone.utc)
        )
        db_session.add_all([b, f])
        db_session.commit()

        outcome, ev = WelfareOutcomeService.evaluate_outcome(db_session, p.id, b, f)
        assert outcome == "PERSISTENT_CONCERN"
        assert ev["score_delta"] == -0.5

    def test_outcome_stable(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        b = StressAssessment(
            personnel_id=p.id, stress_level="Low", low_probability=0.8, medium_probability=0.15,
            high_probability=0.05, risk_score=24.0, risk_priority="Routine",
            assessment_timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc)
        )
        f = StressAssessment(
            personnel_id=p.id, stress_level="Low", low_probability=0.78, medium_probability=0.17,
            high_probability=0.05, risk_score=25.2, risk_priority="Routine",
            assessment_timestamp=datetime(2026, 9, 10, tzinfo=timezone.utc)
        )
        db_session.add_all([b, f])
        db_session.commit()

        outcome, ev = WelfareOutcomeService.evaluate_outcome(db_session, p.id, b, f)
        assert outcome == "STABLE"
        assert ev["score_delta"] == 1.2

    def test_outcome_insufficient_data_missing_followup(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        b = StressAssessment(
            personnel_id=p.id, stress_level="Low", low_probability=0.8, medium_probability=0.15,
            high_probability=0.05, risk_score=20.0, risk_priority="Routine",
            assessment_timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc)
        )
        db_session.add(b)
        db_session.commit()

        outcome, ev = WelfareOutcomeService.evaluate_outcome(db_session, p.id, b, None)
        assert outcome == "INSUFFICIENT_DATA"
        assert ev["data_sufficiency"] == "INSUFFICIENT"

    def test_outcome_insufficient_data_nan_score(self, db_session):
        p = make_personnel()
        b = StressAssessment(
            id=101,
            personnel_id=p.id, stress_level="Low", low_probability=0.8, medium_probability=0.15,
            high_probability=0.05, risk_score=20.0, risk_priority="Routine",
            assessment_timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc)
        )
        f = StressAssessment(
            id=102,
            personnel_id=p.id, stress_level="Low", low_probability=0.8, medium_probability=0.15,
            high_probability=0.05, risk_score=float("nan"), risk_priority="Routine",
            assessment_timestamp=datetime(2026, 9, 10, tzinfo=timezone.utc)
        )

        outcome, ev = WelfareOutcomeService.evaluate_outcome(db_session, p.id, b, f)
        assert outcome == "INSUFFICIENT_DATA"

    def test_outcome_insufficient_data_inf_score(self, db_session):
        p = make_personnel()
        b = StressAssessment(
            id=103, personnel_id=p.id, stress_level="Low", low_probability=0.8, medium_probability=0.15,
            high_probability=0.05, risk_score=float("inf"), risk_priority="Routine",
            assessment_timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc)
        )
        f = StressAssessment(
            id=104, personnel_id=p.id, stress_level="Low", low_probability=0.8, medium_probability=0.15,
            high_probability=0.05, risk_score=float("-inf"), risk_priority="Routine",
            assessment_timestamp=datetime(2026, 9, 10, tzinfo=timezone.utc)
        )
        outcome, ev = WelfareOutcomeService.evaluate_outcome(db_session, p.id, b, f)
        assert outcome == "INSUFFICIENT_DATA"
        assert "invalid non-numeric" in ev["explanation"]

    def test_outcome_insufficient_data_none_score(self, db_session):
        p = make_personnel()
        b = StressAssessment(
            id=105, personnel_id=p.id, stress_level="Low", low_probability=0.8, medium_probability=0.15,
            high_probability=0.05, risk_score=None, risk_priority="Routine",
            assessment_timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc)
        )
        f = StressAssessment(
            id=106, personnel_id=p.id, stress_level="Low", low_probability=0.8, medium_probability=0.15,
            high_probability=0.05, risk_score=35.0, risk_priority="Routine",
            assessment_timestamp=datetime(2026, 9, 10, tzinfo=timezone.utc)
        )
        outcome, ev = WelfareOutcomeService.evaluate_outcome(db_session, p.id, b, f)
        assert outcome == "INSUFFICIENT_DATA"
        assert "invalid non-numeric" in ev["explanation"]



    def test_determinism_identical_runs(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()

        b = StressAssessment(
            personnel_id=p.id, stress_level="High", low_probability=0.1, medium_probability=0.2,
            high_probability=0.7, risk_score=80.0, risk_priority="Priority",
            assessment_timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc)
        )
        f = StressAssessment(
            personnel_id=p.id, stress_level="Low", low_probability=0.8, medium_probability=0.15,
            high_probability=0.05, risk_score=30.0, risk_priority="Routine",
            assessment_timestamp=datetime(2026, 9, 10, tzinfo=timezone.utc)
        )
        db_session.add_all([b, f])
        db_session.commit()

        outcome1, ev1 = WelfareOutcomeService.evaluate_outcome(db_session, p.id, b, f)
        outcome2, ev2 = WelfareOutcomeService.evaluate_outcome(db_session, p.id, b, f)
        assert outcome1 == outcome2 == "IMPROVED"
        assert ev1["score_delta"] == ev2["score_delta"]


# =============================================================================
# 5. MULTIPLE FOLLOW-UPS & TIMELINE PRESERVATION TESTS
# =============================================================================
class TestMultipleFollowupsTimeline:
    def test_multiple_followups_history_preserved(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        f1 = WelfareOutcomeService.create_followup(
            db=db_session, user=u, personnel_id=p.id,
            followup_type="WELFARE_CHECKIN", notes="First check-in"
        )
        f1 = WelfareOutcomeService.complete_followup(db=db_session, followup_id=f1.id, user=u, notes="Done 1")

        f2 = WelfareOutcomeService.create_followup(
            db=db_session, user=u, personnel_id=p.id,
            followup_type="RECOVERY_REVIEW", notes="Second review"
        )
        f2 = WelfareOutcomeService.complete_followup(db=db_session, followup_id=f2.id, user=u, notes="Done 2")

        f3 = WelfareOutcomeService.create_followup(
            db=db_session, user=u, personnel_id=p.id,
            followup_type="DUTY_SCHEDULE_REVIEW", notes="Third review"
        )

        all_records = (
            db_session.query(WelfareFollowup)
            .filter(WelfareFollowup.personnel_id == p.id)
            .order_by(WelfareFollowup.created_at.asc())
            .all()
        )
        assert len(all_records) == 3
        ids = [r.id for r in all_records]
        assert len(set(ids)) == 3
        assert f1.status == "COMPLETED"
        assert f2.status == "COMPLETED"
        assert f3.status == "PENDING"


# =============================================================================
# 6. SECURITY, RBAC & ANTI-IDOR TESTS
# =============================================================================
class TestSecurityRBACAntiIDOR:
    def test_personnel_can_only_access_self(self, db_session):
        p1 = make_personnel()
        p2 = make_personnel()
        db_session.add_all([p1, p2])
        db_session.commit()

        jawan1 = make_user(role="personnel", personnel_id=p1.id)
        db_session.add(jawan1)
        db_session.commit()

        # Accessing self -> OK
        p = WelfareOutcomeService.verify_access_and_get_personnel(p1.id, jawan1, db_session)
        assert p.id == p1.id

        # Accessing other personnel -> PermissionError (Anti-IDOR)
        with pytest.raises(PermissionError, match="Personnel can only access their own welfare follow-ups"):
            WelfareOutcomeService.verify_access_and_get_personnel(p2.id, jawan1, db_session)

    def test_officer_scoped_to_battalion(self, db_session):
        p1 = make_personnel(battalion="1st Battalion", location="Srinagar")
        p2 = make_personnel(battalion="2nd Battalion", location="Jammu")
        db_session.add_all([p1, p2])
        db_session.commit()

        officer = make_user(role="officer", battalion="1st Battalion", location="Srinagar")
        db_session.add(officer)
        db_session.commit()

        # Same battalion -> OK
        p = WelfareOutcomeService.verify_access_and_get_personnel(p1.id, officer, db_session)
        assert p.id == p1.id

        # Different battalion -> PermissionError
        with pytest.raises(PermissionError, match="Cross-battalion access restricted"):
            WelfareOutcomeService.verify_access_and_get_personnel(p2.id, officer, db_session)

    def test_admin_has_unrestricted_access(self, db_session):
        p1 = make_personnel(battalion="1st Battalion")
        p2 = make_personnel(battalion="2nd Battalion")
        db_session.add_all([p1, p2])
        db_session.commit()

        admin = make_user(role="admin")
        db_session.add(admin)
        db_session.commit()

        p_a = WelfareOutcomeService.verify_access_and_get_personnel(p1.id, admin, db_session)
        p_b = WelfareOutcomeService.verify_access_and_get_personnel(p2.id, admin, db_session)
        assert p_a.id == p1.id
        assert p_b.id == p2.id


# =============================================================================
# 7. PRIVACY & SMALL-GROUP SUPPRESSION TESTS
# =============================================================================
class TestPrivacySmallGroupSuppression:
    def test_privacy_suppression_below_threshold(self, db_session):
        bat = f"SmallBat_{uid()}"
        p = make_personnel(battalion=bat, location="Leh")
        db_session.add(p)
        db_session.commit()

        officer = make_user(role="officer", battalion=bat, location="Leh")
        db_session.add(officer)
        db_session.commit()

        analytics = WelfareOutcomeService.get_unit_followup_analytics(db=db_session, user=officer)
        assert analytics["data_suppressed"] is True
        assert analytics["total_personnel_in_scope"] < ANALYTICS_MIN_GROUP_SIZE
        assert "Data suppressed to protect individual privacy" in analytics["suppression_reason"]
        assert analytics["followups_total"] == 0

    def test_disclaimer_present_in_analytics(self, db_session):
        admin = make_user(role="admin")
        db_session.add(admin)
        db_session.commit()

        analytics = WelfareOutcomeService.get_unit_followup_analytics(db=db_session, user=admin)
        assert "disclaimer" in analytics
        assert "not establish clinical recovery" in analytics["disclaimer"]


# =============================================================================
# 8. AUDIT TRAIL TESTS
# =============================================================================
class TestAuditTrail:
    def test_audit_logs_created_on_lifecycle_events(self, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        followup = WelfareOutcomeService.create_followup(
            db=db_session, user=u, personnel_id=p.id,
            followup_type="WELFARE_CHECKIN"
        )
        followup = WelfareOutcomeService.schedule_followup(
            db=db_session, followup_id=followup.id, user=u,
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=2)
        )
        followup = WelfareOutcomeService.complete_followup(
            db=db_session, followup_id=followup.id, user=u
        )

        audits = (
            db_session.query(WelfareFollowupAudit)
            .filter(WelfareFollowupAudit.followup_id == followup.id)
            .order_by(WelfareFollowupAudit.timestamp.asc())
            .all()
        )
        actions = [a.action for a in audits]
        assert "FOLLOWUP_CREATED" in actions
        assert "FOLLOWUP_SCHEDULED" in actions
        assert "FOLLOWUP_COMPLETED" in actions
        assert "OUTCOME_RECORDED" in actions

        for a in audits:
            assert a.actor_id == u.id
            assert a.timestamp is not None


# =============================================================================
# 9. API INTEGRATION TESTS
# =============================================================================
class TestAPIEndpoints:
    def test_api_create_and_complete_followup(self, client, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        token = create_access_token(data={"sub": u.username, "role": u.role})
        headers = {"Authorization": f"Bearer {token}"}

        # 1. POST /api/followups
        res = client.post(
            "/api/followups",
            headers=headers,
            json={
                "personnel_id": p.id,
                "followup_type": "WELFARE_CHECKIN",
                "review_window": "Within 7 days",
                "notes": "API test follow-up",
            },
        )
        assert res.status_code == 201
        data = res.json()
        fid = data["id"]
        assert data["personnel_id"] == p.id
        assert data["status"] == "PENDING"
        assert data["outcome_status"] == "INSUFFICIENT_DATA"

        # 2. GET /api/followups/personnel/{personnel_id}
        res_list = client.get(f"/api/followups/personnel/{p.id}", headers=headers)
        assert res_list.status_code == 200
        assert len(res_list.json()["followups"]) >= 1

        # 3. POST /api/followups/{id}/schedule
        res_sched = client.post(
            f"/api/followups/{fid}/schedule",
            headers=headers,
            json={"scheduled_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(), "notes": "Set for Monday"},
        )
        assert res_sched.status_code == 200
        assert res_sched.json()["status"] == "SCHEDULED"

        # 4. POST /api/followups/{id}/complete
        res_comp = client.post(
            f"/api/followups/{fid}/complete",
            headers=headers,
            json={"notes": "Completed successfully"},
        )
        assert res_comp.status_code == 200
        assert res_comp.json()["status"] == "COMPLETED"

        # 5. GET /api/followups/{id}/audits
        res_aud = client.get(f"/api/followups/{fid}/audits", headers=headers)
        assert res_aud.status_code == 200
        assert len(res_aud.json()) >= 3

    def test_api_unauthenticated_rejected(self, client):
        res = client.get("/api/followups")
        assert res.status_code == 401

        res_p = client.get("/api/followups/personnel/1")
        assert res_p.status_code == 401

    def test_api_idor_cross_personnel_rejected(self, client, db_session):
        p1 = make_personnel()
        p2 = make_personnel()
        db_session.add_all([p1, p2])
        db_session.commit()

        jawan1 = make_user(role="personnel", personnel_id=p1.id)
        db_session.add(jawan1)
        db_session.commit()

        token = create_access_token(data={"sub": jawan1.username, "role": jawan1.role})
        headers = {"Authorization": f"Bearer {token}"}

        # Accessing other personnel's followups must return 403 Forbidden
        res = client.get(f"/api/followups/personnel/{p2.id}", headers=headers)
        assert res.status_code == 403
        assert "own welfare follow-ups" in res.json()["detail"]

    def test_api_idor_cross_battalion_rejected(self, client, db_session):
        p1 = make_personnel(battalion="1st Battalion", location="Srinagar")
        p2 = make_personnel(battalion="2nd Battalion", location="Jammu")
        db_session.add_all([p1, p2])
        db_session.commit()

        officer = make_user(role="officer", battalion="1st Battalion", location="Srinagar")
        db_session.add(officer)
        db_session.commit()

        token = create_access_token(data={"sub": officer.username, "role": officer.role})
        headers = {"Authorization": f"Bearer {token}"}

        # Officer accessing personnel from another battalion must return 403
        res = client.get(f"/api/followups/personnel/{p2.id}", headers=headers)
        assert res.status_code == 403
        assert "Cross-battalion access restricted" in res.json()["detail"]

    def test_api_overdue_flag_logic(self, client, db_session):
        p = make_personnel()
        db_session.add(p)
        db_session.commit()
        u = make_user(role="officer", battalion=p.battalion, location=p.location)
        db_session.add(u)
        db_session.commit()

        token = create_access_token(data={"sub": u.username, "role": u.role})
        headers = {"Authorization": f"Bearer {token}"}

        now = datetime.now(timezone.utc)

        # 1. Future due date -> not overdue
        f_future = WelfareFollowup(
            personnel_id=p.id,
            followup_type="WELFARE_CHECKIN",
            status="PENDING",
            due_date=now + timedelta(days=5),
        )
        # 2. Past due date & PENDING -> overdue
        f_overdue = WelfareFollowup(
            personnel_id=p.id,
            followup_type="RECOVERY_REVIEW",
            status="PENDING",
            due_date=now - timedelta(days=2),
        )
        # 3. Past due date & COMPLETED -> not overdue
        f_completed = WelfareFollowup(
            personnel_id=p.id,
            followup_type="DUTY_SCHEDULE_REVIEW",
            status="COMPLETED",
            due_date=now - timedelta(days=3),
            completed_at=now - timedelta(days=1),
        )
        # 4. Past due date & CANCELLED -> not overdue
        f_cancelled = WelfareFollowup(
            personnel_id=p.id,
            followup_type="SUPPORT_RESOURCE_FOLLOWUP",
            status="CANCELLED",
            due_date=now - timedelta(days=4),
        )
        db_session.add_all([f_future, f_overdue, f_completed, f_cancelled])
        db_session.commit()

        res = client.get(f"/api/followups/personnel/{p.id}", headers=headers)
        assert res.status_code == 200
        items_by_id = {item["id"]: item for item in res.json()["followups"]}

        assert items_by_id[f_future.id]["is_overdue"] is False
        assert items_by_id[f_overdue.id]["is_overdue"] is True
        assert items_by_id[f_completed.id]["is_overdue"] is False
        assert items_by_id[f_cancelled.id]["is_overdue"] is False

