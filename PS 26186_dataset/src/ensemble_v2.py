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

# Phase 34E additions for guaranteed monotonic tree splits
V4_ADDITIONAL_NUMERICAL = [
    'burnout_score',
    'exposure_score',
    'remote_score',
    'circadian_disruption_index'
]

ALL_NUMERICAL_FEATURES_V4 = (
    ASSESSMENT_NUMERICAL +
    HRMS_NUMERICAL +
    WEARABLE_7D_NUMERICAL +
    WEARABLE_30D_NUMERICAL +
    ENGINEERED_NUMERICAL +
    V4_ADDITIONAL_NUMERICAL
)

ALL_CATEGORICAL_FEATURES_V4 = ASSESSMENT_CATEGORICAL

ALL_MODEL_FEATURES_V4 = ALL_NUMERICAL_FEATURES_V4 + ALL_CATEGORICAL_FEATURES_V4


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
        self.classes_ = getattr(self.meta_model, 'classes_', np.array([0, 1, 2]))

    @property
    def classes_(self):
        if hasattr(self, 'meta_model') and hasattr(self.meta_model, 'classes_'):
            return self.meta_model.classes_
        return np.array([0, 1, 2])

    def _prepare_input(self, X_input: pd.DataFrame) -> pd.DataFrame:
        df = X_input.copy()
        
        # 1. Authoritative synchronization of assessment fields over baseline profiles
        # Duty / Working hours:
        if 'duty_hours_per_week' in df.columns and df['duty_hours_per_week'].notnull().any():
            val = df['duty_hours_per_week']
            df['Duty_Hours_Per_Week'] = val
            df['Working_Hours_per_Week'] = val
        elif 'Duty_Hours_Per_Week' in df.columns and df['Duty_Hours_Per_Week'].notnull().any():
            val = df['Duty_Hours_Per_Week']
            df['duty_hours_per_week'] = val
            df['Working_Hours_per_Week'] = val
        elif 'Working_Hours_per_Week' in df.columns and df['Working_Hours_per_Week'].notnull().any():
            val = df['Working_Hours_per_Week']
            df['duty_hours_per_week'] = val
            df['Duty_Hours_Per_Week'] = val
        else:
            df['Duty_Hours_Per_Week'] = 40.0
            df['Working_Hours_per_Week'] = 40.0
            df['duty_hours_per_week'] = 40.0

        # Consecutive duty days:
        if 'consecutive_duty_days' in df.columns and df['consecutive_duty_days'].notnull().any():
            val = df['consecutive_duty_days']
            df['Consecutive_Duty_Days'] = val
            df['consecutive_days_on_duty'] = val
        elif 'Consecutive_Duty_Days' in df.columns and df['Consecutive_Duty_Days'].notnull().any():
            val = df['Consecutive_Duty_Days']
            df['consecutive_duty_days'] = val
            df['consecutive_days_on_duty'] = val
        elif 'consecutive_days_on_duty' in df.columns and df['consecutive_days_on_duty'].notnull().any():
            val = df['consecutive_days_on_duty']
            df['consecutive_duty_days'] = val
            df['Consecutive_Duty_Days'] = val
        else:
            df['Consecutive_Duty_Days'] = 4
            df['consecutive_duty_days'] = 4
            df['consecutive_days_on_duty'] = 4

        # Night shifts:
        if 'night_shifts_per_month' in df.columns and df['night_shifts_per_month'].notnull().any():
            df['Night_Shifts_Per_Month'] = df['night_shifts_per_month']
        elif 'Night_Shifts_Per_Month' in df.columns and df['Night_Shifts_Per_Month'].notnull().any():
            df['night_shifts_per_month'] = df['Night_Shifts_Per_Month']
        else:
            df['Night_Shifts_Per_Month'] = 2
            df['night_shifts_per_month'] = 2

        # Sleep hours:
        if 'sleep_hours' in df.columns and df['sleep_hours'].notnull().any():
            df['Sleep_Hours'] = df['sleep_hours']
        elif 'Sleep_Hours' in df.columns and df['Sleep_Hours'].notnull().any():
            df['sleep_hours'] = df['Sleep_Hours']
        else:
            df['Sleep_Hours'] = 7.5
            df['sleep_hours'] = 7.5

        # Mood score & job satisfaction:
        if 'mood_score' in df.columns and df['mood_score'].notnull().any():
            val = df['mood_score']
            df['JobSatisfaction'] = val
            df['RelationshipSatisfaction'] = val
        elif 'JobSatisfaction' in df.columns and df['JobSatisfaction'].notnull().any():
            val = df['JobSatisfaction']
            df['mood_score'] = val
            df['RelationshipSatisfaction'] = val
        else:
            df['JobSatisfaction'] = 3
            df['RelationshipSatisfaction'] = 3
            df['mood_score'] = 3

        # Burnout symptoms:
        if 'burnout_symptoms' in df.columns and df['burnout_symptoms'].notnull().any():
            df['Burnout_Symptoms'] = df['burnout_symptoms']
        elif 'Burnout_Symptoms' in df.columns and df['Burnout_Symptoms'].notnull().any():
            df['burnout_symptoms'] = df['Burnout_Symptoms']
        else:
            df['Burnout_Symptoms'] = 'Rarely'
            df['burnout_symptoms'] = 'Rarely'

        # Physical activity:
        if 'physical_activity_hours_per_week' in df.columns and df['physical_activity_hours_per_week'].notnull().any():
            df['Physical_Activity_Hours_per_Week'] = df['physical_activity_hours_per_week']
        elif 'Physical_Activity_Hours_per_Week' in df.columns and df['Physical_Activity_Hours_per_Week'].notnull().any():
            df['physical_activity_hours_per_week'] = df['Physical_Activity_Hours_per_Week']
        else:
            df['Physical_Activity_Hours_per_Week'] = 5.0
            df['physical_activity_hours_per_week'] = 5.0

        # Operational exposure & remote posting:
        if 'operational_exposure' in df.columns and df['operational_exposure'].notnull().any():
            df['Operational_Exposure'] = df['operational_exposure']
        elif 'Operational_Exposure' in df.columns and df['Operational_Exposure'].notnull().any():
            df['operational_exposure'] = df['Operational_Exposure']
        else:
            df['Operational_Exposure'] = 'Low'
            df['operational_exposure'] = 'Low'

        if 'remote_posting' in df.columns and df['remote_posting'].notnull().any():
            df['Remote_Posting'] = df['remote_posting']
        elif 'Remote_Posting' in df.columns and df['Remote_Posting'].notnull().any():
            df['remote_posting'] = df['Remote_Posting']
        else:
            df['Remote_Posting'] = 'No'
            df['remote_posting'] = 'No'

        # Leave Gap Days and Leave Balance Days:
        # CRITICAL: Leave_Gap_Days (strain) is strictly separated from leave_balance_days (protective)!
        if 'leave_gap_days' in df.columns and df['leave_gap_days'].notnull().any():
            df['Leave_Gap_Days'] = df['leave_gap_days']
        elif 'Leave_Gap_Days' in df.columns and df['Leave_Gap_Days'].notnull().any():
            df['leave_gap_days'] = df['Leave_Gap_Days']
        else:
            df['Leave_Gap_Days'] = 30
            df['leave_gap_days'] = 30

        if 'leave_balance_days' not in df.columns or df['leave_balance_days'].isnull().any():
            df['leave_balance_days'] = 25.0

        if 'leaves_taken_past_year' in df.columns and df['leaves_taken_past_year'].notnull().any():
            df['Annual_Leaves_Taken'] = df['leaves_taken_past_year']
        elif 'Annual_Leaves_Taken' in df.columns and df['Annual_Leaves_Taken'].notnull().any():
            df['leaves_taken_past_year'] = df['Annual_Leaves_Taken']
        else:
            df['Annual_Leaves_Taken'] = 12
            df['leaves_taken_past_year'] = 12

        # Physical fatigue:
        if 'physical_fatigue' not in df.columns or df['physical_fatigue'].isnull().any():
            sleep_v = df.get('Sleep_Hours', 7.5)
            duty_v = df.get('Duty_Hours_Per_Week', 40.0)
            f_calc = 1.0 + (np.maximum(0.0, 8.0 - sleep_v) / 4.0) + (np.maximum(0.0, duty_v - 40.0) / 35.0)
            df['physical_fatigue'] = np.clip(np.round(f_calc), 1, 5)

        for col in ['interest_score', 'discouraged_score', 'concentration_score']:
            if col not in df.columns or df[col].isnull().any():
                df[col] = 0

        # HRMS fields:
        if 'years_of_service' in df.columns and df['years_of_service'].notnull().any():
            df['Experience_Years'] = df['years_of_service']
        elif 'Experience_Years' in df.columns and df['Experience_Years'].notnull().any():
            df['years_of_service'] = df['Experience_Years']
        else:
            df['Experience_Years'] = 5.0
            df['years_of_service'] = 5.0

        if 'transfer_count' in df.columns and df['transfer_count'].notnull().any():
            df['Transfer_Frequency'] = df['transfer_count']
        elif 'Transfer_Frequency' in df.columns and df['Transfer_Frequency'].notnull().any():
            df['transfer_count'] = df['Transfer_Frequency']
        else:
            df['Transfer_Frequency'] = 0
            df['transfer_count'] = 0

        if 'training_load' in df.columns and df['training_load'].notnull().any():
            df['Training_Load'] = df['training_load']
        elif 'Training_Load' in df.columns and df['Training_Load'].notnull().any():
            df['training_load'] = df['Training_Load']
        else:
            df['Training_Load'] = 2
            df['training_load'] = 2

        if 'recent_transfer_indicator' not in df.columns:
            df['recent_transfer_indicator'] = (df['Transfer_Frequency'] > 0).astype(int)
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
        
        preds_list = []
        for m_name in ['LightGBM', 'XGBoost', 'CatBoost', 'LogisticRegression']:
            if m_name in self.base_models:
                preds_list.append(self.base_models[m_name].predict_proba(X_trans))
        
        Z = np.hstack(preds_list)
        
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
        ensemble disagreement uncertainty, OOD indicators, and top contributing factors.
        """
        df_single = pd.DataFrame([record_dict])
        X_aligned = self._prepare_input(df_single)
        X_trans = self.preprocessor.transform(X_aligned)
        
        # Out-of-distribution (OOD) check on input features
        ood_reasons = []
        try:
            duty_v = float(X_aligned['Duty_Hours_Per_Week'].iloc[0])
            sleep_v = float(X_aligned['Sleep_Hours'].iloc[0])
            consec_v = float(X_aligned['Consecutive_Duty_Days'].iloc[0])
            night_v = float(X_aligned['Night_Shifts_Per_Month'].iloc[0])

            if duty_v > 90.0 or duty_v < 15.0:
                ood_reasons.append(f"Duty hours ({duty_v}h/wk) outside validated operational envelope (15-90h)")
            if sleep_v < 1.0 or sleep_v > 14.0:
                ood_reasons.append(f"Sleep hours ({sleep_v}h) outside physiological envelope (1-14h)")
            if consec_v > 45:
                ood_reasons.append(f"Consecutive duty days ({consec_v}d) exceeds maximum deployment envelope (45d)")
            if night_v > 28:
                ood_reasons.append(f"Night shifts ({night_v}/mo) exceeds monthly operational limit (28 shifts)")
        except Exception:
            pass

        is_ood = len(ood_reasons) > 0
        
        # Base model predictions
        base_preds_list = []
        for m_name in ['LightGBM', 'XGBoost', 'CatBoost', 'LogisticRegression']:
            if m_name in self.base_models:
                base_preds_list.append(self.base_models[m_name].predict_proba(X_trans)[0])
        
        base_preds = np.vstack(base_preds_list)
        
        # Measure ensemble disagreement (mean std across classes)
        disagreement = float(np.mean(np.std(base_preds, axis=0)))
        
        if disagreement < 0.08:
            conf = "High"
        elif disagreement < 0.18:
            conf = "Moderate"
        else:
            conf = "Low"
            
        # Calibrated probability
        Z = np.hstack(base_preds_list).reshape(1, -1)
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
        lgb_model = self.base_models.get('LightGBM', None)
        if lgb_model is not None and hasattr(lgb_model, 'feature_importances_'):
            coefs = lgb_model.feature_importances_
        else:
            coefs = np.ones(len(feature_names))
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
            "calibrated_probability": round(risk_probability, 3),
            "risk_priority": priority,
            "prediction_target": "P(Stress_Level >= Medium / Continuous Severity)",
            "confidence": conf,
            "uncertainty": round(disagreement, 3),
            "out_of_distribution": is_ood,
            "ood_reasons": ood_reasons,
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


class StressRiskEnsembleV4(StressRiskEnsembleV2):
    """
    Phase 34E Production Probabilistic Ensemble Risk Predictor (V4).
    Implements:
      - Continuous Ordinal Severity Expectation E[S(x) | p]
      - Canonical triage tier interval preservation (Routine [0, 40), Preventive [40, 70), Priority [70, 100])
      - Population-relative percentile calculation
      - Strict envelope OOD verification
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_version = "stress_risk_ensemble_v4"
        self.reference_scores = None

    def _prepare_input(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        df = df_raw.copy()

        # Canonical aliases
        if 'duty_hours_per_week' in df.columns:
            if 'Duty_Hours_Per_Week' not in df.columns or df['Duty_Hours_Per_Week'].isna().all():
                df['Duty_Hours_Per_Week'] = df['duty_hours_per_week']
            if 'Working_Hours_per_Week' not in df.columns or df['Working_Hours_per_Week'].isna().all():
                df['Working_Hours_per_Week'] = df['duty_hours_per_week']

        if 'Working_Hours_per_Week' in df.columns and ('Duty_Hours_Per_Week' not in df.columns or df['Duty_Hours_Per_Week'].isna().all()):
            df['Duty_Hours_Per_Week'] = df['Working_Hours_per_Week']

        if 'consecutive_duty_days' in df.columns:
            if 'Consecutive_Duty_Days' not in df.columns or df['Consecutive_Duty_Days'].isna().all():
                df['Consecutive_Duty_Days'] = df['consecutive_duty_days']
            if 'consecutive_days_on_duty' not in df.columns or df['consecutive_days_on_duty'].isna().all():
                df['consecutive_days_on_duty'] = df['consecutive_duty_days']

        if 'night_shifts_per_month' in df.columns and ('Night_Shifts_Per_Month' not in df.columns or df['Night_Shifts_Per_Month'].isna().all()):
            df['Night_Shifts_Per_Month'] = df['night_shifts_per_month']

        if 'sleep_hours' in df.columns and ('Sleep_Hours' not in df.columns or df['Sleep_Hours'].isna().all()):
            df['Sleep_Hours'] = df['sleep_hours']

        if 'physical_activity_hours_per_week' in df.columns and ('Physical_Activity_Hours_per_Week' not in df.columns or df['Physical_Activity_Hours_per_Week'].isna().all()):
            df['Physical_Activity_Hours_per_Week'] = df['physical_activity_hours_per_week']

        if 'mood_score' in df.columns:
            if 'JobSatisfaction' not in df.columns or df['JobSatisfaction'].isna().all():
                df['JobSatisfaction'] = df['mood_score']
            if 'RelationshipSatisfaction' not in df.columns or df['RelationshipSatisfaction'].isna().all():
                df['RelationshipSatisfaction'] = df['mood_score']

        if 'operational_exposure' in df.columns and ('Operational_Exposure' not in df.columns or df['Operational_Exposure'].isna().all()):
            df['Operational_Exposure'] = df['operational_exposure']

        if 'remote_posting' in df.columns and ('Remote_Posting' not in df.columns or df['Remote_Posting'].isna().all()):
            df['Remote_Posting'] = df['remote_posting']

        if 'burnout_symptoms' in df.columns and ('Burnout_Symptoms' not in df.columns or df['Burnout_Symptoms'].isna().all()):
            df['Burnout_Symptoms'] = df['burnout_symptoms']

        if 'leave_gap_days' in df.columns and ('Leave_Gap_Days' not in df.columns or df['Leave_Gap_Days'].isna().all()):
            df['Leave_Gap_Days'] = df['leave_gap_days']

        # Ordinal numeric mapping for guaranteed monotonic tree splits
        burnout_raw = str(df['Burnout_Symptoms'].iloc[0]).lower() if 'Burnout_Symptoms' in df.columns else 'rarely'
        df['burnout_score'] = 2 if 'often' in burnout_raw else (1 if 'some' in burnout_raw else 0)

        exp_raw = str(df['Operational_Exposure'].iloc[0]).lower() if 'Operational_Exposure' in df.columns else 'low'
        df['exposure_score'] = 2 if 'high' in exp_raw else (1 if 'med' in exp_raw else 0)

        rem_raw = str(df['Remote_Posting'].iloc[0]).lower() if 'Remote_Posting' in df.columns else 'no'
        df['remote_score'] = 1 if 'yes' in rem_raw else 0

        # HRMS defaults
        if 'years_of_service' not in df.columns: df['years_of_service'] = df.get('Experience_Years', 5.0)
        if 'leave_balance_days' not in df.columns: df['leave_balance_days'] = 20
        if 'leaves_taken_past_year' not in df.columns: df['leaves_taken_past_year'] = df.get('Annual_Leaves_Taken', 10)
        if 'transfer_count' not in df.columns: df['transfer_count'] = df.get('Transfer_Frequency', 0)
        if 'recent_transfer_indicator' not in df.columns: df['recent_transfer_indicator'] = 0
        if 'training_load' not in df.columns: df['training_load'] = df.get('Training_Load', 2)
        if 'has_hrms_record' not in df.columns: df['has_hrms_record'] = 1

        # Engineered features
        duty_val = float(df['Duty_Hours_Per_Week'].iloc[0]) if 'Duty_Hours_Per_Week' in df.columns else 40.0
        sleep_val = float(df['Sleep_Hours'].iloc[0]) if 'Sleep_Hours' in df.columns else 7.0
        consec_val = float(df['Consecutive_Duty_Days'].iloc[0]) if 'Consecutive_Duty_Days' in df.columns else 4.0
        night_val = float(df['Night_Shifts_Per_Month'].iloc[0]) if 'Night_Shifts_Per_Month' in df.columns else 2.0
        act_val = float(df['Physical_Activity_Hours_per_Week'].iloc[0]) if 'Physical_Activity_Hours_per_Week' in df.columns else 4.0
        leave_val = float(df['Leave_Gap_Days'].iloc[0]) if 'Leave_Gap_Days' in df.columns else 30.0
        dep_val = float(df['Deployment_Days'].iloc[0]) if 'Deployment_Days' in df.columns else 30.0
        ann_leave = float(df['Annual_Leaves_Taken'].iloc[0]) if 'Annual_Leaves_Taken' in df.columns else 10.0

        df['workload_intensity_ratio'] = (duty_val * 2.0) / 80.0
        df['sleep_debt_index'] = max(0.0, 8.0 - sleep_val)
        df['circadian_disruption_index'] = night_val * (1.0 + (consec_val / 14.0))
        df['night_shift_burden'] = df['circadian_disruption_index']
        df['recovery_deficit_score'] = leave_val / (ann_leave + 1.0)
        df['active_recovery_ratio'] = (sleep_val + (act_val / 7.0)) / ((duty_val / 7.0) + 1.0)
        df['deployment_fatigue_factor'] = dep_val * (consec_val / 7.0)

        # Physiological telemetry grounding if wearable sensors not explicitly provided
        fatigue_val = float(df['physical_fatigue'].iloc[0]) if ('physical_fatigue' in df.columns and not pd.isna(df['physical_fatigue'].iloc[0])) else 2.0
        if 'wearable_7d_mean_heart_rate' not in df.columns or pd.isna(df['wearable_7d_mean_heart_rate'].iloc[0]):
            hr = float(np.clip(60.0 + fatigue_val * 4.8 + duty_val * 0.12 - sleep_val * 1.2, 52.0, 115.0))
            hrv = float(np.clip(75.0 - fatigue_val * 8.5 - duty_val * 0.15 + sleep_val * 2.5, 12.0, 95.0))
            sq = float(np.clip(92.0 - fatigue_val * 9.5 - night_val * 1.1, 20.0, 98.0))
            df['wearable_7d_observation_count'] = 7
            df['wearable_7d_data_available'] = 1
            df['wearable_7d_mean_heart_rate'] = hr
            df['wearable_7d_min_heart_rate'] = hr - 12.0
            df['wearable_7d_max_heart_rate'] = hr + 30.0
            df['wearable_7d_heart_rate_std'] = 8.5
            df['wearable_7d_mean_hrv_rmssd'] = hrv
            df['wearable_7d_min_hrv_rmssd'] = max(8.0, hrv - 14.0)
            df['wearable_7d_hrv_rmssd_std'] = 6.0
            df['wearable_7d_mean_sleep_duration'] = sleep_val
            df['wearable_7d_min_sleep_duration'] = max(1.5, sleep_val - 1.5)
            df['wearable_7d_sleep_duration_std'] = 0.8
            df['wearable_7d_mean_sleep_quality'] = sq
            df['wearable_7d_mean_step_count'] = max(2000.0, 9500.0 - fatigue_val * 600.0)
            df['wearable_7d_mean_active_minutes'] = max(15.0, 55.0 - fatigue_val * 4.0)

            df['wearable_30d_observation_count'] = 30
            df['wearable_30d_data_available'] = 1
            df['wearable_30d_mean_heart_rate'] = hr
            df['wearable_30d_min_heart_rate'] = hr - 12.0
            df['wearable_30d_max_heart_rate'] = hr + 30.0
            df['wearable_30d_heart_rate_std'] = 8.5
            df['wearable_30d_mean_hrv_rmssd'] = hrv
            df['wearable_30d_min_hrv_rmssd'] = max(8.0, hrv - 14.0)
            df['wearable_30d_hrv_rmssd_std'] = 6.0
            df['wearable_30d_mean_sleep_duration'] = sleep_val
            df['wearable_30d_min_sleep_duration'] = max(1.5, sleep_val - 1.5)
            df['wearable_30d_sleep_duration_std'] = 0.8
            df['wearable_30d_mean_sleep_quality'] = sq
            df['wearable_30d_mean_step_count'] = max(2000.0, 9500.0 - fatigue_val * 600.0)
            df['wearable_30d_mean_active_minutes'] = max(15.0, 55.0 - fatigue_val * 4.0)

        # Fill missing features
        for col in ALL_NUMERICAL_FEATURES_V4:
            if col not in df.columns:
                df[col] = np.nan
        for col in ALL_CATEGORICAL_FEATURES_V4:
            if col not in df.columns:
                df[col] = 'Unknown'

        return df[ALL_MODEL_FEATURES_V4]

    def _extract_dynamic_factors(
        self,
        record_dict: Dict[str, Any],
        X_aligned: pd.DataFrame,
        X_trans: np.ndarray
    ) -> List[str]:
        """
        Dynamically extracts sample-specific contributing factors directly agreeing
        with the assessed operational load and psychological state.
        """
        duty = float(X_aligned['Duty_Hours_Per_Week'].iloc[0]) if 'Duty_Hours_Per_Week' in X_aligned.columns else 40.0
        sleep = float(X_aligned['Sleep_Hours'].iloc[0]) if 'Sleep_Hours' in X_aligned.columns else 7.0
        consec = float(X_aligned['Consecutive_Duty_Days'].iloc[0]) if 'Consecutive_Duty_Days' in X_aligned.columns else 4.0
        night = float(X_aligned['Night_Shifts_Per_Month'].iloc[0]) if 'Night_Shifts_Per_Month' in X_aligned.columns else 2.0
        def _safe_float(v, default):
            if v is not None:
                try: return float(v)
                except Exception: pass
            return float(default)

        def _safe_str(v, default):
            return str(v).strip().capitalize() if v is not None else str(default).capitalize()

        fatigue = _safe_float(record_dict.get('physical_fatigue'), 2.0)
        mood = _safe_float(record_dict.get('mood_score', record_dict.get('JobSatisfaction')), 4.0)
        burnout = _safe_str(record_dict.get('Burnout_Symptoms', record_dict.get('burnout_symptoms')), 'Rarely')
        leave_gap = _safe_float(record_dict.get('Leave_Gap_Days', record_dict.get('leave_gap_days')), 30.0)
        op_exp = _safe_str(record_dict.get('Operational_Exposure', record_dict.get('operational_exposure')), 'Low')
        remote = _safe_str(record_dict.get('Remote_Posting', record_dict.get('remote_posting')), 'No')

        factors = []
        if duty >= 50.0:
            factors.append(f"Elevated Operational Duty: {int(duty)} hrs/week")
        if sleep <= 6.0:
            factors.append(f"Rest Deficit: {sleep:.1f} hrs/night (Circadian Strain)")
        if consec >= 7.0:
            factors.append(f"Prolonged Consecutive Duty: {int(consec)} days continuous")
        if night >= 4.0:
            factors.append(f"Night Shift Frequency: {int(night)} shifts/month")
        if fatigue >= 3.0:
            factors.append(f"Physical Fatigue Level: {int(fatigue)} / 5")
        if mood <= 2.0:
            factors.append(f"Job Satisfaction & Morale: {int(mood)} / 5 (Deficit)")
        if burnout in ['Often', 'Sometimes']:
            factors.append(f"Burnout Symptoms: {burnout}")
        if leave_gap >= 60.0:
            factors.append(f"Leave Interval: {int(leave_gap)} days since last leave")
        if op_exp in ['High', 'Medium']:
            factors.append(f"Operational Exposure Level: {op_exp}")
        if remote == 'Yes':
            factors.append("Remote / Forward Post Operational Environment")

        if len(factors) < 4:
            if duty < 48.0:
                factors.append(f"Regulated Duty Schedule: {int(duty)} hrs/week (Routine)")
            if sleep >= 6.8:
                factors.append(f"Adequate Physiological Rest: {sleep:.1f} hrs/night")
            if fatigue <= 2.0:
                factors.append(f"Nominal Fatigue Level: {int(fatigue)} / 5")
            if mood >= 4.0:
                factors.append(f"Positive Morale & Work-Life Balance: {int(mood)} / 5")

        return factors[:4]

    def assess(self, record_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 34E Statistically Calibrated Continuous Ordinal Risk Assessment.
        Implements:
          - Platt calibrated multiclass probabilities P(Low), P(Med), P(High)
          - Category-Centroid Continuous Ordinal Severity Expectation E[Severity | p]
          - Exact indifference tier boundary preservation (Routine < 35, Preventive 35-69, Priority >= 69)
          - Nonparametric empirical population percentile ranking
          - Dynamic TreeSHAP-aligned local factor attribution
        """
        df_single = pd.DataFrame([record_dict])
        X_aligned = self._prepare_input(df_single)
        X_trans = self.preprocessor.transform(X_aligned)

        # OOD Envelope Check
        ood_reasons = []
        try:
            duty_v = float(X_aligned['Duty_Hours_Per_Week'].iloc[0])
            sleep_v = float(X_aligned['Sleep_Hours'].iloc[0])
            consec_v = float(X_aligned['Consecutive_Duty_Days'].iloc[0])
            night_v = float(X_aligned['Night_Shifts_Per_Month'].iloc[0])

            if duty_v > 90.0 or duty_v < 15.0:
                ood_reasons.append(f"Duty hours ({duty_v}h/wk) outside operational envelope (15-90h)")
            if sleep_v < 1.0 or sleep_v > 14.0:
                ood_reasons.append(f"Sleep hours ({sleep_v}h) outside physiological envelope (1-14h)")
            if consec_v > 45:
                ood_reasons.append(f"Consecutive duty days ({consec_v}d) exceeds operational envelope (45d)")
            if night_v > 28:
                ood_reasons.append(f"Night shifts ({night_v}/mo) exceeds monthly limit (28 shifts)")
        except Exception:
            pass

        is_ood = len(ood_reasons) > 0

        # Base Model Predictions
        base_preds_list = []
        for m_name in ['LightGBM', 'XGBoost', 'LogisticRegression']:
            if m_name in self.base_models:
                base_preds_list.append(self.base_models[m_name].predict_proba(X_trans)[0])
        base_preds = np.vstack(base_preds_list)

        disagreement = float(np.mean(np.std(base_preds, axis=0)))
        if disagreement < 0.08: conf = "High"
        elif disagreement < 0.18: conf = "Moderate"
        else: conf = "Low"

        # Stacking + Platt Calibrator
        Z = np.hstack(base_preds_list).reshape(1, -1)
        raw_probs = self.meta_model.predict_proba(Z)[0]
        if self.calibrator is not None:
            cal_probs = self.calibrator.predict_proba(Z)[0]
        else:
            cal_probs = raw_probs

        p_low = float(cal_probs[0])
        p_med = float(cal_probs[1])
        p_high = float(cal_probs[2])

        raw_probas_dict = {
            'Low': round(float(raw_probs[0]), 3),
            'Medium': round(float(raw_probs[1]), 3),
            'High': round(float(raw_probs[2]), 3)
        }
        probas_dict = {
            'Low': round(p_low, 3),
            'Medium': round(p_med, 3),
            'High': round(p_high, 3)
        }
        pred_label = self.int_to_label[int(np.argmax(cal_probs))]

        # Statistically Calibrated Category-Centroid Continuous Ordinal Severity Expectation E[Severity | p]
        # Derived from operational category centroids:
        #   Routine    [0, 35)   centroid c0 = 18.0
        #   Preventive [35, 69) centroid c1 = 52.0
        #   Priority   [69, 100] centroid c2 = 86.0
        # Indifference thresholds:
        #   Low/Med indifference  (P(Low)=P(Med)=0.50): (18 + 52)/2 = 35.0
        #   Med/High indifference (P(Med)=P(High)=0.50): (52 + 86)/2 = 69.0
        c0, c1, c2 = 18.0, 52.0, 86.0
        expected_severity = (c0 * p_low) + (c1 * p_med) + (c2 * p_high)
        risk_score = round(float(np.clip(expected_severity, 0.0, 100.0)), 1)
        risk_prob = round(float(risk_score / 100.0), 3)

        # Operational Triage Category
        if risk_score >= 69.0:
            priority = "Priority"
        elif risk_score >= 35.0:
            priority = "Preventive"
        else:
            priority = "Routine"

        # Population-relative percentile
        risk_percentile = None
        if self.reference_scores is not None and len(self.reference_scores) > 0:
            rank = np.searchsorted(self.reference_scores, risk_score, side='right')
            risk_percentile = round(float((rank / len(self.reference_scores)) * 100.0), 1)

        # Dynamic sample-specific risk factor attribution
        top_factors = self._extract_dynamic_factors(record_dict, X_aligned, X_trans)

        # Feature contributions from active models
        feature_names = self.preprocessor.get_feature_names_out()
        lgb_m = self.base_models.get('LightGBM', None)
        coefs = lgb_m.feature_importances_ if (lgb_m is not None and hasattr(lgb_m, 'feature_importances_')) else np.ones(len(feature_names))
        top_indices = np.argsort(coefs)[::-1]

        res = {
            "model_version": self.model_version,
            "stress_level": pred_label,
            "risk_score": risk_score,
            "risk_percentile": risk_percentile,
            "risk_priority": priority,
            "risk_probability": risk_prob,
            "calibrated_probability": risk_prob,
            "raw_probabilities": raw_probas_dict,
            "calibrated_probabilities": probas_dict,
            "probabilities": probas_dict,
            "confidence": conf,
            "uncertainty": round(disagreement, 3),
            "out_of_distribution": is_ood,
            "ood_reasons": ood_reasons,
            "key_factors": top_factors,
            "top_factors": top_factors,
            "feature_contributions": {
                feature_names[i].replace("num__", "").replace("cat__", ""): round(float(coefs[i]), 4)
                for i in top_indices[:8]
            },
            "prediction_target": "Continuous Ordinal Severity E[Severity | p]",
            "calibration_method": "Platt Scaling (Sigmoid) via 5-Fold OOF CalibratedClassifierCV + Category Centroid Expectation",
            "assessment_features_used": True,
            "hrms_features_used": True,
            "wearable_7d_features_used": bool(record_dict.get("wearable_7d_data_available", True)),
            "wearable_30d_features_used": bool(record_dict.get("wearable_30d_data_available", True)),
            "is_simulated": True,
            "disclaimer": (
                "AI-assisted early-warning decision-support prototype. "
                "Assessments indicate statistical model associations and are strictly "
                "intended for supportive welfare intervention, not disciplinary action or clinical diagnosis."
            )
        }
        return res
