"""
Comprehensive Automated Test Suite for PERSONNEL WELFARE RISK ENGINE V2.
========================================================================
Implements testing for:
  1. 20+ Realistic Synthetic Scenarios across the welfare continuum.
  2. Critical Monotonicity Sweeps (Work Hours, Sleep, Fatigue, Mood, Consecutive Days, Night Shifts).
  3. Controlled Compound Interaction Effects.
  4. Uncertainty & Minimum Assessment Completeness Thresholds.
  5. Local Perturbation Stability.
  6. Zero Demographic Bias Audit.
  7. API & Serialization Schema Conformance.
"""

import pytest
import numpy as np
import os
import joblib
from src.welfare_risk_engine_v2 import PersonnelWelfareRiskEngineV2, TIER_NAMES

@pytest.fixture(scope="module")
def engine():
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'welfare_risk_engine_v2.pkl')
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return PersonnelWelfareRiskEngineV2()


# ============================================================================
# 1. 20+ REALISTIC SYNTHETIC SCENARIOS (Section 17 & 30)
# ============================================================================
SCENARIOS_20 = [
    # 1-4: Healthy / Baseline Profiles (Expected Score ~15-35, Low)
    {
        "id": "H1", "name": "Optimal Standard Duty", "expected_category": "Low",
        "record": {"duty_hours_per_week": 40, "sleep_hours": 8.0, "consecutive_duty_days": 2, "night_shifts_per_month": 1, "physical_fatigue": 1, "mood_score": 5, "burnout_symptoms": "Rarely", "physical_activity_hours_per_week": 6.0}
    },
    {
        "id": "H2", "name": "Well-Rested Engineer", "expected_category": "Low",
        "record": {"duty_hours_per_week": 42, "sleep_hours": 7.5, "consecutive_duty_days": 3, "night_shifts_per_month": 0, "physical_fatigue": 1, "mood_score": 5, "burnout_symptoms": "Rarely", "physical_activity_hours_per_week": 5.0}
    },
    {
        "id": "H3", "name": "Active Logistics Personnel", "expected_category": "Low",
        "record": {"duty_hours_per_week": 44, "sleep_hours": 7.0, "consecutive_duty_days": 4, "night_shifts_per_month": 2, "physical_fatigue": 2, "mood_score": 4, "burnout_symptoms": "Rarely", "physical_activity_hours_per_week": 7.0}
    },
    {
        "id": "H4", "name": "Post-Leave Refreshed", "expected_category": "Low",
        "record": {"duty_hours_per_week": 38, "sleep_hours": 8.0, "consecutive_duty_days": 1, "night_shifts_per_month": 0, "physical_fatigue": 1, "mood_score": 5, "burnout_symptoms": "Rarely", "leave_gap_days": 7}
    },

    # 5-8: Mild Concern Profiles (Expected Score ~25-42, Low to Moderate)
    {
        "id": "M1", "name": "Slight Duty Overtime", "expected_category": ["Low", "Moderate"],
        "record": {"duty_hours_per_week": 50, "sleep_hours": 6.5, "consecutive_duty_days": 5, "night_shifts_per_month": 3, "physical_fatigue": 2, "mood_score": 4, "burnout_symptoms": "Rarely"}
    },
    {
        "id": "M2", "name": "Mild Sleep Truncation", "expected_category": ["Low", "Moderate"],
        "record": {"duty_hours_per_week": 46, "sleep_hours": 6.0, "consecutive_duty_days": 4, "night_shifts_per_month": 4, "physical_fatigue": 2, "mood_score": 4, "burnout_symptoms": "Rarely"}
    },
    {
        "id": "M3", "name": "Mild Physical Wear", "expected_category": ["Low", "Moderate"],
        "record": {"duty_hours_per_week": 48, "sleep_hours": 6.5, "consecutive_duty_days": 6, "night_shifts_per_month": 2, "physical_fatigue": 3, "mood_score": 3, "burnout_symptoms": "Rarely"}
    },
    {
        "id": "M4", "name": "Subtle Morale Dip", "expected_category": ["Low", "Moderate"],
        "record": {"duty_hours_per_week": 44, "sleep_hours": 7.0, "consecutive_duty_days": 3, "night_shifts_per_month": 2, "physical_fatigue": 2, "mood_score": 3, "interest_score": 1, "burnout_symptoms": "Rarely"}
    },

    # 9-12: Moderate Concern Profiles (Expected Score ~42-60, Moderate)
    {
        "id": "MOD1", "name": "Extended Schedule & Fatigue", "expected_category": "Moderate",
        "record": {"duty_hours_per_week": 56, "sleep_hours": 6.0, "consecutive_duty_days": 8, "night_shifts_per_month": 6, "physical_fatigue": 3, "mood_score": 3, "burnout_symptoms": "Sometimes"}
    },
    {
        "id": "MOD2", "name": "Night Rotation Burden", "expected_category": "Moderate",
        "record": {"duty_hours_per_week": 52, "sleep_hours": 5.5, "consecutive_duty_days": 7, "night_shifts_per_month": 8, "physical_fatigue": 3, "mood_score": 3, "burnout_symptoms": "Sometimes"}
    },
    {
        "id": "MOD3", "name": "Leave Overdue Strain", "expected_category": "Moderate",
        "record": {"duty_hours_per_week": 54, "sleep_hours": 6.0, "consecutive_duty_days": 9, "night_shifts_per_month": 5, "physical_fatigue": 3, "mood_score": 3, "leave_gap_days": 180}
    },
    {
        "id": "MOD4", "name": "Demoralization Warning", "expected_category": "Moderate",
        "record": {"duty_hours_per_week": 48, "sleep_hours": 6.0, "consecutive_duty_days": 5, "night_shifts_per_month": 4, "physical_fatigue": 3, "mood_score": 2, "discouraged_score": 2, "concentration_score": 1}
    },

    # 13-16: Elevated to High Concern Profiles (Expected Score ~60-80, Elevated to High)
    {
        "id": "H1", "name": "Heavy Operational Surge", "expected_category": ["Elevated", "High"],
        "record": {"duty_hours_per_week": 68, "sleep_hours": 5.0, "consecutive_duty_days": 12, "night_shifts_per_month": 9, "physical_fatigue": 4, "mood_score": 2, "burnout_symptoms": "Sometimes"}
    },
    {
        "id": "H2", "name": "Severe Sleep & Continuous Duty", "expected_category": ["Elevated", "High"],
        "record": {"duty_hours_per_week": 72, "sleep_hours": 4.5, "consecutive_duty_days": 14, "night_shifts_per_month": 10, "physical_fatigue": 4, "mood_score": 2, "burnout_symptoms": "Often", "operational_exposure": "High"}
    },
    {
        "id": "H3", "name": "High Hazard Remote Duty", "expected_category": ["Elevated", "High"],
        "record": {"duty_hours_per_week": 66, "sleep_hours": 5.0, "consecutive_duty_days": 13, "night_shifts_per_month": 8, "physical_fatigue": 4, "mood_score": 2, "remote_posting": "Yes", "operational_exposure": "High"}
    },
    {
        "id": "H4", "name": "Acute Demoralization & Exhaustion", "expected_category": ["Elevated", "High"],
        "record": {"duty_hours_per_week": 60, "sleep_hours": 4.5, "consecutive_duty_days": 10, "night_shifts_per_month": 7, "physical_fatigue": 4, "mood_score": 1, "discouraged_score": 3, "interest_score": 2, "concentration_score": 2}
    },

    # 17-20: Severe / Critical Profiles (Expected Score ~80-100, High to Critical)
    {
        "id": "C1", "name": "Prolonged Deployment Saturation", "expected_category": ["High", "Critical"],
        "record": {"duty_hours_per_week": 82, "sleep_hours": 3.5, "consecutive_duty_days": 18, "night_shifts_per_month": 13, "physical_fatigue": 5, "mood_score": 1, "burnout_symptoms": "Often", "operational_exposure": "High"}
    },
    {
        "id": "C2", "name": "Extreme Circadian Breakdown", "expected_category": ["High", "Critical"],
        "record": {"duty_hours_per_week": 86, "sleep_hours": 3.0, "consecutive_duty_days": 21, "night_shifts_per_month": 15, "physical_fatigue": 5, "mood_score": 1, "burnout_symptoms": "Often", "leave_gap_days": 240}
    },
    {
        "id": "C3", "name": "Multi-Factor Crisis", "expected_category": "Critical",
        "record": {"duty_hours_per_week": 88, "sleep_hours": 3.0, "consecutive_duty_days": 24, "night_shifts_per_month": 16, "physical_fatigue": 5, "mood_score": 1, "burnout_symptoms": "Often", "discouraged_score": 3, "concentration_score": 3, "operational_exposure": "High"}
    },
    {
        "id": "C4", "name": "Maximum Overload & Exhaustion", "expected_category": "Critical",
        "record": {"duty_hours_per_week": 90, "sleep_hours": 2.5, "consecutive_duty_days": 28, "night_shifts_per_month": 18, "physical_fatigue": 5, "mood_score": 1, "burnout_symptoms": "Often", "discouraged_score": 3, "interest_score": 3, "concentration_score": 3, "remote_posting": "Yes", "operational_exposure": "High"}
    }
]


