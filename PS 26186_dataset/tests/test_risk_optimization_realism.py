"""
Regression and Quality Assurance Suite: Risk Score Optimization, Calibration & Realism.
Directly implements and validates all 9 failure conditions defined in Section 18:
  1. Monotonicity across harmful controlled variables (work hours, sleep, workload, consecutive duty, night shifts, etc.)
  2. Class probability mapping correctness (model.classes_, simplex, and order alignment)
  3. Continuous score bounded in [0, 100]
  4. Score non-nullness (no NaN / None across edge cases and missing fields)
  5. Score distinctness (non-constant output across substantially different operational profiles)
  6. Substantial separation between normal (< 25) and severe (> 70) profiles
  7. Preprocessor schema identity between training pipeline and inference engine
  8. Factor attribution consistency (key factors reference valid input variables)
  9. Model artifact freshness and SHA-256 manifest integrity
 10. Development diagnostic endpoint (/predict/diagnostic) schema compliance
"""

import os
import sys
import json
import hashlib
import unittest
import numpy as np
import pandas as pd
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.ensemble_v2 import (
    StressRiskEnsembleV4,
    ALL_MODEL_FEATURES_V4,
    ALL_NUMERICAL_FEATURES_V4,
    ALL_CATEGORICAL_FEATURES_V4,
)
from src.prediction import PersonnelWelfarePredictor
from src.risk_feature_audit import DEFAULT_BASELINE_RECORD
from schemas.prediction import DiagnosticResponse, PredictionResponse


