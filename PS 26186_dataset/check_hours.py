import joblib
import os
import pandas as pd
import numpy as np

# Load models
v1 = joblib.load('models/final_stress_prediction_pipeline.pkl')
v2 = joblib.load('models/stress_risk_ensemble_v2.pkl')

base = {
    'Age': 28, 'Gender': 'Male', 'Marital_Status': 'Married', 'Location': 'Field',
    'Job_Role': 'Rifleman', 'Experience_Years': 5.0, 'years_of_service': 5.0,
    'Monthly_Salary_INR': 52000.0, 'Company_Size': 'Large', 'Department': 'Operations',
    'Working_Hours_per_Week': 40.0, 'Duty_Hours_Per_Week': 40.0, 'Commute_Time_Hours': 0.5,
    'Remote_Work': 'No', 'Annual_Leaves_Taken': 10, 'leaves_taken_past_year': 10,
    'leave_balance_days': 20, 'Team_Size': 30, 'Health_Issues': '', 'Sleep_Hours': 7.5,
    'Physical_Activity_Hours_per_Week': 5.0, 'Mental_Health_Leave_Taken': 'No',
    'Burnout_Symptoms': 'Rarely', 'BusinessTravel': 'Travel_Rarely', 'DistanceFromHome': 15.0,
    'JobLevel': 2, 'JobSatisfaction': 3, 'mood_score': 3, 'NumCompaniesWorked': 1,
    'OverTime': 'No', 'PerformanceRating': 3, 'RelationshipSatisfaction': 3,
    'TrainingTimesLastYear': 2, 'training_load': 2, 'Training_Load': 2, 'WorkLifeBalance': 3,
    'YearsAtCompany': 5.0, 'YearsInCurrentRole': 2.0, 'YearsSinceLastPromotion': 2.0,
    'YearsWithCurrManager': 2.0, 'Deployment_Days': 30, 'Night_Shifts_Per_Month': 2,
    'Consecutive_Duty_Days': 4, 'consecutive_days_on_duty': 4, 'Transfer_Frequency': 0,
    'transfer_count': 0, 'Leave_Gap_Days': 30, 'Remote_Posting': 'No',
    'Operational_Exposure': 'Low', 'physical_fatigue': 2, 'interest_score': 0,
    'discouraged_score': 0, 'concentration_score': 0, 'has_hrms_record': 1
}

print('=== V1 PIPELINE: SWEEPING Working_Hours_per_Week ONLY ===')
for h in [30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]:
    rec = dict(base, Working_Hours_per_Week=h)
    p = v1.predict_proba(pd.DataFrame([rec])).iloc[0].values
    print(f'H={h:2d} | Low={p[0]:.3f}, Med={p[1]:.3f}, High={p[2]:.3f}')

print('\n=== V1 PIPELINE: SWEEPING Duty_Hours_Per_Week ONLY ===')
for h in [30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]:
    rec = dict(base, Duty_Hours_Per_Week=h)
    p = v1.predict_proba(pd.DataFrame([rec])).iloc[0].values
    print(f'H={h:2d} | Low={p[0]:.3f}, Med={p[1]:.3f}, High={p[2]:.3f}')

print('\n=== V1 PIPELINE: SWEEPING BOTH Working_Hours AND Duty_Hours ===')
for h in [30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]:
    rec = dict(base, Working_Hours_per_Week=h, Duty_Hours_Per_Week=h)
    p = v1.predict_proba(pd.DataFrame([rec])).iloc[0].values
    print(f'H={h:2d} | Low={p[0]:.3f}, Med={p[1]:.3f}, High={p[2]:.3f}')

print('\n=== V2 ENSEMBLE: SWEEPING Duty_Hours_Per_Week ONLY ===')
for h in [30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90]:
    rec = dict(base, Duty_Hours_Per_Week=h)
    res = v2.assess(rec)
    print(f"H={h:2d} | Score={res['risk_score']:5.1f} | Low={res['probabilities']['Low']:.3f}, Med={res['probabilities']['Medium']:.3f}, High={res['probabilities']['High']:.3f}")

print('\n=== V2 ENSEMBLE: SWEEPING Working_Hours_per_Week ONLY ===')
for h in [30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90]:
    rec = dict(base, Working_Hours_per_Week=h)
    res = v2.assess(rec)
    print(f"H={h:2d} | Score={res['risk_score']:5.1f} | Low={res['probabilities']['Low']:.3f}, Med={res['probabilities']['Medium']:.3f}, High={res['probabilities']['High']:.3f}")

print('\n=== V2 ENSEMBLE: SWEEPING BOTH Working_Hours AND Duty_Hours ===')
for h in [30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90]:
    rec = dict(base, Working_Hours_per_Week=h, Duty_Hours_Per_Week=h, duty_hours_per_week=h)
    res = v2.assess(rec)
    print(f"H={h:2d} | Score={res['risk_score']:5.1f} | Low={res['probabilities']['Low']:.3f}, Med={res['probabilities']['Medium']:.3f}, High={res['probabilities']['High']:.3f}")
