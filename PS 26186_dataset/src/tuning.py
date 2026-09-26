import os
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

from src.feature_engineering import engineer_features
from src.preprocessing import build_preprocessor
from src.model_training import CLASS_NAMES, LABEL_TO_INT, INT_TO_LABEL

def build_end_to_end_pipeline(
    estimator: Any,
    numerical_features: list,
    categorical_features: list,
    include_feature_engineering: bool = True
) -> Pipeline:
    """
    Constructs a complete self-contained pipeline:
    Raw DataFrame -> Feature Engineering -> Preprocessor -> Estimator.
    """
    preprocessor = build_preprocessor(numerical_features, categorical_features)
    steps = []
    if include_feature_engineering:
        steps.append(('feature_engineering', FunctionTransformer(engineer_features, validate=False)))
    steps.append(('preprocessor', preprocessor))
    steps.append(('classifier', estimator))
    return Pipeline(steps=steps)

def tune_candidate_model(
    model_name: str,
    base_pipeline: Pipeline,
    param_distributions: Dict[str, Any],
    X_train: pd.DataFrame,
    y_train_encoded: np.ndarray,
    n_iter: int = 25,
    cv_splits: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Tunes hyperparameters using RandomizedSearchCV on the training set only.
    Scoring: 'f1_macro'. Stratified 5-Fold CV.
    """
    skf = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=random_state)
    
    search = RandomizedSearchCV(
        estimator=base_pipeline,
        param_distributions=param_distributions,
        n_iter=n_iter,
        scoring='f1_macro',
        cv=skf,
        random_state=random_state,
        n_jobs=-1,
        verbose=1,
        refit=True
    )
    
    search.fit(X_train, y_train_encoded)
    
    best_estimator = search.best_estimator_
    best_params = search.best_params_
    best_cv_score = search.best_score_
    
    return {
        "model_name": model_name,
        "search_object": search,
        "best_pipeline": best_estimator,
        "best_params": best_params,
        "best_cv_macro_f1": best_cv_score,
        "cv_results": search.cv_results_
    }

class CompleteStressPredictor:
    """
    Production-ready wrapper holding the complete end-to-end trained pipeline,
    class mappings, and inference methods for raw input data.
    """
    def __init__(self, pipeline: Pipeline, model_name: str, best_params: dict):
        self.pipeline = pipeline
        self.model_name = model_name
        self.best_params = best_params
        self.class_names = CLASS_NAMES
        self.label_to_int = LABEL_TO_INT
        self.int_to_label = INT_TO_LABEL
        
    def predict(self, X_raw: pd.DataFrame) -> np.ndarray:
        """Outputs string stress level labels ('Low', 'Medium', 'High')."""
        preds_int = np.asarray(self.pipeline.predict(X_raw)).ravel()
        return np.array([self.int_to_label[int(val)] for val in preds_int])
        
    def predict_proba(self, X_raw: pd.DataFrame) -> pd.DataFrame:
        """Outputs predicted probability distributions across classes."""
        if hasattr(self.pipeline.named_steps['classifier'], 'predict_proba'):
            probas = self.pipeline.predict_proba(X_raw)
            return pd.DataFrame(probas, columns=self.class_names)
        raise AttributeError("Underlying classifier does not support predict_proba.")
