import os
import sys
import numpy as np
import pandas as pd
import joblib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.risk_feature_audit import DEFAULT_BASELINE_RECORD

v4_m = joblib.load('models/stress_risk_ensemble_v4.pkl')

profiles = {
    'Healthy Profile (Nominal, 40h, 7.5h sleep, fatigue=1)': {
        'Duty_Hours_Per_Week': 40.0, 'Working_Hours_per_Week': 40.0, 'duty_hours_per_week': 40.0,
        'Sleep_Hours': 7.5, 'physical_fatigue': 1, 'mood_score': 5, 'JobSatisfaction': 5,
        'Consecutive_Duty_Days': 2, 'consecutive_duty_days': 2,
        'Night_Shifts_Per_Month': 1, 'Burnout_Symptoms': 'Rarely',
        'Operational_Exposure': 'Low', 'Remote_Posting': 'No', 'Leave_Gap_Days': 14
    },
    'Peacetime Baseline (44h, 6.8h sleep, fatigue=2)': {
        'Duty_Hours_Per_Week': 44.0, 'Working_Hours_per_Week': 44.0, 'duty_hours_per_week': 44.0,
        'Sleep_Hours': 6.8, 'physical_fatigue': 2, 'mood_score': 4, 'JobSatisfaction': 4,
        'Consecutive_Duty_Days': 4, 'consecutive_duty_days': 4,
        'Night_Shifts_Per_Month': 2, 'Burnout_Symptoms': 'Rarely',
        'Operational_Exposure': 'Low', 'Remote_Posting': 'No', 'Leave_Gap_Days': 25
    },
    'Mild Strain Profile (52h, 6.0h sleep, fatigue=3)': {
        'Duty_Hours_Per_Week': 52.0, 'Working_Hours_per_Week': 52.0, 'duty_hours_per_week': 52.0,
        'Sleep_Hours': 6.0, 'physical_fatigue': 3, 'mood_score': 3, 'JobSatisfaction': 3,
        'Consecutive_Duty_Days': 6, 'consecutive_duty_days': 6,
        'Night_Shifts_Per_Month': 4, 'Burnout_Symptoms': 'Sometimes',
        'Operational_Exposure': 'Medium', 'Remote_Posting': 'No', 'Leave_Gap_Days': 45
    },
    'Moderate Strain Profile (62h, 5.2h sleep, fatigue=4)': {
        'Duty_Hours_Per_Week': 62.0, 'Working_Hours_per_Week': 62.0, 'duty_hours_per_week': 62.0,
        'Sleep_Hours': 5.2, 'physical_fatigue': 4, 'mood_score': 2, 'JobSatisfaction': 2,
        'Consecutive_Duty_Days': 10, 'consecutive_duty_days': 10,
        'Night_Shifts_Per_Month': 7, 'Burnout_Symptoms': 'Sometimes',
        'Operational_Exposure': 'Medium', 'Remote_Posting': 'Yes', 'Leave_Gap_Days': 90
    },
    'Severe Operational Strain (74h, 4.5h sleep, fatigue=5, often burnout)': {
        'Duty_Hours_Per_Week': 74.0, 'Working_Hours_per_Week': 74.0, 'duty_hours_per_week': 74.0,
        'Sleep_Hours': 4.5, 'physical_fatigue': 5, 'mood_score': 2, 'JobSatisfaction': 2,
        'Consecutive_Duty_Days': 16, 'consecutive_duty_days': 16,
        'Night_Shifts_Per_Month': 12, 'Burnout_Symptoms': 'Often',
        'Operational_Exposure': 'High', 'Remote_Posting': 'Yes', 'Leave_Gap_Days': 160,
        'Deployment_Days': 140
    },
    'Extreme Combined Strain (88h, 3.8h sleep, fatigue=5, 18 nights)': {
        'Duty_Hours_Per_Week': 88.0, 'Working_Hours_per_Week': 88.0, 'duty_hours_per_week': 88.0,
        'Sleep_Hours': 3.8, 'physical_fatigue': 5, 'mood_score': 1, 'JobSatisfaction': 1,
        'Consecutive_Duty_Days': 24, 'consecutive_duty_days': 24,
        'Night_Shifts_Per_Month': 18, 'Burnout_Symptoms': 'Often',
        'Operational_Exposure': 'High', 'Remote_Posting': 'Yes', 'Leave_Gap_Days': 240,
        'Deployment_Days': 200
    },
    'Workload Only 90h (Baseline otherwise)': {
        'Duty_Hours_Per_Week': 90.0, 'Working_Hours_per_Week': 90.0, 'duty_hours_per_week': 90.0
    }
}

print(f"{'Profile':<40} | {'P(Low)':<7} | {'P(Med)':<7} | {'P(High)':<7} | {'M1 (0/50/100)':<13} | {'M2 (16/50/88)':<13} | {'M3 (18/52/86)':<13}")
print("-" * 115)

for name, updates in profiles.items():
    rec = DEFAULT_BASELINE_RECORD.copy()
    rec.update(updates)
    
    # Run through model preprocessor and calibrator
    df_single = pd.DataFrame([rec])
    X_aligned = v4_m._prepare_input(df_single)
    X_trans = v4_m.preprocessor.transform(X_aligned)
    
    base_preds_list = []
    for m_name in ['LightGBM', 'XGBoost', 'LogisticRegression']:
        base_preds_list.append(v4_m.base_models[m_name].predict_proba(X_trans)[0])
    Z = np.hstack(base_preds_list).reshape(1, -1)
    
    cal_probs = v4_m.calibrator.predict_proba(Z)[0]
    p_l = cal_probs[0]
    p_m = cal_probs[1]
    p_h = cal_probs[2]
    
    m1 = 0.0 * p_l + 50.0 * p_m + 100.0 * p_h
    m2 = 16.0 * p_l + 50.0 * p_m + 88.0 * p_h
    m3 = 18.0 * p_l + 52.0 * p_m + 86.0 * p_h
    
    print(f"{name:<40} | {p_l:<7.3f} | {p_m:<7.3f} | {p_h:<7.3f} | {m1:<13.1f} | {m2:<13.1f} | {m3:<13.1f}")
