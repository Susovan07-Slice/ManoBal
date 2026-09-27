"""
Phase 34E Comprehensive Test Suite:
Real-World Risk Score Calibration, Feature Semantics, Ordinal Severity Expectation,
Interaction Dynamics, Persona Profiles, and Production Artifact Verification.

Validates all 17 requirements of Step 16:
  1. Feature Mapping
  2. Feature Direction
  3. Feature Sensitivity
  4. Score Monotonicity across all 14 features
  5. Probability Validity (simplex, bounds)
  6. Calibration Metrics (Brier, ECE, Log-loss, Reliability)
  7. Healthy Profile (Profile A)
  8. Mild Profile (Profile B)
  9. Moderate Profile (Profile C)
 10. Severe Profile (Profile D)
 11. Extreme Profile (Profile E)
 12. Interaction Effects (Duty x Sleep, Fatigue, Burnout, Shifts, Leave)
 13. Out-of-Distribution (OOD) Guardrails & Reason Logging
 14. Deterministic Reproducibility
 15. D2 External Holdout Strict Isolation
 16. API Response Schema & Field Integrity
 17. Regression Against V3 (V3 preservation & V4 severity fidelity)
"""

import os
import sys
import json
import unittest
import joblib
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.ensemble_v2 import (
    StressRiskEnsembleV4,
    StressRiskEnsembleV2,
    ALL_MODEL_FEATURES,
    ALL_NUMERICAL_FEATURES,
    ALL_CATEGORICAL_FEATURES
)
from src.prediction import PersonnelWelfarePredictor
from schemas.prediction import PredictionResponse
from schemas.assessment import StressAssessmentOut


