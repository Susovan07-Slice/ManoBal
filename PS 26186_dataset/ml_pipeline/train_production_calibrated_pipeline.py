import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    log_loss,
    confusion_matrix,
    classification_report
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer
from sklearn.impute import SimpleImputer
import lightgbm as lgb

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, DATASET_DIR)

from src.feature_engineering import engineer_features
from src.tuning import CompleteStressPredictor
from src.model_training import CLASS_NAMES, LABEL_TO_INT, INT_TO_LABEL

def compute_multiclass_brier(y_true, y_prob):
    n_classes = y_prob.shape[1]
    y_true_ohe = np.eye(n_classes)[y_true]
    return float(np.mean(np.sum((y_prob - y_true_ohe) ** 2, axis=1)))

def compute_ece(y_true, y_prob, n_bins=10):
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

def build_production_pipeline(X_train):
    num_cols = X_train.select_dtypes(include=['int64', 'float64']).columns.tolist()
    cat_cols = X_train.select_dtypes(include=['object', 'category']).columns.tolist()

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

    # Fit preprocessor to get transformed feature names for monotonic constraints
    preprocessor.fit(X_train)
    feature_names = preprocessor.get_feature_names_out()

    monotone_constraints = []
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

    base_lgbm = lgb.LGBMClassifier(
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

    # 5-fold internal calibration with sigmoid (Platt scaling)
    calibrated_clf = CalibratedClassifierCV(estimator=base_lgbm, method='sigmoid', cv=5)

    full_pipeline = Pipeline([
        ('feature_engineering', FunctionTransformer(engineer_features, validate=False)),
        ('preprocessor', preprocessor),
        ('classifier', calibrated_clf)
    ])

    return full_pipeline

def train_and_save_pipeline():
    data_path = os.path.join(DATASET_DIR, 'data', 'FINAL_MAIN_STRESS_DATASET.csv')
    print(f"Loading primary dataset from: {data_path}")
    raw_df = pd.read_csv(data_path)

    target_col = 'Stress_Level'
    y_raw = raw_df[target_col]
    cols_to_drop = [target_col, 'D3_HR_Features_Synthetic', 'D4_Operational_Features_Synthetic']
    X_raw = raw_df.drop(columns=[c for c in cols_to_drop if c in raw_df.columns])

    label_map = {'Low': 0, 'Medium': 1, 'High': 2}
    y = y_raw.map(label_map).values

    print("Fitting production calibrated pipeline with cross-validated probability calibration...")
    # First apply feature engineering to inspect columns for preprocessor
    X_fe = engineer_features(X_raw)
    pipeline = build_production_pipeline(X_fe)

    # Stratified 5-Fold Evaluation of the complete pipeline
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    oof_probs = np.zeros((len(X_raw), 3))
    oof_preds = np.zeros(len(X_raw), dtype=int)

    for fold, (train_idx, val_idx) in enumerate(skf.split(X_raw, y)):
        X_tr, X_val = X_raw.iloc[train_idx], X_raw.iloc[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]

        pipe_fold = build_production_pipeline(engineer_features(X_tr))
        pipe_fold.fit(X_tr, y_tr)

        val_probs = pipe_fold.predict_proba(X_val)
        oof_probs[val_idx] = val_probs
        oof_preds[val_idx] = np.argmax(val_probs, axis=1)

    macro_f1 = float(f1_score(y, oof_preds, average='macro'))
    bal_acc = float(balanced_accuracy_score(y, oof_preds))
    acc = float(accuracy_score(y, oof_preds))
    loss = float(log_loss(y, oof_probs))
    brier = compute_multiclass_brier(y, oof_probs)
    ece = compute_ece(y, oof_probs)
    cm = confusion_matrix(y, oof_preds).tolist()

    print(f"\n--- Cross-Validation Metrics (5-Fold Out-of-Fold) ---")
    print(f"Accuracy: {acc:.4f} | Balanced Acc: {bal_acc:.4f} | Macro F1: {macro_f1:.4f}")
    print(f"Log Loss: {loss:.4f} | Brier Score: {brier:.4f} | ECE: {ece:.4f}")

    # Now fit the final pipeline on all data for production deployment
    final_pipeline = build_production_pipeline(X_fe)
    final_pipeline.fit(X_raw, y)

    best_params = {
        'n_estimators': 180,
        'learning_rate': 0.08,
        'max_depth': 4,
        'num_leaves': 15,
        'min_child_samples': 20,
        'calibration': 'sigmoid',
        'calibration_cv': 5,
        'monotonic': True
    }

    predictor = CompleteStressPredictor(
        pipeline=final_pipeline,
        model_name="Calibrated_Monotonic_LightGBM",
        best_params=best_params
    )

    models_dir = os.path.join(DATASET_DIR, 'models')
    os.makedirs(models_dir, exist_ok=True)
    out_pipeline_path = os.path.join(models_dir, 'final_stress_prediction_pipeline.pkl')
    joblib.dump(predictor, out_pipeline_path)
    print(f"\nProduction model successfully saved to: {out_pipeline_path}")

    # Evaluate external D2 dataset (without training or tuning on D2)
    d2_path = os.path.join(DATASET_DIR, 'data', 'D2_cleaned.csv')
    d2_report = {}
    if os.path.exists(d2_path):
        print(f"\nEvaluating external D2 dataset (strictly held out): {d2_path}")
        d2_df = pd.read_csv(d2_path)
        if target_col in d2_df.columns:
            y_d2 = d2_df[target_col].map(label_map).values
            valid_mask = ~np.isnan(y_d2)
            if np.sum(valid_mask) > 0:
                X_d2 = d2_df.drop(columns=[target_col]).iloc[valid_mask]
                y_d2 = y_d2[valid_mask].astype(int)

                d2_preds = predictor.predict(X_d2)
                d2_preds_int = np.array([label_map[p] for p in d2_preds])
                d2_probs = predictor.predict_proba(X_d2).values

                d2_report = {
                    'dataset': 'D2_cleaned.csv',
                    'samples': int(len(X_d2)),
                    'accuracy': float(accuracy_score(y_d2, d2_preds_int)),
                    'balanced_accuracy': float(balanced_accuracy_score(y_d2, d2_preds_int)),
                    'macro_f1': float(f1_score(y_d2, d2_preds_int, average='macro')),
                    'brier_score': compute_multiclass_brier(y_d2, d2_probs),
                    'ece': compute_ece(y_d2, d2_probs)
                }
                print(f"D2 External Validation: Macro F1: {d2_report['macro_f1']:.4f}, Bal Acc: {d2_report['balanced_accuracy']:.4f}, ECE: {d2_report['ece']:.4f}")

    eval_report = {
        'model_name': 'Calibrated_Monotonic_LightGBM',
        'pipeline_version': '2.0.0-Phase27',
        'hyperparameters': best_params,
        'cross_validation_results': {
            'accuracy': acc,
            'balanced_accuracy': bal_acc,
            'macro_f1': macro_f1,
            'log_loss': loss,
            'brier_score': brier,
            'expected_calibration_error': ece,
            'confusion_matrix': cm
        },
        'external_d2_validation': d2_report
    }

    report_path = os.path.join(models_dir, 'final_evaluation_report.json')
    with open(report_path, 'w') as f:
        json.dump(eval_report, f, indent=2)
    print(f"Evaluation report written to: {report_path}")

    return eval_report

if __name__ == '__main__':
    train_and_save_pipeline()
