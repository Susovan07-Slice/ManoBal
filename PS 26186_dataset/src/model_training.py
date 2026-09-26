import os
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

from src.preprocessing import build_preprocessor, identify_feature_types

# Class definitions for ordinal stress levels
CLASS_NAMES = ['Low', 'Medium', 'High']
LABEL_TO_INT = {'Low': 0, 'Medium': 1, 'High': 2}
INT_TO_LABEL = {0: 'Low', 1: 'Medium', 2: 'High'}

def encode_target(y: pd.Series) -> np.ndarray:
    """Encodes string target labels into integers 0=Low, 1=Medium, 2=High."""
    return np.array([LABEL_TO_INT[val] for val in y])

def decode_target(y_encoded: np.ndarray) -> np.ndarray:
    """Decodes integer predictions back to string labels."""
    return np.array([INT_TO_LABEL[val] for val in y_encoded])

def create_model_pipeline(
    estimator: Any,
    numerical_features: List[str],
    categorical_features: List[str]
) -> Pipeline:
    """
    Creates a unified Pipeline: Raw Features -> Preprocessor -> Estimator.
    Guarantees no data leakage during cross-validation and deployment.
    """
    preprocessor = build_preprocessor(numerical_features, categorical_features)
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', estimator)
    ])
    return pipeline

def cross_validate_model(
    model_name: str,
    pipeline: Pipeline,
    X_train: pd.DataFrame,
    y_train_encoded: np.ndarray,
    n_splits: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Performs Stratified 5-Fold Cross-Validation on the training set.
    Calculates Accuracy, Macro F1, Weighted F1, Macro Precision, Macro Recall,
    High-Stress Recall, and collects out-of-fold predictions.
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    oof_predictions = np.zeros(len(X_train), dtype=int)
    
    acc_scores = []
    macro_f1_scores = []
    weighted_f1_scores = []
    macro_prec_scores = []
    macro_rec_scores = []
    high_stress_rec_scores = []
    
    # Target index 2 corresponds to 'High' stress
    high_stress_class_idx = 2
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(X_train, y_train_encoded)):
        X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_tr, y_val = y_train_encoded[train_idx], y_train_encoded[val_idx]
        
        # Fit pipeline strictly on fold training data
        pipeline.fit(X_tr, y_tr)
        val_preds = np.asarray(pipeline.predict(X_val)).ravel()
        oof_predictions[val_idx] = val_preds
        
        acc_scores.append(accuracy_score(y_val, val_preds))
        macro_f1_scores.append(f1_score(y_val, val_preds, average='macro', zero_division=0))
        weighted_f1_scores.append(f1_score(y_val, val_preds, average='weighted', zero_division=0))
        macro_prec_scores.append(precision_score(y_val, val_preds, average='macro', zero_division=0))
        macro_rec_scores.append(recall_score(y_val, val_preds, average='macro', zero_division=0))
        
        # High stress recall for this fold
        rec_per_class = recall_score(y_val, val_preds, average=None, zero_division=0)
        high_stress_rec_scores.append(rec_per_class[high_stress_class_idx])
        
    cm_oof = confusion_matrix(y_train_encoded, oof_predictions, labels=[0, 1, 2])
    
    return {
        "model_name": model_name,
        "accuracy_mean": np.mean(acc_scores),
        "accuracy_std": np.std(acc_scores),
        "macro_f1_mean": np.mean(macro_f1_scores),
        "macro_f1_std": np.std(macro_f1_scores),
        "weighted_f1_mean": np.mean(weighted_f1_scores),
        "weighted_f1_std": np.std(weighted_f1_scores),
        "macro_precision_mean": np.mean(macro_prec_scores),
        "macro_recall_mean": np.mean(macro_rec_scores),
        "high_stress_recall_mean": np.mean(high_stress_rec_scores),
        "high_stress_recall_std": np.std(high_stress_rec_scores),
        "oof_predictions": oof_predictions,
        "oof_confusion_matrix": cm_oof
    }

def evaluate_on_test_set(
    pipeline: Pipeline,
    X_train: pd.DataFrame,
    y_train_encoded: np.ndarray,
    X_test: pd.DataFrame,
    y_test_encoded: np.ndarray
) -> Dict[str, Any]:
    """
    Fits final pipeline on the complete training set and evaluates on the held-out test set.
    """
    pipeline.fit(X_train, y_train_encoded)
    test_preds = np.asarray(pipeline.predict(X_test)).ravel()
    
    acc = accuracy_score(y_test_encoded, test_preds)
    macro_f1 = f1_score(y_test_encoded, test_preds, average='macro', zero_division=0)
    weighted_f1 = f1_score(y_test_encoded, test_preds, average='weighted', zero_division=0)
    macro_prec = precision_score(y_test_encoded, test_preds, average='macro', zero_division=0)
    macro_rec = recall_score(y_test_encoded, test_preds, average='macro', zero_division=0)
    cm = confusion_matrix(y_test_encoded, test_preds, labels=[0, 1, 2])
    
    report_dict = classification_report(
        y_test_encoded,
        test_preds,
        labels=[0, 1, 2],
        target_names=CLASS_NAMES,
        output_dict=True,
        zero_division=0
    )
    report_text = classification_report(
        y_test_encoded,
        test_preds,
        labels=[0, 1, 2],
        target_names=CLASS_NAMES,
        zero_division=0
    )
    
    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "macro_precision": macro_prec,
        "macro_recall": macro_rec,
        "confusion_matrix": cm,
        "classification_report_text": report_text,
        "classification_report_dict": report_dict,
        "predictions": test_preds
    }
