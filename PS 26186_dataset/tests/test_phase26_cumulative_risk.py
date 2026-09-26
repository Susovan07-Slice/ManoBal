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
    WEIGHT_DETERMINISTIC,
    WEIGHT_ML,
    WEIGHT_DOMAIN_OPERATIONAL,
    WEIGHT_DOMAIN_RECOVERY,
    WEIGHT_DOMAIN_PSYCHOLOGICAL
)
from src.prediction import get_welfare_service, predict_welfare


class TestPhase26CumulativeRisk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = get_welfare_service()

    def test_case_1_normal(self):
        """
        Case 1 — Normal / Routine:
        Duty = 40, Consec = 4, Night = 2, Sleep = 7.5, Activity = 6, Exposure = Low, Mood = 5, Burnout = Rarely.
        Expected: Score < 40, Routine, Low.
        """
        record = {
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
            'Leave_Gap_Days': 20.0
        }
        probas = {'Low': 0.90, 'Medium': 0.08, 'High': 0.02}
        score, level, priority = calculate_risk_score(probas, 'Low', record)

        self.assertLess(score, 40, f"Expected Routine score < 40, got {score}")
        self.assertEqual(priority, 'Routine')
        self.assertEqual(level, 'Low')

    def test_case_2_moderate(self):
        """
        Case 2 — Moderate / Preventive:
        Duty = 50, Consec = 8, Night = 6, Sleep = 6.0, Activity = 3.5, Exposure = Medium, Mood = 3.
        Expected: 40 <= Score < 70, Preventive, Medium.
        """
        record = {
            'Duty_Hours_Per_Week': 50.0,
            'Working_Hours_per_Week': 50.0,
            'Consecutive_Duty_Days': 8.0,
            'Night_Shifts_Per_Month': 6.0,
            'Sleep_Hours': 6.0,
            'Physical_Activity_Hours_per_Week': 3.5,
            'Operational_Exposure': 'Medium',
            'Remote_Posting': 'No',
            'JobSatisfaction': 3.0,
            'mood_score': 3.0,
            'Burnout_Symptoms': 'Sometimes',
            'Leave_Gap_Days': 60.0
        }
        probas = {'Low': 0.35, 'Medium': 0.50, 'High': 0.15}
        score, level, priority = calculate_risk_score(probas, 'Medium', record)

        self.assertTrue(40 <= score < 70, f"Expected Preventive score 40-69, got {score}")
        self.assertEqual(priority, 'Preventive')
        self.assertEqual(level, 'Medium')

    def test_case_3_high(self):
        """
        Case 3 — High / Priority:
        Duty = 65, Consec = 18, Night = 12, Sleep = 4.0, Exposure = High, Mood = 2.
        Expected: Score >= 70, Priority, High.
        """
        record = {
            'Duty_Hours_Per_Week': 65.0,
            'Working_Hours_per_Week': 65.0,
            'Consecutive_Duty_Days': 18.0,
            'Night_Shifts_Per_Month': 12.0,
            'Sleep_Hours': 4.0,
            'Physical_Activity_Hours_per_Week': 2.0,
            'Operational_Exposure': 'High',
            'Remote_Posting': 'Yes',
            'JobSatisfaction': 2.0,
            'mood_score': 2.0,
            'Burnout_Symptoms': 'Often',
            'Leave_Gap_Days': 100.0
        }
        probas = {'Low': 0.10, 'Medium': 0.30, 'High': 0.60}
        score, level, priority = calculate_risk_score(probas, 'High', record)

        self.assertGreaterEqual(score, 70, f"Expected High score >= 70, got {score}")
        self.assertEqual(priority, 'Priority')
        self.assertEqual(level, 'High')

    def test_case_4_extreme_operational_recovery(self):
        """
        Case 4 — Extreme Operational/Recovery (WITHOUT psychological extras):
        Duty = 90, Consec = 30, Night = 20, Sleep = 2.0, Exposure = High, Mood = 1.
        Expected: Score >= 90, Priority, High.
        CRITICAL: Must NEVER be downgraded to 60 / Medium.
        """
        record = {
            'Duty_Hours_Per_Week': 90.0,
            'Working_Hours_per_Week': 90.0,
            'Consecutive_Duty_Days': 30.0,
            'Night_Shifts_Per_Month': 20.0,
            'Sleep_Hours': 2.0,
            'Physical_Activity_Hours_per_Week': 1.0,
            'Operational_Exposure': 'High',
            'Remote_Posting': 'Yes',
            'JobSatisfaction': 1.0,
            'mood_score': 1.0,
            'Burnout_Symptoms': 'Often',
            'Leave_Gap_Days': 150.0
        }
        # Even if the ML model output Low probability due to synthetic demographic bias:
        skewed_probas = {'Low': 0.85, 'Medium': 0.10, 'High': 0.05}
        score, level, priority = calculate_risk_score(skewed_probas, 'Low', record)

        self.assertGreaterEqual(score, 90, f"Expected extreme op/rec score >= 90, got {score}")
        self.assertEqual(priority, 'Priority')
        self.assertEqual(level, 'High')

    def test_case_5_extreme_plus_psychological(self):
        """
        Case 5 — Extreme + Detailed Psychological Strain:
        Duty = 90, Consec = 30, Night = 20, Sleep = 2.0, Exposure = High, Mood = 1,
        Interest = Very Low (3), Discouraged = Nearly every day (3), Concentration = Severe (3), Burnout = Often.
        Expected: Score >= 90 (approaching 95-100), Priority, High.
        """
        record = {
            'Duty_Hours_Per_Week': 90.0,
            'Working_Hours_per_Week': 90.0,
            'Consecutive_Duty_Days': 30.0,
            'Night_Shifts_Per_Month': 20.0,
            'Sleep_Hours': 2.0,
            'Physical_Activity_Hours_per_Week': 1.0,
            'Operational_Exposure': 'High',
            'Remote_Posting': 'Yes',
            'JobSatisfaction': 1.0,
            'mood_score': 1.0,
            'Burnout_Symptoms': 'Often',
            'interest_score': 3,
            'discouraged_score': 3,
            'concentration_score': 3,
            'Leave_Gap_Days': 180.0
        }
        probas = {'Low': 0.05, 'Medium': 0.15, 'High': 0.80}
        score, level, priority = calculate_risk_score(probas, 'High', record)

        self.assertGreaterEqual(score, 90, f"Expected multi-domain extreme score >= 90, got {score}")
        self.assertEqual(priority, 'Priority')
        self.assertEqual(level, 'High')

    def test_ablation_psychological_not_required_for_extreme(self):
        """
        Ablation Test (Section 26):
        Verify that extreme operational & recovery conditions (90h duty, 30 consec, 20 nights, 2h sleep, High op)
        ALREADY produce High/Priority (>= 90) even without psychological extras or when mood is neutral.
        Adding psychological extras can increase the score, but is NOT required to trigger High/Priority.
        """
        base_extreme_op = {
            'Duty_Hours_Per_Week': 90.0,
            'Working_Hours_per_Week': 90.0,
            'Consecutive_Duty_Days': 30.0,
            'Night_Shifts_Per_Month': 20.0,
            'Sleep_Hours': 2.0,
            'Physical_Activity_Hours_per_Week': 1.0,
            'Operational_Exposure': 'High',
            'Remote_Posting': 'Yes',
            'JobSatisfaction': 3.0,
            'mood_score': 3.0,
            'Burnout_Symptoms': 'Rarely'
        }
        probas = {'Low': 0.80, 'Medium': 0.15, 'High': 0.05}
        score_base, level_base, priority_base = calculate_risk_score(probas, 'Low', base_extreme_op)

        self.assertGreaterEqual(score_base, 90, f"Pure operational/recovery extreme must be >= 90, got {score_base}")
        self.assertEqual(priority_base, 'Priority')
        self.assertEqual(level_base, 'High')
        self.assertNotEqual(score_base, 60, "Must NOT collapse to 60 / Medium!")

        # Now add acute psychological distress
        with_psych = dict(base_extreme_op, mood_score=1.0, JobSatisfaction=1.0, Burnout_Symptoms='Often',
                          interest_score=3, discouraged_score=3, concentration_score=3)
        score_with_psych, _, _ = calculate_risk_score(probas, 'Low', with_psych)

        self.assertGreaterEqual(score_with_psych, score_base,
                                f"Adding psychological strain should increase or maintain score ({score_with_psych} vs {score_base})")
        self.assertGreaterEqual(score_with_psych, 92)

    def test_monotonicity_directions(self):
        """
        Monotonicity Tests (Section 25):
        Ensures that changing individual features in the adverse direction strictly
        increases or maintains risk score, never decreasing.
        """
        base = {
            'Duty_Hours_Per_Week': 40.0,
            'Working_Hours_per_Week': 40.0,
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
        probas = {'Low': 0.70, 'Medium': 0.20, 'High': 0.10}
        score_base, _, _ = calculate_risk_score(probas, 'Low', base)

        # 1. 40 -> 60 duty hours: risk must not decrease
        rec_duty60 = dict(base, Duty_Hours_Per_Week=60.0, Working_Hours_per_Week=60.0)
        score_duty60, _, _ = calculate_risk_score(probas, 'Low', rec_duty60)
        self.assertGreater(score_duty60, score_base)

        # 2. 60 -> 90 duty hours: risk must not decrease
        rec_duty90 = dict(base, Duty_Hours_Per_Week=90.0, Working_Hours_per_Week=90.0)
        score_duty90, _, _ = calculate_risk_score(probas, 'Low', rec_duty90)
        self.assertGreater(score_duty90, score_duty60)

        # 3. 5 -> 2 sleep hours: risk must increase
        rec_sleep5 = dict(base, Sleep_Hours=5.0)
        rec_sleep2 = dict(base, Sleep_Hours=2.0)
        score_sleep5, _, _ = calculate_risk_score(probas, 'Low', rec_sleep5)
        score_sleep2, _, _ = calculate_risk_score(probas, 'Low', rec_sleep2)
        self.assertGreater(score_sleep2, score_sleep5)

        # 4. 5 -> 20 night shifts: risk must increase
        rec_night5 = dict(base, Night_Shifts_Per_Month=5.0)
        rec_night20 = dict(base, Night_Shifts_Per_Month=20.0)
        score_night5, _, _ = calculate_risk_score(probas, 'Low', rec_night5)
        score_night20, _, _ = calculate_risk_score(probas, 'Low', rec_night20)
        self.assertGreater(score_night20, score_night5)

        # 5. 5 -> 30 consecutive days: risk must increase
        rec_consec5 = dict(base, Consecutive_Duty_Days=5.0)
        rec_consec30 = dict(base, Consecutive_Duty_Days=30.0)
        score_consec5, _, _ = calculate_risk_score(probas, 'Low', rec_consec5)
        score_consec30, _, _ = calculate_risk_score(probas, 'Low', rec_consec30)
        self.assertGreater(score_consec30, score_consec5)

        # 6. Low -> High operational exposure: risk must increase
        rec_op_high = dict(base, Operational_Exposure='High')
        score_op_high, _, _ = calculate_risk_score(probas, 'Low', rec_op_high)
        self.assertGreater(score_op_high, score_base)

        # 7. Good (5) -> Bad (1) mood: risk must increase
        rec_mood5 = dict(base, mood_score=5.0, JobSatisfaction=5.0)
        rec_mood1 = dict(base, mood_score=1.0, JobSatisfaction=1.0)
        score_mood5, _, _ = calculate_risk_score(probas, 'Low', rec_mood5)
        score_mood1, _, _ = calculate_risk_score(probas, 'Low', rec_mood1)
        self.assertGreater(score_mood1, score_mood5)

    def test_removal_of_artificial_88_ceiling(self):
        """
        Verify that the risk engine is NOT capped around 88, and can produce
        92, 95, 98, and up to 100 when conditions warrant it.
        """
        c_max = {
            'Duty_Hours_Per_Week': 95.0,
            'Working_Hours_per_Week': 95.0,
            'Consecutive_Duty_Days': 32.0,
            'Night_Shifts_Per_Month': 22.0,
            'Sleep_Hours': 1.5,
            'Physical_Activity_Hours_per_Week': 0.0,
            'Operational_Exposure': 'High',
            'Remote_Posting': 'Yes',
            'mood_score': 1.0,
            'JobSatisfaction': 1.0,
            'Burnout_Symptoms': 'Often',
            'discouraged_score': 3,
            'concentration_score': 3,
            'interest_score': 3,
            'physical_fatigue': 5,
            'Leave_Gap_Days': 210.0
        }
        probas = {'Low': 0.0, 'Medium': 0.05, 'High': 0.95}
        score, level, priority = calculate_risk_score(probas, 'High', c_max)

        self.assertGreater(score, 88, f"Score should exceed legacy 88 ceiling, got {score}")
        self.assertGreaterEqual(score, 95, f"Maximum multi-domain strain should reach >= 95, got {score}")
        self.assertLessEqual(score, 100)
        self.assertEqual(priority, 'Priority')
        self.assertEqual(level, 'High')


if __name__ == '__main__':
    unittest.main()
