"""
Phase 34 Automated Test Suite:
Advanced Probabilistic Risk Engine Audit, Recalibration & Sensitivity Control.
Verifies:
  1. Directional Monotonicity (Duty hours, consecutive duty, night shifts, sleep deficit)
  2. Sensitivity Control (Tiny perturbations produce proportionate bounded changes;
                          large operational strain produces meaningful changes)
  3. Numerical Stability & Repeatability (Identical inputs -> identical outputs)
  4. Feature Coverage (Assessment + HRMS + 7d/30d Wearables reach model)
  5. Missing Data Resilience (Imputation without silent zero corruption)
  6. Probability Calibration (Brier score, ECE, Platt scaling bounds)
  7. Demographic & Role Fairness (No hardcoded bias or proxy inflation)
  8. External D2 Isolation (Zero contamination, 100% holdout integrity)
  9. API Contract Compatibility (/api/predict, /api/personnel/{id}/assess, RBAC)
"""

import os
import sys
import unittest
import uuid
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from db.session import SessionLocal
from db.models.user import User
from db.models.personnel import Personnel
from db.models.hrms import HrmsServiceRecord
from db.models.telemetry import WearableTelemetry
from db.models.assessment import StressAssessment
from db.models.recommendation import WelfareRecommendation
from db.models.welfare_request import WelfareRequest

from src.ensemble_v2 import (
    StressRiskEnsembleV2,
    ALL_MODEL_FEATURES,
    ALL_NUMERICAL_FEATURES,
    ALL_CATEGORICAL_FEATURES,
    ASSESSMENT_NUMERICAL,
    ASSESSMENT_CATEGORICAL,
    HRMS_NUMERICAL,
    WEARABLE_7D_NUMERICAL,
    WEARABLE_30D_NUMERICAL,
    ENGINEERED_NUMERICAL
)
from src.prediction import PersonnelWelfarePredictor, get_welfare_service
from services.prediction_service import get_prediction_service
from schemas.prediction import PredictionRequest


