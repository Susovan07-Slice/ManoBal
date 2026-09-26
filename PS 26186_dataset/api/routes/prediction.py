from fastapi import APIRouter, HTTPException, Depends, status
from core.config import logger, settings
from schemas.prediction import PredictionRequest, PredictionResponse
from services.prediction_service import WelfarePredictionService, get_prediction_service
from api.deps import get_current_user
from db.models.user import User

router = APIRouter(prefix="", tags=["Prediction & Assessment"])

@router.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Personnel Stress Risk & Generate Welfare Recommendations",
    description=(
        "Processes raw personnel operational telemetry and health indicators through the "
        "trained LightGBM pipeline, computes a calibrated 0-100 risk score, extracts TreeSHAP "
        "contributing factors, and produces supportive welfare recommendations. "
        "Protected endpoint: requires valid JWT authentication."
    )
)
def predict_personnel_stress(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
    service: WelfarePredictionService = Depends(get_prediction_service)
) -> PredictionResponse:
    try:
        logger.info(
            f"Authenticated inference request by '{current_user.username}' (Role: {current_user.role}) for Dept: {request.Department}, "
            f"DutyHours: {request.Duty_Hours_Per_Week}, ConsecutiveDays: {request.Consecutive_Duty_Days}"
        )
        response = service.predict(request)
        logger.info(f"Prediction successful: Level={response.stress_level}, Score={response.risk_score}")
        return response
    except Exception as e:
        logger.error(f"Prediction failure: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while evaluating stress risk. Please try again later."
        )

@router.post(
    "/predict/sensitivity",
    status_code=status.HTTP_200_OK,
    summary="Evaluate Counterfactual Feature Sensitivity (Internal / Model Validation)",
    description="Allows controlled sensitivity evaluation of feature perturbations against a baseline feature vector."
)
def evaluate_sensitivity(
    baseline: PredictionRequest,
    current_user: User = Depends(get_current_user),
    service: WelfarePredictionService = Depends(get_prediction_service)
):
    from src.ensemble_v2 import evaluate_counterfactual_sensitivity
    if not hasattr(service.predictor.predictor, 'assess'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active model artifact does not support ensemble sensitivity evaluation."
        )
    b_dict = baseline.to_dataframe_dict()
    perturbations = {
        'physical_fatigue': [1, 2, 3, 4, 5],
        'Sleep_Hours': [8.0, 6.5, 5.0, 3.5],
        'Duty_Hours_Per_Week': [40.0, 50.0, 60.0, 75.0]
    }
    res = evaluate_counterfactual_sensitivity(service.predictor.predictor, b_dict, perturbations)
    return res

from sqlalchemy import text
from db.session import engine

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="System Health Check",
    tags=["System Health"]
)
def health_check(service: WelfarePredictionService = Depends(get_prediction_service)):
    # Safe database probe that validates connectivity without leaking credentials or SQL details
    db_connected = False
    db_engine_name = "unknown"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_connected = True
            db_engine_name = engine.dialect.name
    except Exception as e:
        logger.warning(f"Database health check probe failed: {type(e).__name__}")
        db_connected = False

    return {
        "status": "healthy" if (service.predictor is not None and db_connected) else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "model_loaded": service.predictor is not None,
        "database": {
            "connected": db_connected,
            "engine": db_engine_name
        }
    }