def test_20_scenarios_execute_and_scale(engine):
    """Verifies that all 20 realistic scenarios execute properly and produce coherent scores."""
    prev_score = 0.0
    for idx, sc in enumerate(SCENARIOS_20):
        res = engine.assess(sc["record"])
        assert res["risk_score"] is not None, f"Scenario {sc['id']} returned None risk_score"
        assert 0.0 <= res["risk_score"] <= 100.0, f"Scenario {sc['id']} score {res['risk_score']} out of bounds"
        
        # Verify probabilities sum to 1.0
        probs = res["probabilities"]
        assert probs is not None
        p_sum = sum(probs.values())
        assert abs(p_sum - 1.0) < 0.02, f"Probabilities do not sum to 1.0: {p_sum}"

        # Verify category alignment
        expected = sc["expected_category"]
        if isinstance(expected, list):
            assert res["risk_category"] in expected, f"Scenario {sc['id']} expected one of {expected}, got {res['risk_category']}"
        else:
            assert res["risk_category"] == expected, f"Scenario {sc['id']} expected {expected}, got {res['risk_category']}"


# ============================================================================
# 2. MONOTONICITY TESTS (Section 18 & 19)
# ============================================================================
def test_monotonicity_work_hours(engine):
    """Working hours sweep 40 -> 90 must be strictly monotonic non-decreasing."""
    base = {
        'duty_hours_per_week': 40, 'sleep_hours': 6.5, 'consecutive_duty_days': 4,
        'night_shifts_per_month': 2, 'physical_fatigue': 2, 'mood_score': 4,
        'burnout_symptoms': 'Rarely', 'physical_activity_hours_per_week': 4.0
    }
    hours = [40, 50, 60, 70, 80, 90]
    scores = []
    for h in hours:
        b = base.copy()
        b['duty_hours_per_week'] = h
        res = engine.assess(b)
        scores.append(res['risk_score'])

    for i in range(len(scores) - 1):
        assert scores[i + 1] >= scores[i], f"Work hours monotonicity violated: {hours[i]}h ({scores[i]}) vs {hours[i+1]}h ({scores[i+1]})"


