import os
import sys
import joblib
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.risk_feature_audit import DEFAULT_BASELINE_RECORD
from src.prediction import PersonnelWelfarePredictor

predictor = PersonnelWelfarePredictor()
model = predictor.predictor

# Exact profile producing ~2.2 risk score
rec = DEFAULT_BASELINE_RECORD.copy()
rec.update({
    'Working_Hours_per_Week': 38.0,
    'Duty_Hours_Per_Week': 38.0,
    'duty_hours_per_week': 38.0,
    'Sleep_Hours': 6.5,
    'Consecutive_Duty_Days': 4,
    'consecutive_duty_days': 4,
    'Night_Shifts_Per_Month': 3,
    'night_shifts_per_month': 3,
    'physical_fatigue': 2,
    'mood_score': 3,
    'JobSatisfaction': 3,
    'Operational_Exposure': 'Low',
    'operational_exposure': 'Low',
    'burnout_symptoms': 'Rarely',
    'Burnout_Symptoms': 'Rarely',
})

print("=== 1. RAW ASSESSMENT INPUTS ===")
for k in [
    'Duty_Hours_Per_Week', 'Sleep_Hours', 'Consecutive_Duty_Days', 'Night_Shifts_Per_Month',
    'physical_fatigue', 'mood_score', 'burnout_symptoms', 'Operational_Exposure',
    'Remote_Posting', 'Leave_Gap_Days', 'Age', 'Department', 'Job_Role',
    'interest_score', 'discouraged_score', 'concentration_score'
]:
    print(f"  {k:30s}: {rec.get(k)}")

df_single = pd.DataFrame([rec])
X_aligned = model._prepare_input(df_single)
X_trans = model.preprocessor.transform(X_aligned)
fnames = model.preprocessor.get_feature_names_out()

print("\n=== 2. TRANSFORMED INPUTS (Canonical Preprocessed Features) ===")
for i, fn in enumerate(fnames):
    # Print numerical and active one-hot categorical features
    val = X_trans[0, i]
    if fn.startswith('num__') or val > 0:
        print(f"  {fn:45s}: {val:8.4f}")

bm_preds = {}
for name in ['LightGBM', 'XGBoost', 'LogisticRegression']:
    p = model.base_models[name].predict_proba(X_trans)[0]
    bm_preds[name] = p

Z = np.hstack([bm_preds[m] for m in ['LightGBM', 'XGBoost', 'LogisticRegression']]).reshape(1, -1)
meta_p = model.meta_model.predict_proba(Z)[0]
cal_p = model.calibrator.predict_proba(Z)[0]

print("\n=== 3. MODEL PROBABILITIES & STACKING ===")
for name in ['LightGBM', 'XGBoost', 'LogisticRegression']:
    p = bm_preds[name]
    print(f"  {name:22s}: P(Low)={p[0]:.4f}, P(Medium)={p[1]:.4f}, P(High)={p[2]:.4f}")
print(f"  {'Stacking Meta-Model':22s}: P(Low)={meta_p[0]:.4f}, P(Medium)={meta_p[1]:.4f}, P(High)={meta_p[2]:.4f}")
print(f"  {'Calibrated (Sigmoid)':22s}: P(Low)={cal_p[0]:.4f}, P(Medium)={cal_p[1]:.4f}, P(High)={cal_p[2]:.4f}")

sev = (0.0 * cal_p[0]) + (0.50 * cal_p[1]) + (1.00 * cal_p[2])
score = round(sev * 100.0, 1)

print("\n=== 4. SEVERITY & RISK SCORE ===")
print(f"  P(Low)              : {cal_p[0]:.4f}")
print(f"  P(Medium)           : {cal_p[1]:.4f}")
print(f"  P(High)             : {cal_p[2]:.4f}")
print(f"  Expected Severity   : {sev:.4f}")
print(f"  Final Risk Score    : {score} / 100")
print(f"  Model Version       : {model.model_version}")
print(f"  Calibration Method  : Platt Scaling (Sigmoid) via 5-Fold OOF CalibratedClassifierCV")
