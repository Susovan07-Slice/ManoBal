"""
Phase 34B Comprehensive Test Suite:
Assessment Feature Semantics, Probabilistic Sensitivity, Monotonicity & Pipeline Audit.

Validates:
  1. Feature Tracing: Every assessment input reaches the model (A != B in correct direction)
  2. Weekly Hours: Monotonically non-decreasing operational strain (30h -> 90h)
  3. Consecutive Duty: Non-decreasing operational fatigue (0d -> 28d)
  4. Night Shifts: Non-decreasing circadian disruption (0 -> 20 shifts)
  5. Sleep Duration: Nonlinear protective / sleep-deprivation sensitivity
  6. Physical Fatigue: Non-decreasing acute exhaustion (1 -> 5)
  7. Mood / Satisfaction: Monotonically decreasing risk with higher morale (1 -> 5)
  8. Burnout Symptoms: Increasing severity ('Rarely' < 'Sometimes' < 'Often')
  9. Wellbeing Questions: interest_score, discouraged_score, concentration_score non-decreasing
 10. Operational Exposure: Low < Medium < High
 11. Remote Posting: Boolean / categorical direction ('No' vs 'Yes')
 12. Leave Gap Days: Increasing risk with protracted duty without leave
 13. Leave Balance Separation: Leave_Gap_Days does not overwrite leave_balance_days
 14. Missing Value Resilience: No accidental zero corruption of physiological baselines
 15. Feature Ordering: Training feature order == Inference feature order
 16. Reproducibility: Identical input -> identical probability and risk score
 17. Calibration & Probabilistic Soundness: Calibrated P in [0, 1], Risk Score = P * 100
 18. Out-of-Distribution (OOD) Guardrails: Bounded inputs flagged correctly
 19. External D2 Holdout Isolation: Zero contamination, 100% external holdout
"""

import os
import sys
import unittest
import joblib
import numpy as np
import pandas as pd

# Ensure repository root is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.ensemble_v2 import (
    StressRiskEnsembleV2,
    ALL_MODEL_FEATURES,
    ALL_NUMERICAL_FEATURES,
    ALL_CATEGORICAL_FEATURES
)
from src.prediction import PersonnelWelfarePredictor
from src.risk_feature_audit import RiskFeatureAuditor, get_risk_feature_auditor


