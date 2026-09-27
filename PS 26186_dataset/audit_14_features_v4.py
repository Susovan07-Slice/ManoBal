import os
import sys
import pandas as pd
import numpy as np
import joblib

# Ensure path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from train_phase34e_ensemble import StressRiskEnsembleV4
from src.risk_feature_audit import DEFAULT_BASELINE_RECORD

v4_model_path = os.path.join(os.path.dirname(__file__), 'models', 'stress_risk_ensemble_v4.pkl')
v4_model = joblib.load(v4_model_path)

baseline = DEFAULT_BASELINE_RECORD.copy()
baseline.update({
    'Working_Hours_per_Week': 44.0,
    'Duty_Hours_Per_Week': 44.0,
    'duty_hours_per_week': 44.0,
    'Sleep_Hours': 7.0,
    'sleep_hours': 7.0,
    'Consecutive_Duty_Days': 4,
    'consecutive_duty_days': 4,
    'Night_Shifts_Per_Month': 2,
    'night_shifts_per_month': 2,
    'physical_fatigue': 2,
    'Physical_Activity_Hours_per_Week': 5.0,
    'physical_activity_hours_per_week': 5.0,
    'mood_score': 4,
    'JobSatisfaction': 4,
    'burnout_symptoms': 'Rarely',
    'Burnout_Symptoms': 'Rarely',
    'interest_score': 0,
    'discouraged_score': 0,
    'concentration_score': 0,
    'Operational_Exposure': 'Low',
    'operational_exposure': 'Low',
    'Remote_Posting': 'No',
    'remote_posting': 'No',
    'Leave_Gap_Days': 25,
    'leave_gap_days': 25,
})

sweeps = {
    'duty_hours_per_week': [20.0, 30.0, 40.0, 44.0, 50.0, 60.0, 70.0, 80.0, 90.0],
    'consecutive_duty_days': [1, 2, 4, 7, 10, 14, 21, 30],
    'night_shifts_per_month': [0, 2, 4, 6, 8, 10, 15, 20],
    'sleep_hours': [4.0, 5.0, 6.0, 7.0, 7.5, 8.0, 9.0],
    'physical_fatigue': [1, 2, 3, 4, 5],
    'physical_activity_hours_per_week': [0.0, 2.0, 5.0, 8.0, 12.0],
    'mood_score': [1, 2, 3, 4, 5],
    'burnout_symptoms': ['Rarely', 'Sometimes', 'Often'],
    'interest_score': [0, 1, 2, 3],
    'discouraged_score': [0, 1, 2, 3],
    'concentration_score': [0, 1, 2, 3],
    'operational_exposure': ['Low', 'Medium', 'High'],
    'remote_posting': ['No', 'Yes'],
    'leave_gap_days': [7, 14, 30, 60, 90, 180, 270, 365]
}

alias_map = {
    'duty_hours_per_week': ['Duty_Hours_Per_Week', 'Working_Hours_per_Week'],
    'consecutive_duty_days': ['Consecutive_Duty_Days', 'consecutive_days_on_duty'],
    'night_shifts_per_month': ['Night_Shifts_Per_Month'],
    'sleep_hours': ['Sleep_Hours'],
    'physical_fatigue': ['physical_fatigue'],
    'physical_activity_hours_per_week': ['Physical_Activity_Hours_per_Week'],
    'mood_score': ['mood_score', 'JobSatisfaction', 'RelationshipSatisfaction'],
    'burnout_symptoms': ['Burnout_Symptoms', 'burnout_symptoms'],
    'interest_score': ['interest_score'],
    'discouraged_score': ['discouraged_score'],
    'concentration_score': ['concentration_score'],
    'operational_exposure': ['Operational_Exposure', 'operational_exposure'],
    'remote_posting': ['Remote_Posting', 'remote_posting'],
    'leave_gap_days': ['Leave_Gap_Days', 'leave_gap_days']
}

all_results = []
monotonicity_pass = True

for feat, vals in sweeps.items():
    print(f"\n==================================================")
    print(f"FEATURE: {feat}")
    print(f"==================================================")
    prev_score = None
    mono_inc = True
    mono_dec = True
    for v in vals:
        rec = baseline.copy()
        rec[feat] = v
        for a in alias_map.get(feat, []):
            rec[a] = v
        r = v4_model.assess(rec)
        score = r['risk_score']
        p_low = r['probabilities']['Low']
        p_med = r['probabilities']['Medium']
        p_high = r['probabilities']['High']
        
        print(f"  {feat}={str(v):<10} | P(Low)={p_low:.3f}, P(Med)={p_med:.3f}, P(High)={p_high:.3f} | Score={score:.1f} | Tier={r['risk_priority']}")
        
        if prev_score is not None:
            if score < prev_score - 1e-4:
                mono_inc = False
            if score > prev_score + 1e-4:
                mono_dec = False
        prev_score = score
        
        all_results.append({
            'feature': feat,
            'value': str(v),
            'p_low': p_low,
            'p_med': p_med,
            'p_high': p_high,
            'risk_score': score,
            'tier': r['risk_priority']
        })
    print(f"  Result: mono_increasing={mono_inc}, mono_decreasing={mono_dec}")

df_res = pd.DataFrame(all_results)
df_res.to_csv('feature_sensitivity_sweep_v4.csv', index=False)
print("\nSaved all sweeps to feature_sensitivity_sweep_v4.csv")
