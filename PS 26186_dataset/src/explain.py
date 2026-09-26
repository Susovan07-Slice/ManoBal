import os
import joblib
import shap
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any

from src.model_training import CLASS_NAMES, LABEL_TO_INT, INT_TO_LABEL
from src.tuning import CompleteStressPredictor

class StressModelExplainer:
    """
    Model Explainability module powered by TreeSHAP for the finalized LightGBM pipeline.
    Identifies statistical associations contributing to stress classifications without
    implying clinical or operational causality.
    """
    def __init__(self, predictor_path: str = None):
        if predictor_path is None:
            predictor_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'final_stress_prediction_pipeline.pkl')
            
        self.predictor = joblib.load(predictor_path)
        self.pipeline = self.predictor.pipeline
        raw_model = self.pipeline.named_steps['classifier']
        if hasattr(raw_model, 'calibrated_classifiers_') and len(raw_model.calibrated_classifiers_) > 0:
            self.model = raw_model.calibrated_classifiers_[0].estimator
        else:
            self.model = raw_model
        self.preprocessor = self.pipeline.named_steps['preprocessor']
        self.feature_engineering = self.pipeline.named_steps['feature_engineering']
        
        # Extract preprocessed feature names
        num_features = self.preprocessor.transformers_[0][2]
        cat_features = self.preprocessor.transformers_[1][2]
        cat_encoder = self.preprocessor.named_transformers_['cat'].named_steps['encoder']
        cat_names = cat_encoder.get_feature_names_out(cat_features).tolist()
        self.feature_names = num_features + cat_names
        
        # Initialize TreeExplainer
        self.explainer = shap.TreeExplainer(self.model)

    def transform_raw_data(self, X_raw: pd.DataFrame) -> np.ndarray:
        """Transforms raw input DataFrame through feature engineering and column transformer."""
        X_fe = self.feature_engineering.transform(X_raw)
        return self.preprocessor.transform(X_fe)

    def get_global_feature_importance(self, X_raw: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
        """
        Computes mean absolute SHAP values across all classes for global feature importance.
        """
        X_proc = self.transform_raw_data(X_raw)
        shap_values = self.explainer.shap_values(X_proc)
        
        # shap_values shape: (N, n_features, n_classes) or list of (N, n_features)
        if isinstance(shap_values, list):
            # Sum mean abs across classes
            mean_abs_shap = np.mean([np.mean(np.abs(sv), axis=0) for sv in shap_values], axis=0)
        elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
            mean_abs_shap = np.mean(np.mean(np.abs(shap_values), axis=0), axis=1)
        else:
            mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
            
        df_importance = pd.DataFrame({
            'Feature': self.feature_names,
            'Mean_Abs_SHAP': mean_abs_shap
        }).sort_values('Mean_Abs_SHAP', ascending=False).reset_index(drop=True)
        
        return df_importance.head(top_n)

    def get_class_specific_importance(self, X_raw: pd.DataFrame, class_name: str = 'High', top_n: int = 10) -> pd.DataFrame:
        """
        Computes feature importance specifically associated with predictions for a given target class.
        Class index 2 corresponds to 'High' stress.
        """
        class_idx = LABEL_TO_INT[class_name]
        X_proc = self.transform_raw_data(X_raw)
        shap_values = self.explainer.shap_values(X_proc)
        
        if isinstance(shap_values, list):
            sv_class = shap_values[class_idx]
        elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
            sv_class = shap_values[:, :, class_idx]
        else:
            sv_class = shap_values
            
        mean_abs_class = np.mean(np.abs(sv_class), axis=0)
        mean_directional = np.mean(sv_class, axis=0)
        
        df_class_imp = pd.DataFrame({
            'Feature': self.feature_names,
            'Importance': mean_abs_class,
            'Mean_Directional_Impact': mean_directional
        }).sort_values('Importance', ascending=False).reset_index(drop=True)
        
        return df_class_imp.head(top_n)

    def explain_single_record(self, record_raw: pd.DataFrame) -> Dict[str, Any]:
        """
        Generates an individual prediction explanation for a single raw personnel record.
        Returns predicted level, probabilities, and top contributing model factors.
        """
        if isinstance(record_raw, pd.Series):
            record_raw = record_raw.to_frame().T
            
        pred_label = self.predictor.predict(record_raw)[0]
        pred_probas = self.predictor.predict_proba(record_raw).iloc[0].to_dict()
        
        # Transform through pipeline steps
        X_proc = self.transform_raw_data(record_raw)
        shap_values = self.explainer.shap_values(X_proc)
        
        pred_class_idx = LABEL_TO_INT[pred_label]
        
        if isinstance(shap_values, list):
            sample_shap = shap_values[pred_class_idx][0]
        elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
            sample_shap = shap_values[0, :, pred_class_idx]
        else:
            sample_shap = shap_values[0]
            
        # Rank features by positive contribution toward predicted class
        top_indices = np.argsort(np.abs(sample_shap))[::-1][:6]
        
        factors = []
        for idx in top_indices:
            feat_name = self.feature_names[idx]
            impact = float(sample_shap[idx])
            direction = "Elevating risk score" if impact > 0 else "Lowering risk score"
            factors.append({
                "factor": feat_name,
                "shap_impact": round(impact, 4),
                "direction": direction
            })
            
        return {
            "predicted_stress_level": pred_label,
            "prediction_probabilities": {k: round(v, 3) for k, v in pred_probas.items()},
            "contributing_model_factors": factors,
            "interpretation_notice": "The model identified these features as statistical contributors to the prediction. Associations do not imply clinical or operational causation."
        }