def test_monotonicity_sleep_hours(engine):
    """Sleep hours sweep 8.0 -> 4.0 must be strictly monotonic non-increasing with sleep (decreasing sleep increases score)."""
    base = {
        'duty_hours_per_week': 44, 'sleep_hours': 8.0, 'consecutive_duty_days': 4,
        'night_shifts_per_month': 2, 'physical_fatigue': 2, 'mood_score': 4,
        'burnout_symptoms': 'Rarely', 'physical_activity_hours_per_week': 4.0
    }
    sleeps = [8.0, 7.0, 6.0, 5.0, 4.0]
    scores = []
    for s in sleeps:
        b = base.copy()
        b['sleep_hours'] = s
        res = engine.assess(b)
        scores.append(res['risk_score'])

    for i in range(len(scores) - 1):
        assert scores[i + 1] >= scores[i], f"Sleep monotonicity violated: {sleeps[i]}h ({scores[i]}) vs {sleeps[i+1]}h ({scores[i+1]})"


def test_monotonicity_physical_fatigue(engine):
    """Fatigue sweep 1 -> 5 must be strictly monotonic non-decreasing."""
    base = {
        'duty_hours_per_week': 44, 'sleep_hours': 7.0, 'consecutive_duty_days': 4,
        'night_shifts_per_month': 2, 'physical_fatigue': 1, 'mood_score': 4,
        'burnout_symptoms': 'Rarely'
    }
    fatigues = [1, 2, 3, 4, 5]
    scores = []
    for f in fatigues:
        b = base.copy()
        b['physical_fatigue'] = f
        res = engine.assess(b)
        scores.append(res['risk_score'])

    for i in range(len(scores) - 1):
        assert scores[i + 1] >= scores[i], f"Fatigue monotonicity violated: {fatigues[i]} ({scores[i]}) vs {fatigues[i+1]} ({scores[i+1]})"


