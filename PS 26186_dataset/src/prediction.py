import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Union

from src.risk_scoring import calculate_risk_score
from src.explain import StressModelExplainer
from src.explainability import extract_key_factors
from src.recommendation_engine import WelfareRecommendationEngine

class PersonnelWelfarePredictor:
    """
    Unified, production-ready inference service for Personnel Stress & Welfare.
    Integrates:
      1. Final ML Prediction Pipeline (LightGBM)
      2. Calibrated 0-100 Risk Scoring
      3. TreeSHAP Explainability Factor Translation
      4. Contextualized Welfare Recommendation Engine
    """
    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(__file__), '..', 'models', 'final_stress_prediction_pipeline.pkl'
            )
        self.predictor = joblib.load(model_path)
        self.explainer = StressModelExplainer(predictor_path=model_path)
        self.recommendation_engine = WelfareRecommendationEngine()

    def assess_personnel(
        self,
        record: Union[Dict[str, Any], pd.DataFrame, pd.Series]
    ) -> Dict[str, Any]:
        """
        Processes a single raw personnel record and produces the complete
        welfare risk assessment.
        """
        # Format input as a 1-row DataFrame
        if isinstance(record, dict):
            df_input = pd.DataFrame([record])
        elif isinstance(record, pd.Series):
            df_input = record.to_frame().T
        else:
            df_input = record.copy()
            if len(df_input) > 1:
                df_input = df_input.iloc[[0]]

        # 1. Run ML Pipeline Inference
        pred_label = self.predictor.predict(df_input)[0]
        probas = self.predictor.predict_proba(df_input).iloc[0].to_dict()
        probas_clean = {k: round(float(v), 3) for k, v in probas.items()}

        # 2. Compute Calibrated 0-100 Risk Score and Priority
        risk_score, risk_level, risk_priority = calculate_risk_score(probas_clean, pred_label)

        # 3. Extract Model-Identified Key Contributing Factors
        key_factors = extract_key_factors(self.explainer, df_input, top_k=4)

        # 4. Generate Contextualized Welfare Recommendations
        recommendations = self.recommendation_engine.generate_recommendations(
            risk_level=risk_level,
            key_factors=key_factors,
            record=df_input,
            max_recommendations=4
        )

        return {
            "stress_level": risk_level,
            "risk_score": risk_score,
            "risk_priority": risk_priority,
            "probabilities": probas_clean,
            "key_factors": key_factors,
            "recommendations": recommendations,
            "disclaimer": (
                "AI-assisted early-warning decision-support prototype. "
                "Assessments indicate statistical model associations and are strictly "
                "intended for supportive welfare intervention, not disciplinary action or clinical diagnosis."
            )
        }

# Global singleton helper for fast API calls
_global_service = None

def get_welfare_service():
    global _global_service
    if _global_service is None:
        _global_service = PersonnelWelfarePredictor()
    return _global_service

def predict_welfare(record: Union[Dict[str, Any], pd.DataFrame, pd.Series]) -> Dict[str, Any]:
    service = get_welfare_service()
    return service.assess_personnel(record)
