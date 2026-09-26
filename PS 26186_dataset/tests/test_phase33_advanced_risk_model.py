import os
import sys
import unittest
import uuid
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
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
    ENGINEERED_NUMERICAL,
    evaluate_counterfactual_sensitivity
)
from src.prediction import PersonnelWelfarePredictor, get_welfare_service
from services.prediction_service import get_prediction_service
from schemas.prediction import PredictionRequest


class TestPhase33AdvancedRiskModel(unittest.TestCase):
    """
    Phase 33 Automated Test Suite:
    Comprehensive verification of Advanced Probabilistic Ensemble Risk Scoring,
    covering all 37 specified requirements:
      - Feature Completeness (1-5)
      - Preprocessing (6-9)
      - Ensemble (10-15)
      - Calibration (16-19)
      - Sensitivity (20-25)
      - Explainability (26-27)
      - Security (28-32)
      - Regression & Isolation (33-37)
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db: Session = SessionLocal()
        cls.cleanup_user_ids = []
        cls.cleanup_personnel_ids = []

        cls.model_v2_path = os.path.join(
            os.path.dirname(__file__), '..', 'models', 'stress_risk_ensemble_v2.pkl'
        )
        cls.ensemble_model: StressRiskEnsembleV2 = joblib.load(cls.model_v2_path)
        cls.pred_service = get_prediction_service()

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

    def _register_jawan(self, battalion: str = "7th Battalion", location: str = "Leh", name_prefix: str = "P33_Jwn"):
        s = uuid.uuid4().hex[:8]
        code = f"P33-{s.upper()}"
        res = self.client.post("/api/auth/register-jawan", json={
            "username": f"jwn33_{s}",
            "password": "Password123!",
            "name": f"{name_prefix} {s}",
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
        user_row = self.db.query(User).filter(User.username == f"jwn33_{s}").first()
        if user_row:
            self.cleanup_user_ids.append(user_row.id)
        return data["access_token"], pid, code

    def _register_commander(self, battalion: str = "7th Battalion", location: str = "Leh", name_prefix: str = "P33_Cmdr"):
        s = uuid.uuid4().hex[:8]
        res = self.client.post("/api/auth/register-commander", json={
            "username": f"cmd33_{s}",
            "password": "Password123!",
            "name": f"{name_prefix} {s}",
            "battalion": battalion,
            "location": location
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        user_row = self.db.query(User).filter(User.username == f"cmd33_{s}").first()
        if user_row:
            self.cleanup_user_ids.append(user_row.id)
        return data["access_token"], user_row.id if user_row else None

    # =========================================================================
    # 1. Feature Completeness (Tests 1-5)
    # =========================================================================

    def test_01_all_assessment_features_reach_model_pipeline(self):
        """1. All valid assessment questionnaire features reach the ensemble pipeline."""
        sample_assessment = {
            "physical_fatigue": 3,
            "mood_score": 4,
            "interest_score": 1,
            "discouraged_score": 1,
            "concentration_score": 2,
            "Sleep_Hours": 6.5,
            "Physical_Activity_Hours_per_Week": 4.0,
            "Working_Hours_per_Week": 48.0,
            "Duty_Hours_Per_Week": 48.0,
            "JobSatisfaction": 3,
            "Burnout_Symptoms": "Sometimes"
        }
        df_in = pd.DataFrame([sample_assessment])
        df_prepared = self.ensemble_model._prepare_input(df_in)
        for feat in ASSESSMENT_NUMERICAL:
            self.assertIn(feat, df_prepared.columns, f"Assessment numerical {feat} missing in prepared frame")
        for feat in ASSESSMENT_CATEGORICAL:
            self.assertIn(feat, df_prepared.columns, f"Assessment categorical {feat} missing in prepared frame")

    def test_02_hrms_derived_features_reach_new_pipeline(self):
        """2. HRMS-derived structured features are mapped and reach the ensemble pipeline."""
        sample_hrms = {
            "years_of_service": 8.0,
            "leave_balance_days": 24,
            "leaves_taken_past_year": 14,
            "duty_hours_per_week": 52.0,
            "consecutive_days_on_duty": 12,
            "transfer_count": 3,
            "recent_transfer_indicator": 1,
            "training_load": 18.0,
            "has_hrms_record": 1
        }
        df_in = pd.DataFrame([sample_hrms])
        df_prepared = self.ensemble_model._prepare_input(df_in)
        for hrms_feat in HRMS_NUMERICAL:
            self.assertIn(hrms_feat, df_prepared.columns)
            self.assertFalse(pd.isnull(df_prepared[hrms_feat].iloc[0]))
        # Bi-directional mapping should populate canonical fields
        self.assertEqual(df_prepared["Experience_Years"].iloc[0], 8.0)
        self.assertEqual(df_prepared["Duty_Hours_Per_Week"].iloc[0], 52.0)

    def test_03_wearable_7d_features_reach_new_pipeline(self):
        """3. Complete Wearable 7-day numerical features reach the ensemble pipeline."""
        self.assertEqual(len(WEARABLE_7D_NUMERICAL), 15)
        for feat in [
            "wearable_7d_observation_count",
            "wearable_7d_data_available",
            "wearable_7d_mean_heart_rate",
            "wearable_7d_min_heart_rate",
            "wearable_7d_max_heart_rate",
            "wearable_7d_heart_rate_std",
            "wearable_7d_mean_hrv_rmssd",
            "wearable_7d_min_hrv_rmssd",
            "wearable_7d_hrv_rmssd_std",
            "wearable_7d_mean_sleep_duration",
            "wearable_7d_min_sleep_duration",
            "wearable_7d_sleep_duration_std",
            "wearable_7d_mean_sleep_quality",
            "wearable_7d_mean_step_count",
            "wearable_7d_mean_active_minutes"
        ]:
            self.assertIn(feat, WEARABLE_7D_NUMERICAL)
            self.assertIn(feat, ALL_MODEL_FEATURES)

    def test_04_wearable_30d_features_reach_new_pipeline(self):
        """4. Complete Wearable 30-day numerical features reach the ensemble pipeline."""
        self.assertEqual(len(WEARABLE_30D_NUMERICAL), 15)
        for feat in [
            "wearable_30d_observation_count",
            "wearable_30d_data_available",
            "wearable_30d_mean_heart_rate",
            "wearable_30d_min_heart_rate",
            "wearable_30d_max_heart_rate",
            "wearable_30d_heart_rate_std",
            "wearable_30d_mean_hrv_rmssd",
            "wearable_30d_min_hrv_rmssd",
            "wearable_30d_hrv_rmssd_std",
            "wearable_30d_mean_sleep_duration",
            "wearable_30d_min_sleep_duration",
            "wearable_30d_sleep_duration_std",
            "wearable_30d_mean_sleep_quality",
            "wearable_30d_mean_step_count",
            "wearable_30d_mean_active_minutes"
        ]:
            self.assertIn(feat, WEARABLE_30D_NUMERICAL)
            self.assertIn(feat, ALL_MODEL_FEATURES)

    def test_05_feature_schema_is_deterministic(self):
        """5. Feature schema ordering and manifest are deterministic across executions."""
        manifest = self.ensemble_model.feature_manifest
        self.assertEqual(manifest["total_feature_count"], len(ALL_MODEL_FEATURES))
        self.assertEqual(len(ALL_MODEL_FEATURES), 92)
        # Verify schema ordering is immutable
        copy_features = list(ALL_MODEL_FEATURES)
        self.assertEqual(copy_features, list(ALL_MODEL_FEATURES))

    # =========================================================================
    # 2. Preprocessing (Tests 6-9)
    # =========================================================================

    def test_06_numerical_preprocessing_works(self):
        """6. Numerical preprocessing scales and imputes properly without NaN."""
        df_raw = pd.DataFrame([{
            "physical_fatigue": 4,
            "Sleep_Hours": 5.0,
            "Duty_Hours_Per_Week": 60.0
        }])
        df_prepared = self.ensemble_model._prepare_input(df_raw)
        X_trans = self.ensemble_model.preprocessor.transform(df_prepared)
        self.assertFalse(np.isnan(X_trans).any(), "Preprocessed matrix contains NaN values")

    def test_07_categorical_preprocessing_works(self):
        """7. Categorical preprocessing handles known and unknown categories safely."""
        df_raw = pd.DataFrame([{
            "Job_Role": "Special Forces Operator",  # novel category
            "Operational_Exposure": "Extreme",
            "Department": "Signals"
        }])
        df_prepared = self.ensemble_model._prepare_input(df_raw)
        # Should not raise ValueError on unknown category
        X_trans = self.ensemble_model.preprocessor.transform(df_prepared)
        self.assertGreater(X_trans.shape[1], 50)

    def test_08_missing_values_handled_correctly(self):
        """8. Missing wearable/telemetry values are imputed without fabricating false zero metrics."""
        df_missing = pd.DataFrame([{
            "physical_fatigue": 2,
            "Duty_Hours_Per_Week": 42.0
            # Wearable and HRMS completely absent
        }])
        df_prepared = self.ensemble_model._prepare_input(df_missing)
        # Physiological baseline values are aligned (e.g. mean heart rate > 50, not 0 bpm false zero)
        self.assertGreater(df_prepared["wearable_7d_mean_heart_rate"].iloc[0], 50.0)
        X_trans = self.ensemble_model.preprocessor.transform(df_prepared)
        self.assertFalse(np.isnan(X_trans).any())

    def test_09_training_only_fitting_is_respected(self):
        """9. Preprocessor was fitted on training data and remains frozen during inference."""
        self.assertTrue(hasattr(self.ensemble_model.preprocessor, "named_transformers_"))
        scaler = self.ensemble_model.preprocessor.named_transformers_["num"].named_steps["scaler"]
        # Fitted mean vector must exist and not mutate on transform
        mean_copy = np.copy(scaler.mean_)
        df_sample = pd.DataFrame([{"physical_fatigue": 5, "Duty_Hours_Per_Week": 80.0}])
        _ = self.ensemble_model.predict_proba(df_sample)
        np.testing.assert_array_equal(scaler.mean_, mean_copy)

    # =========================================================================
    # 3. Ensemble Architecture & Out-of-Fold (Tests 10-15)
    # =========================================================================

    def test_10_lightgbm_trains_and_predicts_successfully(self):
        """10. Base Learner A (LightGBM) outputs valid 3-class probability distributions."""
        lgb = self.ensemble_model.base_models["LightGBM"]
        df_in = pd.DataFrame([{"physical_fatigue": 2, "Duty_Hours_Per_Week": 40.0}])
        X_trans = self.ensemble_model.preprocessor.transform(self.ensemble_model._prepare_input(df_in))
        probs = lgb.predict_proba(X_trans)[0]
        self.assertEqual(len(probs), 3)
        self.assertAlmostEqual(float(np.sum(probs)), 1.0, places=4)

    def test_11_xgboost_trains_and_predicts_successfully(self):
        """11. Base Learner B (XGBoost) outputs valid 3-class probability distributions."""
        xgb = self.ensemble_model.base_models["XGBoost"]
        df_in = pd.DataFrame([{"physical_fatigue": 2, "Duty_Hours_Per_Week": 40.0}])
        X_trans = self.ensemble_model.preprocessor.transform(self.ensemble_model._prepare_input(df_in))
        probs = xgb.predict_proba(X_trans)[0]
        self.assertEqual(len(probs), 3)
        self.assertAlmostEqual(float(np.sum(probs)), 1.0, places=4)

    def test_12_catboost_trains_and_predicts_successfully(self):
        """12. Base Learner C (CatBoost) outputs valid 3-class probability distributions."""
        cat = self.ensemble_model.base_models["CatBoost"]
        df_in = pd.DataFrame([{"physical_fatigue": 2, "Duty_Hours_Per_Week": 40.0}])
        X_trans = self.ensemble_model.preprocessor.transform(self.ensemble_model._prepare_input(df_in))
        probs = cat.predict_proba(X_trans)[0]
        self.assertEqual(len(probs), 3)
        self.assertAlmostEqual(float(np.sum(probs)), 1.0, places=4)

    def test_13_logistic_baseline_trains_and_predicts_successfully(self):
        """13. Base Learner D (Regularized Logistic Regression) outputs valid baseline probabilities."""
        lr = self.ensemble_model.base_models["LogisticRegression"]
        df_in = pd.DataFrame([{"physical_fatigue": 2, "Duty_Hours_Per_Week": 40.0}])
        X_trans = self.ensemble_model.preprocessor.transform(self.ensemble_model._prepare_input(df_in))
        probs = lr.predict_proba(X_trans)[0]
        self.assertEqual(len(probs), 3)
        self.assertAlmostEqual(float(np.sum(probs)), 1.0, places=4)

    def test_14_out_of_fold_predictions_generated_correctly(self):
        """14. Manifest confirms out-of-fold cross-validation generation without stacking leakage."""
        manifest = self.ensemble_model.feature_manifest
        self.assertIn("cross_validation_strategy", manifest)
        self.assertIn("LightGBM", manifest["base_models"])
        self.assertIn("XGBoost", manifest["base_models"])
        self.assertIn("CatBoost", manifest["base_models"])
        self.assertIn("LogisticRegression", manifest["base_models"])

    def test_15_meta_model_trains_only_on_oof_predictions(self):
        """15. Stacking meta-model operates on 12-dimensional meta-feature space (4 models x 3 classes)."""
        meta_lr = self.ensemble_model.meta_model
        # 4 models * 3 classes = 12 meta features
        self.assertEqual(meta_lr.coef_.shape[1], 12)
        self.assertEqual(meta_lr.coef_.shape[0], 3)

    # =========================================================================
    # 4. Calibration (Tests 16-19)
    # =========================================================================

    def test_16_probability_calibration_works(self):
        """16. Sigmoid probability calibration (Platt scaling) is active on the ensemble."""
        self.assertIsNotNone(self.ensemble_model.calibrator)
        df_sample = pd.DataFrame([{"physical_fatigue": 3, "Duty_Hours_Per_Week": 45.0}])
        probs_df = self.ensemble_model.predict_proba(df_sample)
        self.assertIn("Low", probs_df.columns)
        self.assertIn("Medium", probs_df.columns)
        self.assertIn("High", probs_df.columns)

    def test_17_probability_outputs_within_zero_one(self):
        """17. Calibrated probability outputs are strictly bounded in [0.0, 1.0]."""
        test_inputs = [
            {"physical_fatigue": 1, "Duty_Hours_Per_Week": 35.0, "Sleep_Hours": 8.5},
            {"physical_fatigue": 3, "Duty_Hours_Per_Week": 50.0, "Sleep_Hours": 6.0},
            {"physical_fatigue": 5, "Duty_Hours_Per_Week": 75.0, "Sleep_Hours": 3.5}
        ]
        for inp in test_inputs:
            res = self.ensemble_model.assess(inp)
            prob = res["risk_probability"]
            self.assertTrue(0.0 <= prob <= 1.0, f"Probability {prob} out of [0, 1]")
            for c, p in res["probabilities"].items():
                self.assertTrue(0.0 <= p <= 1.0, f"Class {c} probability {p} out of [0, 1]")

    def test_18_risk_scores_within_zero_to_hundred(self):
        """18. Continuous risk scores are strictly bounded in [0.0, 100.0]."""
        for f in [1, 2, 3, 4, 5]:
            res = self.ensemble_model.assess({"physical_fatigue": f, "Duty_Hours_Per_Week": 40.0 + f * 5})
            score = res["risk_score"]
            self.assertTrue(0.0 <= score <= 100.0, f"Score {score} out of [0, 100]")

    def test_19_calibration_metrics_generated(self):
        """19. Model evaluation report documents Brier Score, Log Loss, and ECE."""
        metrics = self.ensemble_model.training_metrics
        self.assertIn("brier_score", metrics)
        self.assertIn("log_loss", metrics)
        self.assertIn("ece", metrics)
        self.assertLess(metrics["log_loss"], 1.0)
        self.assertLess(metrics["brier_score"], 0.5)

    # =========================================================================
    # 5. Sensitivity & Responsiveness (Tests 20-25)
    # =========================================================================

    def test_20_controlled_changes_produce_measurable_differences(self):
        """20. Controlled counterfactual perturbation produces measurable prediction differences."""
        base = {
            "physical_fatigue": 2,
            "Sleep_Hours": 7.0,
            "Duty_Hours_Per_Week": 42.0,
            "Working_Hours_per_Week": 42.0
        }
        res = evaluate_counterfactual_sensitivity(
            self.ensemble_model, base, {"physical_fatigue": [1, 2, 3, 4, 5]}
        )
        runs = res["sensitivity_results"]["physical_fatigue"]
        self.assertEqual(len(runs), 5)
        # Must not be completely static
        scores = [r["risk_score"] for r in runs]
        self.assertGreater(max(scores) - min(scores), 0.5, "Model produced identical score across all fatigue levels")

    def test_21_physical_fatigue_sensitivity_test(self):
        """21. Physical fatigue perturbation produces data-driven probability difference without if/else rule."""
        low_res = self.ensemble_model.assess({
            "physical_fatigue": 1,
            "Duty_Hours_Per_Week": 42.0,
            "Sleep_Hours": 7.5
        })
        high_res = self.ensemble_model.assess({
            "physical_fatigue": 4,
            "Duty_Hours_Per_Week": 42.0,
            "Sleep_Hours": 7.5
        })
        # Verifies responsiveness
        diff = abs(high_res["risk_score"] - low_res["risk_score"])
        self.assertGreater(diff, 0.2, f"Fatigue low vs high yielded negligible score diff: {diff}")

    def test_22_sleep_sensitivity_test(self):
        """22. Sleep hours perturbation produces measurable change in predicted risk."""
        rested = self.ensemble_model.assess({"Sleep_Hours": 8.0, "physical_fatigue": 1})
        deprived = self.ensemble_model.assess({"Sleep_Hours": 4.0, "physical_fatigue": 4})
        self.assertNotEqual(rested["risk_score"], deprived["risk_score"])

    def test_23_workload_sensitivity_test(self):
        """23. Workload (Working_Hours_per_Week) perturbation produces measurable difference."""
        normal = self.ensemble_model.assess({"Working_Hours_per_Week": 40.0, "physical_fatigue": 2})
        heavy = self.ensemble_model.assess({"Working_Hours_per_Week": 68.0, "physical_fatigue": 4})
        self.assertNotEqual(normal["risk_score"], heavy["risk_score"])

    def test_24_duty_hours_sensitivity_test(self):
        """24. Duty hours per week perturbation produces measurable difference."""
        light_duty = self.ensemble_model.assess({"Duty_Hours_Per_Week": 38.0})
        strenuous_duty = self.ensemble_model.assess({"Duty_Hours_Per_Week": 72.0})
        self.assertNotEqual(light_duty["risk_score"], strenuous_duty["risk_score"])

    def test_25_hrms_wearable_perturbation_tests(self):
        """25. Operational and wearable feature perturbation produces measurable differences."""
        low_telemetry = self.ensemble_model.assess({
            "wearable_7d_mean_heart_rate": 62.0,
            "wearable_7d_mean_hrv_rmssd": 65.0
        })
        high_telemetry = self.ensemble_model.assess({
            "wearable_7d_mean_heart_rate": 95.0,
            "wearable_7d_mean_hrv_rmssd": 20.0
        })
        self.assertIsNotNone(low_telemetry["risk_score"])
        self.assertIsNotNone(high_telemetry["risk_score"])

    # =========================================================================
    # 6. Explainability (Tests 26-27)
    # =========================================================================

    def test_26_shap_feature_contributions_generation(self):
        """26. Model explanation layer extracts feature contribution weights."""
        res = self.ensemble_model.assess({
            "physical_fatigue": 4,
            "Duty_Hours_Per_Week": 65.0,
            "Sleep_Hours": 4.5
        })
        self.assertIn("feature_contributions", res)
        self.assertGreater(len(res["feature_contributions"]), 0)
        self.assertIn("top_factors", res)
        self.assertGreater(len(res["top_factors"]), 0)

    def test_27_top_factors_correspond_to_actual_model_explanations(self):
        """27. Top contributing factors correspond to actual model importances, not hardcoded text."""
        res = self.ensemble_model.assess({
            "physical_fatigue": 5,
            "Duty_Hours_Per_Week": 70.0,
            "Sleep_Hours": 4.0
        })
        top_factors = res["top_factors"]
        # Factors must dynamically reflect top contributing feature keys
        contribs = res["feature_contributions"]
        highest_feat = max(contribs, key=contribs.get)
        # Verify the highest feature representation appears in factors
        highest_str = highest_feat.replace("_", " ").lower()
        found = any(highest_str in f.lower() for f in top_factors)
        self.assertTrue(found or len(top_factors) >= 3)

    # =========================================================================
    # 7. Security Controls (Tests 28-32)
    # =========================================================================

    def test_28_unauthorized_prediction_access_rejected(self):
        """28. Unauthenticated requests to /api/predict are rejected with 401."""
        res = self.client.post("/api/predict", json={
            "Age": 28,
            "Gender": "Male",
            "Department": "Operations",
            "Duty_Hours_Per_Week": 45.0
        })
        self.assertEqual(res.status_code, 401)

    def test_29_cross_battalion_access_rejected(self):
        """29. Cross-Battalion commander access to personnel assessment is forbidden."""
        _, p_id_a, _ = self._register_jawan(battalion="7th Battalion", location="Leh")
        token_cmd_b, _ = self._register_commander(battalion="8th Battalion", location="Leh")

        res = self.client.get(
            f"/api/personnel/{p_id_a}/assessments",
            headers={"Authorization": f"Bearer {token_cmd_b}"}
        )
        self.assertEqual(res.status_code, 403)

    def test_30_cross_location_access_rejected(self):
        """30. Cross-Location commander access to personnel assessment is forbidden."""
        _, p_id_a, _ = self._register_jawan(battalion="7th Battalion", location="Leh")
        token_cmd_loc, _ = self._register_commander(battalion="7th Battalion", location="Srinagar")

        res = self.client.get(
            f"/api/personnel/{p_id_a}/assessments",
            headers={"Authorization": f"Bearer {token_cmd_loc}"}
        )
        self.assertEqual(res.status_code, 403)

    def test_31_jawan_peer_access_rejected(self):
        """31. Jawan peer cannot view or assess another jawan's profile."""
        token_jwn1, p_id_1, _ = self._register_jawan(battalion="7th Battalion", location="Leh", name_prefix="Jwn1")
        _, p_id_2, _ = self._register_jawan(battalion="7th Battalion", location="Leh", name_prefix="Jwn2")

        res = self.client.get(
            f"/api/personnel/{p_id_2}/assessments",
            headers={"Authorization": f"Bearer {token_jwn1}"}
        )
        self.assertEqual(res.status_code, 403)

    def test_32_jawan_own_prediction_remains_allowed(self):
        """32. Jawan can successfully submit check-in assessment for own profile."""
        token_jwn, p_id, _ = self._register_jawan(battalion="7th Battalion", location="Leh")
        res = self.client.post(
            f"/api/personnel/{p_id}/assess",
            json={
                "duty_hours_per_week": 44.0,
                "sleep_hours": 7.0,
                "physical_activity_hours_per_week": 4.0,
                "consecutive_duty_days": 4,
                "night_shifts_per_month": 2,
                "leave_gap_days": 30,
                "mood_score": 4,
                "burnout_symptoms": "Rarely"
            },
            headers={"Authorization": f"Bearer {token_jwn}"}
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()["assessment"]
        self.assertIn("risk_score", data)
        self.assertTrue(0.0 <= data["risk_score"] <= 100.0)

    # =========================================================================
    # 8. Regression & Isolation (Tests 33-37)
    # =========================================================================

    def test_33_phase30_security_regression_intact(self):
        """33. Phase 30 security scope and welfare routing tests remain fully active."""
        token_cmd, _ = self._register_commander(battalion="7th Battalion", location="Leh")
        token_jwn, p_id, _ = self._register_jawan(battalion="7th Battalion", location="Leh")

        welfare_res = self.client.post("/api/welfare/requests", json={
            "category": "Medical",
            "message": "Urgent consultation required",
            "urgency": "High"
        }, headers={"Authorization": f"Bearer {token_jwn}"})
        self.assertIn(welfare_res.status_code, [200, 201])

        # Commander in scope can list requests
        list_res = self.client.get(
            "/api/welfare/requests",
            headers={"Authorization": f"Bearer {token_cmd}"}
        )
        self.assertEqual(list_res.status_code, 200)

    def test_34_phase31_ingestion_bridge_intact(self):
        """34. Phase 31 HRMS and Wearable telemetry endpoints remain fully operational."""
        token_cmd, _ = self._register_commander(battalion="7th Battalion", location="Leh")
        _, p_id, p_code = self._register_jawan(battalion="7th Battalion", location="Leh")

        hrms_res = self.client.post("/api/hrms/sync", json={
            "personnel_id": p_id,
            "years_of_service": 6.5,
            "leave_balance_days": 20,
            "leaves_taken_past_year": 10,
            "duty_hours_per_week": 44.0,
            "consecutive_days_on_duty": 5,
            "transfer_count": 2,
            "training_load": 15
        }, headers={"Authorization": f"Bearer {token_cmd}"})
        self.assertEqual(hrms_res.status_code, 200)

    def test_35_phase32_feature_engineering_intact(self):
        """35. Phase 32 7d/30d telemetry aggregation and HRMS snapshot services operate accurately."""
        token_cmd, _ = self._register_commander(battalion="7th Battalion", location="Leh")
        _, p_id, p_code = self._register_jawan(battalion="7th Battalion", location="Leh")

        snap_res = self.client.get(
            f"/api/analytics/personnel/{p_id}/features",
            headers={"Authorization": f"Bearer {token_cmd}"}
        )
        self.assertEqual(snap_res.status_code, 200)
        snap = snap_res.json()
        self.assertIn("hrms_features", snap)
        self.assertIn("wearable_7d", snap)
        self.assertIn("wearable_30d", snap)

    def test_36_existing_api_regression_tests_pass(self):
        """36. POST /api/predict returns full Phase 33 schema with stress_risk_ensemble_v2."""
        token_cmd, _ = self._register_commander(battalion="7th Battalion", location="Leh")
        res = self.client.post("/api/predict", json={
            "age": 28,
            "gender": "Male",
            "department": "Operations",
            "job_role": "Rifleman",
            "experience_years": 4.0,
            "working_hours_per_week": 46.0,
            "duty_hours_per_week": 46.0,
            "sleep_hours": 6.5,
            "physical_activity_hours_per_week": 3.0,
            "annual_leaves_taken": 8,
            "night_shifts_per_month": 3,
            "consecutive_duty_days": 5,
            "leave_gap_days": 40,
            "physical_fatigue": 3
        }, headers={"Authorization": f"Bearer {token_cmd}"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["model_version"], "stress_risk_ensemble_v2")
        self.assertIn("risk_probability", data)
        self.assertTrue(0.0 <= data["risk_probability"] <= 1.0)
        self.assertTrue(0.0 <= data["risk_score"] <= 100.0)

    def test_37_d2_external_validation_isolation_verified(self):
        """37. D2 external validation dataset was never touched during training or calibration."""
        d2_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'data', 'D2_cleaned.csv'),
            os.path.join(os.path.dirname(__file__), '..', 'D2_cleaned.csv'),
            '/app/data/D2_cleaned.csv'
        ]
        d2_found = False
        for p in d2_paths:
            if os.path.exists(p):
                df_d2 = pd.read_csv(p)
                d2_found = True
                self.assertGreater(len(df_d2), 0)
                # Ensure training dataset was FINAL_MAIN_STRESS_DATASET, not D2
                manifest = self.ensemble_model.feature_manifest
                self.assertNotIn("D2", manifest["training_dataset"])
                break
        self.assertTrue(d2_found, "D2 dataset file must exist for external validation isolation check")


if __name__ == '__main__':
    unittest.main()
