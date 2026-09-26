# Personnel Stress Monitoring Backend

This repository contains the Machine Learning pipeline and FastAPI backend for the Personnel Stress Monitoring System.

## Project Structure

- `data/`: Contains the raw datasets (place `FINAL_MAIN_STRESS_DATASET.csv` and `D2_cleaned.csv` here).
- `ml_pipeline/`: Contains the data preprocessing, model training (`train.py`), and validation scripts (`validate.py`).
- `models/`: Destination folder for trained model `.pkl` artifacts.
- `api/`: Contains the FastAPI application and Pydantic schemas.

## Running the FastAPI Server

To run the API server locally so that the Next.js frontend or mobile app can communicate with it, follow these steps:

### 1. Install Dependencies
Make sure you have installed the required Python packages defined in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 2. Start the Server
Run the development server on port 8005 (to avoid collisions with other local apps on port 8000):
```bash
python -m uvicorn api.main:app --reload --port 8005
```

### 3. Verify the Deployment
- The API will be active at: `http://localhost:8005`
- Interactive Swagger UI documentation: `http://localhost:8005/docs`
- ReDoc API Specification: `http://localhost:8005/redoc`
- Health check: `http://localhost:8005/api/health`

## Available Endpoints

- **`POST /api/predict`**: Evaluates real-time stress risk (0-100), outputs TreeSHAP factors, and generates welfare recommendations.
- **`GET /api/unit-aggregates`**: Returns aggregated telemetry for the Commander Dashboard.
- **`POST /api/submit-checkin`**: Accepts daily self-reported metrics from the mobile application.
- **`GET /api/health`**: Verifies backend health and in-memory model availability.
