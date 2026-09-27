import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.risk_feature_audit import DEFAULT_BASELINE_RECORD
from src.prediction import PersonnelWelfarePredictor
import src.ensemble_v2 as ens

print("=" * 80)
print("1. FULL PIPELINE AUDIT: CHECKING MODEL FILES & CLASS ORDERING")
print("=" * 80)

models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
model_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
print(f"Found model files in models/: {model_files}")

for mf in ['stress_risk_ensemble_v4.pkl', 'stress_risk_ensemble_v3.pkl', 'final_stress_prediction_pipeline.pkl']:
    path = os.path.join(models_dir, mf)
    if os.path.exists(path):
        m = joblib.load(path)
        print(f"\nModel: {mf}")
        print(f"  Type: {type(m)}")
        if hasattr(m, 'classes_'):
            print(f"  model.classes_: {m.classes_}")
        if hasattr(m, 'int_to_label'):
            print(f"  int_to_label: {m.int_to_label}")
        if hasattr(m, 'label_to_int'):
            print(f"  label_to_int: {m.label_to_int}")
        if hasattr(m, 'base_models'):
            print("  Base models classes_:")
            for bm_name, bm in m.base_models.items():
                print(f"    {bm_name}: classes_ = {getattr(bm, 'classes_', 'N/A')}")
        if hasattr(m, 'meta_model'):
            print(f"  meta_model classes_: {getattr(m.meta_model, 'classes_', 'N/A')}")
        if hasattr(m, 'calibrator') and m.calibrator is not None:
            print(f"  calibrator classes_: {getattr(m.calibrator, 'classes_', 'N/A')}")

print("\n" + "=" * 80)
print("2. PREPROCESSOR FEATURE NAMES & ORDERING AUDIT")
print("=" * 80)
v4_m = joblib.load(os.path.join(models_dir, 'stress_risk_ensemble_v4.pkl'))
prep = v4_m.preprocessor
f_names = prep.get_feature_names_out()
print(f"Total features after preprocessor: {len(f_names)}")
print(f"Sample transformed feature names:\n  {list(f_names[:10])}\n  ...\n  {list(f_names[-10:])}")

print("\n" + "=" * 80)
print("3. RAW BASELINE & INPUT MAPPING AUDIT")
print("=" * 80)
rec = DEFAULT_BASELINE_RECORD.copy()
print(f"Default baseline record keys count: {len(rec)}")
# Check aliases
print(f"Working_Hours_per_Week: {rec.get('Working_Hours_per_Week')}")
print(f"Duty_Hours_Per_Week: {rec.get('Duty_Hours_Per_Week')}")
print(f"duty_hours_per_week: {rec.get('duty_hours_per_week')}")
print(f"Sleep_Hours: {rec.get('Sleep_Hours')}")
print(f"sleep_hours: {rec.get('sleep_hours')}")
print(f"mood_score: {rec.get('mood_score')}")
print(f"JobSatisfaction: {rec.get('JobSatisfaction')}")

print("\n" + "=" * 80)
print("4. AUDITING _prepare_input IN V4")
print("=" * 80)
df_in = pd.DataFrame([rec])
df_aligned = v4_m._prepare_input(df_in)
print(f"df_aligned shape: {df_aligned.shape}")
print(f"df_aligned Duty_Hours_Per_Week: {df_aligned['Duty_Hours_Per_Week'].iloc[0]}")
print(f"df_aligned Working_Hours_per_Week: {df_aligned['Working_Hours_per_Week'].iloc[0]}")
print(f"df_aligned workload_intensity_ratio: {df_aligned['workload_intensity_ratio'].iloc[0]}")
print(f"df_aligned sleep_debt_index: {df_aligned['sleep_debt_index'].iloc[0]}")

print("\n" + "=" * 80)
print("5. AUDITING MONOTONICITY & PROBABILITIES ON V4")
print("=" * 80)
print("Sweeping Duty Hours (40 -> 50 -> 60 -> 70 -> 80 -> 90):")
for h in [40, 50, 60, 70, 80, 90]:
    test_rec = rec.copy()
    test_rec.update({'Duty_Hours_Per_Week': float(h), 'Working_Hours_per_Week': float(h), 'duty_hours_per_week': float(h)})
    res = v4_m.assess(test_rec)
    p = res['probabilities']
    print(f"  Hours={h:2d} | Score={res['risk_score']:5.1f} | Tier={res['risk_priority']:<10} | Stress={res['stress_level']:<6} | Low={p['Low']:.3f}, Med={p['Medium']:.3f}, High={p['High']:.3f}")

print("\nSweeping Sleep Hours (8 -> 7 -> 6 -> 5 -> 4):")
for s in [8.0, 7.0, 6.0, 5.0, 4.0]:
    test_rec = rec.copy()
    test_rec.update({'Sleep_Hours': s, 'sleep_hours': s})
    res = v4_m.assess(test_rec)
    p = res['probabilities']
    print(f"  Sleep={s:3.1f} | Score={res['risk_score']:5.1f} | Tier={res['risk_priority']:<10} | Stress={res['stress_level']:<6} | Low={p['Low']:.3f}, Med={p['Medium']:.3f}, High={p['High']:.3f}")

print("\nSweeping Fatigue (1 -> 2 -> 3 -> 4 -> 5):")
for f in [1, 2, 3, 4, 5]:
    test_rec = rec.copy()
    test_rec.update({'physical_fatigue': f})
    res = v4_m.assess(test_rec)
    p = res['probabilities']
    print(f"  Fatigue={f:1d} | Score={res['risk_score']:5.1f} | Tier={res['risk_priority']:<10} | Stress={res['stress_level']:<6} | Low={p['Low']:.3f}, Med={p['Medium']:.3f}, High={p['High']:.3f}")

print("\nSweeping Mood / Job Satisfaction (5 -> 4 -> 3 -> 2 -> 1):")
for m in [5, 4, 3, 2, 1]:
    test_rec = rec.copy()
    test_rec.update({'mood_score': m, 'JobSatisfaction': m})
    res = v4_m.assess(test_rec)
    p = res['probabilities']
    print(f"  Mood={m:1d} | Score={res['risk_score']:5.1f} | Tier={res['risk_priority']:<10} | Stress={res['stress_level']:<6} | Low={p['Low']:.3f}, Med={p['Medium']:.3f}, High={p['High']:.3f}")

print("\nSweeping Consecutive Duty Days (2 -> 5 -> 10 -> 15 -> 25):")
for c in [2, 5, 10, 15, 25]:
    test_rec = rec.copy()
    test_rec.update({'Consecutive_Duty_Days': c, 'consecutive_duty_days': c, 'consecutive_days_on_duty': c})
    res = v4_m.assess(test_rec)
    p = res['probabilities']
    print(f"  Consec={c:2d} | Score={res['risk_score']:5.1f} | Tier={res['risk_priority']:<10} | Stress={res['stress_level']:<6} | Low={p['Low']:.3f}, Med={p['Medium']:.3f}, High={p['High']:.3f}")

print("\nSweeping Night Shifts (0 -> 2 -> 5 -> 10 -> 18):")
for ns in [0, 2, 5, 10, 18]:
    test_rec = rec.copy()
    test_rec.update({'Night_Shifts_Per_Month': ns, 'night_shifts_per_month': ns})
    res = v4_m.assess(test_rec)
    p = res['probabilities']
    print(f"  NightShifts={ns:2d} | Score={res['risk_score']:5.1f} | Tier={res['risk_priority']:<10} | Stress={res['stress_level']:<6} | Low={p['Low']:.3f}, Med={p['Medium']:.3f}, High={p['High']:.3f}")