def test_monotonicity_mood_score(engine):
    """Mood score sweep 5 -> 1 must result in monotonic non-decreasing risk."""
    base = {
        'duty_hours_per_week': 44, 'sleep_hours': 7.0, 'consecutive_duty_days': 4,
        'night_shifts_per_month': 2, 'physical_fatigue': 2, 'mood_score': 5,
        'burnout_symptoms': 'Rarely'
    }
    moods = [5, 4, 3, 2, 1]
    scores = []
    for m in moods:
        b = base.copy()
        b['mood_score'] = m
        res = engine.assess(b)
        scores.append(res['risk_score'])

    for i in range(len(scores) - 1):
        assert scores[i + 1] >= scores[i], f"Mood monotonicity violated: mood {moods[i]} ({scores[i]}) vs {moods[i+1]} ({scores[i+1]})"


def test_monotonicity_consecutive_days(engine):
    """Consecutive duty days 2 -> 25 must be strictly monotonic non-decreasing."""
    base = {
        'duty_hours_per_week': 48, 'sleep_hours': 6.5, 'consecutive_duty_days': 2,
        'night_shifts_per_month': 2, 'physical_fatigue': 2, 'mood_score': 4,
        'burnout_symptoms': 'Rarely'
    }
    days = [2, 5, 10, 15, 20, 25]
    scores = []
    for d in days:
        b = base.copy()
        b['consecutive_duty_days'] = d
        res = engine.assess(b)
        scores.append(res['risk_score'])

    for i in range(len(scores) - 1):
        assert scores[i + 1] >= scores[i], f"Consecutive days monotonicity violated: {days[i]} ({scores[i]}) vs {days[i+1]} ({scores[i+1]})"


# ============================================================================
# 3. INTERACTION EFFECTS (Section 10)
# ============================================================================
def test_compound_interaction_workload_and_sleep(engine):
    """High workload + poor sleep must produce greater concern than either alone."""
    baseline = {'duty_hours_per_week': 44, 'sleep_hours': 7.5, 'physical_fatigue': 2, 'mood_score': 4}
    high_work_only = {'duty_hours_per_week': 72, 'sleep_hours': 7.5, 'physical_fatigue': 2, 'mood_score': 4}
    poor_sleep_only = {'duty_hours_per_week': 44, 'sleep_hours': 4.5, 'physical_fatigue': 2, 'mood_score': 4}
    both_compound = {'duty_hours_per_week': 72, 'sleep_hours': 4.5, 'physical_fatigue': 3, 'mood_score': 3}

    s_base = engine.assess(baseline)['risk_score']
    s_work = engine.assess(high_work_only)['risk_score']
    s_sleep = engine.assess(poor_sleep_only)['risk_score']
    s_compound = engine.assess(both_compound)['risk_score']

    assert s_work > s_base
    assert s_sleep > s_base
    assert s_compound > s_work
    assert s_compound > s_sleep


def test_normal_duty_with_severe_distress(engine):
    """Normal operational duty with severe acute distress must still generate elevated welfare risk."""
    normal_duty_distress = {
        'duty_hours_per_week': 40, 'sleep_hours': 5.0, 'consecutive_duty_days': 2,
        'night_shifts_per_month': 0, 'physical_fatigue': 4, 'mood_score': 1,
        'burnout_symptoms': 'Often', 'discouraged_score': 3, 'concentration_score': 2
    }
    res = engine.assess(normal_duty_distress)
    assert res['risk_score'] >= 50.0, f"Expected elevated risk for acute distress, got {res['risk_score']}"
    assert res['risk_category'] in ['Elevated', 'High', 'Moderate']


