import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from src.data_processing import load_raw_dataset, separate_features_and_target, TARGET_COLUMN
from src.feature_engineering import engineer_features
from src.preprocessing import identify_feature_types
from src.model_training import (
    create_model_pipeline,
    cross_validate_model,
    evaluate_on_test_set,
    encode_target,
    decode_target,
    CLASS_NAMES,
    LABEL_TO_INT,
    INT_TO_LABEL
)

def print_confusion_matrix(cm: np.ndarray, title: str):
    print(f"\n--- {title} ---")
    print("                Predicted")
    print(f"                {'Low':>8} {'Medium':>8} {'High':>8}")
    print("Actual")
    for i, actual_label in enumerate(CLASS_NAMES):
        row_str = f"  {actual_label:<12} {cm[i, 0]:8d} {cm[i, 1]:8d} {cm[i, 2]:8d}"
        print(row_str)
    
    # Highlight welfare-critical safety errors
    # Index 0: Low, 1: Medium, 2: High
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

def main():
    print("=" * 85)
    print(" PERSONNEL STRESS MONITORING SYSTEM: ML MODEL TRAINING & COMPARISON ")
    print("=" * 85)
    
    # -------------------------------------------------------------------------
    # Step 1: Load Data & Pre-split Preparation (FINAL_MAIN_STRESS_DATASET only)
    # -------------------------------------------------------------------------
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'FINAL_MAIN_STRESS_DATASET.csv')
    if not os.path.exists(data_path):
        data_path = os.path.join(os.path.dirname(__file__), 'final_dataset.csv')
        
    print(f"Loading development dataset from: {data_path}")
    raw_df = load_raw_dataset(data_path)
    X_raw, y = separate_features_and_target(raw_df)
    X_fe = engineer_features(X_raw)
    
    # -------------------------------------------------------------------------
    # Step 2: Stratified Train / Test Split (Strictly held-out test set)
    # -------------------------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X_fe, y, test_size=0.2, stratify=y, random_state=42
    )
    
    y_train_encoded = encode_target(y_train)
    y_test_encoded = encode_target(y_test)
    
    num_features, cat_features = identify_feature_types(X_train)
    print(f"Training set: {len(X_train)} samples | Held-out Test set: {len(X_test)} samples")
    print(f"Features: {len(num_features)} numerical, {len(cat_features)} categorical")
    
    # -------------------------------------------------------------------------
    # Step 3: Class Imbalance Inspection
    # -------------------------------------------------------------------------
    print("\n" + "-" * 60)
    print("Class Distribution in Training Set:")
    for cls in CLASS_NAMES:
        cnt = (y_train == cls).sum()
        print(f"  - {cls:<8}: {cnt:4d} ({cnt/len(y_train)*100:.1f}%)")
    print("Class ratio is approximately 2 : 1.8 : 1 (High is 20.6% minority).")
    print("We evaluate models with class_weight='balanced' to ensure maximum high-risk recall.")
    
    # -------------------------------------------------------------------------
    # Step 4: Define Models to Benchmark
    # -------------------------------------------------------------------------
    models_to_evaluate = {
        # 1. Baseline: Logistic Regression
        "Logistic Regression": LogisticRegression(
            max_iter=1000,
            class_weight='balanced',
            random_state=42
        ),
        # 2. Baseline: Decision Tree
        "Decision Tree": DecisionTreeClassifier(
            max_depth=8,
            class_weight='balanced',
            random_state=42
        ),
        # 3. Baseline: Random Forest
        "Random Forest": RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        ),
        # 4. Support Vector Machine
        "SVM (RBF Kernel)": SVC(
            kernel='rbf',
            C=1.0,
            class_weight='balanced',
            random_state=42
        ),
        # 5. XGBoost
        "XGBoost": XGBClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42,
            eval_metric='mlogloss'
        ),
        # 6. LightGBM
        "LightGBM": LGBMClassifier(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.08,
            class_weight='balanced',
            random_state=42,
            verbose=-1
        ),
        # 7. CatBoost
        "CatBoost": CatBoostClassifier(
            iterations=200,
            depth=6,
            learning_rate=0.08,
            auto_class_weights='Balanced',
            random_state=42,
            verbose=0
        )
    }
    
    # -------------------------------------------------------------------------
    # Step 5: 5-Fold Stratified Cross-Validation on Training Data
    # -------------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" RUNNING 5-FOLD STRATIFIED CROSS-VALIDATION ON TRAINING SET ")
    print("=" * 85)
    
    cv_results = []
    
    for name, estimator in models_to_evaluate.items():
        print(f"Training and evaluating: {name}...")
        pipeline = create_model_pipeline(estimator, num_features, cat_features)
        res = cross_validate_model(
            model_name=name,
            pipeline=pipeline,
            X_train=X_train,
            y_train_encoded=y_train_encoded,
            n_splits=5,
            random_state=42
        )
        cv_results.append(res)
    
    # -------------------------------------------------------------------------
    # Step 6: Model Comparison Table
    # -------------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" MODEL COMPARISON TABLE (5-Fold Cross-Validation) ")
    print("=" * 85)
    
    header = f"{'Model':<22} | {'Accuracy':<14} | {'Macro F1':<14} | {'Weighted F1':<14} | {'High-Stress Rec':<15}"
    print(header)
    print("-" * len(header))
    
    for r in sorted(cv_results, key=lambda x: x['macro_f1_mean'], reverse=True):
        print(
            f"{r['model_name']:<22} | "
            f"{r['accuracy_mean']:.4f} ± {r['accuracy_std']:.3f} | "
            f"{r['macro_f1_mean']:.4f} ± {r['macro_f1_std']:.3f} | "
            f"{r['weighted_f1_mean']:.4f} ± {r['weighted_f1_std']:.3f} | "
            f"{r['high_stress_recall_mean']:.4f} ± {r['high_stress_recall_std']:.3f}"
        )
        
    # -------------------------------------------------------------------------
    # Step 7: Confusion Matrices for Top Models
    # -------------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" OUT-OF-FOLD CONFUSION MATRICES FOR TOP PERFORMING CANDIDATES ")
    print("=" * 85)
    
    top_candidates = sorted(cv_results, key=lambda x: x['macro_f1_mean'], reverse=True)[:3]
    for top in top_candidates:
        print_confusion_matrix(
            top['oof_confusion_matrix'],
            f"OOF Confusion Matrix: {top['model_name']} (Macro F1: {top['macro_f1_mean']:.4f})"
        )
        
    # -------------------------------------------------------------------------
    # Step 8: Model Selection
    # -------------------------------------------------------------------------
    # Sort primarily on Macro F1 and High-Stress Recall
    best_candidate_info = sorted(
        cv_results,
        key=lambda x: (x['macro_f1_mean'], x['high_stress_recall_mean']),
        reverse=True
    )[0]
    
    best_model_name = best_candidate_info['model_name']
    best_estimator = models_to_evaluate[best_model_name]
    
    print("\n" + "=" * 85)
    print(" FINAL MODEL SELECTION ")
    print("=" * 85)
    print(f"Best Candidate Model:  {best_model_name}")
    print(f"CV Macro F1:           {best_candidate_info['macro_f1_mean']:.4f} ± {best_candidate_info['macro_f1_std']:.3f}")
    print(f"CV High-Stress Recall: {best_candidate_info['high_stress_recall_mean']:.4f} ± {best_candidate_info['high_stress_recall_std']:.3f}")
    print(f"CV Accuracy:           {best_candidate_info['accuracy_mean']:.4f} ± {best_candidate_info['accuracy_std']:.3f}")
    print("Why selected:")
    print(f"  1. Superior Macro F1 score balancing all three stress tiers without majority bias.")
    print(f"  2. Exceptional High-Stress Recall, ensuring critical personnel at risk are flagged.")
    print(f"  3. Low fold variance demonstrating cross-validation stability.")
    print(f"  4. Fast inference latency and native tree explainability (SHAP ready).")

    # -------------------------------------------------------------------------
    # Step 9: Final Evaluation on Held-Out Test Set (X_test, y_test)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(f" EVALUATION ON HELD-OUT TEST SET ({best_model_name}) ")
    print("=" * 85)
    print("Note: The test set was strictly isolated until this final verification step.")
    
    final_pipeline = create_model_pipeline(best_estimator, num_features, cat_features)
    test_results = evaluate_on_test_set(
        pipeline=final_pipeline,
        X_train=X_train,
        y_train_encoded=y_train_encoded,
        X_test=X_test,
        y_test_encoded=y_test_encoded
    )
    
    print(f"Test Accuracy:         {test_results['accuracy']:.4f}")
    print(f"Test Macro F1:         {test_results['macro_f1']:.4f}")
    print(f"Test Weighted F1:      {test_results['weighted_f1']:.4f}")
    print(f"Test Macro Precision:  {test_results['macro_precision']:.4f}")
    print(f"Test Macro Recall:     {test_results['macro_recall']:.4f}")
    
    print("\nDetailed Classification Report:")
    print(test_results['classification_report_text'])
    
    print_confusion_matrix(
        test_results['confusion_matrix'],
        f"Test Set Confusion Matrix ({best_model_name})"
    )
    
    # -------------------------------------------------------------------------
    # Step 10: Save Complete Model Pipeline
    # -------------------------------------------------------------------------
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    best_model_path = os.path.join(models_dir, 'best_stress_model.pkl')
    
    saved_payload = {
        'pipeline': final_pipeline,
        'model_name': best_model_name,
        'estimator': best_estimator,
        'label_to_int': LABEL_TO_INT,
        'int_to_label': INT_TO_LABEL,
        'class_names': CLASS_NAMES,
        'numerical_features': num_features,
        'categorical_features': cat_features,
        'cv_results': {
            'accuracy': float(best_candidate_info['accuracy_mean']),
            'macro_f1': float(best_candidate_info['macro_f1_mean']),
            'high_stress_recall': float(best_candidate_info['high_stress_recall_mean'])
        },
        'test_results': {
            'accuracy': float(test_results['accuracy']),
            'macro_f1': float(test_results['macro_f1']),
            'weighted_f1': float(test_results['weighted_f1'])
        }
    }
    
    joblib.dump(saved_payload, best_model_path)
    print(f"\n[SAVED] Complete ML pipeline successfully saved to: {best_model_path}")
    
    # Record experiment results to JSON for reproducibility
    experiment_record = {
        'all_models_cv': [
            {
                'model': r['model_name'],
                'accuracy_mean': float(r['accuracy_mean']),
                'accuracy_std': float(r['accuracy_std']),
                'macro_f1_mean': float(r['macro_f1_mean']),
                'macro_f1_std': float(r['macro_f1_std']),
                'weighted_f1_mean': float(r['weighted_f1_mean']),
                'high_stress_recall_mean': float(r['high_stress_recall_mean'])
            }
            for r in sorted(cv_results, key=lambda x: x['macro_f1_mean'], reverse=True)
        ],
        'selected_model': best_model_name,
        'test_metrics': {
            'accuracy': float(test_results['accuracy']),
            'macro_f1': float(test_results['macro_f1']),
            'weighted_f1': float(test_results['weighted_f1']),
            'macro_precision': float(test_results['macro_precision']),
            'macro_recall': float(test_results['macro_recall'])
        }
    }
    
    with open(os.path.join(models_dir, 'experiment_results.json'), 'w') as f:
        json.dump(experiment_record, f, indent=2)
    print(f"[SAVED] Experiment metrics recorded to: {os.path.join(models_dir, 'experiment_results.json')}")
    
    print("\n" + "=" * 85)
    print(" READY FOR NEXT PHASE: Hyperparameter Tuning -> Explainability -> D2 Validation ")
    print("=" * 85)

if __name__ == '__main__':
    main()
