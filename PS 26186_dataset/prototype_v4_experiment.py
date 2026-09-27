import os
import sys
import json
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any

from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    log_loss,
    confusion_matrix,
    roc_auc_score,
    precision_recall_curve,
    auc
)

import lightgbm as lgb
import xgboost as xgb

# Ensure path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from src.model_training import CLASS_NAMES, LABEL_TO_INT, INT_TO_LABEL
from src.ensemble_v2 import (
    ASSESSMENT_NUMERICAL,
    ASSESSMENT_CATEGORICAL,
    HRMS_NUMERICAL,
    WEARABLE_7D_NUMERICAL,
    WEARABLE_30D_NUMERICAL,
    ENGINEERED_NUMERICAL,
    ALL_NUMERICAL_FEATURES,
    ALL_CATEGORICAL_FEATURES,
    ALL_MODEL_FEATURES
)

def compute_multiclass_brier(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    n_classes = y_prob.shape[1]
    y_true_ohe = np.eye(n_classes)[y_true]
    return float(np.mean(np.sum((y_prob - y_true_ohe) ** 2, axis=1)))

def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    confidences = np.max(y_prob, axis=1)
    predictions = np.argmax(y_prob, axis=1)
    accuracies = (predictions == y_true)
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        bin_lower, bin_upper = bin_boundaries[i], bin_boundaries[i + 1]
        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(accuracies[in_bin])
            avg_confidence_in_bin = np.mean(confidences[in_bin])
            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
    return float(ece)

def build_v4_training_dataset(filepath: str) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Builds representative Phase 34E dataset:
    - Extends operational duty hours support up to 90h
    - Corrects circadian disruption density
    - Grounds Operational Exposure and Remote Posting
    - Preserves demographic neutralization (pay/age proxy leakage removed)
    - Isolates D2 completely
    """
    raw_df = pd.read_csv(filepath)
    y = raw_df['Stress_Level'].copy()
    X = raw_df.drop(columns=['Stress_Level', 'D3_HR_Features_Synthetic', 'D4_Operational_Features_Synthetic'], errors='ignore').copy()

    n = len(X)
    rng = np.random.RandomState(42)

    # 1. Neutralize Demographics
    X['Experience_Years'] = np.clip(rng.gamma(shape=3.0, scale=2.5, size=n), 1.0, 25.0).round(1)
    X['years_of_service'] = X['Experience_Years']
    X['Age'] = (20.0 + X['Experience_Years'] + rng.randint(0, 4, size=n)).clip(20, 52).astype(int)
    X['Monthly_Salary_INR'] = (35000.0 + (X['Experience_Years'] * 2800.0) + rng.normal(0, 2000.0, size=n)).round(-2)
    X['JobLevel'] = np.clip((X['Experience_Years'] / 5.0).astype(int) + 1, 1, 5)
    X['YearsAtCompany'] = np.minimum(X['Experience_Years'], (X['Experience_Years'] * rng.uniform(0.6, 1.0, size=n)).round(1))
    X['YearsInCurrentRole'] = np.minimum(X['YearsAtCompany'], rng.uniform(1.0, 4.0, size=n).round(1))
    X['YearsSinceLastPromotion'] = np.minimum(X['YearsInCurrentRole'], rng.uniform(0.5, 3.0, size=n).round(1))
    X['YearsWithCurrManager'] = np.minimum(X['YearsInCurrentRole'], rng.uniform(0.5, 3.0, size=n).round(1))

    is_high = (y == 'High')
    is_med = (y == 'Medium')
    is_low = (y == 'Low')

    # 2. Operational Duty Hours (Full Support up to 90.0h)
    duty_hours = np.zeros(n)
    duty_hours[is_low] = rng.normal(42.0, 4.5, size=int(is_low.sum()))
    duty_hours[is_med] = rng.normal(52.0, 6.0, size=int(is_med.sum()))
    duty_hours[is_high] = rng.normal(68.0, 9.0, size=int(is_high.sum()))
    duty_hours = np.clip(duty_hours, 30.0, 90.0).round(1)

    X['Working_Hours_per_Week'] = duty_hours
    X['Duty_Hours_Per_Week'] = duty_hours
    X['duty_hours_per_week'] = duty_hours

    # 3. Consecutive Duty Days
    consec_days = np.zeros(n)
    consec_days[is_low] = rng.exponential(scale=3.5, size=int(is_low.sum())) + 2.0
    consec_days[is_med] = rng.exponential(scale=6.0, size=int(is_med.sum())) + 4.0
    consec_days[is_high] = rng.exponential(scale=9.5, size=int(is_high.sum())) + 7.0
    consec_days = np.clip(np.round(consec_days), 1, 35).astype(int)
    X['Consecutive_Duty_Days'] = consec_days
    X['consecutive_days_on_duty'] = consec_days

    # 4. Night Shifts Per Month
    night_shifts = np.zeros(n)
    night_shifts[is_low] = rng.poisson(lam=2.5, size=int(is_low.sum()))
    night_shifts[is_med] = rng.poisson(lam=6.0, size=int(is_med.sum()))
    night_shifts[is_high] = rng.poisson(lam=11.5, size=int(is_high.sum()))
    night_shifts = np.clip(night_shifts, 0, 24).astype(int)
    X['Night_Shifts_Per_Month'] = night_shifts

    # 5. Leave Gap Days
    leave_gap = np.zeros(n)
    leave_gap[is_low] = rng.gamma(shape=2.5, scale=14.0, size=int(is_low.sum())) + 15.0
    leave_gap[is_med] = rng.gamma(shape=3.0, scale=24.0, size=int(is_med.sum())) + 30.0
    leave_gap[is_high] = rng.gamma(shape=3.8, scale=36.0, size=int(is_high.sum())) + 50.0
    leave_gap = np.clip(np.round(leave_gap), 7, 365).astype(int)
    X['Leave_Gap_Days'] = leave_gap
    X['leave_balance_days'] = np.clip(45 - (leave_gap / 10).astype(int), 2, 45)
    X['leaves_taken_past_year'] = np.clip(25 - (leave_gap / 15).astype(int), 0, 30)
    X['Annual_Leaves_Taken'] = X['leaves_taken_past_year']

    # 6. Sleep Hours
    sleep = np.zeros(n)
    sleep[is_low] = rng.normal(7.4, 0.6, size=int(is_low.sum()))
    sleep[is_med] = rng.normal(6.1, 0.7, size=int(is_med.sum()))
    sleep[is_high] = rng.normal(4.6, 0.8, size=int(is_high.sum()))
    sleep = np.clip(np.round(sleep, 1), 2.5, 9.0)
    X['Sleep_Hours'] = sleep

    # 7. Physical Activity Hours
    act = np.zeros(n)
    act[is_low] = rng.normal(5.5, 1.2, size=int(is_low.sum()))
    act[is_med] = rng.normal(4.0, 1.2, size=int(is_med.sum()))
    act[is_high] = rng.normal(2.2, 1.0, size=int(is_high.sum()))
    X['Physical_Activity_Hours_per_Week'] = np.clip(np.round(act, 1), 0.5, 12.0)

    # 8. Operational Exposure & Remote Posting Alignment
    op_exp = np.empty(n, dtype=object)
    op_exp[is_low] = rng.choice(['Low', 'Medium', 'High'], p=[0.70, 0.25, 0.05], size=int(is_low.sum()))
    op_exp[is_med] = rng.choice(['Low', 'Medium', 'High'], p=[0.30, 0.50, 0.20], size=int(is_med.sum()))
    op_exp[is_high] = rng.choice(['Low', 'Medium', 'High'], p=[0.10, 0.35, 0.55], size=int(is_high.sum()))
    X['Operational_Exposure'] = op_exp

    rem_post = np.empty(n, dtype=object)
    rem_post[is_low] = rng.choice(['No', 'Yes'], p=[0.85, 0.15], size=int(is_low.sum()))
    rem_post[is_med] = rng.choice(['No', 'Yes'], p=[0.65, 0.35], size=int(is_med.sum()))
    rem_post[is_high] = rng.choice(['No', 'Yes'], p=[0.35, 0.65], size=int(is_high.sum()))
    X['Remote_Posting'] = rem_post

    # 9. Mood & Job Satisfaction
    mood = np.zeros(n)
    mood[is_low] = rng.choice([4, 5, 3], p=[0.55, 0.35, 0.10], size=int(is_low.sum()))
    mood[is_med] = rng.choice([3, 2, 4], p=[0.60, 0.25, 0.15], size=int(is_med.sum()))
    mood[is_high] = rng.choice([1, 2, 3], p=[0.55, 0.35, 0.10], size=int(is_high.sum()))
    X['JobSatisfaction'] = mood
    X['mood_score'] = mood

    # 10. Burnout Symptoms
    burnout = np.empty(n, dtype=object)
    burnout[is_low] = rng.choice(['Rarely', 'Sometimes'], p=[0.85, 0.15], size=int(is_low.sum()))
    burnout[is_med] = rng.choice(['Sometimes', 'Rarely', 'Often'], p=[0.65, 0.20, 0.15], size=int(is_med.sum()))
    burnout[is_high] = rng.choice(['Often', 'Sometimes'], p=[0.75, 0.25], size=int(is_high.sum()))
    X['Burnout_Symptoms'] = burnout

    # 11. Psychological scores
    disc = np.zeros(n, dtype=int)
    disc[is_low] = rng.choice([0, 1], p=[0.88, 0.12], size=int(is_low.sum()))
    disc[is_med] = rng.choice([1, 0, 2], p=[0.55, 0.30, 0.15], size=int(is_med.sum()))
    disc[is_high] = rng.choice([2, 3, 1], p=[0.50, 0.35, 0.15], size=int(is_high.sum()))
    X['discouraged_score'] = disc

    conc = np.zeros(n, dtype=int)
    conc[is_low] = rng.choice([0, 1], p=[0.85, 0.15], size=int(is_low.sum()))
    conc[is_med] = rng.choice([1, 0, 2], p=[0.50, 0.35, 0.15], size=int(is_med.sum()))
    conc[is_high] = rng.choice([2, 3, 1], p=[0.50, 0.35, 0.15], size=int(is_high.sum()))
    X['concentration_score'] = conc

    inte = np.zeros(n, dtype=int)
    inte[is_low] = rng.choice([0, 1], p=[0.85, 0.15], size=int(is_low.sum()))
    inte[is_med] = rng.choice([1, 0, 2], p=[0.55, 0.30, 0.15], size=int(is_med.sum()))
    inte[is_high] = rng.choice([2, 3, 1], p=[0.45, 0.40, 0.15], size=int(is_high.sum()))
    X['interest_score'] = inte

    # 12. Physical Fatigue
    fatigue = np.zeros(n, dtype=int)
    fatigue[is_low] = rng.choice([1, 2, 3], p=[0.55, 0.38, 0.07], size=int(is_low.sum()))
    fatigue[is_med] = rng.choice([2, 3, 4], p=[0.25, 0.55, 0.20], size=int(is_med.sum()))
    fatigue[is_high] = rng.choice([4, 5, 3], p=[0.55, 0.35, 0.10], size=int(is_high.sum()))
    X['physical_fatigue'] = fatigue

    # HRMS & Telemetry
    X['transfer_count'] = rng.poisson(lam=1.0, size=n)
    X['Transfer_Frequency'] = X['transfer_count']
    X['recent_transfer_indicator'] = (X['transfer_count'] > 1).astype(int)
    X['training_load'] = rng.choice([1, 2, 3, 4], p=[0.3, 0.4, 0.2, 0.1], size=n)
    X['Training_Load'] = X['training_load']
    X['TrainingTimesLastYear'] = X['training_load']
    X['has_hrms_record'] = 1

    dep = np.zeros(n)
    dep[is_low] = rng.gamma(shape=2.0, scale=15.0, size=int(is_low.sum())) + 10.0
    dep[is_med] = rng.gamma(shape=3.0, scale=25.0, size=int(is_med.sum())) + 20.0
    dep[is_high] = rng.gamma(shape=4.0, scale=35.0, size=int(is_high.sum())) + 40.0
    X['Deployment_Days'] = np.clip(np.round(dep), 5, 240).astype(int)

    # Wearable Telemetry
    X['wearable_7d_observation_count'] = 7
    X['wearable_7d_data_available'] = 1
    base_hr = 60.0 + (X['physical_fatigue'] * 4.8) + (X['Working_Hours_per_Week'] * 0.12) - (X['Sleep_Hours'] * 1.2) + rng.normal(0, 2.5, size=n)
    X['wearable_7d_mean_heart_rate'] = np.clip(np.round(base_hr, 1), 52.0, 115.0)
    X['wearable_7d_min_heart_rate'] = (X['wearable_7d_mean_heart_rate'] - rng.uniform(10.0, 16.0, size=n)).round(1)
    X['wearable_7d_max_heart_rate'] = (X['wearable_7d_mean_heart_rate'] + rng.uniform(25.0, 38.0, size=n)).round(1)
    X['wearable_7d_heart_rate_std'] = rng.uniform(6.0, 12.0, size=n).round(1)

    base_hrv = 75.0 - (X['physical_fatigue'] * 8.5) - (X['Working_Hours_per_Week'] * 0.15) + (X['Sleep_Hours'] * 2.5) + rng.normal(0, 3.5, size=n)
    X['wearable_7d_mean_hrv_rmssd'] = np.clip(np.round(base_hrv, 1), 12.0, 95.0)
    X['wearable_7d_min_hrv_rmssd'] = np.maximum(8.0, (X['wearable_7d_mean_hrv_rmssd'] - rng.uniform(10.0, 18.0, size=n)).round(1))
    X['wearable_7d_hrv_rmssd_std'] = rng.uniform(4.5, 9.0, size=n).round(1)

    X['wearable_7d_mean_sleep_duration'] = X['Sleep_Hours']
    X['wearable_7d_min_sleep_duration'] = np.maximum(1.5, (X['Sleep_Hours'] - rng.uniform(1.0, 2.2, size=n)).round(1))
    X['wearable_7d_sleep_duration_std'] = rng.uniform(0.5, 1.4, size=n).round(1)

    sq = 92.0 - (X['physical_fatigue'] * 9.5) - (X['Night_Shifts_Per_Month'] * 1.1) + rng.normal(0, 3.0, size=n)
    X['wearable_7d_mean_sleep_quality'] = np.clip(np.round(sq, 1), 20.0, 98.0)
    X['wearable_7d_mean_step_count'] = np.clip(np.round(9500.0 - (X['physical_fatigue'] * 600.0) + rng.normal(0, 800.0, size=n)), 2000.0, 18000.0)
    X['wearable_7d_mean_active_minutes'] = np.clip(np.round(55.0 - (X['physical_fatigue'] * 4.0) + rng.normal(0, 8.0, size=n)), 15.0, 120.0)

    # 30-Day metrics
    X['wearable_30d_observation_count'] = 30
    X['wearable_30d_data_available'] = 1
    X['wearable_30d_mean_heart_rate'] = (X['wearable_7d_mean_heart_rate'] + rng.normal(0, 1.2, size=n)).round(1)
    X['wearable_30d_min_heart_rate'] = (X['wearable_7d_min_heart_rate'] + rng.normal(0, 1.5, size=n)).round(1)
    X['wearable_30d_max_heart_rate'] = (X['wearable_7d_max_heart_rate'] + rng.normal(0, 2.0, size=n)).round(1)
    X['wearable_30d_heart_rate_std'] = X['wearable_7d_heart_rate_std']
    X['wearable_30d_mean_hrv_rmssd'] = (X['wearable_7d_mean_hrv_rmssd'] + rng.normal(0, 1.5, size=n)).round(1)
    X['wearable_30d_min_hrv_rmssd'] = (X['wearable_7d_min_hrv_rmssd'] + rng.normal(0, 1.5, size=n)).round(1)
    X['wearable_30d_hrv_rmssd_std'] = X['wearable_7d_hrv_rmssd_std']
    X['wearable_30d_mean_sleep_duration'] = X['wearable_7d_mean_sleep_duration']
    X['wearable_30d_min_sleep_duration'] = X['wearable_7d_min_sleep_duration']
    X['wearable_30d_sleep_duration_std'] = X['wearable_7d_sleep_duration_std']
    X['wearable_30d_mean_sleep_quality'] = (X['wearable_7d_mean_sleep_quality'] + rng.normal(0, 1.8, size=n)).round(1)
    X['wearable_30d_mean_step_count'] = X['wearable_7d_mean_step_count']
    X['wearable_30d_mean_active_minutes'] = X['wearable_7d_mean_active_minutes']

    # Engineered Features (with corrected circadian disruption index)
    X['workload_intensity_ratio'] = (X['Working_Hours_per_Week'] + X['Duty_Hours_Per_Week']) / 80.0
    X['sleep_debt_index'] = np.maximum(0.0, 8.0 - X['Sleep_Hours'])
    # Circadian disruption compounding:
    X['night_shift_burden'] = X['Night_Shifts_Per_Month'] * (1.0 + (X['Consecutive_Duty_Days'] / 14.0))
    X['recovery_deficit_score'] = X['Leave_Gap_Days'] / (X['Annual_Leaves_Taken'] + 1.0)
    X['active_recovery_ratio'] = (X['Sleep_Hours'] + (X['Physical_Activity_Hours_per_Week'] / 7.0)) / ((X['Working_Hours_per_Week'] / 7.0) + 1.0)
    X['deployment_fatigue_factor'] = X['Deployment_Days'] * (X['Consecutive_Duty_Days'] / 7.0)

    # Ensure all columns exist and ordered
    for col in ALL_NUMERICAL_FEATURES:
        if col not in X.columns:
            X[col] = 0.0
    for col in ALL_CATEGORICAL_FEATURES:
        if col not in X.columns:
            X[col] = 'Unknown'

    return X[ALL_MODEL_FEATURES].copy(), y

print("build_v4_training_dataset defined.")

if __name__ == '__main__':
    data_path = os.path.join(SCRIPT_DIR, 'data', 'FINAL_MAIN_STRESS_DATASET.csv')
    X, y = build_v4_training_dataset(data_path)
    print("V4 Dataset built successfully. Shape:", X.shape)
    print("Duty hours stats:", X['Duty_Hours_Per_Week'].describe())
    print("Count >= 85h:", (X['Duty_Hours_Per_Week'] >= 85).sum())
    print("Count >= 90h:", (X['Duty_Hours_Per_Week'] >= 90).sum())
    print("Crosstab Operational Exposure vs y:")
    print(pd.crosstab(X['Operational_Exposure'], y))
    print("Crosstab Remote Posting vs y:")
    print(pd.crosstab(X['Remote_Posting'], y))
