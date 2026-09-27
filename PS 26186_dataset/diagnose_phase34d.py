import os
import sys
import joblib
import pandas as pd
import numpy as np

# Ensure path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.prediction import PersonnelWelfarePredictor
from src.risk_feature_audit import DEFAULT_BASELINE_RECORD

predictor = PersonnelWelfarePredictor()
model = predictor.predictor

print("=== 1. DIAGNOSING BASELINE & REPRESENTATIVE ASSESSMENTS ===")

# Test a representative profile: 44 hours/wk, 6.5h sleep, 4 consecutive days, 3 night shifts, mood=3
representative_profile = DEFAULT_BASELINE_RECORD.copy()
representative_profile.update({
    'Working_Hours_per_Week': 44.0,
    'Duty_Hours_Per_Week': 44.0,
    'duty_hours_per_week': 44.0,
    'Sleep_Hours': 6.5,
    'Consecutive_Duty_Days': 4,
    'consecutive_duty_days': 4,
    'Night_Shifts_Per_Month': 3,
    'night_shifts_per_month': 3,
    'mood_score': 3,
    'JobSatisfaction': 3,
    'physical_fatigue': 2,
    'burnout_symptoms': 'Rarely',
    'Burnout_Symptoms': 'Rarely',
})

# Search for the exact assessment producing ~2.2
match_profile = None
match_res = None
for duty in [38.0, 40.0, 42.0, 44.0]:
    for sleep in [6.5, 7.0, 7.2, 7.5]:
        for consec in [3, 4, 5]:
            for night in [1, 2, 3]:
                for fatigue in [1, 2]:
                    for mood in [3, 4]:
                        rec = DEFAULT_BASELINE_RECORD.copy()
                        rec.update({
                            'Working_Hours_per_Week': duty,
                            'Duty_Hours_Per_Week': duty,
                            'duty_hours_per_week': duty,
                            'Sleep_Hours': sleep,
                            'Consecutive_Duty_Days': consec,
                            'consecutive_duty_days': consec,
                            'Night_Shifts_Per_Month': night,
                            'night_shifts_per_month': night,
                            'physical_fatigue': fatigue,
                            'mood_score': mood,
                            'JobSatisfaction': mood,
                            'Operational_Exposure': 'Low',
                            'operational_exposure': 'Low',
                            'burnout_symptoms': 'Rarely',
                            'Burnout_Symptoms': 'Rarely',
                        })
                        r = predictor.assess_personnel(rec)
                        if abs(r['risk_score'] - 2.2) < 0.15:
                            match_profile = rec
                            match_res = r
                            break
                    if match_profile: break
                if match_profile: break
            if match_profile: break
        if match_profile: break
    if match_profile: break

if match_profile is None:
    # Check default assessment in DB or standard assessment
    match_profile = representative_profile
    match_res = res

print(f"Found target profile with risk_score = {match_res['risk_score']}:")
print(f"  Duty Hours: {match_profile.get('Duty_Hours_Per_Week')}")
print(f"  Sleep Hours: {match_profile.get('Sleep_Hours')}")
print(f"  Consecutive Days: {match_profile.get('Consecutive_Duty_Days')}")
print(f"  Night Shifts: {match_profile.get('Night_Shifts_Per_Month')}")
print(f"  Physical Fatigue: {match_profile.get('physical_fatigue')}")
print(f"  Mood Score: {match_profile.get('mood_score')}")
print(f"  Operational Exposure: {match_profile.get('Operational_Exposure')}")
print(f"  Stress Level: {match_res['stress_level']}")
print(f"  Risk Score: {match_res['risk_score']}")
print(f"  Risk Probability: {match_res['risk_probability']}")
print(f"  Calibrated Probabilities: {match_res['probabilities']}")
print(f"  Model Version: {match_res['model_version']}")
print(f"  Calibration Method: {match_res['calibration_method']}")
representative_profile = match_profile

# Now let's trace the exact pipeline components:
df_single = pd.DataFrame([representative_profile])
X_aligned = model._prepare_input(df_single)
X_trans = model.preprocessor.transform(X_aligned)

