"""
Phase 33 — Advanced Probabilistic Ensemble Risk Model Definition
Provides:
  - StressRiskEnsembleV2 inference class
  - Feature lists & mappings (Assessment, HRMS, Wearable 7d/30d, Derived)
  - Controlled counterfactual sensitivity evaluation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional

from src.model_training import CLASS_NAMES, LABEL_TO_INT, INT_TO_LABEL
from src.feature_engineering import engineer_features

ASSESSMENT_NUMERICAL = [
    'physical_fatigue',
    'mood_score',
    'interest_score',
    'discouraged_score',
    'concentration_score',
    'Sleep_Hours',
    'Physical_Activity_Hours_per_Week',
    'Working_Hours_per_Week',
    'Duty_Hours_Per_Week',
    'Consecutive_Duty_Days',
    'Night_Shifts_Per_Month',
    'Leave_Gap_Days',
    'Deployment_Days',
    'Transfer_Frequency',
    'Training_Load',
    'Age',
    'Experience_Years',
    'Monthly_Salary_INR',
    'Annual_Leaves_Taken',
    'Team_Size',
    'Commute_Time_Hours',
    'DistanceFromHome',
    'JobLevel',
    'JobSatisfaction',
    'NumCompaniesWorked',
    'PerformanceRating',
    'RelationshipSatisfaction',
    'TrainingTimesLastYear',
    'WorkLifeBalance',
    'YearsAtCompany',
    'YearsInCurrentRole',
    'YearsSinceLastPromotion',
    'YearsWithCurrManager'
]

ASSESSMENT_CATEGORICAL = [
    'Gender',
    'Marital_Status',
    'Location',
    'Job_Role',
    'Company_Size',
    'Department',
    'Remote_Work',
    'Health_Issues',
    'Mental_Health_Leave_Taken',
    'Burnout_Symptoms',
    'BusinessTravel',
    'OverTime',
    'Remote_Posting',
    'Operational_Exposure'
]

HRMS_NUMERICAL = [
    'years_of_service',
    'leave_balance_days',
    'leaves_taken_past_year',
    'duty_hours_per_week',
    'consecutive_days_on_duty',
    'transfer_count',
    'recent_transfer_indicator',
    'training_load',
    'has_hrms_record'
]

WEARABLE_7D_NUMERICAL = [
    'wearable_7d_observation_count',
    'wearable_7d_data_available',
    'wearable_7d_mean_heart_rate',
    'wearable_7d_min_heart_rate',
    'wearable_7d_max_heart_rate',
    'wearable_7d_heart_rate_std',
    'wearable_7d_mean_hrv_rmssd',
    'wearable_7d_min_hrv_rmssd',
    'wearable_7d_hrv_rmssd_std',
    'wearable_7d_mean_sleep_duration',
    'wearable_7d_min_sleep_duration',
    'wearable_7d_sleep_duration_std',
    'wearable_7d_mean_sleep_quality',
    'wearable_7d_mean_step_count',
    'wearable_7d_mean_active_minutes'
]

WEARABLE_30D_NUMERICAL = [
    'wearable_30d_observation_count',
    'wearable_30d_data_available',
    'wearable_30d_mean_heart_rate',
    'wearable_30d_min_heart_rate',
    'wearable_30d_max_heart_rate',
    'wearable_30d_heart_rate_std',
    'wearable_30d_mean_hrv_rmssd',
    'wearable_30d_min_hrv_rmssd',
    'wearable_30d_hrv_rmssd_std',
    'wearable_30d_mean_sleep_duration',
    'wearable_30d_min_sleep_duration',
    'wearable_30d_sleep_duration_std',
    'wearable_30d_mean_sleep_quality',
    'wearable_30d_mean_step_count',
    'wearable_30d_mean_active_minutes'
]

ENGINEERED_NUMERICAL = [
    'workload_intensity_ratio',
    'sleep_debt_index',
    'night_shift_burden',
    'recovery_deficit_score',
    'active_recovery_ratio',
    'deployment_fatigue_factor'
]

ALL_NUMERICAL_FEATURES = (
    ASSESSMENT_NUMERICAL +
    HRMS_NUMERICAL +
    WEARABLE_7D_NUMERICAL +
    WEARABLE_30D_NUMERICAL +
    ENGINEERED_NUMERICAL
)

ALL_CATEGORICAL_FEATURES = ASSESSMENT_CATEGORICAL

ALL_MODEL_FEATURES = ALL_NUMERICAL_FEATURES + ALL_CATEGORICAL_FEATURES


class StressRiskEnsembleV2:
    """
    Phase 33 Production Probabilistic Ensemble Risk Predictor.
    Combines:
      - Feature Preprocessor (StandardScaler + OneHotEncoder)
      - 4 Trained Base Learners: LightGBM, XGBoost, CatBoost, Regularized Logistic Regression
      - Out-of-Fold Trained Stacking Meta-Learner (LogisticRegression)
      - Sigmoid Probability Calibrator
    """
    def __init__(
        self,
        preprocessor: Any,
        base_models: Dict[str, Any],
        meta_model: Any,
        calibrator: Any,
        feature_manifest: Dict[str, Any],
        training_metrics: Dict[str, Any]
    ):
        self.preprocessor = preprocessor
        self.base_models = base_models
        self.meta_model = meta_model
        self.calibrator = calibrator
        self.feature_manifest = feature_manifest
        self.training_metrics = training_metrics
        self.model_version = "stress_risk_ensemble_v2"
        self.class_names = CLASS_NAMES
        self.label_to_int = LABEL_TO_INT
        self.int_to_label = INT_TO_LABEL

    def _prepare_input(self, X_input: pd.DataFrame) -> pd.DataFrame:
        df = X_input.copy()
        
        # Assessment score derivations if missing
        if 'Duty_Hours_Per_Week' in df.columns and ('Working_Hours_per_Week' not in df.columns or df['Working_Hours_per_Week'].isnull().any()):
            df['Working_Hours_per_Week'] = df['Duty_Hours_Per_Week']
        elif 'Working_Hours_per_Week' in df.columns and ('Duty_Hours_Per_Week' not in df.columns or df['Duty_Hours_Per_Week'].isnull().any()):
            df['Duty_Hours_Per_Week'] = df['Working_Hours_per_Week']
            
        if 'mood_score' not in df.columns:
            df['mood_score'] = df.get('JobSatisfaction', 3)
        if 'physical_fatigue' not in df.columns or df['physical_fatigue'].isnull().any():
            sleep_v = df.get('Sleep_Hours', 7.5)
            duty_v = df.get('Duty_Hours_Per_Week', 40.0)
            f_calc = 1.0 + (np.maximum(0.0, 8.0 - sleep_v) / 4.0) + (np.maximum(0.0, duty_v - 40.0) / 35.0)
            df['physical_fatigue'] = df.get('physical_fatigue', np.clip(np.round(f_calc), 1, 5))
            
        for col in ['interest_score', 'discouraged_score', 'concentration_score']:
            if col not in df.columns:
                df[col] = 0
                
        # Structured HRMS bidirectional mappings
        if 'years_of_service' in df.columns and ('Experience_Years' not in df.columns or df['Experience_Years'].isnull().any()):
            df['Experience_Years'] = df['years_of_service']
        elif 'Experience_Years' in df.columns and ('years_of_service' not in df.columns or df['years_of_service'].isnull().any()):
            df['years_of_service'] = df['Experience_Years']

        if 'duty_hours_per_week' in df.columns and ('Duty_Hours_Per_Week' not in df.columns or df['Duty_Hours_Per_Week'].isnull().any()):
            df['Duty_Hours_Per_Week'] = df['duty_hours_per_week']
            df['Working_Hours_per_Week'] = df['duty_hours_per_week']
        elif 'Duty_Hours_Per_Week' in df.columns and ('duty_hours_per_week' not in df.columns or df['duty_hours_per_week'].isnull().any()):
            df['duty_hours_per_week'] = df['Duty_Hours_Per_Week']

        if 'consecutive_days_on_duty' in df.columns and ('Consecutive_Duty_Days' not in df.columns or df['Consecutive_Duty_Days'].isnull().any()):
            df['Consecutive_Duty_Days'] = df['consecutive_days_on_duty']
        elif 'Consecutive_Duty_Days' in df.columns and ('consecutive_days_on_duty' not in df.columns or df['consecutive_days_on_duty'].isnull().any()):
            df['consecutive_days_on_duty'] = df['Consecutive_Duty_Days']

        if 'leaves_taken_past_year' in df.columns and ('Annual_Leaves_Taken' not in df.columns or df['Annual_Leaves_Taken'].isnull().any()):
            df['Annual_Leaves_Taken'] = df['leaves_taken_past_year']
        elif 'Annual_Leaves_Taken' in df.columns and ('leaves_taken_past_year' not in df.columns or df['leaves_taken_past_year'].isnull().any()):
            df['leaves_taken_past_year'] = df['Annual_Leaves_Taken']

        if 'leave_balance_days' in df.columns and ('Leave_Gap_Days' not in df.columns or df['Leave_Gap_Days'].isnull().any()):
            df['Leave_Gap_Days'] = df['leave_balance_days']
        elif 'Leave_Gap_Days' in df.columns and ('leave_balance_days' not in df.columns or df['leave_balance_days'].isnull().any()):
            df['leave_balance_days'] = df['Leave_Gap_Days']

        if 'transfer_count' in df.columns and ('Transfer_Frequency' not in df.columns or df['Transfer_Frequency'].isnull().any()):
            df['Transfer_Frequency'] = df['transfer_count']
        elif 'Transfer_Frequency' in df.columns and ('transfer_count' not in df.columns or df['transfer_count'].isnull().any()):
            df['transfer_count'] = df['Transfer_Frequency']

        if 'training_load' in df.columns and ('Training_Load' not in df.columns or df['Training_Load'].isnull().any()):
            df['Training_Load'] = df['training_load']
        elif 'Training_Load' in df.columns and ('training_load' not in df.columns or df['training_load'].isnull().any()):
            df['training_load'] = df['Training_Load']

        if 'recent_transfer_indicator' not in df.columns:
            if 'Transfer_Frequency' in df.columns:
                df['recent_transfer_indicator'] = (df['Transfer_Frequency'] > 0).astype(int)
            else:
                df['recent_transfer_indicator'] = 0
        if 'has_hrms_record' not in df.columns:
            df['has_hrms_record'] = 1
            
        # Wearable missing indicators with physiological baseline alignment
        pf_val = df.get('physical_fatigue', 3)
        if 'wearable_7d_observation_count' not in df.columns:
            df['wearable_7d_observation_count'] = 0
        if 'wearable_7d_data_available' not in df.columns:
            df['wearable_7d_data_available'] = 0
        if 'wearable_7d_mean_heart_rate' not in df.columns:
            df['wearable_7d_mean_heart_rate'] = np.clip(68.0 + (pf_val * 4.0), 55.0, 110.0)
        if 'wearable_7d_min_heart_rate' not in df.columns:
            df['wearable_7d_min_heart_rate'] = df['wearable_7d_mean_heart_rate'] - 12.0
        if 'wearable_7d_max_heart_rate' not in df.columns:
            df['wearable_7d_max_heart_rate'] = df['wearable_7d_mean_heart_rate'] + 28.0
        if 'wearable_7d_heart_rate_std' not in df.columns:
            df['wearable_7d_heart_rate_std'] = 8.5
        if 'wearable_7d_mean_hrv_rmssd' not in df.columns:
            df['wearable_7d_mean_hrv_rmssd'] = np.clip(65.0 - (pf_val * 8.0), 15.0, 85.0)
        if 'wearable_7d_min_hrv_rmssd' not in df.columns:
            df['wearable_7d_min_hrv_rmssd'] = np.maximum(10.0, df['wearable_7d_mean_hrv_rmssd'] - 15.0)
        if 'wearable_7d_hrv_rmssd_std' not in df.columns:
            df['wearable_7d_hrv_rmssd_std'] = 6.2
        sleep_v = df.get('Sleep_Hours', 7.5)
        if 'wearable_7d_mean_sleep_duration' not in df.columns:
            df['wearable_7d_mean_sleep_duration'] = float(sleep_v) if isinstance(sleep_v, (int, float)) else 7.5
        if 'wearable_7d_min_sleep_duration' not in df.columns:
            df['wearable_7d_min_sleep_duration'] = np.maximum(2.0, df['wearable_7d_mean_sleep_duration'] - 1.5)
        if 'wearable_7d_sleep_duration_std' not in df.columns:
            df['wearable_7d_sleep_duration_std'] = 0.8
        if 'wearable_7d_mean_sleep_quality' not in df.columns:
            df['wearable_7d_mean_sleep_quality'] = np.clip(88.0 - (pf_val * 10.0), 25.0, 95.0)
        if 'wearable_7d_mean_step_count' not in df.columns:
            df['wearable_7d_mean_step_count'] = 7500.0
        if 'wearable_7d_mean_active_minutes' not in df.columns:
            df['wearable_7d_mean_active_minutes'] = 45.0

        if 'wearable_30d_observation_count' not in df.columns:
            df['wearable_30d_observation_count'] = 0
        if 'wearable_30d_data_available' not in df.columns:
            df['wearable_30d_data_available'] = 0
        if 'wearable_30d_mean_heart_rate' not in df.columns:
            df['wearable_30d_mean_heart_rate'] = df['wearable_7d_mean_heart_rate']
        if 'wearable_30d_min_heart_rate' not in df.columns:
            df['wearable_30d_min_heart_rate'] = df['wearable_7d_min_heart_rate']
        if 'wearable_30d_max_heart_rate' not in df.columns:
            df['wearable_30d_max_heart_rate'] = df['wearable_7d_max_heart_rate']
        if 'wearable_30d_heart_rate_std' not in df.columns:
            df['wearable_30d_heart_rate_std'] = df['wearable_7d_heart_rate_std']
        if 'wearable_30d_mean_hrv_rmssd' not in df.columns:
            df['wearable_30d_mean_hrv_rmssd'] = df['wearable_7d_mean_hrv_rmssd']
        if 'wearable_30d_min_hrv_rmssd' not in df.columns:
            df['wearable_30d_min_hrv_rmssd'] = df['wearable_7d_min_hrv_rmssd']
        if 'wearable_30d_hrv_rmssd_std' not in df.columns:
            df['wearable_30d_hrv_rmssd_std'] = df['wearable_7d_hrv_rmssd_std']
        if 'wearable_30d_mean_sleep_duration' not in df.columns:
            df['wearable_30d_mean_sleep_duration'] = df['wearable_7d_mean_sleep_duration']
        if 'wearable_30d_min_sleep_duration' not in df.columns:
            df['wearable_30d_min_sleep_duration'] = df['wearable_7d_min_sleep_duration']
        if 'wearable_30d_sleep_duration_std' not in df.columns:
            df['wearable_30d_sleep_duration_std'] = df['wearable_7d_sleep_duration_std']
        if 'wearable_30d_mean_sleep_quality' not in df.columns:
            df['wearable_30d_mean_sleep_quality'] = df['wearable_7d_mean_sleep_quality']
        if 'wearable_30d_mean_step_count' not in df.columns:
            df['wearable_30d_mean_step_count'] = df['wearable_7d_mean_step_count']
        if 'wearable_30d_mean_active_minutes' not in df.columns:
            df['wearable_30d_mean_active_minutes'] = df['wearable_7d_mean_active_minutes']

        for col in WEARABLE_7D_NUMERICAL + WEARABLE_30D_NUMERICAL:
            if col not in df.columns:
                df[col] = np.nan
                
        # Engineered features
        df = engineer_features(df)
        
        # Ensure all columns exist
        for col in ALL_NUMERICAL_FEATURES:
            if col not in df.columns:
                df[col] = np.nan
        for col in ALL_CATEGORICAL_FEATURES:
            if col not in df.columns:
                df[col] = 'Unknown'
                
        return df[ALL_MODEL_FEATURES]

    def predict_proba(self, X_raw: pd.DataFrame) -> pd.DataFrame:
        """
        Computes calibrated class probability distribution across [Low, Medium, High].
        Runs: Preprocessor -> Base Models -> Meta-Learner -> Sigmoid Calibrator.
        """
        X_aligned = self._prepare_input(X_raw)
        X_trans = self.preprocessor.transform(X_aligned)
        
        p_lgb = self.base_models['LightGBM'].predict_proba(X_trans)
        p_xgb = self.base_models['XGBoost'].predict_proba(X_trans)
        p_cat = self.base_models['CatBoost'].predict_proba(X_trans)
        p_lr  = self.base_models['LogisticRegression'].predict_proba(X_trans)
        
        Z = np.hstack([p_lgb, p_xgb, p_cat, p_lr])
        
        if self.calibrator is not None:
            cal_probs = self.calibrator.predict_proba(Z)
        else:
            cal_probs = self.meta_model.predict_proba(Z)
            
        return pd.DataFrame(cal_probs, columns=self.class_names)

    def predict(self, X_raw: pd.DataFrame) -> np.ndarray:
        probas = self.predict_proba(X_raw).values
        pred_ints = np.argmax(probas, axis=1)
        return np.array([self.int_to_label[i] for i in pred_ints])

    def assess(self, record_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a single personnel assessment record and outputs:
        calibrated risk probability, continuous 0-100 risk score, priority tier,
        ensemble disagreement uncertainty, and top contributing factors.
        """
        df_single = pd.DataFrame([record_dict])
        X_aligned = self._prepare_input(df_single)
        X_trans = self.preprocessor.transform(X_aligned)
        
        # Base model predictions
        p_lgb = self.base_models['LightGBM'].predict_proba(X_trans)[0]
        p_xgb = self.base_models['XGBoost'].predict_proba(X_trans)[0]
        p_cat = self.base_models['CatBoost'].predict_proba(X_trans)[0]
        p_lr  = self.base_models['LogisticRegression'].predict_proba(X_trans)[0]
        
        base_preds = np.vstack([p_lgb, p_xgb, p_cat, p_lr])
        
        # Measure ensemble disagreement (mean std across classes)
        disagreement = float(np.mean(np.std(base_preds, axis=0)))
        
        if disagreement < 0.08:
            conf = "High"
        elif disagreement < 0.18:
            conf = "Moderate"
        else:
            conf = "Low"
            
        # Calibrated probability
        Z = np.hstack([p_lgb, p_xgb, p_cat, p_lr]).reshape(1, -1)
        if self.calibrator is not None:
            cal_probs = self.calibrator.predict_proba(Z)[0]
        else:
            cal_probs = self.meta_model.predict_proba(Z)[0]
            
        probas_dict = {
            'Low': round(float(cal_probs[0]), 3),
            'Medium': round(float(cal_probs[1]), 3),
            'High': round(float(cal_probs[2]), 3)
        }
        
        pred_label = self.int_to_label[int(np.argmax(cal_probs))]
        
        # Calibrated risk probability: continuous expectation across Low(0.0), Medium(0.50), High(1.00)
        risk_probability = float(np.clip(
            (0.0 * cal_probs[0]) + (0.50 * cal_probs[1]) + (1.00 * cal_probs[2]),
            0.0, 1.0
        ))
        risk_score = round(risk_probability * 100.0, 1)
        
        # Priority mapping
        if risk_score >= 70.0:
            priority = "Priority"
        elif risk_score >= 40.0:
            priority = "Preventive"
        else:
            priority = "Routine"
            
        # Feature importance / top factors
        feature_names = self.preprocessor.get_feature_names_out()
        coefs = self.base_models['LightGBM'].feature_importances_
        top_indices = np.argsort(coefs)[::-1]
        
        top_factors = []
        for idx in top_indices[:6]:
            fname = feature_names[idx]
            clean_name = fname.replace("num__", "").replace("cat__", "")
            val = record_dict.get(clean_name, None)
            if val is not None:
                top_factors.append(f"{clean_name.replace('_', ' ').title()}: {val}")
            else:
                top_factors.append(f"{clean_name.replace('_', ' ').title()} operational indicator")
                
        return {
            "model_version": self.model_version,
            "stress_level": pred_label,
            "risk_score": risk_score,
            "risk_probability": round(risk_probability, 3),
            "risk_priority": priority,
            "prediction_target": "P(Stress_Level >= Medium / Continuous Severity)",
            "confidence": conf,
            "uncertainty": round(disagreement, 3),
            "probabilities": probas_dict,
            "key_factors": top_factors[:4],
            "top_factors": top_factors[:4],
            "feature_contributions": {
                feature_names[i].replace("num__", "").replace("cat__", ""): round(float(coefs[i]), 4)
                for i in top_indices[:8]
            },
            "assessment_features_used": True,
            "hrms_features_used": bool(record_dict.get("has_hrms_record", True)),
            "wearable_7d_features_used": bool(record_dict.get("wearable_7d_data_available", False)),
            "wearable_30d_features_used": bool(record_dict.get("wearable_30d_data_available", False)),
            "is_simulated": True,
            "disclaimer": (
                "AI-assisted early-warning decision-support prototype. "
                "Assessments indicate statistical model associations and are strictly "
                "intended for supportive welfare intervention, not disciplinary action or clinical diagnosis."
            )
        }


