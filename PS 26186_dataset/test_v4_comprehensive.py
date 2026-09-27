import os
import sys
import json
import joblib
import pandas as pd
import numpy as np

# Ensure path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from train_phase34e_ensemble import StressRiskEnsembleV4
from src.risk_feature_audit import DEFAULT_BASELINE_RECORD

v4_model_path = os.path.join(os.path.dirname(__file__), 'models', 'stress_risk_ensemble_v4.pkl')
v4_model = joblib.load(v4_model_path)

print("=== 1. PERSONA PROFILES ON V4 ===")
profiles = {
    'Profile A (Healthy)': {
        'duty_hours_per_week': 40.0,
        'Working_Hours_per_Week': 40.0,
        'Duty_Hours_Per_Week': 40.0,
        'consecutive_duty_days': 2,
        'Consecutive_Duty_Days': 2,
        'night_shifts_per_month': 2,
        'Night_Shifts_Per_Month': 2,
        'sleep_hours': 7.5,
        'Sleep_Hours': 7.5,
        'physical_fatigue': 1,
        'physical_activity_hours_per_week': 5.0,
        'Physical_Activity_Hours_per_Week': 5.0,
        'mood_score': 5,
        'JobSatisfaction': 5,
        'burnout_symptoms': 'Rarely',
        'Burnout_Symptoms': 'Rarely',
        'interest_score': 0,
        'discouraged_score': 0,
        'concentration_score': 0,
        'operational_exposure': 'Low',
        'Operational_Exposure': 'Low',
        'remote_posting': 'No',
        'Remote_Posting': 'No',
        'leave_gap_days': 14,
        'Leave_Gap_Days': 14,
    },
    'Representative Baseline (Peacetime)': {
        'duty_hours_per_week': 44.0,
        'Working_Hours_per_Week': 44.0,
        'Duty_Hours_Per_Week': 44.0,
        'consecutive_duty_days': 4,
        'Consecutive_Duty_Days': 4,
        'night_shifts_per_month': 2,
        'Night_Shifts_Per_Month': 2,
        'sleep_hours': 6.8,
        'Sleep_Hours': 6.8,
        'physical_fatigue': 2,
        'physical_activity_hours_per_week': 4.5,
        'Physical_Activity_Hours_per_Week': 4.5,
        'mood_score': 4,
        'JobSatisfaction': 4,
        'burnout_symptoms': 'Rarely',
        'Burnout_Symptoms': 'Rarely',
        'interest_score': 0,
        'discouraged_score': 0,
        'concentration_score': 0,
        'operational_exposure': 'Low',
        'Operational_Exposure': 'Low',
        'remote_posting': 'No',
        'Remote_Posting': 'No',
        'leave_gap_days': 25,
        'Leave_Gap_Days': 25,
    },
    'Profile B (Mild strain)': {
        'duty_hours_per_week': 48.0,
        'Working_Hours_per_Week': 48.0,
        'Duty_Hours_Per_Week': 48.0,
        'consecutive_duty_days': 5,
        'Consecutive_Duty_Days': 5,
        'night_shifts_per_month': 4,
        'Night_Shifts_Per_Month': 4,
        'sleep_hours': 6.2,
        'Sleep_Hours': 6.2,
        'physical_fatigue': 2,
        'physical_activity_hours_per_week': 4.0,
        'Physical_Activity_Hours_per_Week': 4.0,
        'mood_score': 4,
        'JobSatisfaction': 4,
        'burnout_symptoms': 'Rarely',
        'Burnout_Symptoms': 'Rarely',
        'interest_score': 1,
        'discouraged_score': 1,
        'concentration_score': 1,
        'operational_exposure': 'Low',
        'Operational_Exposure': 'Low',
        'remote_posting': 'No',
        'Remote_Posting': 'No',
        'leave_gap_days': 40,
        'Leave_Gap_Days': 40,
    },
    'Profile C (Moderate stress)': {
        'duty_hours_per_week': 58.0,
        'Working_Hours_per_Week': 58.0,
        'Duty_Hours_Per_Week': 58.0,
        'consecutive_duty_days': 8,
        'Consecutive_Duty_Days': 8,
        'night_shifts_per_month': 6,
        'Night_Shifts_Per_Month': 6,
        'sleep_hours': 6.0,
        'Sleep_Hours': 6.0,
        'physical_fatigue': 3,
        'physical_activity_hours_per_week': 3.0,
        'Physical_Activity_Hours_per_Week': 3.0,
        'mood_score': 3,
        'JobSatisfaction': 3,
        'burnout_symptoms': 'Sometimes',
        'Burnout_Symptoms': 'Sometimes',
        'interest_score': 1,
        'discouraged_score': 1,
        'concentration_score': 1,
        'operational_exposure': 'Medium',
        'Operational_Exposure': 'Medium',
        'remote_posting': 'No',
        'Remote_Posting': 'No',
        'leave_gap_days': 75,
        'Leave_Gap_Days': 75,
    },
    'Profile D (Severe operational strain)': {
        'duty_hours_per_week': 78.0,
        'Working_Hours_per_Week': 78.0,
        'Duty_Hours_Per_Week': 78.0,
        'consecutive_duty_days': 14,
        'Consecutive_Duty_Days': 14,
        'night_shifts_per_month': 10,
        'Night_Shifts_Per_Month': 10,
        'sleep_hours': 4.5,
        'Sleep_Hours': 4.5,
        'physical_fatigue': 4,
        'physical_activity_hours_per_week': 1.5,
        'Physical_Activity_Hours_per_Week': 1.5,
        'mood_score': 2,
        'JobSatisfaction': 2,
        'burnout_symptoms': 'Often',
        'Burnout_Symptoms': 'Often',
        'interest_score': 2,
        'discouraged_score': 2,
        'concentration_score': 2,
        'operational_exposure': 'High',
        'Operational_Exposure': 'High',
        'remote_posting': 'Yes',
        'Remote_Posting': 'Yes',
        'leave_gap_days': 160,
        'Leave_Gap_Days': 160,
    },
    'Profile E (Extreme combined strain)': {
        'duty_hours_per_week': 88.0,
        'Working_Hours_per_Week': 88.0,
        'Duty_Hours_Per_Week': 88.0,
        'consecutive_duty_days': 21,
        'Consecutive_Duty_Days': 21,
        'night_shifts_per_month': 14,
        'Night_Shifts_Per_Month': 14,
        'sleep_hours': 3.5,
        'Sleep_Hours': 3.5,
        'physical_fatigue': 5,
        'physical_activity_hours_per_week': 0.5,
        'Physical_Activity_Hours_per_Week': 0.5,
        'mood_score': 1,
        'JobSatisfaction': 1,
        'burnout_symptoms': 'Often',
        'Burnout_Symptoms': 'Often',
        'interest_score': 3,
        'discouraged_score': 3,
        'concentration_score': 3,
        'operational_exposure': 'High',
        'Operational_Exposure': 'High',
        'remote_posting': 'Yes',
        'Remote_Posting': 'Yes',
        'leave_gap_days': 240,
        'Leave_Gap_Days': 240,
    }
}