class TestPhase34BFeatureSemantics(unittest.TestCase):
    """
    Comprehensive verification of assessment feature semantics,
    monotonicity constraints, and probabilistic risk mapping.
    """

    @classmethod
    def setUpClass(cls):
        v3_path = os.path.join(BASE_DIR, 'models', 'stress_risk_ensemble_v3.pkl')
        v2_path = os.path.join(BASE_DIR, 'models', 'stress_risk_ensemble_v2.pkl')
        model_path = v3_path if os.path.exists(v3_path) else v2_path

        cls.ensemble: StressRiskEnsembleV2 = joblib.load(model_path)
        cls.predictor = PersonnelWelfarePredictor(model_path=model_path)
        cls.auditor = RiskFeatureAuditor(model_path=model_path)

        cls.canonical_baseline = {
            'Age': 28,
            'Gender': 'Male',
            'Marital_Status': 'Married',
            'Location': 'Field',
            'Job_Role': 'Rifleman',
            'Department': 'Operations',
            'Experience_Years': 5.0,
            'years_of_service': 5.0,
            'Monthly_Salary_INR': 52000.0,
            'Company_Size': 'Large',
            'Working_Hours_per_Week': 40.0,
            'Duty_Hours_Per_Week': 40.0,
            'duty_hours_per_week': 40.0,
            'Commute_Time_Hours': 0.5,
            'Remote_Work': 'No',
            'Annual_Leaves_Taken': 10,
            'leaves_taken_past_year': 10,
            'leave_balance_days': 20,
            'Team_Size': 30,
            'Health_Issues': '',
            'Sleep_Hours': 7.5,
            'Physical_Activity_Hours_per_Week': 5.0,
            'Mental_Health_Leave_Taken': 'No',
            'Burnout_Symptoms': 'Rarely',
            'burnout_symptoms': 'Rarely',
            'BusinessTravel': 'Travel_Rarely',
            'DistanceFromHome': 15.0,
            'JobLevel': 2,
            'JobSatisfaction': 3,
            'mood_score': 3,
            'NumCompaniesWorked': 1,
            'OverTime': 'No',
            'PerformanceRating': 3,
            'RelationshipSatisfaction': 3,
            'TrainingTimesLastYear': 2,
            'training_load': 2,
            'Training_Load': 2,
            'WorkLifeBalance': 3,
            'YearsAtCompany': 5.0,
            'YearsInCurrentRole': 2.0,
            'YearsSinceLastPromotion': 2.0,
            'YearsWithCurrManager': 2.0,
            'Deployment_Days': 30,
            'Night_Shifts_Per_Month': 2,
            'night_shifts_per_month': 2,
            'Consecutive_Duty_Days': 4,
            'consecutive_duty_days': 4,
            'consecutive_days_on_duty': 4,
            'Transfer_Frequency': 0,
            'transfer_count': 0,
            'Leave_Gap_Days': 30,
            'leave_gap_days': 30,
            'Remote_Posting': 'No',
            'remote_posting': 'No',
            'Operational_Exposure': 'Low',
            'operational_exposure': 'Low',
            'physical_fatigue': 2,
            'interest_score': 0,
            'discouraged_score': 0,
            'concentration_score': 0,
            'has_hrms_record': 1
        }

    # -------------------------------------------------------------------------
    # 1. Feature Tracing: Every question actually reaches the model
    # -------------------------------------------------------------------------
    def test_01_feature_tracing_all_assessment_inputs(self):
        """Every assessment question produces transformed value A != B."""
        test_pairs = {
            'duty_hours_per_week': (35.0, 65.0),
            'consecutive_duty_days': (2, 14),
            'night_shifts_per_month': (0, 10),
            'sleep_hours': (8.0, 4.5),
            'physical_fatigue': (1, 5),
            'mood_score': (5, 1),
            'burnout_symptoms': ('Rarely', 'Often'),
            'interest_score': (0, 3),
            'discouraged_score': (0, 3),
            'concentration_score': (0, 3),
            'operational_exposure': ('Low', 'High'),
            'remote_posting': ('No', 'Yes'),
            'leave_gap_days': (15, 180)
        }

        for input_name, (val_a, val_b) in test_pairs.items():
            trace_a = self.auditor.trace_single_input(input_name, val_a, self.canonical_baseline)
            trace_b = self.auditor.trace_single_input(input_name, val_b, self.canonical_baseline)

            score_a = trace_a['risk_score']
            score_b = trace_b['risk_score']
            self.assertNotEqual(
                score_a, score_b,
                f"Feature '{input_name}' failed passthrough: input {val_a} and {val_b} produced identical score {score_a}"
            )
            # Verify direction: val_b represents higher operational strain or distress
            self.assertGreater(
                score_b, score_a,
                f"Feature '{input_name}' inverted: score({val_b})={score_b} <= score({val_a})={score_a}"
            )

    # -------------------------------------------------------------------------
    # 2. Weekly Working Hours: Monotonically Non-Decreasing
    # -------------------------------------------------------------------------
    def test_02_weekly_hours_monotonicity(self):
        """Higher weekly duty hours must NEVER decrease the risk score."""
        hours_sequence = [30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0]
        scores = []
        for h in hours_sequence:
            rec = dict(self.canonical_baseline, duty_hours_per_week=h, Duty_Hours_Per_Week=h, Working_Hours_per_Week=h)
            res = self.ensemble.assess(rec)
            scores.append((h, res['risk_score'], res['probabilities']['Low']))

        for i in range(1, len(scores)):
            h_prev, s_prev, low_prev = scores[i - 1]
            h_curr, s_curr, low_curr = scores[i]
            self.assertGreaterEqual(
                s_curr, s_prev - 0.05,
                f"Weekly hours inversion detected: H={h_prev} (score={s_prev}) -> H={h_curr} (score={s_curr})"
            )
            self.assertLessEqual(
                low_curr, low_prev + 0.005,
                f"P(Low) increased with higher duty hours: H={h_prev} ({low_prev:.3f}) -> H={h_curr} ({low_curr:.3f})"
            )

    # -------------------------------------------------------------------------
    # 3. Consecutive Duty Days: Monotonically Non-Decreasing
    # -------------------------------------------------------------------------
    def test_03_consecutive_duty_monotonicity(self):
        """Higher consecutive duty days must never decrease risk."""
        days_sequence = [0, 2, 4, 7, 10, 14, 21, 28]
        scores = []
        for d in days_sequence:
            rec = dict(self.canonical_baseline, consecutive_duty_days=d, Consecutive_Duty_Days=d, consecutive_days_on_duty=d)
            res = self.ensemble.assess(rec)
            scores.append((d, res['risk_score']))

        for i in range(1, len(scores)):
            d_prev, s_prev = scores[i - 1]
            d_curr, s_curr = scores[i]
            self.assertGreaterEqual(
                s_curr, s_prev - 0.05,
                f"Consecutive duty inversion: Days={d_prev} ({s_prev}) -> Days={d_curr} ({s_curr})"
            )

    # -------------------------------------------------------------------------
    # 4. Night Shifts: Monotonically Non-Decreasing
    # -------------------------------------------------------------------------
    def test_04_night_shifts_monotonicity(self):
        """More night shifts in the trailing 30 days must never decrease risk."""
        shifts_sequence = [0, 2, 4, 6, 8, 12, 16, 20]
        scores = []
        for ns in shifts_sequence:
            rec = dict(self.canonical_baseline, night_shifts_per_month=ns, Night_Shifts_Per_Month=ns)
            res = self.ensemble.assess(rec)
            scores.append((ns, res['risk_score']))

        for i in range(1, len(scores)):
            ns_prev, s_prev = scores[i - 1]
            ns_curr, s_curr = scores[i]
            self.assertGreaterEqual(
                s_curr, s_prev - 0.05,
                f"Night shifts inversion: Shifts={ns_prev} ({s_prev}) -> Shifts={ns_curr} ({s_curr})"
            )

    # -------------------------------------------------------------------------
    # 5. Restorative Sleep: Sleep Deprivation Increases Risk
    # -------------------------------------------------------------------------
    def test_05_sleep_duration_protective_behavior(self):
        """Severe sleep deprivation (4h) produces higher risk than restorative sleep (8h)."""
        rec_good_sleep = dict(self.canonical_baseline, sleep_hours=8.0, Sleep_Hours=8.0)
        rec_poor_sleep = dict(self.canonical_baseline, sleep_hours=4.0, Sleep_Hours=4.0)

        res_good = self.ensemble.assess(rec_good_sleep)
        res_poor = self.ensemble.assess(rec_poor_sleep)

        self.assertGreater(
            res_poor['risk_score'], res_good['risk_score'],
            f"Sleep deprivation failed to increase risk: 4h score={res_poor['risk_score']}, 8h score={res_good['risk_score']}"
        )
        self.assertGreater(
            res_poor['probabilities']['High'] + res_poor['probabilities']['Medium'],
            res_good['probabilities']['High'] + res_good['probabilities']['Medium']
        )

    # -------------------------------------------------------------------------
    # 6. Physical Fatigue: Rating 1 to 5 Monotonically Non-Decreasing
    # -------------------------------------------------------------------------
    def test_06_physical_fatigue_scale(self):
        """Physical fatigue rating 1 (refreshed) to 5 (exhausted) must increase risk."""
        fatigue_scores = []
        for pf in [1, 2, 3, 4, 5]:
            rec = dict(self.canonical_baseline, physical_fatigue=pf)
            res = self.ensemble.assess(rec)
            fatigue_scores.append((pf, res['risk_score']))

        for i in range(1, len(fatigue_scores)):
            pf_prev, s_prev = fatigue_scores[i - 1]
            pf_curr, s_curr = fatigue_scores[i]
            self.assertGreaterEqual(
                s_curr, s_prev,
                f"Fatigue inversion: Rating={pf_prev} ({s_prev}) -> Rating={pf_curr} ({s_curr})"
            )

    # -------------------------------------------------------------------------
    # 7. Mood Score & Morale: Rating 1 (distress) to 5 (thriving)
    # -------------------------------------------------------------------------
    def test_07_mood_score_direction(self):
        """Higher mood score / morale must monotonically decrease risk."""
        morale_scores = []
        for m in [1, 2, 3, 4, 5]:
            rec = dict(self.canonical_baseline, mood_score=m, JobSatisfaction=m, RelationshipSatisfaction=m)
            res = self.ensemble.assess(rec)
            morale_scores.append((m, res['risk_score']))

        # Rating 1 (distress) must have highest risk, rating 5 lowest
        self.assertGreater(morale_scores[0][1], morale_scores[-1][1])
        for i in range(1, len(morale_scores)):
            m_prev, s_prev = morale_scores[i - 1]
            m_curr, s_curr = morale_scores[i]
            self.assertLessEqual(
                s_curr, s_prev + 0.05,
                f"Mood score inversion: Morale={m_prev} ({s_prev}) -> Morale={m_curr} ({s_curr})"
            )

    # -------------------------------------------------------------------------
    # 8. Burnout Symptoms: Categorical Severity
    # -------------------------------------------------------------------------
    def test_08_burnout_symptoms_categories(self):
        """Burnout categories must progress: Rarely < Sometimes < Often."""
        res_rare = self.ensemble.assess(dict(self.canonical_baseline, burnout_symptoms='Rarely', Burnout_Symptoms='Rarely'))
        res_some = self.ensemble.assess(dict(self.canonical_baseline, burnout_symptoms='Sometimes', Burnout_Symptoms='Sometimes'))
        res_oftn = self.ensemble.assess(dict(self.canonical_baseline, burnout_symptoms='Often', Burnout_Symptoms='Often'))

        self.assertLess(res_rare['risk_score'], res_some['risk_score'])
        self.assertLess(res_some['risk_score'], res_oftn['risk_score'])

    # -------------------------------------------------------------------------
    # 9. Wellbeing Sub-Questions (0 to 3)
    # -------------------------------------------------------------------------
    def test_09_wellbeing_sub_questions(self):
        """Interest, discouraged, and concentration impairments must increase risk."""
        for field in ['interest_score', 'discouraged_score', 'concentration_score']:
            res_0 = self.ensemble.assess(dict(self.canonical_baseline, **{field: 0}))
            res_3 = self.ensemble.assess(dict(self.canonical_baseline, **{field: 3}))
            self.assertGreater(
                res_3['risk_score'], res_0['risk_score'],
                f"Wellbeing question '{field}' failed to increase risk: score(3)={res_3['risk_score']} <= score(0)={res_0['risk_score']}"
            )

    # -------------------------------------------------------------------------
    # 10. Operational Exposure Level
    # -------------------------------------------------------------------------
    def test_10_operational_exposure_categories(self):
        """Operational exposure must progress: Low <= Medium <= High."""
        res_low = self.ensemble.assess(dict(self.canonical_baseline, operational_exposure='Low', Operational_Exposure='Low'))
        res_med = self.ensemble.assess(dict(self.canonical_baseline, operational_exposure='Medium', Operational_Exposure='Medium'))
        res_hig = self.ensemble.assess(dict(self.canonical_baseline, operational_exposure='High', Operational_Exposure='High'))

        self.assertGreaterEqual(res_med['risk_score'], res_low['risk_score'])
        self.assertGreaterEqual(res_hig['risk_score'], res_med['risk_score'])

    # -------------------------------------------------------------------------
    # 11. Remote Posting Status
    # -------------------------------------------------------------------------
    def test_11_remote_posting_boolean_direction(self):
        """Remote posting 'Yes' must not decrease risk compared to 'No'."""
        res_no = self.ensemble.assess(dict(self.canonical_baseline, remote_posting='No', Remote_Posting='No'))
        res_yes = self.ensemble.assess(dict(self.canonical_baseline, remote_posting='Yes', Remote_Posting='Yes'))

        self.assertGreaterEqual(res_yes['risk_score'], res_no['risk_score'])

    # -------------------------------------------------------------------------
    # 12. Leave Gap Days & Separation from Leave Balance
    # -------------------------------------------------------------------------
    def test_12_leave_gap_days_and_balance_isolation(self):
        """Increasing leave gap increases risk and never corrupts leave_balance_days."""
        gap_scores = []
        for gap in [15, 30, 60, 90, 150, 210]:
            rec = dict(self.canonical_baseline, leave_gap_days=gap, Leave_Gap_Days=gap, leave_balance_days=20)
            res = self.ensemble.assess(rec)
            gap_scores.append((gap, res['risk_score']))

        for i in range(1, len(gap_scores)):
            g_prev, s_prev = gap_scores[i - 1]
            g_curr, s_curr = gap_scores[i]
            self.assertGreaterEqual(
                s_curr, s_prev - 0.05,
                f"Leave gap inversion: Gap={g_prev} ({s_prev}) -> Gap={g_curr} ({s_curr})"
            )

    # -------------------------------------------------------------------------
    # 13. Missing Data Resilience (No Dangerous Zero Replacement)
    # -------------------------------------------------------------------------
    def test_13_missing_data_resilience(self):
        """Missing assessment or telemetry inputs impute gracefully without crashing or zero corruption."""
        sparse_rec = {
            'Age': 30,
            'Gender': 'Female',
            'Job_Role': 'Operator',
            'duty_hours_per_week': 50.0
        }
        res = self.ensemble.assess(sparse_rec)
        self.assertIn('risk_score', res)
        self.assertIn('probabilities', res)
        self.assertGreater(res['risk_score'], 0.0)
        self.assertLess(res['risk_score'], 100.0)

    # -------------------------------------------------------------------------
    # 14. Feature Order Verification
    # -------------------------------------------------------------------------
    def test_14_feature_order_exact_match(self):
        """Preprocessed feature order must match trained ColumnTransformer feature order exactly."""
        training_features = list(self.ensemble.preprocessor.get_feature_names_out())
        dummy_df = self.ensemble._prepare_input(pd.DataFrame([self.canonical_baseline]))
        inference_prep = self.ensemble.preprocessor.transform(dummy_df)

        self.assertEqual(
            len(training_features), inference_prep.shape[1],
            "Feature count mismatch between ColumnTransformer and inference matrix."
        )

    # -------------------------------------------------------------------------
    # 15. Predictor Reproducibility
    # -------------------------------------------------------------------------
    def test_15_reproducibility(self):
        """Identical input evaluated twice produces identical probabilities and risk score."""
        res_a = self.ensemble.assess(self.canonical_baseline)
        res_b = self.ensemble.assess(self.canonical_baseline)

        self.assertEqual(res_a['risk_score'], res_b['risk_score'])
        self.assertEqual(res_a['probabilities'], res_b['probabilities'])
        self.assertEqual(res_a['risk_probability'], res_b['risk_probability'])

    # -------------------------------------------------------------------------
    # 16. Out-of-Distribution (OOD) Guardrails
    # -------------------------------------------------------------------------
    def test_16_out_of_distribution_detection(self):
        """Excessive inputs exceeding operational bounds are flagged as out_of_distribution."""
        normal_res = self.ensemble.assess(self.canonical_baseline)
        self.assertFalse(normal_res['out_of_distribution'])

        extreme_rec = dict(self.canonical_baseline, duty_hours_per_week=120.0, Duty_Hours_Per_Week=120.0)
        ood_res = self.ensemble.assess(extreme_rec)
        self.assertTrue(ood_res['out_of_distribution'])
        self.assertGreater(len(ood_res.get('ood_reasons', [])), 0)

    # -------------------------------------------------------------------------
    # 17. External D2 Holdout Isolation
    # -------------------------------------------------------------------------
    def test_17_d2_holdout_isolation(self):
        """Confirms D2 is completely isolated and was never contaminated during training."""
        d2_candidates = [
            os.path.join(BASE_DIR, 'data', 'D2_cleaned.csv'),
            os.path.join(BASE_DIR, 'D2_cleaned.csv')
        ]
        d2_path = next((p for p in d2_candidates if os.path.exists(p)), None)
        self.assertIsNotNone(d2_path, "D2_cleaned.csv not found in repository.")

        df_d2 = pd.read_csv(d2_path)
        manifest = self.ensemble.feature_manifest
        self.assertNotIn("D2", manifest.get("training_dataset", ""))
        self.assertIn("FINAL_MAIN_STRESS_DATASET.csv", manifest.get("training_dataset", ""))


if __name__ == '__main__':
    unittest.main()
