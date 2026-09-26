import os
from typing import Optional
from core.config import settings, logger
from src.prediction import PersonnelWelfarePredictor
from schemas.prediction import PredictionRequest, PredictionResponse

class WelfarePredictionService:
    """
    Singleton service managing the in-memory ML inference pipeline,
    risk scoring, explainability, and recommendation engine.
    """
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            v2_path = os.path.join(settings.BASE_DIR, "models", "stress_risk_ensemble_v2.pkl")
            if os.path.exists(v2_path):
                model_path = v2_path
            else:
                model_path = settings.MODEL_PATH
            
        if not os.path.exists(model_path):
            logger.error(f"Critical error: ML Model artifact not found at: {model_path}")
            raise FileNotFoundError(f"Model file not found at {model_path}. Run training pipeline first.")
            
        logger.info(f"Loading ML Welfare Pipeline from: {model_path}")
        try:
            self.predictor = PersonnelWelfarePredictor(model_path=model_path)
        except Exception as e:
            logger.warning(f"Failed loading {model_path} ({e}); falling back to default model: {settings.MODEL_PATH}")
            self.predictor = PersonnelWelfarePredictor(model_path=settings.MODEL_PATH)
        logger.info("ML Welfare Pipeline successfully loaded into memory and ready for inference.")

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        """
        Executes end-to-end inference flow:
        Request -> Feature Engineering -> LightGBM -> Risk Scoring -> SHAP Explainability -> Recommendations
        """
        record_dict = request.to_dataframe_dict()
        result = self.predictor.assess_personnel(record_dict)
        return PredictionResponse(**result)

_service_instance: Optional[WelfarePredictionService] = None

def get_prediction_service() -> WelfarePredictionService:
    """Provides singleton access to the loaded in-memory service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = WelfarePredictionService()
    return _service_instance
