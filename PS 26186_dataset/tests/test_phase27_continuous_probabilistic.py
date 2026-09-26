import os
import sys
import unittest
import numpy as np
import pandas as pd

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.risk_scoring import calculate_risk_score
from src.prediction import get_welfare_service, predict_welfare



class TestPhase27ContinuousProbabilisticRisk(unittest.TestCase):
    """
    Comprehensive test suite validating Phase 27 Continuous Probabilistic Risk Engine:
      1. Continuous 0-100 scoring with decimal resolution.
      2. No artificial score ceiling at 88 or 95.
      3. Strict monotonic perturbation curves (Sleep, Duty, Night Shifts, Consecutive Days).
      4. Compound interaction modeling (High Duty x Low Sleep).
      5. Extreme operational/recovery case recognized as High/Priority without psych extras.
      6. Smooth psychological extension escalation.
      7. Normal & moderate case validation.
      8. Uncertainty & confidence estimation.
      9. Longitudinal trend tracking without temporal leakage.
    """

    @classmethod
    def setUpClass(cls):
        cls.service = get_welfare_service()

    def test_01_normal_case_low_risk(self):
        """Validates that a healthy, well-rested personnel achieves low risk (< 40, Routine, Low)."""
        record = {
            'Duty_Hours_Per_Week': 40.0,
            'Working_Hours_per_Week': 40.0,
            'Consecutive_Duty_Days': 4.0,
            'Night_Shifts_Per_Month': 2.0,
            'Sleep_Hours': 8.0,
            'Physical_Activity_Hours_per_Week': 6.0,
            'Operational_Exposure': 'Low',
            'Remote_Posting': 'No',
            'JobSatisfaction': 5.0,
            'mood_score': 5.0,
            'Burnout_Symptoms': 'Rarely',
            'Leave_Gap_Days': 15.0
        }
        probas = {'Low': 0.92, 'Medium': 0.06, 'High': 0.02}
        score, level, priority, meta = calculate_risk_score(
            probas, 'Low', record, return_metadata=True
        )

        self.assertLess(score, 40.0, f"Expected Routine score < 40, got {score}")
        self.assertEqual(priority, 'Routine')
        self.assertEqual(level, 'Low')
        self.assertIn(meta['confidence'], ['High', 'Moderate', 'Low'])
        self.assertGreaterEqual(meta['uncertainty'], 0.0)
        self.assertLessEqual(meta['uncertainty'], 1.0)

    def test_02_moderate_case_preventive_risk(self):
        """Validates that moderate duty and moderate sleep produces intermediate risk (40-69, Preventive, Medium)."""
        record = {
            'Duty_Hours_Per_Week': 52.0,
            'Working_Hours_per_Week': 52.0,
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
        probas = {'Low': 0.30, 'Medium': 0.55, 'High': 0.15}
        score, level, priority, meta = calculate_risk_score(
            probas, 'Medium', record, return_metadata=True
        )

        self.assertTrue(40.0 <= score < 70.0, f"Expected Preventive score 40-69, got {score}")
        self.assertEqual(priority, 'Preventive')
        self.assertEqual(level, 'Medium')

    def test_03_high_operational_case_priority_risk(self):
        """Validates high duty/consecutive strain achieves Priority tier (>= 70, Priority, High)."""
        record = {
            'Duty_Hours_Per_Week': 70.0,
            'Working_Hours_per_Week': 70.0,
            'Consecutive_Duty_Days': 20.0,
            'Night_Shifts_Per_Month': 14.0,
            'Sleep_Hours': 4.0,
            'Physical_Activity_Hours_per_Week': 1.5,
            'Operational_Exposure': 'High',
            'Remote_Posting': 'Yes',
            'JobSatisfaction': 2.0,
            'mood_score': 2.0,
            'Burnout_Symptoms': 'Often',
            'Leave_Gap_Days': 120.0
        }
        probas = {'Low': 0.05, 'Medium': 0.20, 'High': 0.75}
        score, level, priority, meta = calculate_risk_score(
            probas, 'High', record, return_metadata=True
        )

        self.assertGreaterEqual(score, 70.0, f"Expected Priority score >= 70, got {score}")
        self.assertEqual(priority, 'Priority')
        self.assertEqual(level, 'High')

    def test_04_extreme_operational_case_without_psych_extras(self):
        """
        User Test Case 22:
        Duty = 90, Consec = 30, Night = 20, Sleep = 2, Physical Activity = 1,
        Exposure = High, Remote = Yes, Mood = 1
        WITHOUT: interest_score, discouraged_score, concentration_score.
        Must already be recognized as extremely elevated (High / Priority, score >= 90).
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
            'Leave_Gap_Days': 180.0
        }
        probas = {'Low': 0.01, 'Medium': 0.04, 'High': 0.95}
        score, level, priority, meta = calculate_risk_score(
            probas, 'High', record, return_metadata=True
        )

        self.assertGreaterEqual(score, 90.0, f"Expected extreme case score >= 90, got {score}")
        self.assertEqual(priority, 'Priority')
        self.assertEqual(level, 'High')

    def test_05_psychological_extension_smooth_escalation(self):
        """
        User Test Case 23:
        Adding severe psychological strain to the extreme case should smoothly increase
        the score (e.g. 97.1 -> 99.2) without discrete step jumps.
        """
        base_record = {
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
            'Leave_Gap_Days': 180.0
        }
        probas = {'Low': 0.01, 'Medium': 0.04, 'High': 0.95}
        base_score, _, _, _ = calculate_risk_score(probas, 'High', base_record, return_metadata=True)

        extended_record = base_record.copy()
        extended_record.update({
            'interest_score': 3,
            'discouraged_score': 3,
            'concentration_score': 3,
            'Burnout_Symptoms': 'Often'
        })
        ext_score, _, _, _ = calculate_risk_score(probas, 'High', extended_record, return_metadata=True)

        self.assertGreaterEqual(ext_score, base_score, "Extended psychological score must be >= base score")
        self.assertLessEqual(ext_score, 100.0, "Score must not exceed 100.0")
        diff = ext_score - base_score
        self.assertLessEqual(diff, 10.0, f"Escalation should be smooth, not a massive 30-point leap: diff={diff:.2f}")

    def test_06_sleep_perturbation_monotonicity(self):
        """
        User Test Case 24:
        Sleep perturbation: 8 -> 7 -> 6 -> 5 -> 4 -> 3 -> 2.
        Risk score curve must be continuous and strictly non-decreasing.
        """
        base = {
            'Duty_Hours_Per_Week': 45.0,
            'Working_Hours_per_Week': 45.0,
            'Consecutive_Duty_Days': 6.0,
            'Night_Shifts_Per_Month': 4.0,
            'Physical_Activity_Hours_per_Week': 4.0,
            'Operational_Exposure': 'Medium',
            'Remote_Posting': 'No',
            'JobSatisfaction': 3.0,
            'mood_score': 3.0,
            'Burnout_Symptoms': 'Sometimes',
            'Leave_Gap_Days': 30.0
        }
        probas = {'Low': 0.50, 'Medium': 0.40, 'High': 0.10}

        sleep_levels = [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0]
        scores = []
        for s in sleep_levels:
            rec = base.copy()
            rec['Sleep_Hours'] = s
            sc, _, _ = calculate_risk_score(probas, 'Medium', rec)
            scores.append(sc)

        for i in range(len(scores) - 1):
            self.assertGreaterEqual(
                scores[i + 1], scores[i],
                f"Sleep perturbation violated monotonicity: {sleep_levels[i]}h ({scores[i]}) vs {sleep_levels[i+1]}h ({scores[i+1]})"
            )
        self.assertGreater(scores[-1], scores[0], "Severe sleep deficit must produce higher risk than 8h sleep")

    def test_07_duty_hours_perturbation_monotonicity(self):
        """
        Duty perturbation: 40 -> 50 -> 60 -> 70 -> 80 -> 90.
        Risk score curve must be strictly non-decreasing.
        """
        base = {
            'Working_Hours_per_Week': 40.0,
            'Consecutive_Duty_Days': 6.0,
            'Night_Shifts_Per_Month': 4.0,
            'Sleep_Hours': 6.5,
            'Physical_Activity_Hours_per_Week': 4.0,
            'Operational_Exposure': 'Medium',
            'Remote_Posting': 'No',
            'JobSatisfaction': 3.0,
            'mood_score': 3.0,
            'Burnout_Symptoms': 'Sometimes',
            'Leave_Gap_Days': 30.0
        }
        probas = {'Low': 0.40, 'Medium': 0.45, 'High': 0.15}

        duty_levels = [40.0, 50.0, 60.0, 70.0, 80.0, 90.0]
        scores = []
        for d in duty_levels:
            rec = base.copy()
            rec['Duty_Hours_Per_Week'] = d
            rec['Working_Hours_per_Week'] = d
            sc, _, _ = calculate_risk_score(probas, 'Medium', rec)
            scores.append(sc)

        for i in range(len(scores) - 1):
            self.assertGreaterEqual(
                scores[i + 1], scores[i],
                f"Duty perturbation violated monotonicity: {duty_levels[i]}h ({scores[i]}) vs {duty_levels[i+1]}h ({scores[i+1]})"
            )

    def test_08_night_shifts_perturbation_monotonicity(self):
        """
        Night shifts perturbation: 2 -> 5 -> 8 -> 12 -> 16 -> 20.
        Risk score curve must be strictly non-decreasing.
        """
        base = {
            'Duty_Hours_Per_Week': 48.0,
            'Working_Hours_per_Week': 48.0,
            'Consecutive_Duty_Days': 6.0,
            'Sleep_Hours': 6.5,
            'Physical_Activity_Hours_per_Week': 4.0,
            'Operational_Exposure': 'Medium',
            'Remote_Posting': 'No',
            'JobSatisfaction': 3.0,
            'mood_score': 3.0,
            'Burnout_Symptoms': 'Sometimes',
            'Leave_Gap_Days': 30.0
        }
        probas = {'Low': 0.45, 'Medium': 0.40, 'High': 0.15}

        night_levels = [2, 5, 8, 12, 16, 20]
        scores = []
        for n in night_levels:
            rec = base.copy()
            rec['Night_Shifts_Per_Month'] = n
            sc, _, _ = calculate_risk_score(probas, 'Medium', rec)
            scores.append(sc)

        for i in range(len(scores) - 1):
            self.assertGreaterEqual(
                scores[i + 1], scores[i],
                f"Night shifts perturbation violated monotonicity: {night_levels[i]} ({scores[i]}) vs {night_levels[i+1]} ({scores[i+1]})"
            )

    def test_09_consecutive_days_perturbation_monotonicity(self):
        """
        Consecutive duty days perturbation: 5 -> 10 -> 15 -> 20 -> 25 -> 30.
        Risk score curve must be strictly non-decreasing.
        """
        base = {
            'Duty_Hours_Per_Week': 50.0,
            'Working_Hours_per_Week': 50.0,
            'Night_Shifts_Per_Month': 6.0,
            'Sleep_Hours': 6.0,
            'Physical_Activity_Hours_per_Week': 3.0,
            'Operational_Exposure': 'Medium',
            'Remote_Posting': 'No',
            'JobSatisfaction': 3.0,
            'mood_score': 3.0,
            'Burnout_Symptoms': 'Sometimes',
            'Leave_Gap_Days': 30.0
        }
        probas = {'Low': 0.35, 'Medium': 0.50, 'High': 0.15}

        consec_levels = [5, 10, 15, 20, 25, 30]
        scores = []
        for c in consec_levels:
            rec = base.copy()
            rec['Consecutive_Duty_Days'] = c
            sc, _, _ = calculate_risk_score(probas, 'Medium', rec)
            scores.append(sc)

        for i in range(len(scores) - 1):
            self.assertGreaterEqual(
                scores[i + 1], scores[i],
                f"Consecutive days perturbation violated monotonicity: {consec_levels[i]} ({scores[i]}) vs {consec_levels[i+1]} ({scores[i+1]})"
            )

    def test_10_compound_interaction_duty_x_sleep(self):
        """
        User Test Case 25:
        Case A: 90 duty hours, 8 hours sleep
        Case B: 40 duty hours, 2 hours sleep
        Case C: 90 duty hours, 2 hours sleep
        Case C must represent substantially greater combined strain than either isolated case.
        """
        base = {
            'Consecutive_Duty_Days': 7.0,
            'Night_Shifts_Per_Month': 5.0,
            'Physical_Activity_Hours_per_Week': 3.0,
            'Operational_Exposure': 'Medium',
            'Remote_Posting': 'No',
            'JobSatisfaction': 3.0,
            'mood_score': 3.0,
            'Burnout_Symptoms': 'Sometimes',
            'Leave_Gap_Days': 30.0
        }
        probas = {'Low': 0.33, 'Medium': 0.34, 'High': 0.33}

        # Case A: High Duty (90h), Good Sleep (8h)
        case_a = base.copy()
        case_a.update({'Duty_Hours_Per_Week': 90.0, 'Working_Hours_per_Week': 90.0, 'Sleep_Hours': 8.0})
        score_a, _, _ = calculate_risk_score(probas, 'Medium', case_a)

        # Case B: Low Duty (40h), Severe Sleep Deficit (2h)
        case_b = base.copy()
        case_b.update({'Duty_Hours_Per_Week': 40.0, 'Working_Hours_per_Week': 40.0, 'Sleep_Hours': 2.0})
        score_b, _, _ = calculate_risk_score(probas, 'Medium', case_b)

        # Case C: High Duty (90h) AND Severe Sleep Deficit (2h)
        case_c = base.copy()
        case_c.update({'Duty_Hours_Per_Week': 90.0, 'Working_Hours_per_Week': 90.0, 'Sleep_Hours': 2.0})
        score_c, _, _ = calculate_risk_score(probas, 'Medium', case_c)

        self.assertGreater(score_c, score_a, f"Compound Case C ({score_c}) must exceed isolated Case A ({score_a})")
        self.assertGreater(score_c, score_b, f"Compound Case C ({score_c}) must exceed isolated Case B ({score_b})")

        # Verify compound interaction delta
        delta_c_a = score_c - score_a
        delta_c_b = score_c - score_b
        self.assertGreaterEqual(delta_c_a, 15.0, f"Expected substantial interaction escalation: delta_c_a={delta_c_a:.1f}")
        self.assertGreaterEqual(delta_c_b, 15.0, f"Expected substantial interaction escalation: delta_c_b={delta_c_b:.1f}")

    def test_11_no_score_ceiling_at_88(self):
        """Validates that scores above 88 and up into 95-100 are generated naturally without truncation."""
        extreme_record = {
            'Duty_Hours_Per_Week': 100.0,
            'Working_Hours_per_Week': 100.0,
            'Consecutive_Duty_Days': 35.0,
            'Night_Shifts_Per_Month': 25.0,
            'Sleep_Hours': 1.5,
            'Physical_Activity_Hours_per_Week': 0.5,
            'Operational_Exposure': 'High',
            'Remote_Posting': 'Yes',
            'JobSatisfaction': 1.0,
            'mood_score': 1.0,
            'Burnout_Symptoms': 'Often',
            'Leave_Gap_Days': 240.0,
            'interest_score': 3,
            'discouraged_score': 3,
            'concentration_score': 3
        }
        probas = {'Low': 0.005, 'Medium': 0.015, 'High': 0.98}
        score, level, priority, meta = calculate_risk_score(
            probas, 'High', extreme_record, return_metadata=True
        )

        self.assertGreater(score, 92.0, f"Score ceiling detected: expected score > 92, got {score}")
        self.assertLessEqual(score, 100.0, f"Score exceeded 100: {score}")

    def test_12_longitudinal_assessment_trend_tracking(self):
        """Validates temporal trajectory derivation (Worsening, Improving, Stable) without leakage."""
        current_record = {
            'Duty_Hours_Per_Week': 70.0,
            'Working_Hours_per_Week': 70.0,
            'Consecutive_Duty_Days': 18.0,
            'Night_Shifts_Per_Month': 12.0,
            'Sleep_Hours': 4.0,
            'Physical_Activity_Hours_per_Week': 2.0,
            'Operational_Exposure': 'High',
            'Remote_Posting': 'Yes',
            'JobSatisfaction': 2.0,
            'mood_score': 2.0,
            'Burnout_Symptoms': 'Often',
            'Leave_Gap_Days': 90.0
        }
        probas = {'Low': 0.10, 'Medium': 0.30, 'High': 0.60}

        # Scenario A: Previous assessment was low risk -> Worsening
        past_low = [{'risk_score': 35.0, 'stress_level': 'Low', 'risk_priority': 'Routine'}]
        _, _, _, meta_worsening = calculate_risk_score(
            probas, 'High', current_record, past_assessments=past_low, return_metadata=True
        )
        self.assertEqual(meta_worsening['risk_trend'], 'Worsening')
        self.assertGreater(meta_worsening['risk_change'], 0.0)

        # Scenario B: Previous assessment was very high risk -> Improving
        past_extreme = [{'risk_score': 98.0, 'stress_level': 'High', 'risk_priority': 'Priority'}]
        _, _, _, meta_improving = calculate_risk_score(
            probas, 'High', current_record, past_assessments=past_extreme, return_metadata=True
        )
        self.assertEqual(meta_improving['risk_trend'], 'Improving')
        self.assertLess(meta_improving['risk_change'], 0.0)

        # Scenario C: Previous assessment was approximately equal -> Stable
        past_similar = [{'risk_score': 91.0, 'stress_level': 'High', 'risk_priority': 'Priority'}]
        _, _, _, meta_stable = calculate_risk_score(
            probas, 'High', current_record, past_assessments=past_similar, return_metadata=True
        )
        self.assertEqual(meta_stable['risk_trend'], 'Stable')


    def test_13_end_to_end_predictor_pipeline(self):
        """Validates that PersonnelWelfarePredictor end-to-end inference produces complete metadata."""
        input_data = {
            'Age': 32,
            'Gender': 'Male',
            'Marital_Status': 'Married',
            'Location': 'Jammu',
            'Job_Role': 'Field Officer',
            'Experience_Years': 8.0,
            'Monthly_Salary_INR': 65000.0,
            'Company_Size': 'Large',
            'Department': 'Operations',
            'Working_Hours_per_Week': 55.0,
            'Duty_Hours_Per_Week': 55.0,
            'Commute_Time_Hours': 1.0,
            'Remote_Work': 'No',
            'Annual_Leaves_Taken': 10,
            'Team_Size': 25,
            'Health_Issues': '',
            'Sleep_Hours': 5.5,
            'Physical_Activity_Hours_per_Week': 4.0,
            'Mental_Health_Leave_Taken': 'No',
            'Burnout_Symptoms': 'Sometimes',
            'BusinessTravel': 'Travel_Rarely',
            'DistanceFromHome': 20.0,
            'JobLevel': 2,
            'JobSatisfaction': 3,
            'NumCompaniesWorked': 1,
            'OverTime': 'Yes',
            'PerformanceRating': 3,
            'RelationshipSatisfaction': 3,
            'TrainingTimesLastYear': 2,
            'WorkLifeBalance': 2,
            'YearsAtCompany': 6.0,
            'YearsInCurrentRole': 3.0,
            'YearsSinceLastPromotion': 1.0,
            'YearsWithCurrManager': 2.0,
            'Deployment_Days': 60,
            'Night_Shifts_Per_Month': 8,
            'Consecutive_Duty_Days': 10,
            'Transfer_Frequency': 1,
            'Training_Load': 3,
            'Leave_Gap_Days': 45,
            'Remote_Posting': 'No',
            'Operational_Exposure': 'Medium'
        }
        res = self.service.assess_personnel(input_data)

        self.assertIn("risk_score", res)
        self.assertIn("stress_level", res)
        self.assertIn("risk_priority", res)
        self.assertIn("risk_probability", res)
        self.assertIn("confidence", res)
        self.assertIn("uncertainty", res)
        self.assertIn("risk_trend", res)
        self.assertIn("probabilities", res)
        self.assertIn("key_factors", res)
        self.assertIn("recommendations", res)

        # Probabilities sum to 1.0
        prob_sum = sum(res["probabilities"].values())
        self.assertAlmostEqual(prob_sum, 1.0, delta=0.02)


if __name__ == '__main__':
    unittest.main()
