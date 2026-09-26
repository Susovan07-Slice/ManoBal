import os
import sys
import unittest
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.risk_scoring import (
    calculate_risk_score,
    compute_operational_severity,
    extract_operational_risk_factors,
    SAFETY_GUARD_FLOOR,
    WEIGHT_ML,
    WEIGHT_SEVERITY
)
from src.prediction import get_welfare_service, predict_welfare


class TestPhase25RiskEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize welfare service
        cls.service = get_welfare_service()

    def test_a_extreme_high_risk_scenario(self):
        """
        Test A — Extreme High Risk Scenario:
        Duty Hours = 65, Consec Days = 18, Night Shifts = 12, Sleep = 4.0,
        Physical Activity = 1.5, Operational Exposure = High, Remote Posting = Yes,
        Mood = 1, Burnout = Often.
        Expected: Risk Score >= 85, Tier = Priority, Stress Level = High.
        """
        record = {
            'Age': 24,
            'Experience_Years': 2,
            'Rank': 'Constable',
            'Duty_Hours_Per_Week': 65.0,
            'Working_Hours_per_Week': 65.0,
            'Consecutive_Duty_Days': 18.0,
            'Night_Shifts_Per_Month': 12.0,
            'Sleep_Hours': 4.0,
            'Physical_Activity_Hours_per_Week': 1.5,
            'Operational_Exposure': 'High',
            'Remote_Posting': 'Yes',
            'JobSatisfaction': 1.0,
            'mood_score': 1.0,
            'Burnout_Symptoms': 'Often',
            'Leave_Gap_Days': 130.0,
            'Overtime_Hours': 20.0
        }

        # Test calculation directly
        probas = {'Low': 0.80, 'Medium': 0.15, 'High': 0.05} # Simulating ML model predicting Low for junior rank
        score, level, priority = calculate_risk_score(probas, 'Low', record)

        self.assertGreaterEqual(score, 85, f"Expected extreme risk score >= 85, got {score}")
        self.assertEqual(priority, 'Priority')
        self.assertEqual(level, 'High')

        # Test factors extraction
        factors = extract_operational_risk_factors(record)
        self.assertTrue(any('workload' in f.lower() for f in factors), "Should flag duty workload")
        self.assertTrue(any('sleep' in f.lower() for f in factors), "Should flag sleep deficit")
        self.assertTrue(any('night' in f.lower() for f in factors), "Should flag night shifts")
        self.assertTrue(any('consecutive' in f.lower() for f in factors), "Should flag consecutive duty")

    def test_b_normal_routine_scenario(self):
        """
        Test B — Normal / Routine Scenario:
        Duty Hours = 40, Consec Days = 4, Night Shifts = 2, Sleep = 7.5,
        Physical Activity = 6.0, Operational Exposure = Low, Remote Posting = No,
        Mood = 5, Burnout = Rarely.
        Expected: Risk Score < 40, Tier = Routine, Stress Level = Low.
        """
        record = {
            'Age': 32,
            'Experience_Years': 8,
            'Rank': 'Head Constable',
            'Duty_Hours_Per_Week': 40.0,
            'Working_Hours_per_Week': 40.0,
            'Consecutive_Duty_Days': 4.0,
            'Night_Shifts_Per_Month': 2.0,
            'Sleep_Hours': 7.5,
            'Physical_Activity_Hours_per_Week': 6.0,
            'Operational_Exposure': 'Low',
            'Remote_Posting': 'No',
            'JobSatisfaction': 5.0,
            'mood_score': 5.0,
            'Burnout_Symptoms': 'Rarely',
            'Leave_Gap_Days': 20.0,
            'Overtime_Hours': 0.0
        }

        probas = {'Low': 0.90, 'Medium': 0.08, 'High': 0.02}
        score, level, priority = calculate_risk_score(probas, 'Low', record)

        self.assertLess(score, 40, f"Expected routine score < 40, got {score}")
        self.assertEqual(priority, 'Routine')
        self.assertEqual(level, 'Low')

    def test_c_moderate_preventive_scenario(self):
        """
        Test C — Moderate / Preventive Scenario:
        Intermediate values across duty, sleep, and recovery.
        Expected: 40 <= Risk Score < 70, Tier = Preventive, Stress Level = Medium.
        """
        record = {
            'Age': 29,
            'Experience_Years': 5,
            'Rank': 'Constable',
            'Duty_Hours_Per_Week': 52.0,
            'Working_Hours_per_Week': 52.0,
            'Consecutive_Duty_Days': 8.0,
            'Night_Shifts_Per_Month': 5.0,
            'Sleep_Hours': 6.0,
            'Physical_Activity_Hours_per_Week': 3.0,
            'Operational_Exposure': 'Medium',
            'Remote_Posting': 'No',
            'JobSatisfaction': 3.0,
            'mood_score': 3.0,
            'Burnout_Symptoms': 'Sometimes',
            'Leave_Gap_Days': 65.0,
            'Overtime_Hours': 8.0
        }

        probas = {'Low': 0.35, 'Medium': 0.50, 'High': 0.15}
        score, level, priority = calculate_risk_score(probas, 'Medium', record)

        self.assertTrue(40 <= score < 70, f"Expected preventive score in [40, 70), got {score}")
        self.assertEqual(priority, 'Preventive')
        self.assertEqual(level, 'Medium')

    def test_d_feature_directionality_monotonicity(self):
        """
        Test D — Directionality Monotonicity:
        Adverse changes in individual features MUST strictly increase or maintain risk score,
        never decreasing risk score.
        """
        base_record = {
            'Age': 30,
            'Experience_Years': 6,
            'Rank': 'Constable',
            'Duty_Hours_Per_Week': 44.0,
            'Working_Hours_per_Week': 44.0,
            'Consecutive_Duty_Days': 5.0,
            'Night_Shifts_Per_Month': 3.0,
            'Sleep_Hours': 7.0,
            'Physical_Activity_Hours_per_Week': 4.0,
            'Operational_Exposure': 'Low',
            'Remote_Posting': 'No',
            'JobSatisfaction': 4.0,
            'mood_score': 4.0,
            'Burnout_Symptoms': 'Rarely',
            'Leave_Gap_Days': 30.0
        }
        probas = {'Low': 0.70, 'Medium': 0.25, 'High': 0.05}
        base_score, _, _ = calculate_risk_score(probas, 'Low', base_record)

        # 1. Sleep: 7.0 -> 4.0 (less sleep -> higher risk)
        rec_sleep = dict(base_record, Sleep_Hours=4.0)
        score_sleep, _, _ = calculate_risk_score(probas, 'Low', rec_sleep)
        self.assertGreater(score_sleep, base_score, f"Less sleep should increase risk: {score_sleep} vs {base_score}")

        # 2. Duty Hours: 44.0 -> 65.0 (higher duty -> higher risk)
        rec_duty = dict(base_record, Duty_Hours_Per_Week=65.0, Working_Hours_per_Week=65.0)
        score_duty, _, _ = calculate_risk_score(probas, 'Low', rec_duty)
        self.assertGreater(score_duty, base_score, f"Higher duty hours should increase risk: {score_duty} vs {base_score}")

        # 3. Night Shifts: 3.0 -> 12.0 (more night shifts -> higher risk)
        rec_night = dict(base_record, Night_Shifts_Per_Month=12.0)
        score_night, _, _ = calculate_risk_score(probas, 'Low', rec_night)
        self.assertGreater(score_night, base_score, f"More night shifts should increase risk: {score_night} vs {base_score}")

        # 4. Mood: 4.0 -> 1.0 (poorer mood -> higher risk)
        rec_mood = dict(base_record, JobSatisfaction=1.0, mood_score=1.0)
        score_mood, _, _ = calculate_risk_score(probas, 'Low', rec_mood)
        self.assertGreater(score_mood, base_score, f"Lower mood score should increase risk: {score_mood} vs {base_score}")

        # 5. Consecutive Days: 5.0 -> 18.0 (more consecutive days -> higher risk)
        rec_consec = dict(base_record, Consecutive_Duty_Days=18.0)
        score_consec, _, _ = calculate_risk_score(probas, 'Low', rec_consec)
        self.assertGreater(score_consec, base_score, f"More consecutive duty days should increase risk: {score_consec} vs {base_score}")

        # 6. Burnout: Rarely -> Often (more burnout symptoms -> higher risk)
        rec_burnout = dict(base_record, Burnout_Symptoms='Often')
        score_burnout, _, _ = calculate_risk_score(probas, 'Low', rec_burnout)
        self.assertGreater(score_burnout, base_score, f"Burnout symptoms should increase risk: {score_burnout} vs {base_score}")

    def test_e_regression_bug_14_score(self):
        """
        Test E — Regression Test for the 14-Score Bug:
        Ensures the extreme adverse assessment can NEVER produce 14 / Low / Routine.
        """
        extreme_record = {
            'Duty_Hours_Per_Week': 65.0,
            'Consecutive_Duty_Days': 18.0,
            'Night_Shifts_Per_Month': 12.0,
            'Sleep_Hours': 4.0,
            'Physical_Activity_Hours_per_Week': 1.5,
            'Operational_Exposure': 'High',
            'Remote_Posting': 'Yes',
            'JobSatisfaction': 1.0,
            'Burnout_Symptoms': 'Often'
        }
        # Even if LightGBM erroneously predicted 95% Low
        erroneous_probas = {'Low': 0.95, 'Medium': 0.04, 'High': 0.01}
        score, level, priority = calculate_risk_score(erroneous_probas, 'Low', extreme_record)

        self.assertNotEqual(score, 14, "Regression: Risk score must NOT be 14!")
        self.assertGreaterEqual(score, 85, f"Risk score must be at least 85, was {score}")
        self.assertEqual(priority, 'Priority')
        self.assertEqual(level, 'High')

    def test_f_end_to_end_predict_welfare_extreme(self):
        """
        Test F — End-to-End Pipeline Evaluation on Extreme Input:
        Runs through predict_welfare() end-to-end with the LightGBM model, explainability,
        and recommendation engine.
        """
        from schemas.prediction import PredictionRequest

        req = PredictionRequest(
            age=25,
            gender='Male',
            department='Operations',
            experience_years=3.0,
            working_hours_per_week=65.0,
            duty_hours_per_week=65.0,
            consecutive_duty_days=18,
            night_shifts_per_month=12,
            sleep_hours=4.0,
            physical_activity_hours_per_week=1.5,
            operational_exposure='High',
            remote_posting='Yes',
            job_satisfaction=1,
            burnout_symptoms='Often',
            leave_gap_days=140,
            annual_leaves_taken=5
        )
        df_extreme = pd.DataFrame([req.to_dataframe_dict()])

        result = predict_welfare(df_extreme)

        self.assertGreaterEqual(result['risk_score'], 85)
        self.assertEqual(result['stress_level'], 'High')
        self.assertEqual(result['risk_priority'], 'Priority')
        self.assertGreater(len(result['key_factors']), 0)
        self.assertGreater(len(result['recommendations']), 0)
        # Verify supportive, non-punitive recommendations
        for rec in result['recommendations']:
            self.assertFalse('punitive' in rec.lower())
            self.assertFalse('disciplinary' in rec.lower())


if __name__ == '__main__':
    unittest.main()
