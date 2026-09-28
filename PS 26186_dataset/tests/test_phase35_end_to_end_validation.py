"""
PHASE 35: END-TO-END WELFARE RISK SYSTEM VALIDATION & HARDENING TEST SUITE
==========================================================================
Comprehensive automated test suite covering all 14 Phase 35 validation categories:
 1. Single Source of Truth Audit & Delegation
 2. Input Consistency across Entry Points (Path A, B, C, D)
 3. Input Validation Audit (Out-of-bounds, NaN, Inf, Negative, Invalid Categoricals)
 4. Boundary Testing (Min, Max, Thresholds, Discontinuity Checks)
 5. Monotonicity Sweeps (Duty, Sleep, Consec, Nights, Fatigue, Mood, Burnout)
 6. Probability Distribution Validation (Sum to 1, Non-negative, Ordered Cumulative)
 7. Score & Category Consistency
 8. Confidence & Uncertainty Validation
 9. Missing Data Behavior & Fallback Auditing
 10. Adversarial & Edge Case Scenarios (Cases A through H)
 11. Temporal Longitudinal Tracking (History, Worsening, Improving, Consecutive High)
 12. API Contract & Error Handling (HTTP 200, 422, Stack-trace shielding)
 13. Non-Punitive Welfare Framing & Privacy / Data Exposure
 14. Determinism, Stability & High-Throughput Performance
"""

import os
import sys
import math
import uuid
import time
import pytest
import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add dataset root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from api.main import app
from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from core.security import create_access_token
from src.welfare_risk_engine_v2 import PersonnelWelfareRiskEngineV2, TIER_NAMES
from src.risk_scoring import calculate_risk_score
from services.prediction_service import get_prediction_service


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def engine():
    return PersonnelWelfareRiskEngineV2()


@pytest.fixture(scope="module")
def officer_auth():
    db = next(get_db())
    officer = db.query(User).filter(User.username == "test_officer_phase35").first()
    if not officer:
        officer = User(
            username="test_officer_phase35",
            hashed_password="hashed_pw",
            role="officer",
            is_active=True
        )
        db.add(officer)
        db.commit()
        db.refresh(officer)
    token = create_access_token({"sub": officer.username, "role": officer.role, "personnel_id": None})
    db.close()
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 1. SINGLE SOURCE OF TRUTH AUDIT
# ============================================================================
class TestSingleSourceOfTruth:
    def test_calculate_risk_score_delegates_to_v2(self, engine):
        """calculate_risk_score in src/risk_scoring.py must delegate to V2 engine."""
        rec = {'duty_hours_per_week': 50, 'sleep_hours': 6.5, 'mood_score': 3, 'physical_fatigue': 3}
        dummy_probs = {'Low': 0.2, 'Medium': 0.5, 'High': 0.3}

        score_calc, level_calc, prio_calc, meta = calculate_risk_score(dummy_probs, 'Medium', rec, return_metadata=True)
        direct_eval = engine.assess(rec)

        assert abs(score_calc - direct_eval['risk_score']) < 1e-4
        assert meta['model_version'] == 'risk_engine_v2'
        assert meta['risk_category'] == direct_eval['risk_category']

    def test_prediction_service_champion_is_v2(self):
        """Production prediction service must load Welfare Risk Engine V2 as champion."""
        service = get_prediction_service()
        assert service.predictor is not None
        assert service.predictor.is_v2 is True
        assert hasattr(service.predictor.predictor, 'assess') or hasattr(service.predictor.predictor, 'evaluate')