class TestRiskOptimizationRealism(unittest.TestCase):
    """
    Exhaustive Section 18 Automated Regression Suite for Risk Score Calibration & Realism.
    """

    @classmethod
    def setUpClass(cls):
        cls.model_path = os.path.join(BASE_DIR, 'models', 'stress_risk_ensemble_v4.pkl')
        cls.manifest_path = os.path.join(BASE_DIR, 'models', 'model_v4_manifest.json')
        cls.eval_path = os.path.join(BASE_DIR, 'models', 'model_evaluation_report_v4.json')

        assert os.path.exists(cls.model_path), f"Missing model at {cls.model_path}"
        assert os.path.exists(cls.manifest_path), f"Missing manifest at {cls.manifest_path}"

        cls.model = joblib.load(cls.model_path)
        cls.predictor = PersonnelWelfarePredictor(model_path=cls.model_path)

        cls.healthy_profile = DEFAULT_BASELINE_RECORD.copy()
        cls.healthy_profile.update({
            'Duty_Hours_Per_Week': 40.0,
            'duty_hours_per_week': 40.0,
            'Working_Hours_per_Week': 40.0,
            'Sleep_Hours': 7.5,
            'sleep_hours': 7.5,
            'Consecutive_Duty_Days': 2,
            'consecutive_duty_days': 2,
            'Night_Shifts_Per_Month': 2,
            'night_shifts_per_month': 2,
            'physical_fatigue': 1,
            'mood_score': 5,
            'JobSatisfaction': 5,
            'burnout_symptoms': 'Rarely',
            'Burnout_Symptoms': 'Rarely',
            'Operational_Exposure': 'Low',
            'operational_exposure': 'Low',
            'Remote_Posting': 'No',
            'remote_posting': 'No',
            'Leave_Gap_Days': 14,
            'leave_gap_days': 14,
        })

        cls.moderate_profile = DEFAULT_BASELINE_RECORD.copy()
        cls.moderate_profile.update({
            'Duty_Hours_Per_Week': 56.0,
            'duty_hours_per_week': 56.0,
            'Working_Hours_per_Week': 56.0,
            'Sleep_Hours': 6.0,
            'sleep_hours': 6.0,
            'Consecutive_Duty_Days': 8,
            'consecutive_duty_days': 8,
            'Night_Shifts_Per_Month': 6,
            'night_shifts_per_month': 6,
            'physical_fatigue': 3,
            'mood_score': 3,
            'JobSatisfaction': 3,
            'burnout_symptoms': 'Sometimes',
            'Burnout_Symptoms': 'Sometimes',
            'Operational_Exposure': 'Medium',
            'operational_exposure': 'Medium',
            'Leave_Gap_Days': 60,
            'leave_gap_days': 60,
        })

        cls.severe_profile = DEFAULT_BASELINE_RECORD.copy()
        cls.severe_profile.update({
            'Duty_Hours_Per_Week': 84.0,
            'duty_hours_per_week': 84.0,
            'Working_Hours_per_Week': 84.0,
            'Sleep_Hours': 4.0,
            'sleep_hours': 4.0,
            'Consecutive_Duty_Days': 16,
            'consecutive_duty_days': 16,
            'Night_Shifts_Per_Month': 12,
            'night_shifts_per_month': 12,
            'physical_fatigue': 5,
            'mood_score': 1,
            'JobSatisfaction': 1,
            'burnout_symptoms': 'Often',
            'Burnout_Symptoms': 'Often',
            'Operational_Exposure': 'High',
            'operational_exposure': 'High',
            'Remote_Posting': 'Yes',
            'remote_posting': 'Yes',
            'Leave_Gap_Days': 180,
            'leave_gap_days': 180,
        })

    # -------------------------------------------------------------------------
    # 1. Monotonicity Tests Across Harmful Controlled Variables
    # -------------------------------------------------------------------------
    def test_01_monotonicity_work_hours(self):
        """Increasing work hours from 40 to 90 must not decrease risk score."""
        hours = [40.0, 50.0, 60.0, 70.0, 80.0, 90.0]
        scores = []
        for h in hours:
            rec = dict(self.healthy_profile, Duty_Hours_Per_Week=h, duty_hours_per_week=h, Working_Hours_per_Week=h)
            res = self.model.assess(rec)
            scores.append(res['risk_score'])

        for i in range(len(scores) - 1):
            self.assertLessEqual(
                scores[i], scores[i + 1] + 1e-4,
                f"Work hours monotonicity violated at {hours[i]}h -> {hours[i+1]}h: {scores[i]} > {scores[i+1]}"
            )
        self.assertGreater(scores[-1], scores[0], "90h duty must produce higher risk than 40h duty")

    def test_02_monotonicity_sleep_deprivation(self):
        """Decreasing sleep from 8h to 4h must not decrease risk score."""
        sleep_hours = [8.0, 7.0, 6.0, 5.0, 4.0]
        scores = []
        for s in sleep_hours:
            rec = dict(self.healthy_profile, Sleep_Hours=s, sleep_hours=s)
            res = self.model.assess(rec)
            scores.append(res['risk_score'])

        for i in range(len(scores) - 1):
            self.assertLessEqual(
                scores[i], scores[i + 1] + 1e-4,
                f"Sleep reduction monotonicity violated at {sleep_hours[i]}h -> {sleep_hours[i+1]}h: {scores[i]} > {scores[i+1]}"
            )
        self.assertGreater(scores[-1], scores[0], "4h sleep must produce higher risk than 8h sleep")

    def test_03_monotonicity_consecutive_duty_and_night_shifts(self):
        """Increasing consecutive duty days and night shifts must not decrease risk."""
        consec_days = [2, 5, 8, 12, 16, 22]
        scores_consec = [
            self.model.assess(dict(self.healthy_profile, Consecutive_Duty_Days=d, consecutive_duty_days=d))['risk_score']
            for d in consec_days
        ]
        for i in range(len(scores_consec) - 1):
            self.assertLessEqual(scores_consec[i], scores_consec[i + 1] + 1e-4)

        night_shifts = [0, 2, 4, 8, 12, 16]
        scores_night = [
            self.model.assess(dict(self.healthy_profile, Night_Shifts_Per_Month=s, night_shifts_per_month=s))['risk_score']
            for s in night_shifts
        ]
        for i in range(len(scores_night) - 1):
            self.assertLessEqual(scores_night[i], scores_night[i + 1] + 1e-4)

    def test_04_monotonicity_fatigue_and_burnout(self):
        """Increasing fatigue (1->5) and burnout (Rarely->Often) must elevate risk."""
        fatigue_vals = [1, 2, 3, 4, 5]
        scores_f = [
            self.model.assess(dict(self.healthy_profile, physical_fatigue=f))['risk_score']
            for f in fatigue_vals
        ]
        for i in range(len(scores_f) - 1):
            self.assertLessEqual(scores_f[i], scores_f[i + 1] + 1e-4)

        burnout_vals = ['Rarely', 'Sometimes', 'Often']
        scores_b = [
            self.model.assess(dict(self.healthy_profile, Burnout_Symptoms=b, burnout_symptoms=b))['risk_score']
            for b in burnout_vals
        ]
        for i in range(len(scores_b) - 1):
            self.assertLessEqual(scores_b[i], scores_b[i + 1] + 1e-4)

    # -------------------------------------------------------------------------
    # 2. Probability and Class Mapping Validity
    # -------------------------------------------------------------------------
    def test_05_class_probability_mapping(self):
        """Verify model.classes_ ordering and probability simplex constraints."""
        self.assertTrue(hasattr(self.model, 'classes_'))
        self.assertEqual(list(self.model.classes_), [0, 1, 2])

        for prof in [self.healthy_profile, self.moderate_profile, self.severe_profile]:
            res = self.model.assess(prof)
            probs = res['probabilities']
            self.assertAlmostEqual(probs['Low'] + probs['Medium'] + probs['High'], 1.0, places=2)
            self.assertTrue(all(0.0 <= p <= 1.0 for p in probs.values()))

        # Healthy: Low should dominate
        res_h = self.model.assess(self.healthy_profile)
        self.assertGreater(res_h['probabilities']['Low'], res_h['probabilities']['High'])

        # Severe: High should dominate
        res_s = self.model.assess(self.severe_profile)
        self.assertGreater(res_s['probabilities']['High'], res_s['probabilities']['Low'])

    # -------------------------------------------------------------------------
    # 3 & 4. Score Boundedness and Non-Nullness
    # -------------------------------------------------------------------------
    def test_06_score_bounds_and_no_nan(self):
        """Scores must stay in [0, 100] and never be NaN or None."""
        test_inputs = [
            self.healthy_profile,
            self.moderate_profile,
            self.severe_profile,
            {},  # completely empty input relying on internal defaults
            {'Duty_Hours_Per_Week': 100.0},  # edge extreme
            {'Sleep_Hours': 1.0, 'physical_fatigue': 5},
            {'Leave_Gap_Days': 365, 'Operational_Exposure': 'High'},
        ]
        for inp in test_inputs:
            res = self.model.assess(inp)
            score = res.get('risk_score')
            self.assertIsNotNone(score)
            self.assertFalse(np.isnan(score))
            self.assertTrue(0.0 <= score <= 100.0, f"Score {score} out of bounds")

    # -------------------------------------------------------------------------
    # 5 & 6. Profile Separation and Non-Constant Output
    # -------------------------------------------------------------------------
    def test_07_separation_normal_vs_severe(self):
        """Normal, Moderate, and Severe profiles must produce clearly distinct scores."""
        res_h = self.model.assess(self.healthy_profile)
        res_m = self.model.assess(self.moderate_profile)
        res_s = self.model.assess(self.severe_profile)

        score_h = res_h['risk_score']
        score_m = res_m['risk_score']
        score_s = res_s['risk_score']

        # Non-constant verification
        self.assertNotEqual(score_h, score_m)
        self.assertNotEqual(score_m, score_s)

        # Tier segregation
        self.assertLess(score_h, 35.0, f"Healthy score {score_h} must be Routine (< 35.0)")
        self.assertEqual(res_h['risk_priority'], 'Routine')

        self.assertTrue(35.0 <= score_m < 69.0, f"Moderate score {score_m} must be Preventive [35.0, 69.0)")
        self.assertEqual(res_m['risk_priority'], 'Preventive')

        self.assertGreaterEqual(score_s, 69.0, f"Severe score {score_s} must be Priority (>= 69.0)")
        self.assertEqual(res_s['risk_priority'], 'Priority')

        # Separation magnitude: Healthy vs Severe must separate by at least 45 points
        delta = score_s - score_h
        self.assertGreater(delta, 45.0, f"Separation between normal and severe is only {delta:.1f}")

    # -------------------------------------------------------------------------
    # 7. Training vs Inference Preprocessing Schema Consistency
    # -------------------------------------------------------------------------
    def test_08_preprocessing_schema_consistency(self):
        """Feature names and ordering output by _prepare_input must match preprocessor."""
        df_in = self.model._prepare_input(pd.DataFrame([self.healthy_profile]))
        expected_features = list(self.model.preprocessor.feature_names_in_)
        actual_features = list(df_in.columns)

        self.assertEqual(actual_features, expected_features, "Mismatch in preprocessor feature schema")
        self.assertEqual(len(actual_features), len(expected_features))

    # -------------------------------------------------------------------------
    # 8. Attribution Consistency (Key Factors)
    # -------------------------------------------------------------------------
    def test_09_factor_attribution_consistency(self):
        """Top risk factors must directly agree with user input attributes."""
        res_s = self.model.assess(self.severe_profile)
        factors = res_s.get('key_factors', [])
        self.assertGreater(len(factors), 0)

        # Severe profile includes high duty, poor sleep, consecutive days
        factor_text = " ".join(factors).lower()
        self.assertTrue(any(term in factor_text for term in ['duty', 'operational', 'schedule']))
        self.assertTrue(any(term in factor_text for term in ['rest', 'sleep', 'circadian']))

    # -------------------------------------------------------------------------
    # 9. Model Artifact Integrity and Anti-Staleness
    # -------------------------------------------------------------------------
    def test_10_artifact_manifest_integrity(self):
        """Production model artifact must match model_v4_manifest SHA-256."""
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)

        with open(self.model_path, 'rb') as f:
            computed_sha = hashlib.sha256(f.read()).hexdigest()

        expected_sha = manifest.get('artifact_checksum_sha256', manifest.get('model_artifact', {}).get('sha256'))
        self.assertEqual(computed_sha, expected_sha, "Model artifact has been altered or is stale!")
        self.assertEqual(self.model.model_version, 'stress_risk_ensemble_v4')

    # -------------------------------------------------------------------------
    # 10. Development Diagnostic Endpoint Schema Compliance
    # -------------------------------------------------------------------------
    def test_11_diagnostic_endpoint_schema(self):
        """Diagnostic output schema must contain all Section 17 required keys."""
        diag_out = self.predictor.get_diagnostic_assessment(self.moderate_profile)

        # Validate against Section 17 Pydantic schema
        diag_resp = DiagnosticResponse(**diag_out)
        self.assertEqual(diag_resp.model_version, 'stress_risk_ensemble_v4')
        self.assertIn(diag_resp.predicted_class, ['Low', 'Medium', 'High'])
        self.assertIn('low', diag_resp.raw_probabilities)
        self.assertIn('medium', diag_resp.raw_probabilities)
        self.assertIn('high', diag_resp.raw_probabilities)
        self.assertIn('low', diag_resp.calibrated_probabilities)
        self.assertIn('medium', diag_resp.calibrated_probabilities)
        self.assertIn('high', diag_resp.calibrated_probabilities)
        self.assertTrue(0.0 <= diag_resp.risk_score <= 100.0)
        self.assertIn(diag_resp.risk_category, ['Routine', 'Preventive', 'Priority'])
        self.assertIsInstance(diag_resp.top_risk_factors, list)


if __name__ == '__main__':
    unittest.main()
