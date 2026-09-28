import pytest
from datetime import datetime, timezone, timedelta
from db.models.assessment import StressAssessment
from services.longitudinal_analytics_service import LongitudinalAnalyticsService

def _create_assessment(id: int, score: float, category: str, priority: str, days_ago: int, key_factors=None, protective_factors=None):
    if key_factors is None:
        key_factors = []
    if protective_factors is None:
        protective_factors = []
        
    ts = datetime.now(timezone.utc) - timedelta(days=days_ago)
    import json
    kf_str = json.dumps({"top_risk_factors": key_factors, "protective_factors": protective_factors})
    
    # Mock StressAssessment
    a = StressAssessment(
        personnel_id=1,
        stress_level=category,
        risk_score=score,
        risk_priority=priority,
        key_factors=kf_str,
        assessment_timestamp=ts
    )
    a.id = id
    return a


class TestPhase36LongitudinalAnalytics:

    # Basic history
    def test_no_history(self):
        res = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [])
        assert res["history"]["assessment_count"] == 0
        assert res["trend"]["direction"] == "INSUFFICIENT_DATA"
        assert res["history"]["data_sufficiency"] == "INSUFFICIENT_DATA"

    def test_one_assessment(self):
        a1 = _create_assessment(1, 40.0, "Moderate", "Preventive", 0)
        res = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1])
        assert res["history"]["assessment_count"] == 1
        assert res["trend"]["direction"] == "INSUFFICIENT_DATA"
        assert res["history"]["data_sufficiency"] == "INSUFFICIENT_DATA"

    def test_two_assessments(self):
        a1 = _create_assessment(1, 40.0, "Moderate", "Preventive", 1)
        a2 = _create_assessment(2, 50.0, "Moderate", "Preventive", 0)
        res = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1, a2])
        assert res["history"]["assessment_count"] == 2
        assert res["history"]["data_sufficiency"] == "LIMITED_HISTORY"
        assert res["trend"]["direction"] == "WORSENING"

    # Trend
    def test_improving_trend(self):
        a1 = _create_assessment(1, 60.0, "Elevated", "Preventive", 2)
        a2 = _create_assessment(2, 50.0, "Moderate", "Preventive", 1)
        a3 = _create_assessment(3, 40.0, "Moderate", "Routine", 0)
        res = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1, a2, a3])
        assert res["trend"]["direction"] == "IMPROVING"

    def test_stable_trend(self):
        a1 = _create_assessment(1, 40.0, "Moderate", "Routine", 2)
        a2 = _create_assessment(2, 42.0, "Moderate", "Routine", 1)
        a3 = _create_assessment(3, 41.0, "Moderate", "Routine", 0)
        res = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1, a2, a3])
        assert res["trend"]["direction"] == "STABLE"

    def test_worsening_trend(self):
        a1 = _create_assessment(1, 40.0, "Moderate", "Routine", 2)
        a2 = _create_assessment(2, 55.0, "Elevated", "Preventive", 1)
        a3 = _create_assessment(3, 65.0, "Elevated", "Preventive", 0)
        res = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1, a2, a3])
        assert res["trend"]["direction"] == "WORSENING"

    # Category persistence
    def test_repeated_elevated(self):
        a1 = _create_assessment(1, 56.0, "Elevated", "Preventive", 2)
        a2 = _create_assessment(2, 58.0, "Elevated", "Preventive", 1)
        a3 = _create_assessment(3, 60.0, "Elevated", "Preventive", 0)
        res = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1, a2, a3])
        assert res["history"]["persistent_elevated_risk"] is True
        assert res["history"]["consecutive_elevated_assessments"] == 3

    def test_temporary_high(self):
        a1 = _create_assessment(1, 40.0, "Moderate", "Routine", 2)
        a2 = _create_assessment(2, 75.0, "High", "Priority", 1)
        a3 = _create_assessment(3, 45.0, "Moderate", "Routine", 0)
        res = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1, a2, a3])
        assert res["history"]["persistent_elevated_risk"] is False
        assert res["history"]["consecutive_elevated_assessments"] == 0

    def test_progressive_escalation(self):
        a1 = _create_assessment(1, 40.0, "Moderate", "Routine", 3)
        a2 = _create_assessment(2, 56.0, "Elevated", "Preventive", 2)
        a3 = _create_assessment(3, 72.0, "High", "Priority", 1)
        a4 = _create_assessment(4, 86.0, "Critical", "Priority", 0)
        res = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1, a2, a3, a4])
        assert res["history"]["persistent_elevated_risk"] is True
        assert res["history"]["consecutive_elevated_assessments"] == 3

    # Baseline
    def test_personal_baseline(self):
        a1 = _create_assessment(1, 40.0, "Moderate", "Routine", 2)
        a2 = _create_assessment(2, 50.0, "Moderate", "Routine", 1)
        a3 = _create_assessment(3, 60.0, "Elevated", "Preventive", 0)
        res = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1, a2, a3])
        assert res["baseline"]["historical_mean"] == 50.0
        assert res["baseline"]["current_deviation"] == 10.0

    # Robustness
    def test_unordered_timestamps(self):
        a1 = _create_assessment(1, 40.0, "Moderate", "Routine", 0)
        a2 = _create_assessment(2, 50.0, "Moderate", "Routine", 2)
        a3 = _create_assessment(3, 60.0, "Elevated", "Preventive", 1)
        res = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1, a2, a3])
        assert res["current"]["risk_score"] == 40.0  # since days_ago=0 is the latest
        assert res["trend"]["direction"] == "IMPROVING" # from 60 (days_ago=1) to 40 (days_ago=0)

    def test_duplicate_timestamps(self):
        a1 = _create_assessment(1, 40.0, "Moderate", "Routine", 0)
        a2 = _create_assessment(2, 50.0, "Moderate", "Routine", 0)
        res = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1, a2])
        assert res["history"]["assessment_count"] == 2
        # sorted by timestamp, then id. so a2 is the latest.
        assert res["current"]["risk_score"] == 50.0

    def test_missing_timestamps(self):
        a1 = _create_assessment(1, 40.0, "Moderate", "Routine", 0)
        a1.assessment_timestamp = None
        a2 = _create_assessment(2, 50.0, "Moderate", "Routine", 0)
        a2.assessment_timestamp = None
        res = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1, a2])
        assert res["history"]["assessment_count"] == 2
        
    def test_nan_infinite_scores(self):
        a1 = _create_assessment(1, float("nan"), "Moderate", "Routine", 1)
        a2 = _create_assessment(2, float("inf"), "Moderate", "Routine", 0)
        res = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1, a2])
        assert res["history"]["assessment_count"] == 0
        
    # Repeated factors
    def test_repeated_risk_factor(self):
        a1 = _create_assessment(1, 40.0, "Moderate", "Routine", 2, ["Sleep duration concern"])
        a2 = _create_assessment(2, 50.0, "Moderate", "Routine", 1, ["Sleep duration concern"])
        a3 = _create_assessment(3, 60.0, "Elevated", "Preventive", 0, ["Workload concern"])
        res = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1, a2, a3])
        assert len(res["repeated_factors"]) == 1
        assert res["repeated_factors"][0]["factor"] == "Sleep duration concern"
        assert res["repeated_factors"][0]["frequency"] == 2
        
    def test_same_history_deterministic(self):
        a1 = _create_assessment(1, 40.0, "Moderate", "Routine", 2)
        a2 = _create_assessment(2, 50.0, "Moderate", "Routine", 1)
        a3 = _create_assessment(3, 60.0, "Elevated", "Preventive", 0)
        res1 = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1, a2, a3])
        res2 = LongitudinalAnalyticsService.calculate_longitudinal_trend(1, [a1, a2, a3])
        assert res1 == res2
