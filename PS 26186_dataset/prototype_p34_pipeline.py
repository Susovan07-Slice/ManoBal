import os
import sys
import json
import time
import numpy as np
import pandas as pd

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
    precision_score,
    recall_score,
    f1_score,
    log_loss,
    confusion_matrix,
    roc_auc_score,
    precision_recall_curve,
    auc
)

import lightgbm as lgb
import xgboost as xgb
import catboost as cb

# Ensure repository root is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.model_training import CLASS_NAMES, LABEL_TO_INT, INT_TO_LABEL
from src.feature_engineering import engineer_features
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

def compute_pr_auc_multiclass(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    n_classes = y_prob.shape[1]
    y_true_ohe = np.eye(n_classes)[y_true]
    pr_aucs = []
    for c in range(n_classes):
        precision, recall, _ = precision_recall_curve(y_true_ohe[:, c], y_prob[:, c])
        pr_aucs.append(auc(recall, precision))
    return float(np.mean(pr_aucs))

def prepare_clean_training_dataset(filepath: str) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepares training data WITHOUT target leakage.
    Ensures Duty_Hours_Per_Week is semantically aligned with Working_Hours_per_Week.
    Derives realistic physiological features without referencing Stress_Level.
    """
    df = pd.read_csv(filepath)
    y = df['Stress_Level'].copy()
    X = df.drop(columns=['Stress_Level', 'D3_HR_Features_Synthetic', 'D4_Operational_Features_Synthetic'], errors='ignore').copy()

    # 1. Assessment Question Derivations
    X['mood_score'] = X['JobSatisfaction'].clip(1, 5)

    burnout_str = X['Burnout_Symptoms'].astype(str).str.lower()
    mental_leave = X['Mental_Health_Leave_Taken'].astype(str).str.lower() == 'yes'
    disc = np.zeros(len(X), dtype=int)
    disc[burnout_str.str.contains('some')] = 1
    disc[burnout_str.str.contains('often')] = 2
    disc[mental_leave & (X['JobSatisfaction'] <= 2)] = 3
    X['discouraged_score'] = disc

    conc = np.zeros(len(X), dtype=int)
    conc[X['Sleep_Hours'] <= 6.0] = 1
    conc[(X['Sleep_Hours'] <= 5.0) | (X['Night_Shifts_Per_Month'] >= 8)] = 2
    conc[(X['Sleep_Hours'] <= 4.0) & (X['Night_Shifts_Per_Month'] >= 10)] = 3
    X['concentration_score'] = conc

    inte = np.zeros(len(X), dtype=int)
    inte[X['JobSatisfaction'] <= 3] = 1
    inte[X['JobSatisfaction'] <= 2] = 2
    inte[(X['WorkLifeBalance'] <= 1) & (X['JobSatisfaction'] <= 2)] = 3
    X['interest_score'] = inte

    # Align Duty_Hours_Per_Week with Working_Hours_per_Week so they don't contradict
    # In raw data Duty_Hours was random noise; align it with Working_Hours_per_Week + small operational variation
    rng = np.random.RandomState(42)
    X['Duty_Hours_Per_Week'] = X['Working_Hours_per_Week'] + rng.normal(0, 2.0, len(X))
    X['Duty_Hours_Per_Week'] = X['Duty_Hours_Per_Week'].clip(30.0, 95.0)
    X['duty_hours_per_week'] = X['Duty_Hours_Per_Week']

    # Demographics
    X['years_of_service'] = X['Experience_Years']
    X['consecutive_days_on_duty'] = X['Consecutive_Duty_Days']
    X['leaves_taken_past_year'] = X['Annual_Leaves_Taken']
    X['leave_balance_days'] = X['Leave_Gap_Days']
    X['transfer_count'] = X['Transfer_Frequency']
    X['training_load'] = X['Training_Load']
    X['recent_transfer_indicator'] = (X['Transfer_Frequency'] > 0).astype(int)
    X['has_hrms_record'] = 1

    # Physical Fatigue: Derived purely from workload, sleep deficit, exercise deficit, and duty strain
    # NO TARGET LEAKAGE (no y_num)!
    work_load = np.maximum(0.0, X['Working_Hours_per_Week'] - 40.0) / 25.0
    sleep_debt = np.maximum(0.0, 8.0 - X['Sleep_Hours']) / 3.5
    act_def = np.maximum(0.0, 6.0 - X['Physical_Activity_Hours_per_Week']) / 5.0
    duty_b = np.maximum(0.0, X['Duty_Hours_Per_Week'] - 40.0) / 25.0
    consec_b = np.maximum(0.0, X['Consecutive_Duty_Days'] - 5.0) / 10.0

    f_smooth = 1.0 + (0.9 * work_load) + (0.9 * sleep_debt) + (0.4 * act_def) + (0.5 * duty_b) + (0.5 * consec_b)
    X['physical_fatigue'] = np.clip(np.round(f_smooth), 1, 5).astype(int)

    # Wearable Physiological Baselines (derived from fatigue and sleep, without target)
    X['wearable_7d_observation_count'] = 0
    X['wearable_7d_data_available'] = 0
    X['wearable_7d_mean_heart_rate'] = np.clip(66.0 + (X['physical_fatigue'] * 4.5), 55.0, 110.0)
    X['wearable_7d_min_heart_rate'] = X['wearable_7d_mean_heart_rate'] - 12.0
    X['wearable_7d_max_heart_rate'] = X['wearable_7d_mean_heart_rate'] + 28.0
    X['wearable_7d_heart_rate_std'] = 8.5
    X['wearable_7d_mean_hrv_rmssd'] = np.clip(68.0 - (X['physical_fatigue'] * 7.5), 15.0, 85.0)
    X['wearable_7d_min_hrv_rmssd'] = np.maximum(10.0, X['wearable_7d_mean_hrv_rmssd'] - 15.0)
    X['wearable_7d_hrv_rmssd_std'] = 6.2
    X['wearable_7d_mean_sleep_duration'] = X['Sleep_Hours'].astype(float)
    X['wearable_7d_min_sleep_duration'] = np.maximum(2.0, X['Sleep_Hours'] - 1.5)
    X['wearable_7d_sleep_duration_std'] = 0.8
    X['wearable_7d_mean_sleep_quality'] = np.clip(88.0 - (X['physical_fatigue'] * 9.0), 25.0, 95.0)
    X['wearable_7d_mean_step_count'] = 7500.0
    X['wearable_7d_mean_active_minutes'] = 45.0

    X['wearable_30d_observation_count'] = 0
    X['wearable_30d_data_available'] = 0
    X['wearable_30d_mean_heart_rate'] = X['wearable_7d_mean_heart_rate']
    X['wearable_30d_min_heart_rate'] = X['wearable_7d_min_heart_rate']
    X['wearable_30d_max_heart_rate'] = X['wearable_7d_max_heart_rate']
    X['wearable_30d_heart_rate_std'] = X['wearable_7d_heart_rate_std']
    X['wearable_30d_mean_hrv_rmssd'] = X['wearable_7d_mean_hrv_rmssd']
    X['wearable_30d_min_hrv_rmssd'] = X['wearable_7d_min_hrv_rmssd']
    X['wearable_30d_hrv_rmssd_std'] = X['wearable_7d_hrv_rmssd_std']
    X['wearable_30d_mean_sleep_duration'] = X['wearable_7d_mean_sleep_duration']
    X['wearable_30d_min_sleep_duration'] = X['wearable_7d_min_sleep_duration']
    X['wearable_30d_sleep_duration_std'] = X['wearable_7d_sleep_duration_std']
    X['wearable_30d_mean_sleep_quality'] = X['wearable_7d_mean_sleep_quality']
    X['wearable_30d_mean_step_count'] = X['wearable_7d_mean_step_count']
    X['wearable_30d_mean_active_minutes'] = X['wearable_7d_mean_active_minutes']

    # 4. Feature Engineering
    X = engineer_features(X)

    for col in ALL_NUMERICAL_FEATURES:
        if col not in X.columns:
            X[col] = 0.0
    for col in ALL_CATEGORICAL_FEATURES:
        if col not in X.columns:
            X[col] = 'Unknown'

    return X[ALL_MODEL_FEATURES].copy(), y

def get_monotonic_constraints(numerical_features: List[str], categorical_features: List[str], preprocessor) -> List[int]:
    """
    Builds monotonic constraint vector matching the preprocessed feature order.
    +1: increasing feature increases risk of High stress.
    -1: increasing feature decreases risk of High stress.
     0: no monotonic constraint.
    """
    feature_names = preprocessor.get_feature_names_out()
    constraints = []

    # Features where higher value justifies higher risk:
    positive_strain = [
        'Working_Hours_per_Week', 'Duty_Hours_Per_Week', 'duty_hours_per_week',
        'Consecutive_Duty_Days', 'consecutive_days_on_duty', 'Night_Shifts_Per_Month',
        'Leave_Gap_Days', 'physical_fatigue', 'workload_intensity_ratio',
        'sleep_debt_index', 'night_shift_burden', 'recovery_deficit_score',
        'deployment_fatigue_factor', 'Deployment_Days', 'Transfer_Frequency',
        'transfer_count', 'recent_transfer_indicator', 'wearable_7d_mean_heart_rate',
        'wearable_30d_mean_heart_rate', 'discouraged_score', 'concentration_score'
    ]

    # Features where higher value justifies lower risk:
    protective_features = [
        'JobSatisfaction', 'mood_score', 'WorkLifeBalance',
        'active_recovery_ratio', 'wearable_7d_mean_hrv_rmssd',
        'wearable_30d_mean_hrv_rmssd', 'wearable_7d_mean_sleep_quality',
        'wearable_30d_mean_sleep_quality', 'Annual_Leaves_Taken',
        'leaves_taken_past_year', 'leave_balance_days'
    ]

    for fn in feature_names:
        clean = fn.replace('num__', '').replace('cat__', '')
        if any(clean == p or clean.startswith(p + '_') for p in positive_strain):
            constraints.append(1)
        elif any(clean == pr or clean.startswith(pr + '_') for pr in protective_features):
            constraints.append(-1)
        else:
            constraints.append(0)

    return constraints

print("prototype_p34_pipeline.py loaded successfully.")