for name, prof in profiles.items():
    rec = DEFAULT_BASELINE_RECORD.copy()
    rec.update(prof)
    r = v4_model.assess(rec)
    print(f"{name:<38} | Score={r['risk_score']:<5.1f} | Tier={r['risk_priority']:<10} | Stress={r['stress_level']:<6} | P(Low)={r['probabilities']['Low']:.3f}, P(Med)={r['probabilities']['Medium']:.3f}, P(High)={r['probabilities']['High']:.3f} | Pct={r['risk_percentile']}")

print("\n=== 2. INTERACTION EFFECTS (STEP 9) ===")
interactions = [
    ("90h + 8.0h sleep", {'duty_hours_per_week': 90.0, 'Working_Hours_per_Week': 90.0, 'Duty_Hours_Per_Week': 90.0, 'sleep_hours': 8.0, 'Sleep_Hours': 8.0}),
    ("90h + 4.0h sleep", {'duty_hours_per_week': 90.0, 'Working_Hours_per_Week': 90.0, 'Duty_Hours_Per_Week': 90.0, 'sleep_hours': 4.0, 'Sleep_Hours': 4.0}),
    ("50h + 8.0h sleep", {'duty_hours_per_week': 50.0, 'Working_Hours_per_Week': 50.0, 'Duty_Hours_Per_Week': 50.0, 'sleep_hours': 8.0, 'Sleep_Hours': 8.0}),
    ("50h + 4.0h sleep", {'duty_hours_per_week': 50.0, 'Working_Hours_per_Week': 50.0, 'Duty_Hours_Per_Week': 50.0, 'sleep_hours': 4.0, 'Sleep_Hours': 4.0}),
    ("High duty + High fatigue", {'duty_hours_per_week': 80.0, 'Working_Hours_per_Week': 80.0, 'Duty_Hours_Per_Week': 80.0, 'physical_fatigue': 5}),
    ("High duty + Low fatigue",  {'duty_hours_per_week': 80.0, 'Working_Hours_per_Week': 80.0, 'Duty_Hours_Per_Week': 80.0, 'physical_fatigue': 1}),
    ("High duty + Burnout Often", {'duty_hours_per_week': 80.0, 'Working_Hours_per_Week': 80.0, 'Duty_Hours_Per_Week': 80.0, 'burnout_symptoms': 'Often', 'Burnout_Symptoms': 'Often'}),
    ("High duty + Burnout Rarely", {'duty_hours_per_week': 80.0, 'Working_Hours_per_Week': 80.0, 'Duty_Hours_Per_Week': 80.0, 'burnout_symptoms': 'Rarely', 'Burnout_Symptoms': 'Rarely'}),
    ("Poor sleep + 12 night shifts", {'sleep_hours': 4.0, 'Sleep_Hours': 4.0, 'night_shifts_per_month': 12, 'Night_Shifts_Per_Month': 12}),
    ("Good sleep + 0 night shifts",  {'sleep_hours': 8.0, 'Sleep_Hours': 8.0, 'night_shifts_per_month': 0, 'Night_Shifts_Per_Month': 0}),
    ("Long leave gap (240d) + 70h duty", {'leave_gap_days': 240, 'Leave_Gap_Days': 240, 'duty_hours_per_week': 70.0, 'Working_Hours_per_Week': 70.0, 'Duty_Hours_Per_Week': 70.0}),
    ("Short leave gap (14d) + 40h duty", {'leave_gap_days': 14, 'Leave_Gap_Days': 14, 'duty_hours_per_week': 40.0, 'Working_Hours_per_Week': 40.0, 'Duty_Hours_Per_Week': 40.0}),
    ("High op exposure + 75h duty", {'operational_exposure': 'High', 'Operational_Exposure': 'High', 'duty_hours_per_week': 75.0, 'Working_Hours_per_Week': 75.0, 'Duty_Hours_Per_Week': 75.0}),
    ("Low op exposure + 40h duty",  {'operational_exposure': 'Low', 'Operational_Exposure': 'Low', 'duty_hours_per_week': 40.0, 'Working_Hours_per_Week': 40.0, 'Duty_Hours_Per_Week': 40.0}),
]

for label, override in interactions:
    rec = DEFAULT_BASELINE_RECORD.copy()
    rec.update(override)
    r = v4_model.assess(rec)
    print(f"  {label:<34} -> Score={r['risk_score']:<5.1f} | Tier={r['risk_priority']:<10} | Probs={r['probabilities']}")

print("\n=== 3. SWEEP DUTY HOURS ON V4 ===")
duty_vals = [20, 30, 40, 44, 50, 60, 70, 80, 85, 90]
for d in duty_vals:
    rec = DEFAULT_BASELINE_RECORD.copy()
    rec.update({'duty_hours_per_week': float(d), 'Working_Hours_per_Week': float(d), 'Duty_Hours_Per_Week': float(d)})
    r = v4_model.assess(rec)
    print(f"  Duty={d:<3}h -> Score={r['risk_score']:<5.1f} | Tier={r['risk_priority']:<10} | Probs={r['probabilities']}")
