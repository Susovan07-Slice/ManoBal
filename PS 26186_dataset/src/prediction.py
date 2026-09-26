import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Union, Optional, List

from src.risk_scoring import calculate_risk_score
from src.explain import StressModelExplainer
from src.explainability import extract_key_factors
from src.recommendation_engine import WelfareRecommendationEngine

class PersonnelWelfarePredictor:
    """
    Unified, production-ready inference service for Personnel Stress & Welfare.
    Integrates:
      1. Advanced Probabilistic Ensemble V2 (or fallback LightGBM V1)
      2. Calibrated 0-100 Continuous Probabilistic Risk Scoring
      3. Explainability Factor Translation
      4. Contextualized Welfare Recommendation Engine
    """
    def __init__(self, model_path: str = None):
        if model_path is None:
            v1_path = os.path.join(
                os.path.dirname(__file__), '..', 'models', 'final_stress_prediction_pipeline.pkl'
            )
            model_path = v1_path
            
        self.model_path = model_path
        self.predictor = joblib.load(model_path)
        self.is_v2 = hasattr(self.predictor, 'assess')
        
        if not self.is_v2:
            self.explainer = StressModelExplainer(predictor_path=model_path)
        else:
            self.explainer = None
            
        self.recommendation_engine = WelfareRecommendationEngine()

    def assess_personnel(
        self,
        record: Union[Dict[str, Any], pd.DataFrame, pd.Series],
        past_assessments: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Processes a single raw personnel record and produces the complete
        welfare risk assessment with continuous probabilistic calibration.
        """
        if isinstance(record, pd.DataFrame):
            record_dict = record.iloc[0].to_dict() if not record.empty else {}
            df_input = record
        elif isinstance(record, pd.Series):
            record_dict = record.to_dict()
            df_input = record.to_frame().T
        else:
            record_dict = dict(record)
            df_input = pd.DataFrame([record])

        if self.is_v2:
            # Phase 33 Probabilistic Ensemble Assessment
            assessment = self.predictor.assess(record_dict)
            
            # Incorporate past assessment trajectory if available
            consecutive_high = 0
            risk_trend = "Stable"
            risk_change = 0.0
            if past_assessments and len(past_assessments) > 0:
                prev = past_assessments[0]
                prev_score = float(prev.get("risk_score", assessment["risk_score"]))
                risk_change = round(assessment["risk_score"] - prev_score, 1)
                if risk_change >= 5.0:
                    risk_trend = "Worsening"
                elif risk_change <= -5.0:
                    risk_trend = "Improving"
                    
                for past in past_assessments:
                    if past.get("stress_level") in ["High", "Priority"] or float(past.get("risk_score", 0.0)) >= 70.0:
                        consecutive_high += 1
                    else:
                        break
                        
            key_factors = assessment.get("key_factors", [])
            recommendations = self.recommendation_engine.generate_recommendations(
                risk_level=assessment["stress_level"],
                key_factors=key_factors,
                record=df_input,
                max_recommendations=4
            )
            
            return {
                "stress_level": assessment["stress_level"],
                "risk_score": assessment["risk_score"],
                "risk_priority": assessment["risk_priority"],
                "risk_probability": assessment["risk_probability"],
                "confidence": assessment.get("confidence", "Moderate"),
                "uncertainty": assessment.get("uncertainty", 0.0),
                "risk_trend": risk_trend,
                "risk_change": risk_change,
                "consecutive_high_risk": consecutive_high,
                "probabilities": assessment["probabilities"],
                "key_factors": key_factors,
                "top_factors": key_factors,
                "feature_contributions": assessment.get("feature_contributions", {}),
                "model_version": assessment.get("model_version", "stress_risk_ensemble_v2"),
                "prediction_target": assessment.get("prediction_target", "P(Stress_Level >= Medium / Continuous Severity)"),
                "recommendations": recommendations,
                "assessment_features_used": assessment.get("assessment_features_used", True),
                "hrms_features_used": assessment.get("hrms_features_used", True),
                "wearable_7d_features_used": assessment.get("wearable_7d_features_used", False),
                "wearable_30d_features_used": assessment.get("wearable_30d_features_used", False),
                "is_simulated": True,
                "disclaimer": assessment.get("disclaimer", (
                    "AI-assisted early-warning decision-support prototype. "
                    "Assessments indicate statistical model associations and are strictly "
                    "intended for supportive welfare intervention, not disciplinary action or clinical diagnosis."
                ))
            }

        # ---------------------------------------------------------------------
        # Fallback to V1 Single-Model Pipeline if V1 artifact was explicitly loaded
        # ---------------------------------------------------------------------
        pred_label = self.predictor.predict(df_input)[0]
        probas = self.predictor.predict_proba(df_input).iloc[0].to_dict()
        probas_clean = {k: round(float(v), 3) for k, v in probas.items()}

        risk_score, risk_level, risk_priority, meta = calculate_risk_score(
            probas_clean, pred_label, df_input,
            past_assessments=past_assessments,
            return_metadata=True
        )

        key_factors = extract_key_factors(self.explainer, df_input, top_k=4)

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
            "risk_probability": meta.get("risk_probability", round(risk_score / 100.0, 3)),
            "confidence": meta.get("confidence", "Moderate"),
            "uncertainty": meta.get("uncertainty", 0.0),
            "risk_trend": meta.get("risk_trend", "Stable"),
            "risk_change": meta.get("risk_change", 0.0),
            "consecutive_high_risk": meta.get("consecutive_high_risk", 0),
            "probabilities": probas_clean,
            "key_factors": key_factors,
            "top_factors": key_factors,
            "recommendations": recommendations,
            "model_version": "1.0.0-LightGBM",
            "prediction_target": "P(Stress_Level >= Medium / Continuous Severity)",
            "assessment_features_used": True,
            "hrms_features_used": False,
            "wearable_7d_features_used": False,
            "wearable_30d_features_used": False,
            "is_simulated": True,
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

def predict_welfare(
    record: Union[Dict[str, Any], pd.DataFrame, pd.Series],
    past_assessments: Optional[list] = None
) -> Dict[str, Any]:
    service = get_welfare_service()
    return service.assess_personnel(record, past_assessments=past_assessments)
