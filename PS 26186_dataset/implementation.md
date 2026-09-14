# ML Pipeline & Backend API — Personnel Stress Monitoring System

**Purpose:** Architectural blueprint for an AI coding agent to scaffold a Python Machine Learning environment and a FastAPI backend.
**Critical Data Rule:** The system contains two datasets: `FINAL_MAIN_STRESS_DATASET.csv` and `D2_cleaned.csv`. They must NEVER be merged. `FINAL_MAIN_STRESS_DATASET.csv` is exclusively for training/development. `D2_cleaned.csv` is exclusively for final external validation. 

## Phase 1: Project Setup & Structure
**Tech Stack:** Python 3.10+, FastAPI, Pandas, Scikit-learn, XGBoost, SHAP (for explainability).

**Folder Structure:**
/
  /data
    FINAL_MAIN_STRESS_DATASET.csv    # Place original file here
    D2_cleaned.csv                   # Place original file here
  /ml_pipeline
    preprocess.py                    # Handles scaling and encoding
    train.py                         # Trains model on FINAL_MAIN_STRESS_DATASET
    validate.py                      # Tests model on D2_cleaned
    explain.py                       # SHAP logic for Risk Explanation
  /api
    main.py                          # FastAPI server to connect to web/mobile apps
    schemas.py                       # Pydantic models for request/response
  /models
    # Saved .pkl files will go here
  requirements.txt

## Phase 2: Execution Rules
1. **Model Training (`train.py`):** Must read ONLY from `FINAL_MAIN_STRESS_DATASET.csv`. Apply a train/test split. Train an XGBoost or Random Forest classifier to output a Stress Risk Score (0-100) and Level (Low, Moderate, High, Critical). Save the pipeline as a `.pkl` file.
2. **External Validation (`validate.py`):** Must read ONLY from `D2_cleaned.csv`. Load the saved `.pkl` model. Evaluate performance using only features common to both datasets. 
3. **API (`main.py`):** Create a FastAPI server with two endpoints: `/api/unit-aggregates` (for the Commander Dashboard) and `/api/submit-checkin` (for the Mobile App). For now, these can return the dummy JSON schemas defined in the frontend, but structured so the ML model can easily plug into them later.

## Phase 3: Execution Prompts
(These will be fed sequentially to build the codebase).