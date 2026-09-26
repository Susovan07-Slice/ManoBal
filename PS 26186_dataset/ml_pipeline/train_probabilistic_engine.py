import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    f1_score,
    balanced_accuracy_score,
    log_loss,
    brier_score_loss,
    confusion_matrix,
    classification_report
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
import lightgbm as lgb

# Ensure paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, DATASET_DIR)

from src.feature_engineering import engineer_features

def compute_multiclass_brier(y_true, y_prob):
    """Computes multi-class Brier score = 1/N * sum((y_ik - p_ik)^2)."""
    n_classes = y_prob.shape[1]
    y_true_ohe = np.eye(n_classes)[y_true]
    return float(np.mean(np.sum((y_prob - y_true_ohe) ** 2, axis=1)))

def compute_ece(y_true, y_prob, n_bins=10):
    """Expected Calibration Error."""
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

def build_feature_preprocessor(X):
    num_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    cat_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()

    num_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    cat_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    preprocessor = ColumnTransformer([
        ('num', num_pipe, num_cols),
        ('cat', cat_pipe, cat_cols)
    ], remainder='drop')
    return preprocessor, num_cols, cat_cols

def evaluate_models():
    data_path = os.path.join(DATASET_DIR, 'data', 'FINAL_MAIN_STRESS_DATASET.csv')
    if not os.path.exists(data_path):
        data_path = os.path.join(DATASET_DIR, 'final_dataset.csv')
    
    print(f"Loading data from: {data_path}")
    raw_df = pd.read_csv(data_path)
    
    # Feature engineering without target
    target_col = 'Stress_Level'
    y_raw = raw_df[target_col]
    X_raw = raw_df.drop(columns=[target_col])
    
    # Add continuous engineered features
    X_feat = engineer_features(X_raw)
    
    # Label encoding: 0 = Low, 1 = Medium, 2 = High (Strict Ordinal Order)
    label_map = {'Low': 0, 'Medium': 1, 'High': 2}
    inv_label_map = {0: 'Low', 1: 'Medium', 2: 'High'}
    y = y_raw.map(label_map).values
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    models = {
        'A_Standard_LightGBM': {
            'type': 'lgbm',
            'monotonic': False,
            'calibrated': False
        },
        'B_Monotonic_LightGBM': {
            'type': 'lgbm',
            'monotonic': True,
            'calibrated': False
        },
        'C_Calibrated_LightGBM': {
            'type': 'lgbm',
            'monotonic': False,
            'calibrated': True
        },
        'D_Calibrated_Monotonic_LightGBM': {
            'type': 'lgbm',
            'monotonic': True,
            'calibrated': True
        }
    }
    
    results = {}
    
    for model_name, cfg in models.items():
        print(f"\n--- Evaluating {model_name} (5-Fold CV) ---")
        oof_probs = np.zeros((len(X_feat), 3))
        oof_preds = np.zeros(len(X_feat), dtype=int)
        
        for fold, (train_idx, val_idx) in enumerate(skf.split(X_feat, y)):
            X_tr, X_val = X_feat.iloc[train_idx], X_feat.iloc[val_idx]
            y_tr, y_val = y[train_idx], y[val_idx]
            
            prep, num_cols, cat_cols = build_feature_preprocessor(X_tr)
            X_tr_trans = prep.fit_transform(X_tr)
            X_val_trans = prep.transform(X_val)
            
            # Setup Monotonic constraints if requested
            feature_names = prep.get_feature_names_out()
            monotone_constraints = []
            if cfg['monotonic']:
                for fn in feature_names:
                    if any(fn.startswith(f"num__{k}") for k in [
                        'Duty_Hours_Per_Week', 'Working_Hours_per_Week', 'workload_intensity_ratio',
                        'Night_Shifts_Per_Month', 'night_shift_burden', 'Consecutive_Duty_Days',
                        'Leave_Gap_Days', 'recovery_deficit_score', 'sleep_debt_index', 'deployment_fatigue_factor'
                    ]):
                        monotone_constraints.append(1)
                    elif any(fn.startswith(f"num__{k}") for k in [
                        'Sleep_Hours', 'Physical_Activity_Hours_per_Week', 'JobSatisfaction',
                        'WorkLifeBalance', 'active_recovery_ratio'
                    ]):
                        monotone_constraints.append(-1)
                    else:
                        monotone_constraints.append(0)
            else:
                monotone_constraints = None
                
            base_clf = lgb.LGBMClassifier(
                n_estimators=180,
                learning_rate=0.08,
                max_depth=4,
                num_leaves=15,
                min_child_samples=20,
                subsample=0.8,
                colsample_bytree=0.9,
                monotone_constraints=monotone_constraints,
                random_state=42,
                verbose=-1
            )
            
            if cfg['calibrated']:
                # Internal 3-fold calibration on train split to avoid test leakage
                cal_clf = CalibratedClassifierCV(estimator=base_clf, method='sigmoid', cv=3)
                cal_clf.fit(X_tr_trans, y_tr)
                val_probs = cal_clf.predict_proba(X_val_trans)
            else:
                base_clf.fit(X_tr_trans, y_tr)
                val_probs = base_clf.predict_proba(X_val_trans)
                
            oof_probs[val_idx] = val_probs
            oof_preds[val_idx] = np.argmax(val_probs, axis=1)
            
        macro_f1 = f1_score(y, oof_preds, average='macro')
        bal_acc = balanced_accuracy_score(y, oof_preds)
        loss = log_loss(y, oof_probs)
        brier = compute_multiclass_brier(y, oof_probs)
        ece = compute_ece(y, oof_probs)
        
        results[model_name] = {
            'macro_f1': round(macro_f1, 4),
            'balanced_accuracy': round(bal_acc, 4),
            'log_loss': round(loss, 4),
            'brier_score': round(brier, 4),
            'expected_calibration_error': round(ece, 4)
        }
        print(f"Results for {model_name}:")
        print(f"  Macro F1: {macro_f1:.4f} | Balanced Acc: {bal_acc:.4f}")
        print(f"  Log Loss: {loss:.4f} | Brier: {brier:.4f} | ECE: {ece:.4f}")
        
    print("\n=== SUMMARY COMPARISON TABLE ===")
    print(f"{'Model':<35} {'Macro F1':<10} {'Bal Acc':<10} {'Log Loss':<10} {'Brier':<10} {'ECE':<10}")
    for name, m in results.items():
        print(f"{name:<35} {m['macro_f1']:<10.4f} {m['balanced_accuracy']:<10.4f} {m['log_loss']:<10.4f} {m['brier_score']:<10.4f} {m['expected_calibration_error']:<10.4f}")

    return results

if __name__ == '__main__':
    evaluate_models()