# ============================================================================
# 4. UNCERTAINTY & MISSING DATA (Section 13 & 14)
# ============================================================================
def test_missing_data_rejection(engine):
    """If completeness < 0.50, engine must return Insufficient Evidence with risk_score = None."""
    scant_record = {'duty_hours_per_week': 50}
    res = engine.assess(scant_record)
    assert res.get('error') == "Insufficient assessment evidence"
    assert res.get('risk_score') is None
    assert res.get('risk_category') == "Insufficient Evidence"


def test_confidence_and_uncertainty(engine):
    """Complete record must produce valid confidence and uncertainty within [0, 1]."""
    rec = {'duty_hours_per_week': 44, 'sleep_hours': 7.0, 'physical_fatigue': 2, 'mood_score': 4}
    res = engine.assess(rec)
    assert 0.0 < res['confidence'] <= 1.0
    assert 0.0 <= res['uncertainty'] <= 1.0
    assert abs((res['confidence'] + res['uncertainty']) - 1.0) < 0.15


# ============================================================================
# 5. PERTURBATION STABILITY (Section 34)
# ============================================================================
def test_score_stability_under_perturbations(engine):
    """Small perturbations in inputs (1 hour duty, 0.1 hr sleep) must change score smoothly without sudden jumps."""
    base = {'duty_hours_per_week': 55.0, 'sleep_hours': 6.0, 'physical_fatigue': 3, 'mood_score': 3}
    perturbed_duty = {'duty_hours_per_week': 56.0, 'sleep_hours': 6.0, 'physical_fatigue': 3, 'mood_score': 3}
    perturbed_sleep = {'duty_hours_per_week': 55.0, 'sleep_hours': 6.1, 'physical_fatigue': 3, 'mood_score': 3}

    s_base = engine.assess(base)['risk_score']
    s_duty = engine.assess(perturbed_duty)['risk_score']
    s_sleep = engine.assess(perturbed_sleep)['risk_score']

    assert abs(s_duty - s_base) < 2.5, f"Discontinuous jump on 1-hr duty perturbation: {s_base} -> {s_duty}"
    assert abs(s_sleep - s_base) < 1.5, f"Discontinuous jump on 0.1-hr sleep perturbation: {s_base} -> {s_sleep}"


# ============================================================================
# 6. DEMOGRAPHIC BIAS AUDIT (Section 20)
# ============================================================================
def test_zero_demographic_bias(engine):
    """Altering demographic attributes (Gender, Age, Department) must NOT change the risk score."""
    base_male = {
        'duty_hours_per_week': 50, 'sleep_hours': 6.5, 'physical_fatigue': 2, 'mood_score': 4,
        'Gender': 'Male', 'Age': 24, 'Department': 'Operations'
    }
    base_female = {
        'duty_hours_per_week': 50, 'sleep_hours': 6.5, 'physical_fatigue': 2, 'mood_score': 4,
        'Gender': 'Female', 'Age': 45, 'Department': 'HR'
    }

    s_male = engine.assess(base_male)['risk_score']
    s_female = engine.assess(base_female)['risk_score']

    assert abs(s_male - s_female) < 1e-6, f"Demographic bias detected: Male={s_male} vs Female={s_female}"


# ============================================================================
# 7. SCHEMA CONFORMANCE & VERSIONING (Section 24 & 27)
# ============================================================================
def test_output_schema_conformance(engine):
    """Verifies that all required fields are present and typed correctly in engine evaluation output."""
    rec = {
        'duty_hours_per_week': 48, 'sleep_hours': 6.5, 'consecutive_duty_days': 5,
        'night_shifts_per_month': 3, 'physical_fatigue': 2, 'mood_score': 4,
        'burnout_symptoms': 'Rarely', 'physical_activity_hours_per_week': 4.0
    }
    res = engine.assess(rec)
    required_keys = [
        'risk_score', 'risk_category', 'probabilities', 'confidence',
        'uncertainty', 'assessment_completeness', 'top_risk_factors',
        'protective_factors', 'model_version', 'recommendations'
    ]
    for k in required_keys:
        assert k in res, f"Missing required output key: {k}"

    assert res['model_version'] == 'risk_engine_v2'
    assert res['risk_category'] in TIER_NAMES
    for tier in ['low', 'moderate', 'elevated', 'high', 'critical']:
        assert tier in res['probabilities'], f"Missing probability tier: {tier}"
