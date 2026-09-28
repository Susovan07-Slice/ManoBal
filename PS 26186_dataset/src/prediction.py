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
            v2_engine_path = os.path.join(
                os.path.dirname(__file__), '..', 'models', 'welfare_risk_engine_v2.pkl'
            )
            v4_path = os.path.join(
                os.path.dirname(__file__), '..', 'models', 'stress_risk_ensemble_v4.pkl'
            )
            v3_path = os.path.join(
                os.path.dirname(__file__), '..', 'models', 'stress_risk_ensemble_v3.pkl'
            )
            v2_path = os.path.join(
                os.path.dirname(__file__), '..', 'models', 'stress_risk_ensemble_v2.pkl'
            )
            v1_path = os.path.join(
                os.path.dirname(__file__), '..', 'models', 'final_stress_prediction_pipeline.pkl'
            )
            if os.path.exists(v2_engine_path):
                model_path = v2_engine_path
            elif os.path.exists(v4_path):
                model_path = v4_path
            elif os.path.exists(v3_path):
                model_path = v3_path
            elif os.path.exists(v2_path):
                model_path = v2_path
            else:
                model_path = v1_path
            
        self.model_path = model_path
        self.predictor = joblib.load(model_path)
        self.is_v2 = hasattr(self.predictor, 'assess') or hasattr(self.predictor, 'evaluate')
        
        if not self.is_v2:
            self.explainer = StressModelExplainer(predictor_path=model_path)
        else:
            try:
                v1_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'final_stress_prediction_pipeline.pkl')
                self.explainer = StressModelExplainer(predictor_path=v1_path)
            except Exception:
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
            # Welfare Risk Engine V2 assessment
            if hasattr(self.predictor, 'assess'):
                import inspect
                sig = inspect.signature(self.predictor.assess)
                if 'past_assessments' in sig.parameters:
                    assessment = self.predictor.assess(record_dict, past_assessments=past_assessments)
                else:
                    assessment = self.predictor.assess(record_dict)
            else:
                import inspect
                sig = inspect.signature(self.predictor.evaluate)
                if 'past_history' in sig.parameters:
                    assessment = self.predictor.evaluate(record_dict, past_history=past_assessments)
                else:
                    assessment = self.predictor.evaluate(record_dict)

            # If insufficient evidence
            if assessment.get("risk_score") is None:
                return assessment
            
            # Incorporate past assessment trajectory if available
            consecutive_high = assessment.get("consecutive_high_risk", 0)
            risk_trend = assessment.get("risk_trend", "Stable")
            risk_change = assessment.get("risk_change", 0.0)
            if (not past_assessments or len(past_assessments) == 0) and risk_trend == "Stable":
                risk_trend = "No prior history"
            key_factors = assessment.get("top_risk_factors", assessment.get("key_factors", []))
            protective_factors = assessment.get("protective_factors", [])
            raw_recs = assessment.get("recommendations", [])
            if not raw_recs:
                raw_recs = self.recommendation_engine.generate_recommendations(
                    risk_level=assessment.get("stress_level", "Medium"),
                    key_factors=key_factors,
                    record=df_input,
                    max_recommendations=4
                )
            recommendations = [
                rec.get("action", str(rec)) if isinstance(rec, dict) else str(rec)
                for rec in raw_recs
            ]
            
            risk_prob = assessment.get("risk_probability", round(assessment["risk_score"] / 100.0, 3))
            conf_val = assessment.get("confidence", 0.85)
            if isinstance(conf_val, (int, float)):
                conf_str = "High" if conf_val >= 0.70 else ("Moderate" if conf_val >= 0.40 else "Low")
            else:
                conf_str = str(conf_val)
            
            return {
                "stress_level": assessment.get("stress_level", "Medium"),
                "risk_score": assessment["risk_score"],
                "risk_category": assessment.get("risk_category", "Moderate"),
                "risk_percentile": assessment.get("risk_percentile", None),
                "risk_priority": assessment.get("risk_priority", "Routine"),
                "risk_probability": risk_prob,
                "calibrated_probability": risk_prob,
                "confidence": conf_str,
                "uncertainty": assessment.get("uncertainty", 0.15),
                "prediction_uncertainty": assessment.get("uncertainty", 0.15),
                "calibration_method": "Platt Sigmoid / Ordinal Cumulative Logit Exceedance",
                "out_of_distribution": assessment.get("out_of_distribution", False),
                "ood_reasons": assessment.get("ood_reasons", []),
                "risk_trend": risk_trend,
                "risk_change": risk_change,
                "consecutive_high_risk": consecutive_high,
                "probabilities": assessment["probabilities"],
                "raw_probabilities": assessment.get("raw_probabilities", assessment["probabilities"]),
                "calibrated_probabilities": assessment.get("calibrated_probabilities", assessment["probabilities"]),
                "key_factors": key_factors,
                "top_factors": key_factors,
                "top_risk_factors": key_factors,
                "protective_factors": protective_factors,
                "assessment_completeness": assessment.get("assessment_completeness", 1.0),
                "feature_contributions": assessment.get("feature_contributions", {}),
                "model_version": assessment.get("model_version", "risk_engine_v2"),
                "prediction_target": "Probabilistic Personnel Welfare Risk Score (0-100)",
                "recommendations": recommendations,
                "assessment_features_used": True,
                "hrms_features_used": True,
                "wearable_7d_features_used": False,
                "wearable_30d_features_used": False,
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
            "calibrated_probability": meta.get("risk_probability", round(risk_score / 100.0, 3)),
            "confidence": meta.get("confidence", "Moderate"),
            "uncertainty": meta.get("uncertainty", 0.0),
            "prediction_uncertainty": meta.get("uncertainty", 0.0),
            "calibration_method": "Platt Scaling (Sigmoid) via 5-Fold OOF CalibratedClassifierCV",
            "out_of_distribution": False,
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

    def get_diagnostic_assessment(
        self,
        record: Union[Dict[str, Any], pd.DataFrame, pd.Series]
    ) -> Dict[str, Any]:
        """
        Development diagnostic assessment complying with Section 17 schema.
        """
        raw_res = self.assess_personnel(record)
        raw_probs = raw_res.get("raw_probabilities", raw_res.get("probabilities", {}))
        cal_probs = raw_res.get("calibrated_probabilities", raw_res.get("probabilities", {}))
        return {
            "model_version": str(raw_res.get("model_version", "stress_risk_ensemble_v4")),
            "predicted_class": str(raw_res.get("stress_level", "Routine")),
            "raw_probabilities": {
                "low": float(raw_probs.get("Low", raw_probs.get("low", 0.0))),
                "medium": float(raw_probs.get("Medium", raw_probs.get("medium", 0.0))),
                "high": float(raw_probs.get("High", raw_probs.get("high", 0.0))),
            },
            "calibrated_probabilities": {
                "low": float(cal_probs.get("Low", cal_probs.get("low", 0.0))),
                "medium": float(cal_probs.get("Medium", cal_probs.get("medium", 0.0))),
                "high": float(cal_probs.get("High", cal_probs.get("high", 0.0))),
            },
            "risk_score": float(raw_res.get("risk_score", 0.0)),
            "risk_category": str(raw_res.get("risk_priority", "Routine")),
            "top_risk_factors": list(raw_res.get("key_factors", [])),
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
