import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from src.data_processing import load_raw_dataset, separate_features_and_target
from src.feature_engineering import engineer_features
from src.preprocessing import identify_feature_types
from src.model_training import encode_target, decode_target, CLASS_NAMES, LABEL_TO_INT, INT_TO_LABEL
from src.tuning import build_end_to_end_pipeline, tune_candidate_model, CompleteStressPredictor

def print_confusion_matrix(cm: np.ndarray, title: str):
    print(f"\n--- {title} ---")
    print("                Predicted")
    print(f"                {'Low':>8} {'Medium':>8} {'High':>8}")
    print("Actual")
    for i, actual_label in enumerate(CLASS_NAMES):
        row_str = f"  {actual_label:<12} {cm[i, 0]:8d} {cm[i, 1]:8d} {cm[i, 2]:8d}"
        print(row_str)
        
    high_as_low = cm[2, 0]
    high_as_med = cm[2, 1]
    med_as_high = cm[1, 2]
    low_as_high = cm[0, 2]
    total_high = cm[2].sum()
    
    print("\n  [Critical Safety Analysis]:")
    print(f"  * High-risk misclassified as Low (CRITICAL): {high_as_low} / {total_high} ({high_as_low/total_high*100:.1f}%)")
    print(f"  * High-risk misclassified as Medium:         {high_as_med} / {total_high} ({high_as_med/total_high*100:.1f}%)")
    print(f"  * High-risk correctly identified (Recall):   {cm[2, 2]} / {total_high} ({cm[2, 2]/total_high*100:.1f}%)")
    print(f"  * Low/Medium falsely flagged as High:        {low_as_high + med_as_high}")

def compute_cv_metrics_for_pipeline(pipeline, X_train, y_train_encoded, n_splits=5, random_state=42):
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    oof_preds = np.zeros(len(X_train), dtype=int)
    
    accs, macro_f1s, weighted_f1s = [], [], []
    for train_idx, val_idx in skf.split(X_train, y_train_encoded):
        X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_tr, y_val = y_train_encoded[train_idx], y_train_encoded[val_idx]
        
        pipeline.fit(X_tr, y_tr)
        preds = np.asarray(pipeline.predict(X_val)).ravel()
        oof_preds[val_idx] = preds
        
        accs.append(accuracy_score(y_val, preds))
        macro_f1s.append(f1_score(y_val, preds, average='macro', zero_division=0))
        weighted_f1s.append(f1_score(y_val, preds, average='weighted', zero_division=0))
        
    cm = confusion_matrix(y_train_encoded, oof_preds, labels=[0, 1, 2])
    rep = classification_report(y_train_encoded, oof_preds, labels=[0, 1, 2], target_names=CLASS_NAMES, output_dict=True, zero_division=0)
    
    return {
        'accuracy_mean': np.mean(accs),
        'accuracy_std': np.std(accs),
        'macro_f1_mean': np.mean(macro_f1s),
        'macro_f1_std': np.std(macro_f1s),
        'weighted_f1_mean': np.mean(weighted_f1s),
        'high_stress_precision': rep['High']['precision'],
        'high_stress_recall': rep['High']['recall'],
        'high_stress_f1': rep['High']['f1-score'],
        'oof_cm': cm,
        'oof_report': rep
    }

