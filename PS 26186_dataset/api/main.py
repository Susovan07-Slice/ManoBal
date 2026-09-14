from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.schemas import DailyCheckIn

app = FastAPI(
    title="Personnel Stress Monitoring API",
    description="Backend API for the ML pipeline and frontend communication.",
    version="1.0.0"
)

# CORS middleware to allow requests from Next.js frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development (update in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/unit-aggregates")
def get_unit_aggregates():
    """
    Returns aggregated stress data for the Commander Dashboard.
    Currently returns dummy data structured for the frontend.
    """
    return {
        "unit_id": "UNIT-7",
        "total_personnel": 150,
        "critical_cases": 3,
        "high_risk_cases": 12,
        "average_stress_score": 45.2,
        "recent_alerts": [
            {
                "personnel_id": "P-104",
                "risk_level": "Critical",
                "timestamp": "2026-09-14T12:00:00Z"
            },
            {
                "personnel_id": "P-211",
                "risk_level": "High",
                "timestamp": "2026-09-14T10:30:00Z"
            }
        ]
    }

@app.post("/api/submit-checkin")
def submit_checkin(checkin_data: DailyCheckIn):
    """
    Receives daily check-in data from the Mobile App.
    Future ML Integration: This endpoint will load the model, run predictions
    on the incoming data, and return a computed risk score/alert.
    """
    # Placeholder response. 
    # The actual implementation will pass this data through the XGBoost model pipeline.
    return {
        "status": "success",
        "message": f"Check-in recorded successfully for personnel {checkin_data.personnel_id}",
        "received_data": checkin_data
    }
