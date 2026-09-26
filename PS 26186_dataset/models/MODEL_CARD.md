# Model Card: AI Personnel Stress & Welfare Monitoring System

## 1. Model Details
- **Model Architecture:** Tuned LightGBM Multi-Class Classifier (`LGBMClassifier`)
- **Pipeline Structure:** Raw Features $\rightarrow$ Domain Feature Engineering $\rightarrow$ ColumnTransformer (Median/MostFrequent Imputation + StandardScaler + OneHotEncoder) $\rightarrow$ LightGBM Estimator
- **Hyperparameters:** `max_depth=4`, `num_leaves=15`, `learning_rate=0.12`, `n_estimators=200`, `min_child_samples=20`, `subsample=0.75`, `colsample_bytree=1.0`
- **Primary Objective:** Stratify personnel into 3 operational stress tiers (`Low`, `Medium`, `High`) with safety-critical zero-false-negative priority on high-risk personnel.
- **Target Variable:** `Stress_Level` (`Low`, `Medium`, `High`)

## 2. Dataset Lineage & Separation
- **Training & Dev Dataset:** `FINAL_MAIN_STRESS_DATASET.csv` ($N = 2,000$ records, 48 features after domain engineering). Contains synthetic operational features (duty hours, night shifts, leave gaps, deployments).
- **External Validation Dataset:** `D2_cleaned.csv` ($N = 2,000$ records, 14 features). Completely held out; never used for training, feature engineering, or hyperparameter tuning.
- **Critical Data Rule:** The two datasets were never concatenated, merged, or co-trained.

## 3. Performance Summary
| Metric | Internal Held-Out Test (Full 48 Features) | D2 External Validation (10 Shared Features) |
|---|:---:|:---:|
| **Accuracy** | **0.6000** | **0.2610** |
| **Macro F1** | **0.6632** | **0.2476** |
| **Weighted F1** | **0.6000** | **0.2275** |
| **High-Stress Recall** | **1.0000 (100.0%)** | **0.6791** |
| **High-Stress Precision**| **1.0000** | **0.2078** |
| **High-Stress F1** | **1.0000** | **0.3182** |

## 4. Key Contributing Features (TreeSHAP)
1. **Sleep_Hours / Sleep Debt:** Primary restorative deficit factor associated with stress tier elevation.
2. **Duty_Hours_Per_Week & Working_Hours:** Chronic workload duration beyond physiological recovery thresholds.
3. **Consecutive_Duty_Days & Night_Shifts:** Circadian disruption density and cumulative physical fatigue.
4. **Leave_Gap_Days / Recovery Deficit:** Extended intervals between sanctioned leaves.
5. **Health_Issues & Burnout Symptoms:** Clinical self-report indicators correlating with high risk.

## 5. Known Limitations & Prototype Boundaries
- **Synthetic Augmentation:** `FINAL_MAIN_STRESS_DATASET.csv` is a prototype dataset synthetically augmented with operational features.
- **External Dataset Scope:** `D2_cleaned.csv` represents corporate/workplace stress, lacking specific military operational environments.
- **No CRPF Records:** Neither dataset represents actual, real-world CRPF personnel records. Results establish technical proof-of-concept feasibility rather than operational/clinical certification.
- **Statistical Association, Not Causation:** Model feature importance reflects statistical predictive associations, not medical or operational causation.
