import os
import sys
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss

# Ensure path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.prediction import PersonnelWelfarePredictor
from dataset_builder_p34 import build_scientifically_grounded_training_dataset

predictor = PersonnelWelfarePredictor()
model = predictor.predictor

X, y = build_scientifically_grounded_training_dataset('data/FINAL_MAIN_STRESS_DATASET.csv')
y_int = y.map({'Low': 0, 'Medium': 1, 'High': 2}).values

# Get calibrated probabilities for all samples
df_proc = model.predict_proba(X)
p_low = df_proc['Low'].values
p_med = df_proc['Medium'].values
p_high = df_proc['High'].values
P = np.column_stack([p_low, p_med, p_high])

# Method 0: Current V3 Expected Value (0, 50, 100)
scores_m0 = (0.0 * p_low + 50.0 * p_med + 100.0 * p_high)

# Method 1: Centroid Expected Ordinal Severity (18, 52, 85)
scores_m1 = (18.0 * p_low + 52.0 * p_med + 85.0 * p_high)

# Method 2: Continuous Ordinal Severity Expectation modulated by operational strain index z
# z is the linear combination of normalized operational indicators:
# duty hours (30-90), sleep debt (0-4), consecutive days (1-30), fatigue (1-5), mood deficit (0-4)
duty_norm = np.clip((X['Duty_Hours_Per_Week'].values - 30.0) / 60.0, 0.0, 1.0)
sleep_debt_norm = np.clip((8.0 - X['Sleep_Hours'].values) / 5.0, 0.0, 1.0)
consec_norm = np.clip((X['Consecutive_Duty_Days'].values - 1.0) / 29.0, 0.0, 1.0)
night_norm = np.clip(X['Night_Shifts_Per_Month'].values / 20.0, 0.0, 1.0)
fatigue_norm = np.clip((X['physical_fatigue'].values - 1.0) / 4.0, 0.0, 1.0)
mood_def_norm = np.clip((5.0 - X['mood_score'].values) / 4.0, 0.0, 1.0)

z = (
    0.25 * duty_norm +
    0.20 * sleep_debt_norm +
    0.15 * consec_norm +
    0.10 * night_norm +
    0.15 * fatigue_norm +
    0.15 * mood_def_norm
)
z = np.clip(z, 0.0, 1.0)

s0_x = 10.0 + (16.0 * z)  # [10.0, 26.0]
s1_x = 44.0 + (16.0 * z)  # [44.0, 60.0]
s2_x = 74.0 + (24.0 * z)  # [74.0, 98.0]

scores_m2 = (s0_x * p_low + s1_x * p_med + s2_x * p_high)

# Method 3: Ordinal Cumulative Probability of Elevated Risk
# P(Elevated) = P(Med) + P(High), P(Severe) = P(High)
scores_m3 = (p_med + p_high) * 100.0

methods = {
    'M0: Current V3 (0/50/100)': scores_m0,
    'M1: Centroid Expected Severity (18/52/85)': scores_m1,
    'M2: Continuous Ordinal Severity (Modulated z)': scores_m2,
    'M3: Cumulative Probability P(>=Med)*100': scores_m3
}

print(f"{'Method':<42} | {'Min':<5} | {'P5':<5} | {'P50':<5} | {'Mean':<5} | {'P95':<5} | {'Max':<5} | {'Std':<5}")
print("-" * 90)
for name, s in methods.items():
    print(f"{name:<42} | {np.min(s):<5.1f} | {np.percentile(s, 5):<5.1f} | {np.median(s):<5.1f} | {np.mean(s):<5.1f} | {np.percentile(s, 95):<5.1f} | {np.max(s):<5.1f} | {np.std(s):<5.1f}")

# Check class breakdown for Method 2
print("\n=== METHOD 2 CLASS BREAKDOWN ===")
for cls_name, cls_val in [('Low', 0), ('Medium', 1), ('High', 2)]:
    mask = (y_int == cls_val)
    sub = scores_m2[mask]
    print(f"Class {cls_name:<6} (N={np.sum(mask)}): Min={np.min(sub):.1f}, P10={np.percentile(sub, 10):.1f}, Median={np.median(sub):.1f}, Mean={np.mean(sub):.1f}, P90={np.percentile(sub, 90):.1f}, Max={np.max(sub):.1f}, Std={np.std(sub):.1f}")
