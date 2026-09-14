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
Run the `uvicorn` development server from the root directory of the project:
```bash
uvicorn api.main:app --reload --port 8000
```

### 3. Verify the Deployment
- The API will be active at: `http://localhost:8000`
- You can access the automatic interactive Swagger UI documentation at: `http://localhost:8000/docs`

## Available Endpoints

- **`GET /api/unit-aggregates`**: Returns aggregated statistics formatted for the Commander Dashboard.
- **`POST /api/submit-checkin`**: Accepts daily self-reported metrics from the mobile application. In production, this will trigger the XGBoost ML pipeline to evaluate real-time stress risk.