print("\n=== PIPELINE TRACE ===")
base_preds_list = []
for name in ['LightGBM', 'XGBoost', 'LogisticRegression']:
    bm = model.base_models[name]
    p = bm.predict_proba(X_trans)[0]
    base_preds_list.append(p)
    print(f"  {name:20s}: P(Low)={p[0]:.4f}, P(Med)={p[1]:.4f}, P(High)={p[2]:.4f}")

Z = np.hstack(base_preds_list).reshape(1, -1)
meta_p = model.meta_model.predict_proba(Z)[0]
print(f"  Meta-model (Stacking LR)  : P(Low)={meta_p[0]:.4f}, P(Med)={meta_p[1]:.4f}, P(High)={meta_p[2]:.4f}")

cal_p = model.calibrator.predict_proba(Z)[0]
print(f"  Calibrator (Platt Sigmoid): P(Low)={cal_p[0]:.4f}, P(Med)={cal_p[1]:.4f}, P(High)={cal_p[2]:.4f}")

# Current expected ordinal severity calculation in ensemble_v2.py lines 511-515:
# risk_probability = (0.0 * cal_probs[0]) + (0.50 * cal_probs[1]) + (1.00 * cal_probs[2])
# risk_score = round(risk_probability * 100.0, 1)
raw_expected_sev = (0.0 * cal_p[0]) + (0.50 * cal_p[1]) + (1.00 * cal_p[2])
print(f"\nCurrent formula: (0.0 * P(Low)) + (0.50 * P(Med)) + (1.00 * P(High))")
print(f"  = (0.0 * {cal_p[0]:.4f}) + (0.50 * {cal_p[1]:.4f}) + (1.00 * {cal_p[2]:.4f})")
print(f"  = {raw_expected_sev:.4f} -> risk_score = {raw_expected_sev * 100:.1f}")

# Let's inspect class distribution of the training dataset
dataset_path = os.path.join(os.path.dirname(__file__), 'final_dataset.csv')
if os.path.exists(dataset_path):
    df_train = pd.read_csv(dataset_path)
    print("\n=== 2. TRAINING DATASET CLASS DISTRIBUTION ===")
    if 'Stress_Level' in df_train.columns:
        counts = df_train['Stress_Level'].value_counts()
        pcts = df_train['Stress_Level'].value_counts(normalize=True) * 100
        for cls in counts.index:
            print(f"  {cls}: {counts[cls]} ({pcts[cls]:.1f}%)")
    else:
        print("Stress_Level column not found in final_dataset.csv")

# Let's inspect holdout / external validation datasets if any
d2_path = os.path.join(os.path.dirname(__file__), 'external_holdout_d2.csv')
if os.path.exists(d2_path):
    df_d2 = pd.read_csv(d2_path)
    print("\n=== D2 EXTERNAL HOLDOUT CLASS DISTRIBUTION ===")
    if 'Stress_Level' in df_d2.columns:
        counts = df_d2['Stress_Level'].value_counts()
        pcts = df_d2['Stress_Level'].value_counts(normalize=True) * 100
        for cls in counts.index:
            print(f"  {cls}: {counts[cls]} ({pcts[cls]:.1f}%)")

# Let's inspect feature values in the training set vs the representative profile
print("\n=== 3. TRAINING DATASET FEATURE DISTRIBUTIONS VS REPRESENTATIVE PROFILE ===")
key_cols = ['Duty_Hours_Per_Week', 'Sleep_Hours', 'Consecutive_Duty_Days', 'Night_Shifts_Per_Month', 'mood_score', 'physical_fatigue']
for col in key_cols:
    matched = None
    for c in df_train.columns:
        if c.lower() == col.lower():
            matched = c
            break
    if matched:
        s = df_train[matched].dropna()
        rep_val = representative_profile.get(col, representative_profile.get(matched, 'N/A'))
        print(f"  {col:25s}: Mean={s.mean():.2f}, Std={s.std():.2f}, Median={s.median():.2f}, 25%={s.quantile(0.25):.2f}, 75%={s.quantile(0.75):.2f} | Rep Val={rep_val}")

