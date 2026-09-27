import os
import sys
import pandas as pd
import numpy as np

# Ensure root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.prediction_service import get_prediction_service
from src.prediction import PersonnelWelfarePredictor
from src.risk_scoring import calculate_risk_score

def run_audit():
    print("=" * 80)
    print("AUDITING RISK ENGINE: SENSITIVITY, MONOTONICITY & SCORE DRIFT")
    print("=" * 80)

    service = get_prediction_service()
    predictor = service.predictor
    is_v2 = predictor.is_v2
    print(f"Loaded predictor model_path: {predictor.model_path}")
    print(f"Is V2 model loaded: {is_v2}")

    baseline_record = {
        'Age': 28,
        'Gender': 'Male',
        'Marital_Status': 'Married',
        'Location': 'Field',
        'Job_Role': 'Rifleman',
        'Experience_Years': 5.0,
        'years_of_service': 5.0,
        'Monthly_Salary_INR': 52000.0,
        'Company_Size': 'Large',
        'Department': 'Operations',
        'Working_Hours_per_Week': 40.0,
        'Duty_Hours_Per_Week': 40.0,
        'duty_hours_per_week': 40.0,
        'Commute_Time_Hours': 0.5,
        'Remote_Work': 'No',
        'Annual_Leaves_Taken': 10,
        'leaves_taken_past_year': 10,
        'leave_balance_days': 20,
        'Team_Size': 30,
        'Health_Issues': '',
        'Sleep_Hours': 7.5,
        'Physical_Activity_Hours_per_Week': 5.0,
        'Mental_Health_Leave_Taken': 'No',
        'Burnout_Symptoms': 'Rarely',
        'BusinessTravel': 'Travel_Rarely',
        'DistanceFromHome': 15.0,
        'JobLevel': 2,
        'JobSatisfaction': 3,
        'mood_score': 3,
        'NumCompaniesWorked': 1,
        'OverTime': 'No',
        'PerformanceRating': 3,
        'RelationshipSatisfaction': 3,
        'TrainingTimesLastYear': 2,
        'training_load': 2,
        'WorkLifeBalance': 3,
        'YearsAtCompany': 5.0,
        'YearsInCurrentRole': 2.0,
        'YearsSinceLastPromotion': 2.0,
        'YearsWithCurrManager': 2.0,
        'Deployment_Days': 30,
        'Night_Shifts_Per_Month': 2,
        'Consecutive_Duty_Days': 4,
        'consecutive_days_on_duty': 4,
        'Transfer_Frequency': 0,
        'transfer_count': 0,
        'Leave_Gap_Days': 30,
        'Remote_Posting': 'No',
        'Operational_Exposure': 'Low',
        'physical_fatigue': 2,
        'interest_score': 0,
        'discouraged_score': 0,
        'concentration_score': 0,
        'has_hrms_record': 1
    }

    base_res = predictor.assess_personnel(baseline_record)
    print("\n--- BASELINE PREDICTION ---")
    print(f"Risk Score: {base_res['risk_score']}")
    print(f"Stress Level: {base_res['stress_level']}")
    print(f"Risk Probability: {base_res.get('risk_probability')}")
    print(f"Probabilities: {base_res['probabilities']}")
    print(f"Key Factors: {base_res['key_factors']}")

    # 1. Sweep Duty Hours
    print("\n" + "=" * 50)
    print("1. SWEEPING DUTY / WORKING HOURS PER WEEK:")
    print("=" * 50)
    hours_to_test = [35.0, 40.0, 45.0, 50.0, 51.0, 52.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 90.0]
    for h in hours_to_test:
        rec = dict(baseline_record)
        rec['Working_Hours_per_Week'] = h
        rec['Duty_Hours_Per_Week'] = h
        rec['duty_hours_per_week'] = h
        res = predictor.assess_personnel(rec)
        print(f"Hours: {h:4.1f} | Score: {res['risk_score']:5.1f} | Level: {res['stress_level']:6} | P(Low): {res['probabilities']['Low']:.3f} | P(Med): {res['probabilities']['Medium']:.3f} | P(High): {res['probabilities']['High']:.3f}")

    # 2. Sweep Sleep Hours
    print("\n" + "=" * 50)
    print("2. SWEEPING SLEEP HOURS:")
    print("=" * 50)
    sleep_to_test = [8.0, 7.5, 7.1, 7.0, 6.9, 6.5, 6.0, 5.5, 5.0, 4.5, 4.0, 3.5, 3.0]
    for s in sleep_to_test:
        rec = dict(baseline_record)
        rec['Sleep_Hours'] = s
        res = predictor.assess_personnel(rec)
        print(f"Sleep: {s:4.1f} | Score: {res['risk_score']:5.1f} | Level: {res['stress_level']:6} | P(Low): {res['probabilities']['Low']:.3f} | P(Med): {res['probabilities']['Medium']:.3f} | P(High): {res['probabilities']['High']:.3f}")

    # 3. Sweep Consecutive Duty Days
    print("\n" + "=" * 50)
    print("3. SWEEPING CONSECUTIVE DUTY DAYS:")
    print("=" * 50)
    days_to_test = [2, 4, 5, 7, 8, 10, 14, 18, 21, 25, 30]
    for d in days_to_test:
        rec = dict(baseline_record)
        rec['Consecutive_Duty_Days'] = d
        rec['consecutive_days_on_duty'] = d
        res = predictor.assess_personnel(rec)
        print(f"Consecutive Days: {d:2d} | Score: {res['risk_score']:5.1f} | Level: {res['stress_level']:6} | P(Low): {res['probabilities']['Low']:.3f} | P(Med): {res['probabilities']['Medium']:.3f} | P(High): {res['probabilities']['High']:.3f}")

    # 4. Sweep Night Shifts
    print("\n" + "=" * 50)
    print("4. SWEEPING NIGHT SHIFTS PER MONTH:")
    print("=" * 50)
    night_to_test = [0, 2, 4, 6, 8, 10, 12, 14, 16, 20]
    for n in night_to_test:
        rec = dict(baseline_record)
        rec['Night_Shifts_Per_Month'] = n
        res = predictor.assess_personnel(rec)
        print(f"Night Shifts: {n:2d} | Score: {res['risk_score']:5.1f} | Level: {res['stress_level']:6} | P(Low): {res['probabilities']['Low']:.3f} | P(Med): {res['probabilities']['Medium']:.3f} | P(High): {res['probabilities']['High']:.3f}")

    # 5. Check calculate_risk_score from src/risk_scoring.py
    print("\n" + "=" * 50)
    print("5. CHECKING src/risk_scoring.py calculate_risk_score:")
    print("=" * 50)
    dummy_probs = {'Low': 0.70, 'Medium': 0.25, 'High': 0.05}
    for h in [40.0, 45.0, 50.0, 60.0, 70.0, 80.0]:
        rec = dict(baseline_record)
        rec['Working_Hours_per_Week'] = h
        rec['Duty_Hours_Per_Week'] = h
        sc, lvl, prio = calculate_risk_score(dummy_probs, 'Low', rec)
        print(f"calculate_risk_score with Hours {h:4.1f}: Score={sc:5.1f}, Level={lvl}, Prio={prio}")

if __name__ == '__main__':
    run_audit()