def evaluate_counterfactual_sensitivity(
    model: StressRiskEnsembleV2,
    baseline_dict: Dict[str, Any],
    perturbations: Dict[str, List[Any]]
) -> Dict[str, Any]:
    """
    Evaluates controlled counterfactual feature perturbations against a baseline.
    Returns delta probabilities and delta risk scores.
    """
    baseline_res = model.assess(baseline_dict)
    base_score = baseline_res["risk_score"]
    base_prob = baseline_res["risk_probability"]
    
    sensitivity_results = {}
    for feature_name, new_values in perturbations.items():
        feature_runs = []
        for val in new_values:
            mod_dict = dict(baseline_dict)
            mod_dict[feature_name] = val
            mod_res = model.assess(mod_dict)
            feature_runs.append({
                "value": val,
                "risk_score": mod_res["risk_score"],
                "risk_probability": mod_res["risk_probability"],
                "delta_score": round(mod_res["risk_score"] - base_score, 1),
                "delta_probability": round(mod_res["risk_probability"] - base_prob, 3),
                "probabilities": mod_res["probabilities"]
            })
        sensitivity_results[feature_name] = feature_runs
        
    return {
        "baseline": {
            "risk_score": base_score,
            "risk_probability": base_prob,
            "probabilities": baseline_res["probabilities"]
        },
        "perturbations": sensitivity_results,
        "sensitivity_results": sensitivity_results
    }