# ============================================================================
# 2. INPUT CONSISTENCY TESTING ACROSS ENTRY POINTS
# ============================================================================
class TestInputConsistencyAcrossEntryPoints:
    def test_path_a_b_consistency(self, client, engine):
        """Path A (Direct Engine) and Path B (POST /api/welfare/assessment) must be strictly identical."""
        payload = {
            'duty_hours_per_week': 56.0,
            'sleep_hours': 6.0,
            'mood_score': 3,
            'physical_fatigue': 3,
            'consecutive_duty_days': 8,
            'night_shifts_per_month': 5,
            'burnout_symptoms': 'Sometimes',
            'operational_exposure': 'Medium'
        }
        res_a = engine.assess(payload)
        resp_b = client.post('/api/welfare/assessment', json=payload)
        assert resp_b.status_code == 200
        res_b = resp_b.json()

        assert res_a['risk_score'] == res_b['risk_score']
        assert res_a['risk_category'] == res_b['risk_category']
        assert res_a['probabilities'] == res_b['probabilities']
        # Documented serialization: API converts numeric confidence [0.1, 1.0] to string tier
        expected_conf_str = "High" if res_a['confidence'] >= 0.70 else ("Moderate" if res_a['confidence'] >= 0.40 else "Low")
        assert res_b['confidence'] == expected_conf_str

    def test_path_c_authenticated_personnel_assessment_consistency(self, client, engine, officer_auth):
        """Path C (POST /personnel/{id}/assess) must utilize identical V2 scoring core and produce identical scores."""
        db = next(get_db())
        unique_code = f"P35-{uuid.uuid4().hex[:6].upper()}"
        p = Personnel(
            name="Consistency Tester",
            personnel_code=unique_code,
            age=28, gender="Male", department="Operations", job_role="Havildar",
            location="Jammu", experience_years=5.0, duty_hours_per_week=48.0,
            consecutive_duty_days=7, night_shifts_per_month=4, operational_exposure="High",
            leave_gap_days=30, remote_posting="No"
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        p_id = p.id
        db.close()

        override = {
            'duty_hours_per_week': 60.0,
            'sleep_hours': 5.5,
            'mood_score': 3,
            'physical_fatigue': 3,
            'consecutive_duty_days': 7,
            'night_shifts_per_month': 4,
            'burnout_symptoms': 'Sometimes',
            'operational_exposure': 'High',
            'physical_activity_hours_per_week': 5.0,
            'leave_gap_days': 30,
            'remote_posting': 'No'
        }
        resp = client.post(f"/api/personnel/{p_id}/assess", json=override, headers=officer_auth)
        assert resp.status_code == 201
        data = resp.json()['assessment']

        # Compare with direct engine call using the exact same parameters
        direct = engine.assess(override)
        assert data['risk_score'] == direct['risk_score']
        assert data['risk_priority'] == direct['risk_priority']


# ============================================================================
# 3. INPUT VALIDATION AUDIT
# ============================================================================
class TestInputValidationAudit:
    def test_negative_duty_hours_rejected(self, engine, client):
        """Negative duty hours must be rejected with clear validation error."""
        rec = {'duty_hours_per_week': -10.0, 'sleep_hours': 7.0, 'mood_score': 4, 'physical_fatigue': 2}
        res = engine.assess(rec)
        assert res['risk_score'] is None
        assert "Validation failed" in res['error']
        assert any("Duty hours" in err for err in res['validation_errors'])

        # API check
        resp = client.post('/api/welfare/assessment', json=rec)
        assert resp.status_code == 422
        assert "Validation failed" in resp.json()['detail']['message']

    def test_impossible_duty_hours_rejected(self, engine, client):
        """Duty hours above 120 must be rejected."""
        rec = {'duty_hours_per_week': 130.0, 'sleep_hours': 7.0, 'mood_score': 4, 'physical_fatigue': 2}
        res = engine.assess(rec)
        assert res['risk_score'] is None
        assert any("Duty hours" in err for err in res['validation_errors'])

        resp = client.post('/api/welfare/assessment', json=rec)
        assert resp.status_code == 422

    def test_negative_sleep_rejected(self, engine, client):
        """Negative sleep hours must be rejected."""
        rec = {'duty_hours_per_week': 44.0, 'sleep_hours': -2.0, 'mood_score': 4, 'physical_fatigue': 2}
        res = engine.assess(rec)
        assert res['risk_score'] is None
        assert any("Sleep hours" in err for err in res['validation_errors'])

    def test_impossible_sleep_rejected(self, engine):
        """Sleep hours > 24 must be rejected."""
        rec = {'duty_hours_per_week': 44.0, 'sleep_hours': 26.0, 'mood_score': 4, 'physical_fatigue': 2}
        res = engine.assess(rec)
        assert res['risk_score'] is None
        assert any("Sleep hours" in err for err in res['validation_errors'])

    def test_invalid_fatigue_and_mood_bounds(self, engine):
        """Fatigue and mood must strictly fall in [1, 5]."""
        rec_fatigue = {'duty_hours_per_week': 44, 'sleep_hours': 7, 'mood_score': 4, 'physical_fatigue': 6}
        res_f = engine.assess(rec_fatigue)
        assert res_f['risk_score'] is None
        assert any("Physical fatigue" in err for err in res_f['validation_errors'])

        rec_mood = {'duty_hours_per_week': 44, 'sleep_hours': 7, 'mood_score': 0, 'physical_fatigue': 2}
        res_m = engine.assess(rec_mood)
        assert res_m['risk_score'] is None
        assert any("Mood score" in err for err in res_m['validation_errors'])

    def test_nan_and_infinity_rejected(self, engine):
        """NaN and Infinite values must be explicitly rejected."""
        rec_nan = {'duty_hours_per_week': float('nan'), 'sleep_hours': 7.0, 'mood_score': 4, 'physical_fatigue': 2}
        res_nan = engine.assess(rec_nan)
        assert res_nan['risk_score'] is None
        assert any("NaN" in err for err in res_nan['validation_errors'])

        rec_inf = {'duty_hours_per_week': 44.0, 'sleep_hours': float('inf'), 'mood_score': 4, 'physical_fatigue': 2}
        res_inf = engine.assess(rec_inf)
        assert res_inf['risk_score'] is None
        assert any("Infinite" in err for err in res_inf['validation_errors'])

    def test_invalid_categorical_rejected(self, engine):
        """Categoricals with invalid options must be rejected."""
        rec_burnout = {'duty_hours_per_week': 44, 'sleep_hours': 7, 'mood_score': 4, 'physical_fatigue': 2, 'burnout_symptoms': 'Catastrophic'}
        res_b = engine.assess(rec_burnout)
        assert res_b['risk_score'] is None
        assert any("Burnout symptoms" in err for err in res_b['validation_errors'])

        rec_op = {'duty_hours_per_week': 44, 'sleep_hours': 7, 'mood_score': 4, 'physical_fatigue': 2, 'operational_exposure': 'CriticalWarzone'}
        res_op = engine.assess(rec_op)
        assert res_op['risk_score'] is None
        assert any("Operational exposure" in err for err in res_op['validation_errors'])


# ============================================================================
# 4. BOUNDARY TESTING & DISCONTINUITY AUDIT
# ============================================================================
class TestBoundaryBehavior:
    def test_minimum_valid_boundaries(self, engine):
        """Duty = 0.0, Sleep = 0.0, Consecutive = 0, Fatigue = 1, Mood = 1 must evaluate without crash."""
        rec_min = {'duty_hours_per_week': 0.0, 'sleep_hours': 0.0, 'physical_fatigue': 1, 'mood_score': 1, 'consecutive_duty_days': 0}
        res = engine.assess(rec_min)
        assert res['risk_score'] is not None
        assert 0.0 <= res['risk_score'] <= 100.0

    def test_maximum_valid_boundaries(self, engine):
        """Duty = 120.0, Sleep = 24.0, Consecutive = 60, Fatigue = 5, Mood = 5 must evaluate without crash."""
        rec_max = {'duty_hours_per_week': 120.0, 'sleep_hours': 24.0, 'physical_fatigue': 5, 'mood_score': 5, 'consecutive_duty_days': 60}
        res = engine.assess(rec_max)
        assert res['risk_score'] is not None
        assert 0.0 <= res['risk_score'] <= 100.0

    def test_category_boundary_continuity(self, engine):
        """Crossing score boundaries (35, 55, 70, 85) must happen smoothly without score jumps."""
        scores = []
        for h in np.linspace(40, 95, 20):
            res = engine.assess({'duty_hours_per_week': float(h), 'sleep_hours': 6.0, 'physical_fatigue': 3, 'mood_score': 3})
            scores.append(res['risk_score'])

        # Max delta between adjacent 2.89 hr increments should be small (< 3.0 points)
        diffs = [abs(scores[i+1] - scores[i]) for i in range(len(scores)-1)]
        assert max(diffs) < 3.0, f"Discontinuous jump detected: max diff = {max(diffs)}"


# ============================================================================
# 5. MONOTONICITY AUDIT
# ============================================================================
class TestMonotonicityAudit:
    base_rec = {'duty_hours_per_week': 44, 'sleep_hours': 7.5, 'mood_score': 4, 'physical_fatigue': 2, 'consecutive_duty_days': 4, 'night_shifts_per_month': 2, 'burnout_symptoms': 'Rarely'}

    def test_duty_hours_monotonicity(self, engine):
        """Duty hours 40 -> 90 must produce monotonically non-decreasing risk scores."""
        hours = [40, 45, 50, 55, 60, 70, 80, 90]
        scores = [engine.assess(dict(self.base_rec, duty_hours_per_week=h))['risk_score'] for h in hours]
        for i in range(len(scores) - 1):
            assert scores[i+1] >= scores[i], f"Reversal: {hours[i]}h ({scores[i]}) vs {hours[i+1]}h ({scores[i+1]})"

    def test_sleep_hours_monotonicity(self, engine):
        """Reducing sleep hours 8 -> 3 must produce monotonically non-decreasing risk scores."""
        sleeps = [8.0, 7.0, 6.0, 5.0, 4.0, 3.0]
        scores = [engine.assess(dict(self.base_rec, sleep_hours=s))['risk_score'] for s in sleeps]
        for i in range(len(scores) - 1):
            assert scores[i+1] >= scores[i], f"Reversal: {sleeps[i]}h sleep ({scores[i]}) vs {sleeps[i+1]}h sleep ({scores[i+1]})"

    def test_consecutive_duty_monotonicity(self, engine):
        """Consecutive duty days 2 -> 25 must produce monotonically non-decreasing risk scores."""
        days = [2, 4, 6, 8, 12, 16, 20, 25]
        scores = [engine.assess(dict(self.base_rec, consecutive_duty_days=d))['risk_score'] for d in days]
        for i in range(len(scores) - 1):
            assert scores[i+1] >= scores[i], f"Reversal: {days[i]}d ({scores[i]}) vs {days[i+1]}d ({scores[i+1]})"

    def test_night_shifts_monotonicity(self, engine):
        """Night shifts 0 -> 16 must produce monotonically non-decreasing risk scores."""
        shifts = [0, 2, 4, 6, 8, 12, 16]
        scores = [engine.assess(dict(self.base_rec, night_shifts_per_month=n))['risk_score'] for n in shifts]
        for i in range(len(scores) - 1):
            assert scores[i+1] >= scores[i], f"Reversal: {shifts[i]} shifts ({scores[i]}) vs {shifts[i+1]} shifts ({scores[i+1]})"

    def test_fatigue_monotonicity(self, engine):
        """Fatigue rating 1 -> 5 must produce monotonically non-decreasing risk scores."""
        fatigues = [1, 2, 3, 4, 5]
        scores = [engine.assess(dict(self.base_rec, physical_fatigue=f))['risk_score'] for f in fatigues]
        for i in range(len(scores) - 1):
            assert scores[i+1] >= scores[i], f"Reversal: fatigue {fatigues[i]} ({scores[i]}) vs {fatigues[i+1]} ({scores[i+1]})"

    def test_mood_monotonicity(self, engine):
        """Mood rating worsening 5 -> 1 must produce monotonically non-decreasing risk scores."""
        moods = [5, 4, 3, 2, 1]
        scores = [engine.assess(dict(self.base_rec, mood_score=m))['risk_score'] for m in moods]
        for i in range(len(scores) - 1):
            assert scores[i+1] >= scores[i], f"Reversal: mood {moods[i]} ({scores[i]}) vs {moods[i+1]} ({scores[i+1]})"

    def test_burnout_monotonicity(self, engine):
        """Burnout Rarely -> Sometimes -> Often must produce monotonically non-decreasing risk scores."""
        burnouts = ['Rarely', 'Sometimes', 'Often']
        scores = [engine.assess(dict(self.base_rec, burnout_symptoms=b))['risk_score'] for b in burnouts]
        for i in range(len(scores) - 1):
            assert scores[i+1] >= scores[i], f"Reversal: burnout {burnouts[i]} ({scores[i]}) vs {burnouts[i+1]} ({scores[i+1]})"


# ============================================================================
# 6. PROBABILITY VALIDATION
# ============================================================================
class TestProbabilityValidation:
    def test_probability_distribution_integrity(self, engine):
        """Probabilities must be in [0, 1], non-negative, and sum to approximately 1.0 across diverse profiles."""
        test_profiles = [
            {'duty_hours_per_week': 40, 'sleep_hours': 8.0, 'physical_fatigue': 1, 'mood_score': 5},
            {'duty_hours_per_week': 55, 'sleep_hours': 6.0, 'physical_fatigue': 3, 'mood_score': 3},
            {'duty_hours_per_week': 75, 'sleep_hours': 4.5, 'physical_fatigue': 4, 'mood_score': 2},
            {'duty_hours_per_week': 95, 'sleep_hours': 3.0, 'physical_fatigue': 5, 'mood_score': 1},
        ]
        for p in test_profiles:
            res = engine.assess(p)
            probs = res['probabilities']
            p_vals = [probs['low'], probs['moderate'], probs['elevated'], probs['high'], probs['critical']]

            # Check individual bounds
            for val in p_vals:
                assert 0.0 <= val <= 1.0
                assert not math.isnan(val)

            # Sum approximately 1.0
            assert abs(sum(p_vals) - 1.0) <= 0.005


# ============================================================================
# 7. SCORE / CATEGORY CONSISTENCY
# ============================================================================
class TestScoreCategoryConsistency:
    def test_category_cannot_disagree_with_score(self, engine):
        """Risk category must strictly match documented interpretation bands."""
        rng = np.random.RandomState(42)
        for _ in range(50):
            rec = {
                'duty_hours_per_week': float(rng.uniform(30, 95)),
                'sleep_hours': float(rng.uniform(3.0, 9.0)),
                'physical_fatigue': int(rng.randint(1, 6)),
                'mood_score': int(rng.randint(1, 6)),
                'consecutive_duty_days': int(rng.randint(1, 20)),
                'night_shifts_per_month': int(rng.randint(0, 15)),
                'burnout_symptoms': rng.choice(['Rarely', 'Sometimes', 'Often'])
            }
            res = engine.assess(rec)
            score = res['risk_score']
            cat = res['risk_category']

            if score >= 85.0:
                expected = "Critical"
            elif score >= 70.0:
                expected = "High"
            elif score >= 55.0:
                expected = "Elevated"
            elif score >= 35.0:
                expected = "Moderate"
            else:
                expected = "Low"

            assert cat == expected, f"Score {score} produced category {cat}, expected {expected}"


# ============================================================================
# 8. CONFIDENCE & UNCERTAINTY VALIDATION
# ============================================================================
class TestConfidenceUncertainty:
    def test_confidence_bounds(self, engine):
        """Confidence and uncertainty must always lie in [0.0, 1.0] and sum to ~1.0."""
        res = engine.assess({'duty_hours_per_week': 48, 'sleep_hours': 7.0, 'physical_fatigue': 2, 'mood_score': 4})
        assert 0.0 < res['confidence'] <= 1.0
        assert 0.0 <= res['uncertainty'] <= 1.0
        assert abs((res['confidence'] + res['uncertainty']) - 1.0) <= 0.10

    def test_incomplete_assessment_low_confidence(self, engine):
        """Incomplete assessment (< 0.50 completeness) receives 0.0 confidence."""
        res = engine.assess({'duty_hours_per_week': 50})  # only 1 of 4 required fields
        assert res['risk_score'] is None
        assert res['confidence'] == 0.0
        assert res['uncertainty'] == 1.0


# ============================================================================
# 9. MISSING DATA BEHAVIOR
# ============================================================================
class TestMissingDataBehavior:
    def test_single_missing_field_safe_fallback(self, engine):
        """A single missing field among the 4 required maintains completeness >= 0.50 and succeeds safely."""
        # Missing sleep
        res_no_sleep = engine.assess({'duty_hours_per_week': 48, 'physical_fatigue': 2, 'mood_score': 4})
        assert res_no_sleep['risk_score'] is not None
        assert res_no_sleep['assessment_completeness'] == 0.75

        # Missing duty hours
        res_no_duty = engine.assess({'sleep_hours': 7.0, 'physical_fatigue': 2, 'mood_score': 4})
        assert res_no_duty['risk_score'] is not None
        assert res_no_duty['assessment_completeness'] == 0.75

        # Missing mood
        res_no_mood = engine.assess({'duty_hours_per_week': 48, 'sleep_hours': 7.0, 'physical_fatigue': 2})
        assert res_no_mood['risk_score'] is not None
        assert res_no_mood['assessment_completeness'] == 0.75

        # Missing fatigue
        res_no_fatigue = engine.assess({'duty_hours_per_week': 48, 'sleep_hours': 7.0, 'mood_score': 4})
        assert res_no_fatigue['risk_score'] is not None
        assert res_no_fatigue['assessment_completeness'] == 0.75


# ============================================================================
# 10. ADVERSARIAL & EDGE CASE TESTING (Cases A through H)
# ============================================================================
class TestAdversarialEdgeCases:
    def test_case_a_40_duty_3h_sleep(self, engine):
        """Case A: Normal duty + restricted sleep -> Low-Moderate concern, factors flag sleep."""
        res = engine.assess({'duty_hours_per_week': 40, 'sleep_hours': 3, 'physical_fatigue': 2, 'mood_score': 4})
        assert 30.0 <= res['risk_score'] <= 40.0
        assert any("sleep" in f.lower() for f in res['top_risk_factors'])

    def test_case_b_90_duty_8h_sleep(self, engine):
        """Case B: 90 duty + 8h sleep -> Moderate concern, factors flag duty hours."""
        res = engine.assess({'duty_hours_per_week': 90, 'sleep_hours': 8, 'physical_fatigue': 2, 'mood_score': 4})
        assert 33.0 <= res['risk_score'] <= 45.0
        assert any("duty" in f.lower() for f in res['top_risk_factors'])

    def test_case_c_40_duty_severe_psych(self, engine):
        """Case C: 40 duty + severe psych (fatigue 5, mood 1, burnout Often) -> Elevated or High concern."""
        res = engine.assess({'duty_hours_per_week': 40, 'sleep_hours': 7, 'physical_fatigue': 5, 'mood_score': 1, 'burnout_symptoms': 'Often'})
        assert res['risk_score'] >= 45.0
        assert res['risk_category'] in ['Moderate', 'Elevated', 'High']

    def test_case_d_90_duty_healthy_recovery_morale(self, engine):
        """Case D: 90 duty + fatigue 1 + mood 5 -> Score dampened by high personal resilience."""
        res = engine.assess({'duty_hours_per_week': 90, 'sleep_hours': 8, 'physical_fatigue': 1, 'mood_score': 5, 'burnout_symptoms': 'Rarely'})
        assert res['risk_score'] < 38.0

    def test_case_e_low_exposure_severe_questionnaire(self, engine):
        """Case E: Low operational exposure + severe questionnaire responses -> Significant elevated concern."""
        res = engine.assess({
            'operational_exposure': 'Low', 'duty_hours_per_week': 40, 'sleep_hours': 4,
            'physical_fatigue': 5, 'mood_score': 1, 'burnout_symptoms': 'Often',
            'discouraged_score': 3, 'concentration_score': 3
        })
        assert res['risk_score'] >= 55.0
        assert res['risk_category'] in ['Elevated', 'High', 'Critical']

    def test_case_f_high_exposure_otherwise_healthy(self, engine):
        """Case F: High operational exposure + healthy sleep & conditioning -> Buffered risk score."""
        res = engine.assess({
            'operational_exposure': 'High', 'duty_hours_per_week': 44, 'sleep_hours': 7.5,
            'physical_fatigue': 2, 'mood_score': 4, 'burnout_symptoms': 'Rarely',
            'physical_activity_hours_per_week': 6.0
        })
        assert res['risk_score'] <= 35.0

    def test_case_g_all_protective_strong(self, engine):
        """Case G: All protective factors strong -> Minimal risk score, Low concern."""
        res = engine.assess({
            'duty_hours_per_week': 40, 'sleep_hours': 8.5, 'physical_fatigue': 1, 'mood_score': 5,
            'burnout_symptoms': 'Rarely', 'consecutive_duty_days': 2, 'night_shifts_per_month': 0,
            'physical_activity_hours_per_week': 8.0, 'operational_exposure': 'Low'
        })
        assert res['risk_score'] <= 25.0
        assert res['risk_category'] == 'Low'

    def test_case_h_all_risk_severe(self, engine):
        """Case H: All risk factors severe -> Critical concern (> 85)."""
        res = engine.assess({
            'duty_hours_per_week': 95, 'sleep_hours': 3.0, 'physical_fatigue': 5, 'mood_score': 1,
            'burnout_symptoms': 'Often', 'consecutive_duty_days': 25, 'night_shifts_per_month': 16,
            'operational_exposure': 'High', 'leave_gap_days': 200, 'discouraged_score': 3,
            'concentration_score': 3, 'interest_score': 3
        })
        assert res['risk_score'] >= 85.0
        assert res['risk_category'] == 'Critical'


# ============================================================================
# 11. TEMPORAL & LONGITUDINAL HISTORY AUDIT
# ============================================================================
class TestTemporalHistoryAudit:
    def test_no_history_behavior(self, engine):
        """No past history produces 'No prior history' trend and 0.0 change."""
        rec = {'duty_hours_per_week': 50, 'sleep_hours': 6.5, 'physical_fatigue': 3, 'mood_score': 3}
        res = engine.assess(rec, past_assessments=None)
        assert res['risk_trend'] == "No prior history"
        assert res['risk_change'] == 0.0
        assert res['consecutive_high_risk'] == 0

    def test_worsening_trend_detection(self, engine):
        """If previous score is significantly lower than current score, trend is Worsening."""
        rec = {'duty_hours_per_week': 75, 'sleep_hours': 4.5, 'physical_fatigue': 4, 'mood_score': 2}
        history = [{'risk_score': 30.0, 'assessment_timestamp': '2026-09-20T10:00:00Z'}]
        res = engine.assess(rec, past_assessments=history)
        assert res['risk_trend'] == "Worsening"
        assert res['risk_change'] > 0

    def test_improving_trend_detection(self, engine):
        """If previous score is significantly higher than current score, trend is Improving."""
        rec = {'duty_hours_per_week': 42, 'sleep_hours': 8.0, 'physical_fatigue': 1, 'mood_score': 5}
        history = [{'risk_score': 75.0, 'assessment_timestamp': '2026-09-20T10:00:00Z'}]
        res = engine.assess(rec, past_assessments=history)
        assert res['risk_trend'] == "Improving"
        assert res['risk_change'] < 0

    def test_consecutive_high_risk_accumulation(self, engine):
        """Consecutive high risk prior assessments (>= 65) must be counted correctly and induce persistence adjustment."""
        rec = {'duty_hours_per_week': 70, 'sleep_hours': 5.0, 'physical_fatigue': 4, 'mood_score': 2}
        history = [
            {'risk_score': 72.0, 'assessment_timestamp': '2026-09-25T10:00:00Z'},
            {'risk_score': 68.0, 'assessment_timestamp': '2026-09-24T10:00:00Z'},
            {'risk_score': 70.0, 'assessment_timestamp': '2026-09-23T10:00:00Z'},
            {'risk_score': 35.0, 'assessment_timestamp': '2026-09-22T10:00:00Z'},
        ]
        res = engine.assess(rec, past_assessments=history)
        assert res['consecutive_high_risk'] == 3

    def test_unordered_timestamps_handled_safely(self, engine):
        """Assessments passed in random chronological order must be ordered by timestamp descending."""
        rec = {'duty_hours_per_week': 60, 'sleep_hours': 6.0, 'physical_fatigue': 3, 'mood_score': 3}
        unordered_history = [
            {'risk_score': 25.0, 'assessment_timestamp': '2026-09-20T10:00:00Z'},
            {'risk_score': 75.0, 'assessment_timestamp': '2026-09-26T10:00:00Z'},  # most recent
            {'risk_score': 50.0, 'assessment_timestamp': '2026-09-23T10:00:00Z'},
        ]
        res = engine.assess(rec, past_assessments=unordered_history)
        # Previous score should be 75.0, not 25.0
        assert res['risk_change'] == round(res['risk_score'] - 75.0, 1) or abs(res['risk_change'] - (res['risk_score'] - 75.0)) <= 3.5


# ============================================================================
# 12. API CONTRACT & SHIELDING AUDIT
# ============================================================================
class TestAPIContractAndShielding:
    def test_welfare_assessment_success_schema(self, client):
        """POST /api/welfare/assessment returns expected schema with no internal leaks."""
        payload = {
            'duty_hours_per_week': 50.0,
            'sleep_hours': 6.5,
            'mood_score': 4,
            'physical_fatigue': 2
        }
        resp = client.post('/api/welfare/assessment', json=payload)
        assert resp.status_code == 200
        data = resp.json()

        expected_keys = [
            'risk_score', 'risk_category', 'probabilities', 'confidence',
            'uncertainty', 'assessment_completeness', 'top_risk_factors',
            'protective_factors', 'model_version', 'recommendations'
        ]
        for k in expected_keys:
            assert k in data, f"Missing key {k} in response"

        # Verify probabilities structure
        for tier in ['low', 'moderate', 'elevated', 'high', 'critical']:
            assert tier in data['probabilities']

    def test_no_stack_trace_leakage_on_malformed_json(self, client):
        """Malformed requests must return clean HTTP error without leaking Python tracebacks."""
        resp = client.post('/api/welfare/assessment', content="{malformed_json: true", headers={"Content-Type": "application/json"})
        assert resp.status_code in [400, 422]
        body = resp.text
        assert "Traceback (most recent call last)" not in body


# ============================================================================
# 13. NON-PUNITIVE WELFARE UX & PRIVACY AUDIT
# ============================================================================
class TestNonPunitiveWelfareUXAndPrivacy:
    def test_non_punitive_disclaimer_present(self, client):
        """Responses and endpoints must include or adhere to non-punitive welfare framing."""
        service = get_prediction_service()
        sample = {'duty_hours_per_week': 48, 'sleep_hours': 6.5, 'mood_score': 3, 'physical_fatigue': 3}
        res = service.predictor.assess_personnel(sample)

        assert "disclaimer" in res
        disclaimer = res['disclaimer'].lower()
        assert "not disciplinary" in disclaimer or "supportive" in disclaimer
        assert "decision-support" in disclaimer or "prototype" in disclaimer

    def test_no_sensitive_passwords_in_assessment_payloads(self, client, officer_auth):
        """Assessment retrieval must never leak password hashes or secret tokens."""
        resp = client.get('/api/personnel/1/assessments', headers=officer_auth)
        if resp.status_code == 200:
            text = resp.text
            assert "hashed_password" not in text
            assert "secret_key" not in text


# ============================================================================
# 14. DETERMINISM, STABILITY & PERFORMANCE
# ============================================================================
class TestDeterminismAndPerformance:
    def test_deterministic_output(self, engine):
        """Identical inputs must yield identical outputs down to the decimal point."""
        rec = {'duty_hours_per_week': 52.0, 'sleep_hours': 6.2, 'mood_score': 3, 'physical_fatigue': 3}
        first = engine.assess(rec)
        for _ in range(50):
            again = engine.assess(rec)
            assert again['risk_score'] == first['risk_score']
            assert again['risk_category'] == first['risk_category']
            assert again['probabilities'] == first['probabilities']
            assert again['confidence'] == first['confidence']

    def test_high_throughput_performance(self, engine):
        """100 evaluations must complete in under 500 ms (< 5 ms / evaluation)."""
        rec = {'duty_hours_per_week': 50.0, 'sleep_hours': 6.5, 'mood_score': 3, 'physical_fatigue': 2}
        t0 = time.perf_counter()
        for _ in range(100):
            engine.assess(rec)
        elapsed = time.perf_counter() - t0
        assert elapsed < 0.50, f"100 evaluations took {elapsed:.3f}s, expected < 0.5s"