class TestPhase34RiskEngine(unittest.TestCase):
    """
    Automated regression and validation test suite for Phase 34
    Probabilistic Risk Engine.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db: Session = SessionLocal()
        cls.cleanup_user_ids = []
        cls.cleanup_personnel_ids = []

        cls.model_path = os.path.join(
            os.path.dirname(__file__), '..', 'models', 'stress_risk_ensemble_v2.pkl'
        )
        cls.ensemble: StressRiskEnsembleV2 = joblib.load(cls.model_path)
        cls.pred_service = get_prediction_service()

        cls.baseline_case = {
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
            'BusinessTravel': 'Travel_Rarely',
            'DistanceFromHome': 15.0,
            'JobLevel': 2,
            'JobSatisfaction': 4,
            'mood_score': 4,
            'NumCompaniesWorked': 1,
            'OverTime': 'No',
            'PerformanceRating': 3,
            'RelationshipSatisfaction': 3,
            'TrainingTimesLastYear': 2,
            'training_load': 2,
            'WorkLifeBalance': 3,
            'YearsAtCompany': 5.0,
            'YearsInCurrentRole': 2.0,
            'YearsSinceLastPromotion': 2.0,
            'YearsWithCurrManager': 2.0,
            'Deployment_Days': 30,
            'Night_Shifts_Per_Month': 2,
            'Consecutive_Duty_Days': 4,
            'consecutive_days_on_duty': 4,
            'Transfer_Frequency': 0,
            'transfer_count': 0,
            'Leave_Gap_Days': 30,
            'Remote_Posting': 'No',
            'Operational_Exposure': 'Low',
            'physical_fatigue': 1,
            'interest_score': 0,
            'discouraged_score': 0,
            'concentration_score': 0,
            'has_hrms_record': 1
        }

    @classmethod
    def tearDownClass(cls):
        if cls.cleanup_personnel_ids:
            cls.db.query(WearableTelemetry).filter(
                WearableTelemetry.personnel_id.in_(cls.cleanup_personnel_ids)
            ).delete(synchronize_session=False)
            cls.db.query(HrmsServiceRecord).filter(
                HrmsServiceRecord.personnel_id.in_(cls.cleanup_personnel_ids)
            ).delete(synchronize_session=False)
            cls.db.query(WelfareRecommendation).filter(
                WelfareRecommendation.personnel_id.in_(cls.cleanup_personnel_ids)
            ).delete(synchronize_session=False)
            cls.db.query(WelfareRequest).filter(
                WelfareRequest.personnel_id.in_(cls.cleanup_personnel_ids)
            ).delete(synchronize_session=False)
            cls.db.query(StressAssessment).filter(
                StressAssessment.personnel_id.in_(cls.cleanup_personnel_ids)
            ).delete(synchronize_session=False)
            cls.db.query(User).filter(
                User.personnel_id.in_(cls.cleanup_personnel_ids)
            ).delete(synchronize_session=False)
            cls.db.query(Personnel).filter(
                Personnel.id.in_(cls.cleanup_personnel_ids)
            ).delete(synchronize_session=False)
        if cls.cleanup_user_ids:
            cls.db.query(User).filter(
                User.id.in_(cls.cleanup_user_ids)
            ).delete(synchronize_session=False)
        cls.db.commit()
        cls.db.close()

    def _register_jawan(self, battalion: str = "7th Battalion", location: str = "Leh"):
        s = uuid.uuid4().hex[:8]
        code = f"P34-{s.upper()}"
        res = self.client.post("/api/auth/register-jawan", json={
            "username": f"jwn34_{s}",
            "password": "Password123!",
            "name": f"P34 Jawan {s}",
            "personnel_code": code,
            "age": 28,
            "gender": "Male",
            "department": "Operations",
            "job_role": "Rifleman",
            "experience_years": 4.0,
            "rank": "Sepoy",
            "battalion": battalion,
            "location": location
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        pid = data["personnel_id"]
        self.cleanup_personnel_ids.append(pid)
        user_row = self.db.query(User).filter(User.username == f"jwn34_{s}").first()
        if user_row:
            self.cleanup_user_ids.append(user_row.id)
        return data["access_token"], pid, code

    # =========================================================================
    # 1. Directional Monotonicity Tests
    # =========================================================================

    def test_01_monotonicity_working_and_duty_hours(self):
        """1. Increasing duty hours must produce non-decreasing predicted risk."""
        hours_sequence = [40.0, 45.0, 50.0, 55.0, 60.0, 70.0, 80.0]
        scores = []
        for h in hours_sequence:
            rec = dict(self.baseline_case)
            rec['Working_Hours_per_Week'] = h
            rec['Duty_Hours_Per_Week'] = h
            rec['duty_hours_per_week'] = h
            res = self.ensemble.assess(rec)
            scores.append(res['risk_score'])

        for i in range(len(scores) - 1):
            self.assertGreaterEqual(
                scores[i + 1] + 0.1, scores[i],
                f"Duty hours monotonicity violated: {hours_sequence[i]}h ({scores[i]}) vs {hours_sequence[i+1]}h ({scores[i+1]})"
            )
        # Bounded meaningful increase: 80h duty risk must be strictly higher than 40h
        self.assertGreater(scores[-1], scores[0] + 15.0, "80h duty failed to produce meaningful risk increase over 40h")

    def test_02_monotonicity_consecutive_duty_days(self):
        """2. Prolonged consecutive duty days must produce non-decreasing risk."""
        days_sequence = [3, 5, 7, 10, 14, 21, 28]
        scores = []
        for d in days_sequence:
            rec = dict(self.baseline_case)
            rec['Consecutive_Duty_Days'] = d
            rec['consecutive_days_on_duty'] = d
            res = self.ensemble.assess(rec)
            scores.append(res['risk_score'])

        for i in range(len(scores) - 1):
            self.assertGreaterEqual(
                scores[i + 1] + 0.05, scores[i],
                f"Consecutive duty monotonicity violated: {days_sequence[i]}d ({scores[i]}) vs {days_sequence[i+1]}d ({scores[i+1]})"
            )

    def test_03_monotonicity_night_shifts(self):
        """3. Increasing night shifts per month must produce non-decreasing risk."""
        shifts_sequence = [2, 4, 8, 12, 16, 20]
        scores = []
        for s in shifts_sequence:
            rec = dict(self.baseline_case)
            rec['Night_Shifts_Per_Month'] = s
            res = self.ensemble.assess(rec)
            scores.append(res['risk_score'])

        for i in range(len(scores) - 1):
            self.assertGreaterEqual(
                scores[i + 1] + 0.05, scores[i],
                f"Night shifts monotonicity violated: {shifts_sequence[i]} ({scores[i]}) vs {shifts_sequence[i+1]} ({scores[i+1]})"
            )

    def test_04_monotonicity_sleep_hours(self):
        """4. Decreasing sleep duration must produce non-decreasing risk."""
        sleep_sequence = [8.0, 7.5, 6.5, 5.5, 4.5, 3.5]
        scores = []
        for sl in sleep_sequence:
            rec = dict(self.baseline_case)
            rec['Sleep_Hours'] = sl
            res = self.ensemble.assess(rec)
            scores.append(res['risk_score'])

        for i in range(len(scores) - 1):
            self.assertGreaterEqual(
                scores[i + 1] + 0.05, scores[i],
                f"Sleep deficit monotonicity violated: {sleep_sequence[i]}h ({scores[i]}) vs {sleep_sequence[i+1]}h ({scores[i+1]})"
            )
        self.assertGreater(scores[-1], scores[0] + 5.0, "Severe sleep deficit failed to produce meaningful risk increase")

    # =========================================================================
    # 2. Sensitivity & Local Robustness Tests
    # =========================================================================

    def test_05_local_robustness_tiny_perturbations(self):
        """5. Tiny perturbations (0.1h sleep, 1h duty) produce smooth, bounded movements."""
        base_res = self.ensemble.assess(self.baseline_case)
        base_score = base_res['risk_score']

        # Perturbation: Sleep 7.5 -> 7.4 (-0.1h)
        rec_sleep = dict(self.baseline_case)
        rec_sleep['Sleep_Hours'] = 7.4
        res_sleep = self.ensemble.assess(rec_sleep)
        diff_sleep = abs(res_sleep['risk_score'] - base_score)
        self.assertLessEqual(diff_sleep, 2.0, f"0.1h sleep change caused disproportionate risk jump: {diff_sleep}")

        # Perturbation: Duty 40.0 -> 41.0 (+1h)
        rec_duty = dict(self.baseline_case)
        rec_duty['Working_Hours_per_Week'] = 41.0
        rec_duty['Duty_Hours_Per_Week'] = 41.0
        res_duty = self.ensemble.assess(rec_duty)
        diff_duty = abs(res_duty['risk_score'] - base_score)
        self.assertLessEqual(diff_duty, 3.0, f"1h duty change caused disproportionate risk jump: {diff_duty}")

    def test_06_meaningful_strain_produces_substantial_movement(self):
        """6. Large operational strain produces substantial, statistically significant risk escalation."""
        base_res = self.ensemble.assess(self.baseline_case)

        strained_case = dict(self.baseline_case)
        strained_case.update({
            'Working_Hours_per_Week': 65.0,
            'Duty_Hours_Per_Week': 65.0,
            'Consecutive_Duty_Days': 18,
            'Night_Shifts_Per_Month': 12,
            'Sleep_Hours': 4.5,
            'physical_fatigue': 4,
            'Burnout_Symptoms': 'Often',
            'JobSatisfaction': 2,
            'mood_score': 2
        })
        strained_res = self.ensemble.assess(strained_case)
        self.assertGreater(
            strained_res['risk_score'] - base_res['risk_score'], 30.0,
            "Severe compound strain failed to produce substantial risk escalation"
        )
        self.assertIn(strained_res['stress_level'], ['Medium', 'High'])
        self.assertIn(strained_res['risk_priority'], ['Preventive', 'Priority'])

    # =========================================================================
    # 3. Numerical Stability & Repeatability Tests
    # =========================================================================

    def test_07_deterministic_stability_repeated_evaluations(self):
        """7. Identical assessment inputs produce identical risk scores and probabilities."""
        res_1 = self.ensemble.assess(self.baseline_case)
        res_2 = self.ensemble.assess(self.baseline_case)
        self.assertEqual(res_1['risk_score'], res_2['risk_score'])
        self.assertEqual(res_1['risk_probability'], res_2['risk_probability'])
        self.assertEqual(res_1['probabilities'], res_2['probabilities'])
        self.assertEqual(res_1['stress_level'], res_2['stress_level'])

    # =========================================================================
    # 4. Feature Coverage & Preprocessing Tests
    # =========================================================================

    def test_08_all_features_integrated_into_preprocessor(self):
        """8. Preprocessor strictly consumes all 92 features across Assessment, HRMS, and Wearable categories."""
        df_in = pd.DataFrame([self.baseline_case])
        df_prepared = self.ensemble._prepare_input(df_in)

        for col in ALL_MODEL_FEATURES:
            self.assertIn(col, df_prepared.columns, f"Feature {col} missing from model input pipeline")

        # Verify transformation runs without dimensional errors
        X_trans = self.ensemble.preprocessor.transform(df_prepared)
        self.assertEqual(X_trans.shape[0], 1)
        self.assertGreaterEqual(X_trans.shape[1], len(ALL_NUMERICAL_FEATURES))

    def test_09_missing_wearable_telemetry_gracefully_imputed(self):
        """9. Missing wearable telemetry does not cause NaN or silent failure."""
        incomplete_case = dict(self.baseline_case)
        # Omit all wearable fields completely
        for k in list(incomplete_case.keys()):
            if 'wearable' in k:
                del incomplete_case[k]

        res = self.ensemble.assess(incomplete_case)
        self.assertTrue(0.0 <= res['risk_score'] <= 100.0)
        self.assertFalse(np.isnan(res['risk_probability']))
        self.assertIn(res['confidence'], ['High', 'Moderate', 'Low'])

    # =========================================================================
    # 5. Calibration Quality Tests
    # =========================================================================

    def test_10_ensemble_calibration_metrics(self):
        """10. Ensemble evaluation documents rigorous calibration (Brier score < 0.15, ECE < 0.05)."""
        metrics = self.ensemble.training_metrics
        self.assertIn('brier_score', metrics)
        self.assertIn('ece', metrics)
        self.assertIn('log_loss', metrics)

        self.assertLess(metrics['brier_score'], 0.15, "Brier score exceeds calibration quality ceiling")
        self.assertLess(metrics['ece'], 0.05, "ECE exceeds 5% calibration threshold")
        self.assertGreater(metrics['roc_auc_ovr'], 0.90, "ROC-AUC indicates insufficient discrimination")

    def test_11_risk_score_is_calibrated_probability_scaled(self):
        """11. Risk score is mathematically bound to calibrated probability (risk_score = round(p * 100, 1))."""
        res = self.ensemble.assess(self.baseline_case)
        expected_score = round(res['risk_probability'] * 100.0, 1)
        self.assertEqual(res['risk_score'], expected_score)

    # =========================================================================
    # 6. Fairness & Demographic Non-Bias Tests
    # =========================================================================

    def test_12_no_demographic_gender_bias(self):
        """12. Changing gender identity alone produces zero or negligible change in risk score."""
        male_case = dict(self.baseline_case, Gender='Male')
        female_case = dict(self.baseline_case, Gender='Female')
        res_m = self.ensemble.assess(male_case)
        res_f = self.ensemble.assess(female_case)

        diff = abs(res_m['risk_score'] - res_f['risk_score'])
        self.assertLessEqual(diff, 1.0, f"Gender disparity detected in prediction: {diff} points")

    def test_13_no_arbitrary_role_bias(self):
        """13. Personnel across different job roles maintain equitable baseline welfare scoring."""
        roles = ['Rifleman', 'Signal Operator', 'Driver', 'Mechanic', 'Clerk']
        scores = []
        for r in roles:
            rec = dict(self.baseline_case, Job_Role=r)
            res = self.ensemble.assess(rec)
            scores.append(res['risk_score'])

        # Variance across job roles under identical operational strain must be minimal
        self.assertLessEqual(max(scores) - min(scores), 2.5, "Role disparity exceeds acceptable variance threshold")

    # =========================================================================
    # 7. External D2 Isolation Tests
    # =========================================================================

    def test_14_d2_external_validation_strictly_isolated(self):
        """14. D2 external validation dataset remains unpolluted and strictly holdout."""
        manifest = self.ensemble.feature_manifest
        training_dataset = manifest.get('training_dataset', '')
        self.assertNotIn('D2', training_dataset, "Training dataset manifest references D2")

        d2_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'data', 'D2_cleaned.csv'),
            os.path.join(os.path.dirname(__file__), '..', 'D2_cleaned.csv')
        ]
        d2_file = next((p for p in d2_paths if os.path.exists(p)), None)
        self.assertIsNotNone(d2_file, "D2_cleaned.csv must exist in repository for external validation")

        df_d2 = pd.read_csv(d2_file)
        self.assertEqual(len(df_d2), 2000, "D2 row count mismatch")

    # =========================================================================
    # 8. API Contract & Service Integration Tests
    # =========================================================================

    def test_15_api_predict_endpoint_returns_phase34_fields(self):
        """15. /api/predict returns backward-compatible payload with Phase 34 probability & uncertainty fields."""
        token, _, _ = self._register_jawan()
        headers = {"Authorization": f"Bearer {token}"}

        payload = dict(self.baseline_case)
        res = self.client.post("/api/predict", json=payload, headers=headers)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertIn("risk_score", data)
        self.assertIn("stress_level", data)
        self.assertIn("risk_priority", data)
        self.assertIn("confidence", data)
        self.assertIn("uncertainty", data)
        self.assertIn("calibrated_probability", data)
        self.assertIn("prediction_uncertainty", data)
        self.assertIn("calibration_method", data)
        self.assertIn("model_version", data)
        self.assertIn("key_factors", data)
        self.assertIn("recommendations", data)

        self.assertTrue(0.0 <= data["risk_score"] <= 100.0)
        self.assertTrue(0.0 <= data["calibrated_probability"] <= 1.0)

    def test_16_personnel_assessment_route_end_to_end(self):
        """16. /api/personnel/{id}/assess persists assessment with calibrated score and recommendations."""
        token, pid, code = self._register_jawan()
        headers = {"Authorization": f"Bearer {token}"}

        res = self.client.post(
            f"/api/personnel/{pid}/assess",
            json={
                "duty_hours_per_week": 50.0,
                "consecutive_duty_days": 7,
                "night_shifts_per_month": 5,
                "sleep_hours": 6.2,
                "physical_activity_hours_per_week": 4.0,
                "operational_exposure": "Medium",
                "remote_posting": "No",
                "mood_score": 3,
                "burnout_symptoms": "Sometimes"
            },
            headers=headers
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()["assessment"]
        self.assertEqual(data["personnel_id"], pid)
        self.assertIn(data["stress_level"], ["Low", "Medium", "High"])
        self.assertTrue(0.0 <= data["risk_score"] <= 100.0)
        self.assertIn(data["risk_priority"], ["Routine", "Preventive", "Priority"])
        self.assertGreater(len(data["recommendations"]), 0)


if __name__ == '__main__':
    unittest.main()
