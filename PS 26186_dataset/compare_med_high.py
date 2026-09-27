import os
import sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from train_phase34e_ensemble import build_v4_training_dataset

X, y = build_v4_training_dataset('data/FINAL_MAIN_STRESS_DATASET.csv')
X['y'] = y

med_samples = X[y == 'Medium']
high_samples = X[y == 'High']

print('Comparing Medium vs High in training dataset:')
num_cols = [c for c in X.select_dtypes(include=['float64', 'int64']).columns if c != 'y']
diffs = []
for c in num_cols:
    m_med = med_samples[c].mean()
    m_high = high_samples[c].mean()
    diffs.append((c, m_med, m_high, m_high - m_med))

diffs.sort(key=lambda x: abs(x[3]), reverse=True)
print(f"{'Feature':<35} | {'Medium Mean':<12} | {'High Mean':<12} | {'Diff (High - Med)':<15}")
print('-' * 80)
for c, m_m, m_h, d in diffs[:30]:
    print(f"{c:<35} | {m_m:<12.2f} | {m_h:<12.2f} | {d:<15.2f}")

print("\nCategorical distributions Medium vs High:")
cat_cols = ['Burnout_Symptoms', 'Operational_Exposure', 'Remote_Posting', 'Department', 'Job_Role']
for c in cat_cols:
    if c in X.columns:
        print(f"\n--- {c} ---")
        ct = pd.crosstab(X[c], y, normalize='columns')
        print(ct[['Medium', 'High']])
