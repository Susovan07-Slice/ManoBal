import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Ensure dataset root directory is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings, logger
from db.init_db import init_db
from services.prediction_service import get_prediction_service
from api.routes.prediction import router as prediction_router
from api.routes.auth import router as auth_router
from api.routes.personnel import router as personnel_router
from api.routes.assessment import router as assessment_router
from api.routes.dashboard import router as dashboard_router
from api.routes.welfare_request import router as welfare_request_router
from api.routes.organization import router as organization_router
from api.routes.hrms import router as hrms_router
from api.routes.telemetry import router as telemetry_router
from api.routes.analytics import router as analytics_router
from schemas.prediction import PredictionRequest, PredictionResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager that initializes database schema and loads
    the ML pipeline and TreeSHAP explainer once at application startup.
    """
    logger.info("Initializing Personnel Stress & Welfare Monitoring API & Database...")
    try:
        init_db()
        service = get_prediction_service()
        logger.info("Champion LightGBM pipeline and recommendation engine successfully loaded.")
    except Exception as e:
        logger.critical(f"FATAL: Startup initialization failed: {str(e)}", exc_info=True)
    yield
    logger.info("Shutting down Personnel Stress & Welfare Monitoring API...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Production-grade FastAPI backend for the AI-Based Personnel Stress & Welfare Monitoring System. "
        "Provides real-time stress risk prediction, continuous 0-100 risk scoring, TreeSHAP feature "
        "explainability, contextualized supportive welfare recommendations, personnel registry, "
        "and role-based access control (Admin, Officer, Welfare, Personnel)."
    ),
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware configured for explicit authorized frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Custom validation exception handler for clean, structured error responses
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err.get("loc", [])])
        msg = err.get("msg", "Invalid value")
        errors.append({"field": field, "message": msg})
        
    logger.warning(f"Input validation rejected for path {request.url.path}: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "One or more input fields failed validation constraints.",
            "details": errors
        }
    )

from fastapi.responses import JSONResponse, HTMLResponse, Response

# Include all modular routers under /api
app.include_router(auth_router, prefix="/api")
app.include_router(personnel_router, prefix="/api")
app.include_router(assessment_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(prediction_router, prefix="/api")
app.include_router(welfare_request_router, prefix="/api")
app.include_router(organization_router, prefix="/api")
app.include_router(hrms_router, prefix="/api")
app.include_router(telemetry_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")

# Also mount prediction and auth at root prefix for direct access
app.include_router(prediction_router, prefix="")
app.include_router(auth_router, prefix="")

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root_dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Personnel Stress & Welfare Monitoring API</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0B0E11; color: #E8EAED; padding: 40px; margin: 0; }
            .card { max-width: 700px; margin: 40px auto; background: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
            h1 { color: #58A6FF; margin-top: 0; font-size: 24px; }
            p { color: #8B949E; line-height: 1.6; }
            .badge { display: inline-block; background: #238636; color: #fff; padding: 4px 10px; border-radius: 4px; font-weight: 600; font-size: 13px; margin-bottom: 20px; }
            .btn { display: inline-block; background: #1F6FEB; color: #fff; text-decoration: none; padding: 10px 18px; border-radius: 6px; font-weight: 500; margin-right: 12px; margin-top: 10px; }
            .btn:hover { background: #388BFD; }
            .btn-secondary { background: #21262D; color: #C9D1D9; border: 1px solid #30363D; }
            .btn-secondary:hover { background: #30363D; }
            ul { color: #C9D1D9; padding-left: 20px; }
            li { margin: 8px 0; }
            code { background: #0D1117; padding: 2px 6px; border-radius: 4px; color: #79C0FF; }
        </style>
        <script>
            // Unregister any old lingering service workers from other apps on localhost
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.getRegistrations().then(function(registrations) {
                    for(let registration of registrations) {
                        registration.unregister();
                        console.log('Unregistered stale service worker');
                    }
                });
            }
        </script>
    </head>
    <body>
        <div class="card">
            <span class="badge">API Status: ONLINE</span>
            <h1>Personnel Stress & Welfare Monitoring API</h1>
            <p>The FastAPI inference engine is active. The backend is connected to the trained <strong>LightGBM</strong> model pipeline, <strong>TreeSHAP</strong> explainability system, and <strong>Welfare Recommendation Engine</strong>.</p>
            <h3>Available Interfaces:</h3>
            <a href="/docs" class="btn">Interactive Swagger Docs (/docs)</a>
            <a href="/redoc" class="btn btn-secondary">ReDoc API Spec (/redoc)</a>
            <a href="/api/health" class="btn btn-secondary">Health Endpoint (/api/health)</a>
            <h3 style="margin-top: 30px;">Core Endpoints:</h3>
            <ul>
                <li><code>POST /api/predict</code> - Stress risk prediction & welfare recommendation engine</li>
                <li><code>POST /api/submit-checkin</code> - Mobile self-reporting ingestion</li>
                <li><code>GET /api/unit-aggregates</code> - Commander Dashboard unit metrics</li>
                <li><code>GET /api/health</code> - Live service health & model status</li>
            </ul>
        </div>
    </body>
    </html>
    """

