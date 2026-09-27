import os
import sys
import json
import joblib
import pandas as pd
import numpy as np

# Ensure path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.prediction import PersonnelWelfarePredictor
from src.ensemble_v2 import ALL_MODEL_FEATURES, ALL_NUMERICAL_FEATURES, ALL_CATEGORICAL_FEATURES

predictor = PersonnelWelfarePredictor()
model = predictor.predictor

# Load preprocessor and base models
preprocessor = model.preprocessor
feature_names = list(preprocessor.get_feature_names_out())

# Base model importances
lgb_model = model.base_models['LightGBM']
xgb_model = model.base_models['XGBoost']
lr_model = model.base_models['LogisticRegression']

lgb_imp = lgb_model.feature_importances_
xgb_imp = xgb_model.feature_importances_
lr_coef = np.abs(lr_model.coef_).mean(axis=0)

features_14 = [
    {
        'api_field': 'duty_hours_per_week',
        'internal_field': 'duty_hours_per_week / Working_Hours_per_Week / Duty_Hours_Per_Week',
        'model_features': ['Duty_Hours_Per_Week', 'Working_Hours_per_Week', 'workload_intensity_ratio', 'active_recovery_ratio'],
        'datatype': 'float',
        'encoding': 'StandardScaler (numeric)',
        'allowed_range': '[0.0, 120.0] (typical [20, 90])',
        'semantic_meaning': 'Weekly operational duty hours assigned/worked',
        'expected_direction': 'Increasing (+1)',
        'consumed': True,
        'aliased': 'Working_Hours_per_Week, Duty_Hours_Per_Week, duty_hours_per_week'
    },
    {
        'api_field': 'consecutive_duty_days',
        'internal_field': 'consecutive_duty_days / Consecutive_Duty_Days / consecutive_days_on_duty',
        'model_features': ['Consecutive_Duty_Days', 'consecutive_days_on_duty', 'night_shift_burden', 'deployment_fatigue_factor'],
        'datatype': 'int',
        'encoding': 'StandardScaler (numeric)',
        'allowed_range': '[0, 60] (typical [0, 30])',
        'semantic_meaning': 'Continuous consecutive duty days without a 24h rest period',
        'expected_direction': 'Increasing (+1)',
        'consumed': True,
        'aliased': 'Consecutive_Duty_Days, consecutive_days_on_duty'
    },
    {
        'api_field': 'night_shifts_per_month',
        'internal_field': 'night_shifts_per_month / Night_Shifts_Per_Month',
        'model_features': ['Night_Shifts_Per_Month', 'night_shift_burden'],
        'datatype': 'int',
        'encoding': 'StandardScaler (numeric)',
        'allowed_range': '[0, 31] (typical [0, 20])',
        'semantic_meaning': 'Night shifts assigned in trailing 30 days (circadian strain)',
        'expected_direction': 'Increasing (+1)',
        'consumed': True,
        'aliased': 'Night_Shifts_Per_Month'
    },
    {
        'api_field': 'sleep_hours',
        'internal_field': 'sleep_hours / Sleep_Hours',
        'model_features': ['Sleep_Hours', 'sleep_debt_index', 'active_recovery_ratio'],
        'datatype': 'float',
        'encoding': 'StandardScaler (numeric)',
        'allowed_range': '[0.0, 24.0] (typical [2.5, 9.0])',
        'semantic_meaning': 'Average nightly restorative sleep hours',
        'expected_direction': 'Decreasing (-1) (Protective)',
        'consumed': True,
        'aliased': 'Sleep_Hours'
    },
    {
        'api_field': 'physical_fatigue',
        'internal_field': 'physical_fatigue',
        'model_features': ['physical_fatigue'],
        'datatype': 'int',
        'encoding': 'StandardScaler (numeric)',
        'allowed_range': '[1, 5] (1=Refreshed, 5=Exhausted)',
        'semantic_meaning': 'Self-reported physical fatigue and muscular exhaustion',
        'expected_direction': 'Increasing (+1)',
        'consumed': True,
        'aliased': 'physical_fatigue'
    },
    {
        'api_field': 'physical_activity_hours_per_week',
        'internal_field': 'physical_activity_hours_per_week / Physical_Activity_Hours_per_Week',
        'model_features': ['Physical_Activity_Hours_per_Week', 'active_recovery_ratio'],
        'datatype': 'float',
        'encoding': 'StandardScaler (numeric)',
        'allowed_range': '[0.0, 50.0] (typical [0.5, 15.0])',
        'semantic_meaning': 'Weekly physical conditioning / exercise hours',
        'expected_direction': 'Decreasing (-1) (Protective)',
        'consumed': True,
        'aliased': 'Physical_Activity_Hours_per_Week'
    },
    {
        'api_field': 'mood_score',
        'internal_field': 'mood_score / JobSatisfaction / RelationshipSatisfaction',
        'model_features': ['mood_score', 'JobSatisfaction', 'RelationshipSatisfaction'],
        'datatype': 'int',
        'encoding': 'StandardScaler (numeric)',
        'allowed_range': '[1, 5] (1=Distressed/Depressed, 5=Highly Resilient)',
        'semantic_meaning': 'Self-reported psychological morale, mood and satisfaction',
        'expected_direction': 'Decreasing (-1) (Protective)',
        'consumed': True,
        'aliased': 'JobSatisfaction, RelationshipSatisfaction, mood_score'
    },
    {
        'api_field': 'burnout_symptoms',
        'internal_field': 'burnout_symptoms / Burnout_Symptoms',
        'model_features': ['Burnout_Symptoms'],
        'datatype': 'str',
        'encoding': 'OneHotEncoder (Rarely, Sometimes, Often)',
        'allowed_range': '["Rarely", "Sometimes", "Often"]',
        'semantic_meaning': 'Frequency of feeling emotionally overwhelmed/burned out',
        'expected_direction': 'Increasing (Often > Sometimes > Rarely)',
        'consumed': True,
        'aliased': 'Burnout_Symptoms'
    },
    {
        'api_field': 'interest_score',
        'internal_field': 'interest_score',
        'model_features': ['interest_score'],
        'datatype': 'int',
        'encoding': 'StandardScaler (numeric)',
        'allowed_range': '[0, 3] (0=None/Normal, 1=Mild loss, 2=Moderate loss, 3=Severe loss/Anhedonia)',
        'semantic_meaning': 'Severity of loss of interest/satisfaction in tasks (PHQ-9 item 1)',
        'expected_direction': 'Increasing (+1)',
        'consumed': True,
        'aliased': 'interest_score'
    },
    {
        'api_field': 'discouraged_score',
        'internal_field': 'discouraged_score',
        'model_features': ['discouraged_score'],
        'datatype': 'int',
        'encoding': 'StandardScaler (numeric)',
        'allowed_range': '[0, 3] (0=Never, 1=Several days, 2=More than half, 3=Nearly every day)',
        'semantic_meaning': 'Frequency of feeling down, depressed, discouraged, or exhausted (PHQ-9 item 2)',
        'expected_direction': 'Increasing (+1)',
        'consumed': True,
        'aliased': 'discouraged_score'
    },
    {
        'api_field': 'concentration_score',
        'internal_field': 'concentration_score',
        'model_features': ['concentration_score'],
        'datatype': 'int',
        'encoding': 'StandardScaler (numeric)',
        'allowed_range': '[0, 3] (0=Never, 1=Several days, 2=More than half, 3=Nearly every day)',
        'semantic_meaning': 'Difficulty concentrating on operational procedures (PHQ-9 item 7)',
        'expected_direction': 'Increasing (+1)',
        'consumed': True,
        'aliased': 'concentration_score'
    },
    {
        'api_field': 'operational_exposure',
        'internal_field': 'operational_exposure / Operational_Exposure',
        'model_features': ['Operational_Exposure'],
        'datatype': 'str',
        'encoding': 'OneHotEncoder (Low, Medium, High)',
        'allowed_range': '["Low", "Medium", "High"]',
        'semantic_meaning': 'Environmental and operational hazard exposure level',
        'expected_direction': 'Increasing (High > Medium > Low)',
        'consumed': True,
        'aliased': 'Operational_Exposure'
    },
    {
        'api_field': 'remote_posting',
        'internal_field': 'remote_posting / Remote_Posting',
        'model_features': ['Remote_Posting'],
        'datatype': 'str',
        'encoding': 'OneHotEncoder (No, Yes)',
        'allowed_range': '["No", "Yes"]',
        'semantic_meaning': 'Stationed at isolated / high-altitude / remote military post',
        'expected_direction': 'Increasing (Yes > No)',
        'consumed': True,
        'aliased': 'Remote_Posting'
    },
    {
        'api_field': 'leave_gap_days',
        'internal_field': 'leave_gap_days / Leave_Gap_Days',
        'model_features': ['Leave_Gap_Days', 'recovery_deficit_score'],
        'datatype': 'int',
        'encoding': 'StandardScaler (numeric)',
        'allowed_range': '[0, 365] (typical [7, 365])',
        'semantic_meaning': 'Days elapsed since personnel last took sanctioned restorative leave',
        'expected_direction': 'Increasing (+1)',
        'consumed': True,
        'aliased': 'Leave_Gap_Days'
    }
]

# Calculate total importance per feature
for f in features_14:
    tot_lgb, tot_xgb, tot_lr = 0.0, 0.0, 0.0
    for mf in f['model_features']:
        for idx, fn in enumerate(feature_names):
            clean = fn.replace('num__', '').replace('cat__', '')
            if clean == mf or clean.startswith(mf + '_'):
                tot_lgb += lgb_imp[idx]
                tot_xgb += xgb_imp[idx]
                tot_lr += lr_coef[idx]
    f['lgb_importance'] = float(tot_lgb)
    f['xgb_importance'] = float(tot_xgb)
    f['lr_coef_mean'] = float(tot_lr)

print("=== 14 ASSESSMENT FEATURES AUDIT SUMMARY ===")
audit_df = pd.DataFrame(features_14)
print(audit_df[['api_field', 'expected_direction', 'consumed', 'lgb_importance', 'xgb_importance', 'lr_coef_mean']].to_string())

with open('feature_audit_14.json', 'w') as f:
    json.dump(features_14, f, indent=2)
print("\nSaved full audit to feature_audit_14.json")