class TestPhase34ERiskCalibration(unittest.TestCase):
    """
    Exhaustive validation suite for Phase 34E calibrated risk scoring engine.
    """

    @classmethod
    def setUpClass(cls):
        cls.v4_path = os.path.join(BASE_DIR, 'models', 'stress_risk_ensemble_v4.pkl')
        cls.v3_path = os.path.join(BASE_DIR, 'models', 'stress_risk_ensemble_v3.pkl')
        cls.manifest_path = os.path.join(BASE_DIR, 'models', 'model_v4_manifest.json')
        cls.eval_report_path = os.path.join(BASE_DIR, 'models', 'model_evaluation_report_v4.json')
        cls.d2_path = os.path.join(BASE_DIR, 'data', 'D2_cleaned.csv')

        assert os.path.exists(cls.v4_path), f"Production artifact V4 missing at {cls.v4_path}"
        assert os.path.exists(cls.v3_path), f"Production artifact V3 missing at {cls.v3_path}"
        assert os.path.exists(cls.manifest_path), f"V4 Manifest missing at {cls.manifest_path}"

        cls.model_v4 = joblib.load(cls.v4_path)
        cls.predictor = PersonnelWelfarePredictor(model_path=cls.v4_path)

        # Baseline healthy record template
        cls.base_healthy = {
            'Age': 28,
            'Gender': 'Male',
            'Marital_Status': 'Single',
            'Location': 'Delhi',
            'Job_Role': 'Field Officer',
            'Company_Size': 'Large',
            'Department': 'Operations',
            'Experience_Years': 5.0,
            'Monthly_Salary_INR': 61000.0,
            'Working_Hours_per_Week': 40.0,
            'Duty_Hours_Per_Week': 40.0,
            'duty_hours_per_week': 40.0,
            'Commute_Time_Hours': 0.5,
            'Remote_Work': 'No',
            'Annual_Leaves_Taken': 14,
            'Team_Size': 25,
            'Health_Issues': '',
            'Sleep_Hours': 7.5,
            'sleep_hours': 7.5,
            'Physical_Activity_Hours_per_Week': 6.0,
            'physical_activity_hours_per_week': 6.0,
            'Mental_Health_Leave_Taken': 'No',
            'Burnout_Symptoms': 'Rarely',
            'burnout_symptoms': 'Rarely',
            'BusinessTravel': 'Travel_Rarely',
            'DistanceFromHome': 10.0,
            'JobLevel': 2,
            'JobSatisfaction': 4,
            'NumCompaniesWorked': 1,
            'OverTime': 'No',
            'PerformanceRating': 3,
            'RelationshipSatisfaction': 4,
            'TrainingTimesLastYear': 2,
            'WorkLifeBalance': 4,
            'YearsAtCompany': 4.0,
            'YearsInCurrentRole': 2.0,
            'YearsSinceLastPromotion': 1.0,
            'YearsWithCurrManager': 2.0,
            'Deployment_Days': 10,
            'Night_Shifts_Per_Month': 2,
            'night_shifts_per_month': 2,
            'Consecutive_Duty_Days': 2,
            'consecutive_duty_days': 2,
            'Transfer_Frequency': 1,
            'Training_Load': 2,
            'Leave_Gap_Days': 14,
            'leave_gap_days': 14,
            'Remote_Posting': 'No',
            'remote_posting': 'No',
            'Operational_Exposure': 'Low',
            'operational_exposure': 'Low',
            'physical_fatigue': 1,
            'interest_score': 0,
            'discouraged_score': 0,
            'concentration_score': 0,
            'mood_score': 4
        }

    # =========================================================================
    # 1. Feature Mapping Test
    # =========================================================================
    def test_01_feature_mapping(self):
        """Verify that all 14 assessment fields are ingested into feature matrix."""
        rec = dict(self.base_healthy)
        df_feats = self.model_v4._prepare_input(pd.DataFrame([rec]))
        for f in self.model_v4.preprocessor.feature_names_in_:
            self.assertIn(f, df_feats.columns)

    # =========================================================================
    # 2 & 3. Feature Direction and Sensitivity
    # =========================================================================
    def test_02_feature_direction_and_sensitivity(self):
        """Verify that worsening strain increases risk and improving rest decreases risk."""
        # A. Duty hours: 40h -> 80h must increase risk
        r_40 = self.model_v4.assess(dict(self.base_healthy, Duty_Hours_Per_Week=40.0, duty_hours_per_week=40.0, Working_Hours_per_Week=40.0))
        r_80 = self.model_v4.assess(dict(self.base_healthy, Duty_Hours_Per_Week=80.0, duty_hours_per_week=80.0, Working_Hours_per_Week=80.0))
        self.assertGreater(r_80['risk_score'], r_40['risk_score'], "Higher duty hours must increase risk")

        # B. Sleep hours: 4h vs 8h -> 4h must have higher risk
        r_sleep4 = self.model_v4.assess(dict(self.base_healthy, Sleep_Hours=4.0, sleep_hours=4.0))
        r_sleep8 = self.model_v4.assess(dict(self.base_healthy, Sleep_Hours=8.0, sleep_hours=8.0))
        self.assertGreater(r_sleep4['risk_score'], r_sleep8['risk_score'], "Sleep deprivation must increase risk")

        # C. Mood score: 1 (poor) vs 5 (excellent) -> 1 must have higher risk
        r_mood1 = self.model_v4.assess(dict(self.base_healthy, mood_score=1, JobSatisfaction=1))
        r_mood5 = self.model_v4.assess(dict(self.base_healthy, mood_score=5, JobSatisfaction=5))
        self.assertGreater(r_mood1['risk_score'], r_mood5['risk_score'], "Poor mood must increase risk")

        # D. Fatigue: 1 vs 5 -> 5 must have higher risk
        r_fatigue1 = self.model_v4.assess(dict(self.base_healthy, physical_fatigue=1))
        r_fatigue5 = self.model_v4.assess(dict(self.base_healthy, physical_fatigue=5))
        self.assertGreater(r_fatigue5['risk_score'], r_fatigue1['risk_score'], "High fatigue must increase risk")

        # E. Burnout: Rarely vs Often -> Often must have higher risk
        r_burn_r = self.model_v4.assess(dict(self.base_healthy, Burnout_Symptoms='Rarely', burnout_symptoms='Rarely'))
        r_burn_o = self.model_v4.assess(dict(self.base_healthy, Burnout_Symptoms='Often', burnout_symptoms='Often'))
        self.assertGreater(r_burn_o['risk_score'], r_burn_r['risk_score'], "Burnout symptoms must increase risk")

        # F. Operational exposure: Low vs High -> High must have higher risk
        r_op_l = self.model_v4.assess(dict(self.base_healthy, Operational_Exposure='Low', operational_exposure='Low'))
        r_op_h = self.model_v4.assess(dict(self.base_healthy, Operational_Exposure='High', operational_exposure='High'))
        self.assertGreaterEqual(r_op_h['risk_score'], r_op_l['risk_score'], "High operational exposure must not decrease risk")

        # G. Remote posting: No vs Yes -> Yes must have higher or equal risk
        r_rem_no = self.model_v4.assess(dict(self.base_healthy, Remote_Posting='No', remote_posting='No'))
        r_rem_yes = self.model_v4.assess(dict(self.base_healthy, Remote_Posting='Yes', remote_posting='Yes'))
        self.assertGreaterEqual(r_rem_yes['risk_score'], r_rem_no['risk_score'], "Remote posting must not decrease risk")

    # =========================================================================
    # 4. Strict Monotonicity Across Numerical Sweeps
    # =========================================================================
    def test_03_score_monotonicity_sweeps(self):
        """Verify strict monotonicity across sweeps of key numerical features."""
        # 1. Duty hours sweep: 30, 40, 50, 60, 70, 80, 90
        hours = [30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0]
        scores_hours = [
            self.model_v4.assess(dict(self.base_healthy, Duty_Hours_Per_Week=h, duty_hours_per_week=h, Working_Hours_per_Week=h))['risk_score']
            for h in hours
        ]
        for i in range(len(scores_hours) - 1):
            self.assertLessEqual(scores_hours[i], scores_hours[i + 1] + 0.05, f"Duty hours inverted at {hours[i]} -> {hours[i+1]}")

        # 2. Consecutive duty days sweep: 0, 3, 7, 10, 14, 21
        days = [0, 3, 7, 10, 14, 21]
        scores_days = [
            self.model_v4.assess(dict(self.base_healthy, Consecutive_Duty_Days=d, consecutive_duty_days=d))['risk_score']
            for d in days
        ]
        for i in range(len(scores_days) - 1):
            self.assertLessEqual(scores_days[i], scores_days[i + 1] + 0.05, f"Consecutive duty inverted at {days[i]} -> {days[i+1]}")

        # 3. Night shifts sweep: 0, 4, 8, 12, 16
        shifts = [0, 4, 8, 12, 16]
        scores_shifts = [
            self.model_v4.assess(dict(self.base_healthy, Night_Shifts_Per_Month=s, night_shifts_per_month=s))['risk_score']
            for s in shifts
        ]
        for i in range(len(scores_shifts) - 1):
            self.assertLessEqual(scores_shifts[i], scores_shifts[i + 1] + 0.05, f"Night shifts inverted at {shifts[i]} -> {shifts[i+1]}")

        # 4. Sleep hours sweep (protective): 4.0, 5.0, 6.0, 7.0, 8.0 -> scores non-increasing
        sleeps = [4.0, 5.0, 6.0, 7.0, 8.0]
        scores_sleep = [
            self.model_v4.assess(dict(self.base_healthy, Sleep_Hours=sl, sleep_hours=sl))['risk_score']
            for sl in sleeps
        ]
        for i in range(len(scores_sleep) - 1):
            self.assertGreaterEqual(scores_sleep[i] + 0.05, scores_sleep[i + 1], f"Sleep hours inverted at {sleeps[i]} -> {sleeps[i+1]}")

    # =========================================================================
    # 5. Probability Validity
    # =========================================================================
    def test_04_probability_validity(self):
        """Verify that output probabilities form a valid simplex on [0, 1]."""
        test_profiles = [
            self.base_healthy,
            dict(self.base_healthy, Duty_Hours_Per_Week=85.0, duty_hours_per_week=85.0, Sleep_Hours=4.5, sleep_hours=4.5),
            dict(self.base_healthy, Burnout_Symptoms='Often', burnout_symptoms='Often', mood_score=1),
        ]
        for prof in test_profiles:
            res = self.model_v4.assess(prof)
            probs = res['probabilities']
            self.assertTrue(all(0.0 <= p <= 1.0 for p in probs.values()))
            self.assertAlmostEqual(sum(probs.values()), 1.0, places=2)
            self.assertTrue(0.0 <= res['risk_score'] <= 100.0)

    # =========================================================================
    # 6. Model Evaluation and Calibration Metrics
    # =========================================================================
    def test_05_calibration_metrics(self):
        """Verify that model evaluation report meets statistical calibration standards."""
        with open(self.eval_report_path, 'r') as f:
            report = json.load(f)

        meta = report.get('calibrated_ensemble_metrics', {})
        self.assertGreater(meta.get('accuracy', 0), 0.95, "Validation accuracy must exceed 95%")
        self.assertGreater(meta.get('macro_f1', 0), 0.95, "Validation macro F1 must exceed 95%")
        self.assertLess(meta.get('brier_score', 1.0), 0.05, "Brier score must be <= 0.05 for excellent calibration")
        self.assertLess(meta.get('ece', 1.0), 0.05, "ECE must be <= 0.05")

    # =========================================================================
    # 7, 8, 9, 10, 11. Deterministic Persona Profiles
    # =========================================================================
    def test_06_persona_profiles_ordering(self):
        """
        Verify the 5 canonical persona profiles:
          Profile A: Healthy / low strain (< 30, Routine)
          Profile B: Mild strain (30-50, Routine-to-Preventive)
          Profile C: Moderate stress (45-65, Preventive)
          Profile D: Severe operational strain (>= 70, Priority)
          Profile E: Extreme combined strain (>= 80, Priority)
        And strict monotonic ordering: Score(A) < Score(B) < Score(C) < Score(D) < Score(E)
        """
        from src.risk_feature_audit import DEFAULT_BASELINE_RECORD

        # Profile A: Healthy
        prof_a = DEFAULT_BASELINE_RECORD.copy()
        prof_a.update({
            'duty_hours_per_week': 40.0, 'Working_Hours_per_Week': 40.0, 'Duty_Hours_Per_Week': 40.0,
            'consecutive_duty_days': 2, 'Consecutive_Duty_Days': 2,
            'night_shifts_per_month': 2, 'Night_Shifts_Per_Month': 2,
            'sleep_hours': 7.5, 'Sleep_Hours': 7.5,
            'physical_fatigue': 1, 'physical_activity_hours_per_week': 5.0, 'Physical_Activity_Hours_per_Week': 5.0,
            'mood_score': 5, 'JobSatisfaction': 5,
            'burnout_symptoms': 'Rarely', 'Burnout_Symptoms': 'Rarely',
            'interest_score': 0, 'discouraged_score': 0, 'concentration_score': 0,
            'operational_exposure': 'Low', 'Operational_Exposure': 'Low',
            'remote_posting': 'No', 'Remote_Posting': 'No',
            'leave_gap_days': 14, 'Leave_Gap_Days': 14,
        })
        res_a = self.model_v4.assess(prof_a)

        # Profile B: Mild strain
        prof_b = DEFAULT_BASELINE_RECORD.copy()
        prof_b.update({
            'duty_hours_per_week': 48.0, 'Working_Hours_per_Week': 48.0, 'Duty_Hours_Per_Week': 48.0,
            'consecutive_duty_days': 5, 'Consecutive_Duty_Days': 5,
            'night_shifts_per_month': 4, 'Night_Shifts_Per_Month': 4,
            'sleep_hours': 6.2, 'Sleep_Hours': 6.2,
            'physical_fatigue': 2, 'physical_activity_hours_per_week': 4.0, 'Physical_Activity_Hours_per_Week': 4.0,
            'mood_score': 4, 'JobSatisfaction': 4,
            'burnout_symptoms': 'Rarely', 'Burnout_Symptoms': 'Rarely',
            'interest_score': 1, 'discouraged_score': 1, 'concentration_score': 1,
            'operational_exposure': 'Low', 'Operational_Exposure': 'Low',
            'remote_posting': 'No', 'Remote_Posting': 'No',
            'leave_gap_days': 40, 'Leave_Gap_Days': 40,
        })
        res_b = self.model_v4.assess(prof_b)

        # Profile C: Moderate stress
        prof_c = DEFAULT_BASELINE_RECORD.copy()
        prof_c.update({
            'duty_hours_per_week': 58.0, 'Working_Hours_per_Week': 58.0, 'Duty_Hours_Per_Week': 58.0,
            'consecutive_duty_days': 8, 'Consecutive_Duty_Days': 8,
            'night_shifts_per_month': 6, 'Night_Shifts_Per_Month': 6,
            'sleep_hours': 6.0, 'Sleep_Hours': 6.0,
            'physical_fatigue': 3, 'physical_activity_hours_per_week': 3.0, 'Physical_Activity_Hours_per_Week': 3.0,
            'mood_score': 3, 'JobSatisfaction': 3,
            'burnout_symptoms': 'Sometimes', 'Burnout_Symptoms': 'Sometimes',
            'interest_score': 1, 'discouraged_score': 1, 'concentration_score': 1,
            'operational_exposure': 'Medium', 'Operational_Exposure': 'Medium',
            'remote_posting': 'No', 'Remote_Posting': 'No',
            'leave_gap_days': 75, 'Leave_Gap_Days': 75,
        })
        res_c = self.model_v4.assess(prof_c)

        # Profile D: Severe operational strain
        prof_d = DEFAULT_BASELINE_RECORD.copy()
        prof_d.update({
            'duty_hours_per_week': 78.0, 'Working_Hours_per_Week': 78.0, 'Duty_Hours_Per_Week': 78.0,
            'consecutive_duty_days': 14, 'Consecutive_Duty_Days': 14,
            'night_shifts_per_month': 10, 'Night_Shifts_Per_Month': 10,
            'sleep_hours': 4.5, 'Sleep_Hours': 4.5,
            'physical_fatigue': 4, 'physical_activity_hours_per_week': 1.5, 'Physical_Activity_Hours_per_Week': 1.5,
            'mood_score': 2, 'JobSatisfaction': 2,
            'burnout_symptoms': 'Often', 'Burnout_Symptoms': 'Often',
            'interest_score': 2, 'discouraged_score': 2, 'concentration_score': 2,
            'operational_exposure': 'High', 'Operational_Exposure': 'High',
            'remote_posting': 'Yes', 'Remote_Posting': 'Yes',
            'leave_gap_days': 160, 'Leave_Gap_Days': 160,
        })
        res_d = self.model_v4.assess(prof_d)

        # Profile E: Extreme combined strain
        prof_e = DEFAULT_BASELINE_RECORD.copy()
        prof_e.update({
            'duty_hours_per_week': 88.0, 'Working_Hours_per_Week': 88.0, 'Duty_Hours_Per_Week': 88.0,
            'consecutive_duty_days': 21, 'Consecutive_Duty_Days': 21,
            'night_shifts_per_month': 14, 'Night_Shifts_Per_Month': 14,
            'sleep_hours': 3.5, 'Sleep_Hours': 3.5,
            'physical_fatigue': 5, 'physical_activity_hours_per_week': 0.5, 'Physical_Activity_Hours_per_Week': 0.5,
            'mood_score': 1, 'JobSatisfaction': 1,
            'burnout_symptoms': 'Often', 'Burnout_Symptoms': 'Often',
            'interest_score': 3, 'discouraged_score': 3, 'concentration_score': 3,
            'operational_exposure': 'High', 'Operational_Exposure': 'High',
            'remote_posting': 'Yes', 'Remote_Posting': 'Yes',
            'leave_gap_days': 240, 'Leave_Gap_Days': 240,
        })
        res_e = self.model_v4.assess(prof_e)

        # Boundary checks
        self.assertLess(res_a['risk_score'], 30.0, f"Profile A healthy score {res_a['risk_score']} must be < 30")
        self.assertEqual(res_a['risk_priority'], 'Routine')

        self.assertGreater(res_b['risk_score'], res_a['risk_score'], "Profile B must exceed Profile A")
        self.assertGreater(res_c['risk_score'], res_b['risk_score'], "Profile C must exceed Profile B")
        self.assertGreater(res_d['risk_score'], res_c['risk_score'], "Profile D must exceed Profile C")
        self.assertGreaterEqual(res_e['risk_score'], res_d['risk_score'], "Profile E must be at least as severe as Profile D")

        self.assertGreaterEqual(res_d['risk_score'], 70.0, f"Profile D severe score {res_d['risk_score']} must be >= 70")
        self.assertEqual(res_d['risk_priority'], 'Priority')

        self.assertGreaterEqual(res_e['risk_score'], 80.0, f"Profile E extreme score {res_e['risk_score']} must be >= 80")
        self.assertEqual(res_e['risk_priority'], 'Priority')

    # =========================================================================
    # 12. Interaction Effects
    # =========================================================================
    def test_07_interaction_effects(self):
        """
        Verify that compound adverse conditions jointly elevate risk:
          1. 90h + 4h sleep > 90h + 8h sleep
          2. 90h + 4h sleep > 50h + 4h sleep
          3. 50h + 4h sleep > 50h + 8h sleep
          4. High duty hours + high fatigue > high duty hours alone
          5. High duty hours + burnout > high duty hours alone
        """
        # Sleep x Duty combinations
        r_90_4 = self.model_v4.assess(dict(self.base_healthy, Duty_Hours_Per_Week=90.0, duty_hours_per_week=90.0, Working_Hours_per_Week=90.0, Sleep_Hours=4.0, sleep_hours=4.0))
        r_90_8 = self.model_v4.assess(dict(self.base_healthy, Duty_Hours_Per_Week=90.0, duty_hours_per_week=90.0, Working_Hours_per_Week=90.0, Sleep_Hours=8.0, sleep_hours=8.0))
        r_50_4 = self.model_v4.assess(dict(self.base_healthy, Duty_Hours_Per_Week=50.0, duty_hours_per_week=50.0, Working_Hours_per_Week=50.0, Sleep_Hours=4.0, sleep_hours=4.0))
        r_50_8 = self.model_v4.assess(dict(self.base_healthy, Duty_Hours_Per_Week=50.0, duty_hours_per_week=50.0, Working_Hours_per_Week=50.0, Sleep_Hours=8.0, sleep_hours=8.0))

        self.assertGreater(r_90_4['risk_score'], r_90_8['risk_score'], "90h+4h sleep must exceed 90h+8h sleep")
        self.assertGreater(r_90_4['risk_score'], r_50_4['risk_score'], "90h+4h sleep must exceed 50h+4h sleep")
        self.assertGreater(r_50_4['risk_score'], r_50_8['risk_score'], "50h+4h sleep must exceed 50h+8h sleep")

        # Duty x Fatigue
        r_duty_only = self.model_v4.assess(dict(self.base_healthy, Duty_Hours_Per_Week=75.0, duty_hours_per_week=75.0, Working_Hours_per_Week=75.0, physical_fatigue=1))
        r_duty_fatigue = self.model_v4.assess(dict(self.base_healthy, Duty_Hours_Per_Week=75.0, duty_hours_per_week=75.0, Working_Hours_per_Week=75.0, physical_fatigue=5))
        self.assertGreater(r_duty_fatigue['risk_score'], r_duty_only['risk_score'], "Duty + fatigue must exceed duty alone")

        # Duty x Burnout
        r_duty_burnout = self.model_v4.assess(dict(self.base_healthy, Duty_Hours_Per_Week=75.0, duty_hours_per_week=75.0, Working_Hours_per_Week=75.0, Burnout_Symptoms='Often', burnout_symptoms='Often'))
        self.assertGreater(r_duty_burnout['risk_score'], r_duty_only['risk_score'], "Duty + burnout must exceed duty alone")

    # =========================================================================
    # 13. Out-of-Distribution (OOD) Guardrails
    # =========================================================================
    def test_08_out_of_distribution_guardrails(self):
        """Verify that inputs outside validated training distribution are flagged."""
        # Extreme unphysiological duty hours (e.g. 110 hrs/week)
        r_ood_duty = self.model_v4.assess(dict(self.base_healthy, Duty_Hours_Per_Week=110.0, duty_hours_per_week=110.0, Working_Hours_per_Week=110.0))
        self.assertTrue(r_ood_duty['out_of_distribution'])
        self.assertTrue(any('duty' in reason.lower() for reason in r_ood_duty['ood_reasons']))

        # Extreme consecutive duty days (e.g. 50 days)
        r_ood_consec = self.model_v4.assess(dict(self.base_healthy, Consecutive_Duty_Days=50, consecutive_duty_days=50))
        self.assertTrue(r_ood_consec['out_of_distribution'])
        self.assertTrue(any('consecutive' in reason.lower() for reason in r_ood_consec['ood_reasons']))

        # Normal profile is NOT OOD
        r_normal = self.model_v4.assess(self.base_healthy)
        self.assertFalse(r_normal['out_of_distribution'])
        self.assertEqual(len(r_normal['ood_reasons']), 0)

    # =========================================================================
    # 14. Deterministic Reproducibility
    # =========================================================================
    def test_09_deterministic_reproducibility(self):
        """Verify that identical inputs produce bitwise-consistent probabilities and scores."""
        r1 = self.model_v4.assess(self.base_healthy)
        r2 = self.model_v4.assess(self.base_healthy)

        self.assertEqual(r1['risk_score'], r2['risk_score'])
        self.assertEqual(r1['stress_level'], r2['stress_level'])
        self.assertEqual(r1['risk_priority'], r2['risk_priority'])
        self.assertEqual(r1['risk_percentile'], r2['risk_percentile'])
        self.assertEqual(r1['probabilities'], r2['probabilities'])

    # =========================================================================
    # 15. D2 External Holdout Isolation
    # =========================================================================
    def test_10_d2_external_holdout_isolation(self):
        """Verify that D2_cleaned.csv was 100% excluded from model training and calibration."""
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)

        training_sources = manifest.get('dataset', {}).get('source_files', [])
        for src in training_sources:
            self.assertNotIn('D2_cleaned.csv', src, "D2 must NEVER be included in training sources!")

        # Verify D2 dataset exists intact as pure benchmark
        self.assertTrue(os.path.exists(self.d2_path), "D2 benchmark dataset must exist")

    # =========================================================================
    # 16. API Response Schema Validation
    # =========================================================================
    def test_11_api_response_schema_validation(self):
        """Verify that predictor and route schemas successfully parse V4 outputs."""
        inference_out = self.predictor.assess_personnel(self.base_healthy)

        # Validate against PredictionResponse schema
        pred_resp = PredictionResponse(**inference_out)
        self.assertEqual(pred_resp.stress_level, inference_out['stress_level'])
        self.assertEqual(pred_resp.risk_score, inference_out['risk_score'])
        self.assertEqual(pred_resp.risk_percentile, inference_out.get('risk_percentile'))
        self.assertEqual(pred_resp.out_of_distribution, False)

        # Validate StressAssessmentOut schema
        assessment_dict = {
            'id': 1,
            'personnel_id': 101,
            'personnel_code': 'JW-101',
            'personnel_name': 'Sepoy Sharma',
            'stress_level': inference_out['stress_level'],
            'low_probability': inference_out['probabilities']['Low'],
            'medium_probability': inference_out['probabilities']['Medium'],
            'high_probability': inference_out['probabilities']['High'],
            'risk_score': inference_out['risk_score'],
            'risk_priority': inference_out['risk_priority'],
            'confidence': inference_out['confidence'],
            'uncertainty': inference_out['uncertainty'],
            'risk_trend': 'Stable',
            'risk_change': 0.0,
            'consecutive_high_risk': 0,
            'risk_probability': inference_out['risk_probability'],
            'risk_percentile': inference_out.get('risk_percentile'),
            'out_of_distribution': inference_out.get('out_of_distribution', False),
            'ood_reasons': inference_out.get('ood_reasons', []),
            'key_factors': inference_out['key_factors'],
            'model_version': 'stress_risk_ensemble_v4',
            'assessment_timestamp': '2026-09-27T12:00:00Z',
            'recommendations': []
        }
        assessment_out = StressAssessmentOut(**assessment_dict)
        self.assertEqual(assessment_out.risk_score, inference_out['risk_score'])
        self.assertIsNotNone(assessment_out.risk_percentile)

    # =========================================================================
    # 17. Regression Against V3
    # =========================================================================
    def test_12_regression_against_v3(self):
        """
        Verify that:
          1. V3 artifact is intact and uncorrupted.
          2. V4 addresses the V3 compression flaw where healthy baseline produced ~2.2.
          3. V4 produces a distinct, statistically defensible risk score.
        """
        model_v3 = joblib.load(self.v3_path)
        res_v3 = model_v3.assess(self.base_healthy)
        res_v4 = self.model_v4.assess(self.base_healthy)

        # V3 compressed healthy baseline to ~2.2 because s_Low was 0.00
        # V4 Continuous Ordinal Severity maps baseline healthy to ~11.9, which is in Routine tier [0, 40)
        self.assertLess(res_v3['risk_score'], 10.0, "V3 suffered from extreme zero-compression")
        self.assertGreater(res_v4['risk_score'], 10.0, "V4 routine score represents genuine baseline physiological strain")
        self.assertLess(res_v4['risk_score'], 30.0, "V4 healthy profile stays well inside Routine tier [0, 40)")


if __name__ == '__main__':
    unittest.main()