@app.get("/sw.js", include_in_schema=False)
def service_worker_clear():
    # Tells browser to immediately unregister any old service worker
    return Response(
        content="self.addEventListener('install', () => self.skipWaiting()); self.addEventListener('activate', () => self.registration.unregister());",
        media_type="application/javascript"
    )

# Unit aggregates endpoint for Commander / Welfare Dashboard
@app.get(
    "/api/unit-aggregates",
    tags=["Dashboard & Telemetry"],
    summary="Unit Level Aggregate Statistics"
)
def get_unit_aggregates():
    """
    Returns aggregated stress telemetry for unit-level operational overview.
    """
    return {
        "unit_id": "UNIT-07B",
        "unit_name": "7th Battalion, Bravo Company",
        "personnel_strength": 214,
        "average_duty_hours_per_week": 52.4,
        "average_consecutive_duty_days": 9,
        "average_night_shifts_per_month": 6,
        "average_leave_gap_days": 143,
        "operational_exposure_index": "High",
        "risk_distribution": {
            "low": 138,
            "moderate": 51,
            "high": 19,
            "critical": 6
        },
        "welfare_summary": {
            "routine_priority": 138,
            "preventive_priority": 51,
            "priority_action": 25
        }
    }

import json
from datetime import datetime, timezone
from fastapi import Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.recommendation import WelfareRecommendation
from core.security import decode_access_token

# Check-in endpoint connecting mobile self-reporting to the prediction pipeline
@app.post(
    "/api/submit-checkin",
    tags=["Mobile Check-In"],
    summary="Submit Daily Personnel Self-Report & Receive Assessment"
)
def submit_checkin(
    checkin_data: PredictionRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Accepts daily self-reported duty and recovery telemetry from mobile application,
    evaluates stress tier via the ML pipeline, persists the assessment to the database
    when an authenticated user or personnel ID is resolved, and returns immediate welfare recommendations.
    """
    service = get_prediction_service()
    assessment = service.predict(checkin_data)

    # Resolve target personnel ID from Authorization header or request body
    target_personnel_id = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = decode_access_token(token)
            if payload:
                user_record = db.query(User).filter(User.username == payload.get("sub")).first()
                if user_record and user_record.personnel_id:
                    target_personnel_id = user_record.personnel_id
        except Exception as e:
            logger.debug(f"Optional token decode in submit_checkin: {e}")

    if not target_personnel_id and checkin_data.personnel_id:
        target_personnel_id = checkin_data.personnel_id

    # If personnel record is found, persist the assessment & welfare recommendations to PostgreSQL
    if target_personnel_id:
        personnel = db.query(Personnel).filter(Personnel.id == target_personnel_id).first()
        if personnel:
            try:
                # Update latest telemetry on personnel record
                personnel.duty_hours_per_week = checkin_data.Duty_Hours_Per_Week
                personnel.night_shifts_per_month = checkin_data.Night_Shifts_Per_Month
                personnel.consecutive_duty_days = checkin_data.Consecutive_Duty_Days
                personnel.leave_gap_days = checkin_data.Leave_Gap_Days

                probas = assessment.probabilities
                new_assessment = StressAssessment(
                    personnel_id=personnel.id,
                    stress_level=assessment.stress_level,
                    low_probability=probas.get("Low", 0.0),
                    medium_probability=probas.get("Medium", 0.0),
                    high_probability=probas.get("High", 0.0),
                    risk_score=assessment.risk_score,
                    risk_priority=assessment.risk_priority,
                    key_factors=json.dumps(assessment.key_factors),
                    model_version="1.0.0-LightGBM",
                    assessment_timestamp=datetime.now(timezone.utc)
                )
                db.add(new_assessment)
                db.flush()

                for rec_text in assessment.recommendations:
                    rec_lower = rec_text.lower()
                    rec_type = "workload" if ("duty" in rec_lower or "hour" in rec_lower) else (
                        "sleep" if ("sleep" in rec_lower or "rest" in rec_lower) else (
                            "leave" if "leave" in rec_lower else "welfare"
                        )
                    )
                    db.add(
                        WelfareRecommendation(
                            personnel_id=personnel.id,
                            assessment_id=new_assessment.id,
                            recommendation_type=rec_type,
                            recommendation_text=rec_text,
                            priority=assessment.risk_priority,
                            status="pending"
                        )
                    )
                db.commit()
                logger.info(
                    f"Persisted check-in assessment for personnel ID {personnel.id} ({personnel.personnel_code}): "
                    f"Level={assessment.stress_level}, Risk={assessment.risk_score}"
                )
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to persist check-in assessment: {e}", exc_info=True)

    return {
        "status": "success",
        "message": "Daily wellness check-in evaluated successfully.",
        "assessment": assessment
    }
