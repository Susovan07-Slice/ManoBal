"""
Phase 34B: Complete Assessment Feature-to-Prediction Audit Utility
Provides comprehensive tracing for every assessment question:
  Assessment question
        ↓
  Raw answer
        ↓
  Normalized value
        ↓
  Model feature name
        ↓
  Encoded/scaled representation
        ↓
  Actual model input
        ↓
  Model probability
        ↓
  Calibrated probability
        ↓
  0–100 risk score
        ↓
  SHAP contribution
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union

# Ensure PS 26186_dataset is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DEFAULT_BASELINE_RECORD = {
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
    'RelationshipSatisfaction': 4,
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
    'physical_fatigue': 2,
    'interest_score': 0,
    'discouraged_score': 0,
    'concentration_score': 0,
    'has_hrms_record': 1
}

FEATURE_NAME_MAPPINGS = {
    'duty_hours_per_week': 'Duty_Hours_Per_Week',
    'consecutive_duty_days': 'Consecutive_Duty_Days',
    'night_shifts_per_month': 'Night_Shifts_Per_Month',
    'sleep_hours': 'Sleep_Hours',
    'physical_fatigue': 'physical_fatigue',
    'physical_activity_hours_per_week': 'Physical_Activity_Hours_per_Week',
    'mood_score': 'mood_score',
    'burnout_symptoms': 'Burnout_Symptoms',
    'interest_score': 'interest_score',
    'discouraged_score': 'discouraged_score',
    'concentration_score': 'concentration_score',
    'operational_exposure': 'Operational_Exposure',
    'remote_posting': 'Remote_Posting',
    'leave_gap_days': 'Leave_Gap_Days'
}

class RiskFeatureAuditor:
    """
    Complete Feature Passthrough & Sensitivity Auditor.
    Provides verifiable inspection of feature transformations, encoding,
    probabilities, calibration, and SHAP contributions.
    """
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            v3_path = os.path.join(BASE_DIR, 'models', 'stress_risk_ensemble_v3.pkl')
            v2_path = os.path.join(BASE_DIR, 'models', 'stress_risk_ensemble_v2.pkl')
            v1_path = os.path.join(BASE_DIR, 'models', 'final_stress_prediction_pipeline.pkl')
            if os.path.exists(v3_path):
                model_path = v3_path
            elif os.path.exists(v2_path):
                model_path = v2_path
            else:
                model_path = v1_path

        self.model_path = model_path
        self.model = joblib.load(model_path)
        self.is_ensemble = hasattr(self.model, 'assess')
        
        # Preprocessor & feature names
        if self.is_ensemble:
            self.preprocessor = self.model.preprocessor
            self.feature_names = list(self.preprocessor.get_feature_names_out())
            # SHAP explainer for LightGBM base learner
            try:
                import shap
                lgb_m = self.model.base_models.get('LightGBM', None)
                self.shap_explainer = shap.TreeExplainer(lgb_m) if lgb_m else None
            except Exception:
                self.shap_explainer = None
        else:
            self.preprocessor = self.model.pipeline.named_steps['preprocessor']
            self.shap_explainer = None
            self.feature_names = []

    def trace_single_input(
        self,
        assessment_input: str,
        raw_value: Any,
        baseline_record: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Traces a single assessment input end-to-end through the pipeline.
        Returns exact requested JSON structure:
          assessment_input, raw_value, normalized_value, model_feature,
          transformed_value, model_probability, calibrated_probability,
          risk_score, shap_contribution
        """
        base = dict(baseline_record or DEFAULT_BASELINE_RECORD)
        model_feat = FEATURE_NAME_MAPPINGS.get(assessment_input, assessment_input)

        # Normalize value
        normalized_val = raw_value
        if isinstance(raw_value, (int, float)):
            normalized_val = float(raw_value)
        elif isinstance(raw_value, str):
            normalized_val = raw_value.strip()

        # Update record with proper synchronization
        rec = dict(base)
        rec[assessment_input] = normalized_val
        rec[model_feat] = normalized_val

        # Specific alias synchronization to ensure model features match input
        if assessment_input in ['duty_hours_per_week', 'Duty_Hours_Per_Week', 'Working_Hours_per_Week']:
            rec['Duty_Hours_Per_Week'] = normalized_val
            rec['Working_Hours_per_Week'] = normalized_val
            rec['duty_hours_per_week'] = normalized_val
        elif assessment_input in ['consecutive_duty_days', 'Consecutive_Duty_Days', 'consecutive_days_on_duty']:
            rec['Consecutive_Duty_Days'] = normalized_val
            rec['consecutive_days_on_duty'] = normalized_val
        elif assessment_input in ['mood_score', 'JobSatisfaction']:
            rec['mood_score'] = normalized_val
            rec['JobSatisfaction'] = normalized_val
            rec['RelationshipSatisfaction'] = normalized_val
        elif assessment_input in ['burnout_symptoms', 'Burnout_Symptoms']:
            rec['Burnout_Symptoms'] = normalized_val
            rec['burnout_symptoms'] = normalized_val
        elif assessment_input in ['leave_gap_days', 'Leave_Gap_Days']:
            rec['Leave_Gap_Days'] = normalized_val
            rec['leave_gap_days'] = normalized_val

        # Execute transformation
        df_single = pd.DataFrame([rec])
        if self.is_ensemble:
            X_prepared = self.model._prepare_input(df_single)
            X_trans = self.preprocessor.transform(X_prepared)
            
            # Find index of model_feat in preprocessor features
            matching_indices = [i for i, fn in enumerate(self.feature_names) if fn.endswith(f"__{model_feat}") or fn == f"num__{model_feat}"]
            if matching_indices:
                t_val = round(float(X_trans[0, matching_indices[0]]), 4)
            else:
                t_val = "N/A"

            # Predict probabilities
            assessment = self.model.assess(rec)
            cal_prob = assessment['risk_probability']
            risk_score = assessment['risk_score']
            probas = assessment['probabilities']
            # Uncalibrated / base probability (raw ensemble expectation before calibration)
            model_prob = round(float(probas.get('Medium', 0.0) * 0.50 + probas.get('High', 0.0) * 1.00), 3)

            # SHAP contribution
            shap_val = 0.0
            if self.shap_explainer is not None and matching_indices:
                try:
                    sv = self.shap_explainer.shap_values(X_trans)
                    # Use class 2 (High) or class 1 (Medium)
                    idx = matching_indices[0]
                    if isinstance(sv, list):
                        shap_val = round(float(sv[2][0][idx]), 4)
                    elif isinstance(sv, np.ndarray) and sv.ndim == 3:
                        shap_val = round(float(sv[0, idx, 2]), 4)
                except Exception:
                    shap_val = 0.0
        else:
            t_val = "N/A"
            probas = self.model.predict_proba(df_single).iloc[0].to_dict()
            cal_prob = round(float(probas.get('Medium', 0.0) * 0.50 + probas.get('High', 0.0) * 1.00), 3)
            model_prob = cal_prob
            risk_score = round(cal_prob * 100.0, 1)
            shap_val = 0.0

        return {
            "assessment_input": assessment_input,
            "raw_value": raw_value,
            "normalized_value": normalized_val,
            "model_feature": model_feat,
            "transformed_value": t_val,
            "model_probability": model_prob,
            "calibrated_probability": cal_prob,
            "risk_score": risk_score,
            "shap_contribution": shap_val
        }

    def audit_feature_passthrough(
        self,
        feature_name: str,
        test_values: List[Any],
        baseline_record: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Audits a list of sequential values for a single feature."""
        return [
            self.trace_single_input(feature_name, val, baseline_record=baseline_record)
            for val in test_values
        ]

    def audit_all_assessment_inputs(
        self,
        baseline_record: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Audits all 14 assessment inputs with canonical test sequences."""
        test_suite = {
            'duty_hours_per_week': [30.0, 40.0, 50.0, 60.0, 70.0, 80.0],
            'consecutive_duty_days': [2, 4, 7, 14, 21, 28],
            'night_shifts_per_month': [0, 2, 5, 8, 12, 16],
            'sleep_hours': [8.0, 7.5, 6.5, 5.5, 4.5, 3.5],
            'physical_fatigue': [1, 2, 3, 4, 5],
            'physical_activity_hours_per_week': [0.0, 2.0, 4.0, 6.0, 8.0],
            'mood_score': [5, 4, 3, 2, 1],
            'burnout_symptoms': ['Rarely', 'Sometimes', 'Often'],
            'interest_score': [0, 1, 2, 3],
            'discouraged_score': [0, 1, 2, 3],
            'concentration_score': [0, 1, 2, 3],
            'operational_exposure': ['Low', 'Medium', 'High'],
            'remote_posting': ['No', 'Yes'],
            'leave_gap_days': [15, 30, 60, 90, 150, 210]
        }

        results = {}
        for feat, vals in test_suite.items():
            results[feat] = self.audit_feature_passthrough(feat, vals, baseline_record)
        return results

def get_risk_feature_auditor(model_path: Optional[str] = None) -> RiskFeatureAuditor:
    return RiskFeatureAuditor(model_path=model_path)

if __name__ == '__main__':
    auditor = get_risk_feature_auditor()
    print(f"Loaded RiskFeatureAuditor with model: {auditor.model_path}")
    print("\nAuditing Duty Hours Per Week:")
    dh_audit = auditor.audit_feature_passthrough('duty_hours_per_week', [30.0, 40.0, 50.0, 60.0, 70.0, 80.0])
    print(json.dumps(dh_audit, indent=2))
