import joblib
import shap
import pandas as pd
import numpy as np

v2 = joblib.load('models/stress_risk_ensemble_v2.pkl')
lgb_model = v2.base_models['LightGBM']
preprocessor = v2.preprocessor
feature_names = preprocessor.get_feature_names_out()

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

explainer = shap.TreeExplainer(lgb_model)

idx_work = [i for i, fn in enumerate(feature_names) if 'Working_Hours_per_Week' in fn][0]
idx_duty = [i for i, fn in enumerate(feature_names) if 'Duty_Hours_Per_Week' in fn][0]
idx_ratio = [i for i, fn in enumerate(feature_names) if 'workload_intensity_ratio' in fn][0]
idx_recov = [i for i, fn in enumerate(feature_names) if 'active_recovery_ratio' in fn][0]

print(f"{'Hours':>5} | {'Score':>5} | {'P(Low)':>6} | {'P(Med)':>6} | {'P(High)':>7} | {'SHAP Work':>10} | {'SHAP Duty':>10} | {'SHAP Ratio':>10} | {'SHAP Recov':>10}")
print("-" * 85)

for h in [30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90]:
    rec = dict(base, Working_Hours_per_Week=float(h), Duty_Hours_Per_Week=float(h), duty_hours_per_week=float(h))
    df_single = pd.DataFrame([rec])
    X_aligned = v2._prepare_input(df_single)
    X_trans = preprocessor.transform(X_aligned)
    
    sv = explainer.shap_values(X_trans)
    sv_low = sv[0][0] if isinstance(sv, list) else sv[0, :, 0]
    sv_high = sv[2][0] if isinstance(sv, list) else sv[0, :, 2]
    
    res = v2.assess(rec)
    p_low = res["probabilities"]["Low"]
    p_med = res["probabilities"]["Medium"]
    p_high = res["probabilities"]["High"]
    sc = res["risk_score"]
    
    print(f"{h:5d} | {sc:5.1f} | {p_low:6.3f} | {p_med:6.3f} | {p_high:7.3f} | {sv_high[idx_work]:+10.4f} | {sv_high[idx_duty]:+10.4f} | {sv_high[idx_ratio]:+10.4f} | {sv_high[idx_recov]:+10.4f}")