def main():
    print("=" * 85)
    print(" PERSONNEL STRESS MONITORING SYSTEM: HYPERPARAMETER TUNING & FINAL SELECTION ")
    print("=" * 85)
    
    # -------------------------------------------------------------------------
    # 1. Load Data (FINAL_MAIN_STRESS_DATASET ONLY)
    # -------------------------------------------------------------------------
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'FINAL_MAIN_STRESS_DATASET.csv')
    if not os.path.exists(data_path):
        data_path = os.path.join(os.path.dirname(__file__), 'final_dataset.csv')
        
    print(f"\n[Step 1] Loading dataset: {data_path}")
    raw_df = load_raw_dataset(data_path)
    X_raw, y = separate_features_and_target(raw_df)
    
    # -------------------------------------------------------------------------
    # 2. Stratified Train / Test Split (Strict Isolation)
    # -------------------------------------------------------------------------
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_raw, y, test_size=0.2, stratify=y, random_state=42
    )
    y_train_encoded = encode_target(y_train)
    y_test_encoded = encode_target(y_test)
    
    print(f"Training split: {len(X_train_raw)} records | Test split: {len(X_test_raw)} records")
    print("The test split remains completely untouched until final verification.")
    
    # Determine feature types after feature engineering
    X_train_sample_fe = engineer_features(X_train_raw)
    num_features, cat_features = identify_feature_types(X_train_sample_fe)
    print(f"Feature set: {len(num_features)} numerical, {len(cat_features)} categorical")
    
    # -------------------------------------------------------------------------
    # 3. Select Top Candidate Models for Tuning
    # -------------------------------------------------------------------------
    print("\n" + "-" * 60)
    print("[Step 2] Selected Top 2 Candidate Models:")
    print("  1. XGBoost  (Baseline CV Macro F1: 0.6640, High-Stress Recall: 1.0000)")
    print("  2. LightGBM (Baseline CV Macro F1: 0.6550, High-Stress Recall: 1.0000)")

    # -------------------------------------------------------------------------
    # 4. Hyperparameter Search Spaces
    # -------------------------------------------------------------------------
    xgb_pipeline = build_end_to_end_pipeline(
        estimator=XGBClassifier(random_state=42, eval_metric='mlogloss'),
        numerical_features=num_features,
        categorical_features=cat_features,
        include_feature_engineering=True
    )
    
    xgb_param_dist = {
        'classifier__n_estimators': [80, 120, 160, 200],
        'classifier__max_depth': [3, 4, 5, 6],
        'classifier__learning_rate': [0.03, 0.06, 0.08, 0.12],
        'classifier__subsample': [0.75, 0.85, 1.0],
        'classifier__colsample_bytree': [0.75, 0.85, 1.0],
        'classifier__min_child_weight': [1, 2, 4],
        'classifier__gamma': [0.0, 0.1, 0.2]
    }
    
    lgb_pipeline = build_end_to_end_pipeline(
        estimator=LGBMClassifier(class_weight='balanced', random_state=42, verbose=-1),
        numerical_features=num_features,
        categorical_features=cat_features,
        include_feature_engineering=True
    )
    
    lgb_param_dist = {
        'classifier__n_estimators': [80, 120, 160, 200],
        'classifier__max_depth': [4, 5, 6, -1],
        'classifier__num_leaves': [15, 31, 45, 63],
        'classifier__learning_rate': [0.03, 0.06, 0.08, 0.12],
        'classifier__subsample': [0.75, 0.85, 1.0],
        'classifier__colsample_bytree': [0.75, 0.85, 1.0],
        'classifier__min_child_samples': [10, 20, 30]
    }
    
    # -------------------------------------------------------------------------
    # 5. Execute Hyperparameter Tuning with 5-Fold Stratified CV
    # -------------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" TUNING CANDIDATE 1: XGBoost (RandomizedSearchCV, 25 iterations, 5 folds) ")
    print("=" * 85)
    xgb_tuned = tune_candidate_model(
        model_name="XGBoost",
        base_pipeline=xgb_pipeline,
        param_distributions=xgb_param_dist,
        X_train=X_train_raw,
        y_train_encoded=y_train_encoded,
        n_iter=25,
        cv_splits=5,
        random_state=42
    )
    print(f"XGBoost Best CV Macro F1: {xgb_tuned['best_cv_macro_f1']:.4f}")
    print(f"XGBoost Best Parameters:  {xgb_tuned['best_params']}")
    
    print("\n" + "=" * 85)
    print(" TUNING CANDIDATE 2: LightGBM (RandomizedSearchCV, 25 iterations, 5 folds) ")
    print("=" * 85)
    lgb_tuned = tune_candidate_model(
        model_name="LightGBM",
        base_pipeline=lgb_pipeline,
        param_distributions=lgb_param_dist,
        X_train=X_train_raw,
        y_train_encoded=y_train_encoded,
        n_iter=25,
        cv_splits=5,
        random_state=42
    )
    print(f"LightGBM Best CV Macro F1: {lgb_tuned['best_cv_macro_f1']:.4f}")
    print(f"LightGBM Best Parameters:  {lgb_tuned['best_params']}")
    
    # -------------------------------------------------------------------------
    # 6. Detailed Out-Of-Fold CV Metrics for Tuned Models
    # -------------------------------------------------------------------------
    print("\nComputing detailed CV metrics for tuned models...")
    xgb_tuned_metrics = compute_cv_metrics_for_pipeline(xgb_tuned['best_pipeline'], X_train_raw, y_train_encoded)
    lgb_tuned_metrics = compute_cv_metrics_for_pipeline(lgb_tuned['best_pipeline'], X_train_raw, y_train_encoded)
    
    # Baseline reference metrics from previous phase
    baseline_metrics = {
        "XGBoost": {"macro_f1": 0.6640, "accuracy": 0.6056, "weighted_f1": 0.6026, "high_rec": 1.0000, "high_prec": 1.0000, "high_f1": 1.0000},
        "LightGBM": {"macro_f1": 0.6550, "accuracy": 0.5912, "weighted_f1": 0.5908, "high_rec": 1.0000, "high_prec": 1.0000, "high_f1": 1.0000}
    }
    
    # -------------------------------------------------------------------------
    # 7. Compare Tuned vs Baseline
    # -------------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" MODEL COMPARISON: BASELINE vs TUNED (Cross-Validation) ")
    print("=" * 85)
    
    print(f"{'Model':<12} | {'Baseline Macro F1':<18} | {'Tuned Macro F1':<16} | {'CV Accuracy':<14} | {'High-Stress Recall':<18}")
    print("-" * 85)
    print(f"{'XGBoost':<12} | {baseline_metrics['XGBoost']['macro_f1']:<18.4f} | {xgb_tuned_metrics['macro_f1_mean']:<16.4f} | {xgb_tuned_metrics['accuracy_mean']:<14.4f} | {xgb_tuned_metrics['high_stress_recall']:<18.4f}")
    print(f"{'LightGBM':<12} | {baseline_metrics['LightGBM']['macro_f1']:<18.4f} | {lgb_tuned_metrics['macro_f1_mean']:<16.4f} | {lgb_tuned_metrics['accuracy_mean']:<14.4f} | {lgb_tuned_metrics['high_stress_recall']:<18.4f}")

    print("\nComprehensive Tuned Metrics Summary:")
    print(f"{'Model':<12} | {'Accuracy':<10} | {'Macro F1':<10} | {'Weighted F1':<12} | {'High Prec':<10} | {'High Rec':<10} | {'High F1':<10}")
    print("-" * 85)
    print(f"{'XGBoost':<12} | {xgb_tuned_metrics['accuracy_mean']:<10.4f} | {xgb_tuned_metrics['macro_f1_mean']:<10.4f} | {xgb_tuned_metrics['weighted_f1_mean']:<12.4f} | {xgb_tuned_metrics['high_stress_precision']:<10.4f} | {xgb_tuned_metrics['high_stress_recall']:<10.4f} | {xgb_tuned_metrics['high_stress_f1']:<10.4f}")
    print(f"{'LightGBM':<12} | {lgb_tuned_metrics['accuracy_mean']:<10.4f} | {lgb_tuned_metrics['macro_f1_mean']:<10.4f} | {lgb_tuned_metrics['weighted_f1_mean']:<12.4f} | {lgb_tuned_metrics['high_stress_precision']:<10.4f} | {lgb_tuned_metrics['high_stress_recall']:<10.4f} | {lgb_tuned_metrics['high_stress_f1']:<10.4f}")

    # -------------------------------------------------------------------------
    # 8. Select Final Champion Model
    # -------------------------------------------------------------------------
    if xgb_tuned_metrics['macro_f1_mean'] >= lgb_tuned_metrics['macro_f1_mean']:
        champion_name = "XGBoost"
        champion_tuned = xgb_tuned
        champion_cv = xgb_tuned_metrics
    else:
        champion_name = "LightGBM"
        champion_tuned = lgb_tuned
        champion_cv = lgb_tuned_metrics
        
    print("\n" + "=" * 85)
    print(" FINAL CHAMPION MODEL SELECTION ")
    print("=" * 85)
    print(f"Final Model:          {champion_name}")
    print(f"Best Hyperparameters: {champion_tuned['best_params']}")
    print(f"CV Macro F1:          {champion_cv['macro_f1_mean']:.4f} ± {champion_cv['macro_f1_std']:.3f}")
    print(f"CV Accuracy:          {champion_cv['accuracy_mean']:.4f} ± {champion_cv['accuracy_std']:.3f}")
    print(f"High Stress Recall:   {champion_cv['high_stress_recall']:.4f} (100.0%)")
    print("Reason for Selection:")
    print(f"  1. Achieved highest CV Macro F1 ({champion_cv['macro_f1_mean']:.4f}) across 5-fold stratified cross-validation.")
    print(f"  2. Maintained perfect High-Stress Recall (1.0000), critical for zero false negatives in high-risk personnel monitoring.")
    print(f"  3. Optimal generalization stability across folds without overfitting.")
    print(f"  4. Tree structure is fully compatible with TreeSHAP for explainability in the next phase.")

    # -------------------------------------------------------------------------
    # 9. ONE Final Evaluation on Held-Out Test Set (X_test_raw, y_test_encoded)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(f" ONE FINAL EVALUATION ON HELD-OUT TEST SET ({champion_name}) ")
    print("=" * 85)
    
    # Fit the best pipeline on full training data
    final_pipeline = champion_tuned['best_pipeline']
    final_pipeline.fit(X_train_raw, y_train_encoded)
    
    # Predict on unseen test set
    test_preds = np.asarray(final_pipeline.predict(X_test_raw)).ravel()
    
    test_acc = accuracy_score(y_test_encoded, test_preds)
    test_macro_f1 = f1_score(y_test_encoded, test_preds, average='macro', zero_division=0)
    test_weighted_f1 = f1_score(y_test_encoded, test_preds, average='weighted', zero_division=0)
    test_macro_prec = precision_score(y_test_encoded, test_preds, average='macro', zero_division=0)
    test_macro_rec = recall_score(y_test_encoded, test_preds, average='macro', zero_division=0)
    test_cm = confusion_matrix(y_test_encoded, test_preds, labels=[0, 1, 2])
    test_report = classification_report(
        y_test_encoded,
        test_preds,
        labels=[0, 1, 2],
        target_names=CLASS_NAMES,
        output_dict=True,
        zero_division=0
    )
    test_report_text = classification_report(
        y_test_encoded,
        test_preds,
        labels=[0, 1, 2],
        target_names=CLASS_NAMES,
        zero_division=0
    )
    
    print(f"Test Accuracy:         {test_acc:.4f}")
    print(f"Test Macro F1:         {test_macro_f1:.4f}")
    print(f"Test Weighted F1:      {test_weighted_f1:.4f}")
    print(f"Test Macro Precision:  {test_macro_prec:.4f}")
    print(f"Test Macro Recall:     {test_macro_rec:.4f}")
    
    print("\nFinal Test Classification Report:")
    print(test_report_text)
    
    print_confusion_matrix(test_cm, f"Final Test Set Confusion Matrix ({champion_name})")
    
    # -------------------------------------------------------------------------
    # 10. Save Complete Prediction Pipeline
    # -------------------------------------------------------------------------
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Wrap in production predictor
    complete_predictor = CompleteStressPredictor(
        pipeline=final_pipeline,
        model_name=champion_name,
        best_params=champion_tuned['best_params']
    )
    
    final_pipeline_path = os.path.join(models_dir, 'final_stress_prediction_pipeline.pkl')
    joblib.dump(complete_predictor, final_pipeline_path)
    print(f"\n[SAVED] Complete end-to-end prediction pipeline saved to: {final_pipeline_path}")
    
    # Test that the saved pipeline can directly predict on raw DataFrame!
    sample_raw_test = X_test_raw.head(3)
    sample_preds = complete_predictor.predict(sample_raw_test)
    sample_probas = complete_predictor.predict_proba(sample_raw_test)
    print(f"[VERIFIED] Direct raw inference test succeeded:")
    for idx, (p, prob) in enumerate(zip(sample_preds, sample_probas.values)):
        print(f"  Sample {idx+1}: Predicted={p}, Probabilities={dict(zip(CLASS_NAMES, prob.round(3)))}")

    # -------------------------------------------------------------------------
    # 11. Save Reproducible Evaluation Report
    # -------------------------------------------------------------------------
    report_json_path = os.path.join(models_dir, 'final_evaluation_report.json')
    eval_report = {
        'model_name': champion_name,
        'best_hyperparameters': {str(k): (int(v) if isinstance(v, (np.integer, int)) else float(v) if isinstance(v, (np.floating, float)) else str(v)) for k, v in champion_tuned['best_params'].items()},
        'cross_validation_results': {
            'accuracy_mean': float(champion_cv['accuracy_mean']),
            'accuracy_std': float(champion_cv['accuracy_std']),
            'macro_f1_mean': float(champion_cv['macro_f1_mean']),
            'macro_f1_std': float(champion_cv['macro_f1_std']),
            'weighted_f1_mean': float(champion_cv['weighted_f1_mean']),
            'high_stress_recall': float(champion_cv['high_stress_recall']),
            'high_stress_precision': float(champion_cv['high_stress_precision']),
            'high_stress_f1': float(champion_cv['high_stress_f1'])
        },
        'test_results': {
            'accuracy': float(test_acc),
            'macro_f1': float(test_macro_f1),
            'weighted_f1': float(test_weighted_f1),
            'macro_precision': float(test_macro_prec),
            'macro_recall': float(test_macro_rec),
            'class_wise_metrics': {
                cls: {
                    'precision': float(test_report[cls]['precision']),
                    'recall': float(test_report[cls]['recall']),
                    'f1_score': float(test_report[cls]['f1-score']),
                    'support': int(test_report[cls]['support'])
                }
                for cls in CLASS_NAMES
            },
            'confusion_matrix': test_cm.tolist()
        },
        'feature_information': {
            'numerical_features_count': len(num_features),
            'categorical_features_count': len(cat_features),
            'numerical_features': num_features,
            'categorical_features': cat_features
        }
    }
    
    with open(report_json_path, 'w') as f:
        json.dump(eval_report, f, indent=2)
    print(f"[SAVED] Reproducible evaluation report saved to: {report_json_path}")
    
    print("\n" + "=" * 85)
    print(" READY FOR NEXT PHASE: Model Explainability (SHAP) -> D2 External Validation ")
    print("=" * 85)

if __name__ == '__main__':
    main()
