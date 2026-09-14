# ManoBal 🛡️
**AI-Based Personnel Stress and Welfare Monitoring System**

**Smart India Hackathon (SIH) 2026**
**Problem Statement:** PS 26186

ManoBal (translating to "Mental Strength" or "Morale") is a comprehensive, proactive AI system designed to monitor and support the psychological welfare and operational readiness of uniformed personnel. By analyzing duty rotations, sleep patterns, and self-reported assessments, ManoBal identifies early indicators of operational burnout and stress, allowing commanding officers to intervene before crises occur.

## 🏗️ System Architecture (Monorepo)

This repository contains the complete end-to-end system, divided into three isolated micro-architectures to ensure clean data flow and separation of concerns:

### 1. `/PS 26186` (Commander Web Dashboard)
*   **Target User:** Commanding Officers and Unit Welfare Officers.
*   **Tech Stack:** Next.js (App Router), React, Tailwind CSS, Recharts.
*   **Functionality:** A desktop-optimized web interface that displays unit-level stress aggregates, AI-generated risk alerts, and SHAP-based explanations for individual personnel flags.

### 2. `/PS 26186_app` (Jawan Mobile Interface)
*   **Target User:** Uniformed Personnel (Jawans).
*   **Tech Stack:** Next.js (Mobile-constrained web app), Tailwind CSS.
*   **Functionality:** A low-friction, calming mobile interface for daily check-ins (sleep, fatigue, operational workload) and clinical-style assessments. Includes an always-accessible, two-step SOS welfare request workflow.

### 3. `/PS 26186_dataset` (ML Backend & API)
*   **Target User:** System integration and data pipeline.
*   **Tech Stack:** Python 3.10+, FastAPI, Pandas, Scikit-learn, XGBoost, SHAP.
*   **Functionality:** The machine learning engine and REST API. It ingests the personnel data, calculates the Stress Risk Score (0-100), and serves the inferences to the frontends.

---

## 📊 Machine Learning Data Strategy (Judge's Note)

To ensure the highest standard of intellectual honesty and model generalization, our data pipeline strictly adheres to the following methodology:
*   **Training & Development:** `FINAL_MAIN_STRESS_DATASET.csv` is used exclusively for EDA, feature engineering, hyperparameter tuning, and cross-validation.
*   **External Validation:** `D2_cleaned.csv` acts as a strictly independent validation dataset. It is **never** merged with the training data and is used only for final model evaluation to prove real-world generalization.

---

## 🚀 Local Setup & Installation

To run the full system locally, you will need three separate terminal windows.

Step 1: Start the ML Backend
```bash
cd "PS 26186_dataset"
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

The API will be available at http://localhost:8000

Step 2: Start the Commander Dashboard
Bash
cd "PS 26186"
npm install
npm run dev
The Web Dashboard will be available at http://localhost:3000

Step 3: Start the Jawan Mobile App
Bash
cd "PS 26186_app"
npm install
npm run dev -- -p 3001
The Mobile App will be available at http://localhost:3001 (Running on port 3001 prevents conflicts with the dashboard).
