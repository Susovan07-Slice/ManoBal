from fastapi import APIRouter, HTTPException, Depends, status
from core.config import logger, settings
from schemas.prediction import PredictionRequest, PredictionResponse, DiagnosticResponse
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

@router.post(
    "/predict/diagnostic",
    response_model=DiagnosticResponse,
    status_code=status.HTTP_200_OK,
    summary="Development Diagnostic Stress Inference Endpoint",
    description="Development-only diagnostic response providing full raw vs calibrated probabilities, risk score, and factors."
)
def predict_diagnostic(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
    service: WelfarePredictionService = Depends(get_prediction_service)
) -> DiagnosticResponse:
    record_dict = request.to_dataframe_dict()
    raw_res = service.predictor.assess_personnel(record_dict)
    
    # Extract internal raw and calibrated probabilities
    raw_probs = raw_res.get("raw_probabilities", raw_res.get("probabilities", {}))
    cal_probs = raw_res.get("calibrated_probabilities", raw_res.get("probabilities", {}))
    
    return DiagnosticResponse(
        model_version=str(raw_res.get("model_version", "stress_risk_ensemble_v4")),
        predicted_class=str(raw_res.get("stress_level", "Routine")),
        raw_probabilities={
            "low": float(raw_probs.get("Low", 0.0)),
            "medium": float(raw_probs.get("Medium", 0.0)),
            "high": float(raw_probs.get("High", 0.0)),
        },
        calibrated_probabilities={
            "low": float(cal_probs.get("Low", 0.0)),
            "medium": float(cal_probs.get("Medium", 0.0)),
            "high": float(cal_probs.get("High", 0.0)),
        },
        risk_score=float(raw_res.get("risk_score", 0.0)),
        risk_category=str(raw_res.get("risk_priority", "Routine")),
        top_risk_factors=raw_res.get("key_factors", raw_res.get("top_factors", []))
    )


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
        "environment": settings.ENVIRONMENT,
        "model_loaded": service.predictor is not None,
        "database": {
            "connected": db_connected,
            "engine": db_engine_name
        }
    }
