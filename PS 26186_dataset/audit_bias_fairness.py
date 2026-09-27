import os
import sys
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, log_loss
import joblib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from train_phase34e_ensemble import build_v4_training_dataset, compute_multiclass_brier, compute_ece

data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'FINAL_MAIN_STRESS_DATASET.csv')
X, y = build_v4_training_dataset(data_path)
y_encoded = y.map({'Low': 0, 'Medium': 1, 'High': 2}).values

v4_m = joblib.load('models/stress_risk_ensemble_v4.pkl')
prep = v4_m.preprocessor
X_proc = prep.transform(v4_m._prepare_input(X))

base_preds = [v4_m.base_models[m].predict_proba(X_proc) for m in ['LightGBM', 'XGBoost', 'LogisticRegression']]
Z = np.hstack(base_preds)
cal_probs = v4_m.calibrator.predict_proba(Z)
y_preds = np.argmax(cal_probs, axis=1)

# Centroid scores
C_LOW, C_MED, C_HIGH = 18.0, 52.0, 86.0
risk_scores = C_LOW * cal_probs[:, 0] + C_MED * cal_probs[:, 1] + C_HIGH * cal_probs[:, 2]

df_eval = X.copy()
df_eval['y_true'] = y_encoded
df_eval['y_pred'] = y_preds
df_eval['risk_score'] = risk_scores
df_eval['p_low'] = cal_probs[:, 0]
df_eval['p_med'] = cal_probs[:, 1]
df_eval['p_high'] = cal_probs[:, 2]

print("=" * 95)
print("SECTION 15: COMPREHENSIVE BIAS & FAIRNESS SUBGROUP AUDIT")
print("=" * 95)

def audit_subgroups(col_name, bins=None, labels=None):
    print(f"\n--- SUBGROUP AUDIT: {col_name} ---")
    if bins is not None:
        group_col = pd.cut(df_eval[col_name], bins=bins, labels=labels)
    else:
        group_col = df_eval[col_name]
        
    results = []
    for g in group_col.unique():
        if pd.isna(g): continue
        mask = (group_col == g).values
        n = np.sum(mask)
        if n < 20: continue
        
        y_t = y_encoded[mask]
        y_p = y_preds[mask]
        p_sub = cal_probs[mask]
        
        acc = accuracy_score(y_t, y_p)
        f1 = f1_score(y_t, y_p, average='macro', zero_division=0)
        brier = compute_multiclass_brier(y_t, p_sub)
        ece = compute_ece(y_t, p_sub)
        mean_score = np.mean(risk_scores[mask])
        pct_high = np.mean(y_p == 2) * 100
        
        results.append({
            'Subgroup': str(g),
            'N': n,
            'Mean Risk': mean_score,
            '% High Pred': pct_high,
            'Accuracy': acc,
            'Macro F1': f1,
            'Brier': brier,
            'ECE': ece
        })
        
    df_res = pd.DataFrame(results).sort_values('N', ascending=False)
    print(df_res.to_string(index=False))

# 1. Gender
audit_subgroups('Gender')

# 2. Age Groups
audit_subgroups('Age', bins=[18, 25, 35, 45, 60], labels=['<25', '25-35', '35-45', '45+'])

# 3. Department
audit_subgroups('Department')

# 4. Job Role
audit_subgroups('Job_Role')
