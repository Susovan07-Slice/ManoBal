import os
import sys
import numpy as np
import pandas as pd
from scipy.special import expit, logit
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from train_phase34e_ensemble import build_v4_training_dataset
import joblib

data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'FINAL_MAIN_STRESS_DATASET.csv')
X, y = build_v4_training_dataset(data_path)
y_int = y.map({'Low': 0, 'Medium': 1, 'High': 2}).values

v4_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'stress_risk_ensemble_v4.pkl')
v4_model = joblib.load(v4_model_path)

# Extract out-of-fold calibrated probabilities from 5-fold CV
print("Extracting calibrated probabilities on validation data...")
prep = v4_model.preprocessor
X_proc = prep.transform(v4_model._prepare_input(X))

base_preds = []
for m_name in ['LightGBM', 'XGBoost', 'LogisticRegression']:
    base_preds.append(v4_model.base_models[m_name].predict_proba(X_proc))
Z = np.hstack(base_preds)

if v4_model.calibrator is not None:
    cal_probs = v4_model.calibrator.predict_proba(Z)
else:
    cal_probs = v4_model.meta_model.predict_proba(Z)

p_low = cal_probs[:, 0]
p_med = cal_probs[:, 1]
p_high = cal_probs[:, 2]

print("Calibrated probabilities summary:")
print(f"  P(Low)   mean={p_low.mean():.3f}, std={p_low.std():.3f}, min={p_low.min():.3f}, max={p_low.max():.3f}")
print(f"  P(Med)   mean={p_med.mean():.3f}, std={p_med.std():.3f}, min={p_med.min():.3f}, max={p_med.max():.3f}")
print(f"  P(High)  mean={p_high.mean():.3f}, std={p_high.std():.3f}, min={p_high.min():.3f}, max={p_high.max():.3f}")

# Define candidate scoring methods
# M1: Naive Expected Ordinal Risk (0, 50, 100)
s_m1 = 0.0 * p_low + 50.0 * p_med + 100.0 * p_high

# M2: Category-Centroid Ordinal Expectation (15, 50, 85)
s_m2 = 15.0 * p_low + 50.0 * p_med + 85.0 * p_high

# M3: Category-Centroid Ordinal Expectation (18, 52, 85)
s_m3 = 18.0 * p_low + 52.0 * p_med + 85.0 * p_high

# M4: Cumulative Exceedance: 100 * [0.45 * P(>=Med) + 0.55 * P(>=High)]
# = 45 * P(Med) + 100 * P(High)
p_ge_med = p_med + p_high
p_ge_high = p_high
s_m4 = 100.0 * (0.45 * p_ge_med + 0.55 * p_ge_high)

# M5: Latent Logit Ordinal Transformation
# log-odds of exceeding low: logit(p_ge_med), clipped to prevent inf
eps = 1e-4
lo_med = logit(np.clip(p_ge_med, eps, 1 - eps))
lo_high = logit(np.clip(p_ge_high, eps, 1 - eps))
latent = 0.65 * lo_med + 0.35 * lo_high
s_m5 = 100.0 * expit(latent / 2.5)

# M6: Empirical Percentile Transform of M1
sorted_m1 = np.sort(s_m1)
s_m6 = 100.0 * (np.searchsorted(sorted_m1, s_m1, side='right') / len(s_m1))

methods = {
    'M1: Naive Expected (0, 50, 100)': s_m1,
    'M2: Centroid Expected (15, 50, 85)': s_m2,
    'M3: Centroid Expected (18, 52, 85)': s_m3,
    'M4: Cumulative Exceedance (45/100)': s_m4,
    'M5: Latent Logit Logistic Transform': s_m5,
    'M6: Empirical CDF Percentile': s_m6,
}

print("\n" + "=" * 95)
print(f"{'Method':<38} | {'Min':<5} | {'P10':<5} | {'Median':<6} | {'Mean':<5} | {'P90':<5} | {'Max':<5} | {'Std':<5}")
print("=" * 95)
for name, s in methods.items():
    print(f"{name:<38} | {np.min(s):<5.1f} | {np.percentile(s, 10):<5.1f} | {np.median(s):<6.1f} | {np.mean(s):<5.1f} | {np.percentile(s, 90):<5.1f} | {np.max(s):<5.1f} | {np.std(s):<5.1f}")

# Evaluation by ground-truth class
print("\n" + "=" * 95)
print("SEPARATION AND DISCRIMINATION BY GROUND-TRUTH CLASS")
print("=" * 95)
for name, s in methods.items():
    print(f"\n--- {name} ---")
    for c_name, c_idx in [('Low', 0), ('Medium', 1), ('High', 2)]:
        sub = s[y_int == c_idx]
        print(f"  {c_name:<6} (N={len(sub)}): Min={np.min(sub):4.1f}, P10={np.percentile(sub, 10):4.1f}, Median={np.median(sub):4.1f}, Mean={np.mean(sub):4.1f}, P90={np.percentile(sub, 90):4.1f}, Max={np.max(sub):4.1f}")

# Spearman rank correlation with ground-truth ordinal y
from scipy.stats import spearmanr
print("\n" + "=" * 95)
print("ORDINAL DISCRIMINATION METRICS")
print("=" * 95)
for name, s in methods.items():
    corr, _ = spearmanr(s, y_int)
    # Measure separation: Cohen's d between Low and High, Med and Low, High and Med
    s_low = s[y_int == 0]
    s_med = s[y_int == 1]
    s_high = s[y_int == 2]
    d_low_med = (s_med.mean() - s_low.mean()) / np.sqrt((s_med.var() + s_low.var()) / 2)
    d_med_high = (s_high.mean() - s_med.mean()) / np.sqrt((s_high.var() + s_med.var()) / 2)
    d_low_high = (s_high.mean() - s_low.mean()) / np.sqrt((s_high.var() + s_low.var()) / 2)
    print(f"{name:<38} | Spearman r={corr:.4f} | d(Med-Low)={d_low_med:5.2f} | d(High-Med)={d_med_high:5.2f} | d(High-Low)={d_low_high:5.2f}")
