import os
import sys
import numpy as np
import pandas as pd
import joblib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.risk_feature_audit import DEFAULT_BASELINE_RECORD

# Load V4 ensemble model
v4_m = joblib.load('models/stress_risk_ensemble_v4.pkl')

# Category centroids: c_low = 18.0, c_med = 52.0, c_high = 86.0
# Tier thresholds: Routine < 35.0, Preventive 35.0 - 69.0, Priority >= 69.0
C_LOW = 18.0
C_MED = 52.0
C_HIGH = 86.0
TH_PREVENTIVE = 35.0
TH_PRIORITY = 69.0

def evaluate_record(rec_in):
    rec = DEFAULT_BASELINE_RECORD.copy()
    rec.update(rec_in)
    
    # Ensure canonical aliases are synchronized
    duty = rec.get('Duty_Hours_Per_Week', rec.get('Working_Hours_per_Week', 40.0))
    rec['Duty_Hours_Per_Week'] = duty
    rec['Working_Hours_per_Week'] = duty
    rec['duty_hours_per_week'] = duty
    
    sleep = rec.get('Sleep_Hours', rec.get('sleep_hours', 7.5))
    rec['Sleep_Hours'] = sleep
    rec['sleep_hours'] = sleep
    
    consec = rec.get('Consecutive_Duty_Days', rec.get('consecutive_duty_days', 4))
    rec['Consecutive_Duty_Days'] = consec
    rec['consecutive_duty_days'] = consec
    rec['consecutive_days_on_duty'] = consec
    
    night = rec.get('Night_Shifts_Per_Month', rec.get('night_shifts_per_month', 2))
    rec['Night_Shifts_Per_Month'] = night
    rec['night_shifts_per_month'] = night
    
    mood = rec.get('mood_score', rec.get('JobSatisfaction', 4))
    rec['mood_score'] = mood
    rec['JobSatisfaction'] = mood
    
    fatigue = rec.get('physical_fatigue', 2)
    rec['physical_fatigue'] = fatigue
    
    # Grounded physiological synthesis for wearable features if not provided
    hr = np.clip(60.0 + fatigue * 4.8 + duty * 0.12 - sleep * 1.2, 52.0, 115.0)
    hrv = np.clip(75.0 - fatigue * 8.5 - duty * 0.15 + sleep * 2.5, 12.0, 95.0)
    sq = np.clip(92.0 - fatigue * 9.5 - night * 1.1, 20.0, 98.0)
    
    rec.update({
        'wearable_7d_observation_count': 7,
        'wearable_7d_data_available': 1,
        'wearable_7d_mean_heart_rate': hr,
        'wearable_7d_min_heart_rate': hr - 12.0,
        'wearable_7d_max_heart_rate': hr + 30.0,
        'wearable_7d_heart_rate_std': 8.5,
        'wearable_7d_mean_hrv_rmssd': hrv,
        'wearable_7d_min_hrv_rmssd': max(8.0, hrv - 14.0),
        'wearable_7d_hrv_rmssd_std': 6.0,
        'wearable_7d_mean_sleep_duration': sleep,
        'wearable_7d_min_sleep_duration': max(1.5, sleep - 1.5),
        'wearable_7d_sleep_duration_std': 0.8,
        'wearable_7d_mean_sleep_quality': sq,
        'wearable_7d_mean_step_count': max(2000.0, 9500.0 - fatigue * 600.0),
        'wearable_7d_mean_active_minutes': max(15.0, 55.0 - fatigue * 4.0),
        'wearable_30d_observation_count': 30,
        'wearable_30d_data_available': 1,
        'wearable_30d_mean_heart_rate': hr,
        'wearable_30d_min_heart_rate': hr - 12.0,
        'wearable_30d_max_heart_rate': hr + 30.0,
        'wearable_30d_heart_rate_std': 8.5,
        'wearable_30d_mean_hrv_rmssd': hrv,
        'wearable_30d_min_hrv_rmssd': max(8.0, hrv - 14.0),
        'wearable_30d_hrv_rmssd_std': 6.0,
        'wearable_30d_mean_sleep_duration': sleep,
        'wearable_30d_min_sleep_duration': max(1.5, sleep - 1.5),
        'wearable_30d_sleep_duration_std': 0.8,
        'wearable_30d_mean_sleep_quality': sq,
        'wearable_30d_mean_step_count': max(2000.0, 9500.0 - fatigue * 600.0),
        'wearable_30d_mean_active_minutes': max(15.0, 55.0 - fatigue * 4.0),
    })
    
    df_s = pd.DataFrame([rec])
    X_al = v4_m._prepare_input(df_s)
    X_tr = v4_m.preprocessor.transform(X_al)
    
    p_lgb = v4_m.base_models['LightGBM'].predict_proba(X_tr)[0]
    p_xgb = v4_m.base_models['XGBoost'].predict_proba(X_tr)[0]
    p_lr = v4_m.base_models['LogisticRegression'].predict_proba(X_tr)[0]
    
    Z = np.hstack([p_lgb, p_xgb, p_lr]).reshape(1, -1)
    raw_p = v4_m.meta_model.predict_proba(Z)[0]
    cal_p = v4_m.calibrator.predict_proba(Z)[0]
    
    p_l, p_m, p_h = cal_p[0], cal_p[1], cal_p[2]
    score = round(float(C_LOW * p_l + C_MED * p_m + C_HIGH * p_h), 1)
    
    if score >= TH_PRIORITY:
        category = "Priority"
    elif score >= TH_PREVENTIVE:
        category = "Preventive"
    else:
        category = "Routine"
        
    pred_class = ['Low', 'Medium', 'High'][int(np.argmax(cal_p))]
    
    return {
        'pred_class': pred_class,
        'raw_p': raw_p,
        'cal_p': cal_p,
        'risk_score': score,
        'category': category
    }

print("=" * 105)
print("PHASE: COMPLETE CRITICAL MONOTONICITY & SENSITIVITY TEST SUITE")
print("=" * 105)

# Test 1: Work Hours: 40 -> 50 -> 60 -> 70 -> 80 -> 90
print("\n--- TEST 1: WORK HOURS (40 -> 50 -> 60 -> 70 -> 80 -> 90) ---")
print(f"{'Work Hours':<12} | {'Raw Probs (L/M/H)':<24} | {'Calibrated Probs (L/M/H)':<28} | {'Risk Score':<12} | {'Category':<12}")
print("-" * 105)
for h in [40, 50, 60, 70, 80, 90]:
    r = evaluate_record({'Duty_Hours_Per_Week': float(h)})
    raw_s = f"{r['raw_p'][0]:.3f}/{r['raw_p'][1]:.3f}/{r['raw_p'][2]:.3f}"
    cal_s = f"{r['cal_p'][0]:.3f}/{r['cal_p'][1]:.3f}/{r['cal_p'][2]:.3f}"
    print(f"{h:<12d} | {raw_s:<24} | {cal_s:<28} | {r['risk_score']:<12.1f} | {r['category']:<12}")

# Test 2: Sleep: 8 -> 7 -> 6 -> 5 -> 4
print("\n--- TEST 2: SLEEP HOURS (8 -> 7 -> 6 -> 5 -> 4) ---")
print(f"{'Sleep Hours':<12} | {'Raw Probs (L/M/H)':<24} | {'Calibrated Probs (L/M/H)':<28} | {'Risk Score':<12} | {'Category':<12}")
print("-" * 105)
for s in [8.0, 7.0, 6.0, 5.0, 4.0]:
    r = evaluate_record({'Sleep_Hours': s})
    raw_s = f"{r['raw_p'][0]:.3f}/{r['raw_p'][1]:.3f}/{r['raw_p'][2]:.3f}"
    cal_s = f"{r['cal_p'][0]:.3f}/{r['cal_p'][1]:.3f}/{r['cal_p'][2]:.3f}"
    print(f"{s:<12.1f} | {raw_s:<24} | {cal_s:<28} | {r['risk_score']:<12.1f} | {r['category']:<12}")

# Test 3: Workload Score: low -> medium -> high
print("\n--- TEST 3: WORKLOAD SCORE (Low -> Medium -> High) ---")
print(f"{'Workload Tier':<14} | {'Raw Probs (L/M/H)':<24} | {'Calibrated Probs (L/M/H)':<28} | {'Risk Score':<12} | {'Category':<12}")
print("-" * 105)
workload_tiers = [
    ('Low (38h, load 1)', {'Duty_Hours_Per_Week': 38.0, 'Training_Load': 1}),
    ('Med (52h, load 2)', {'Duty_Hours_Per_Week': 52.0, 'Training_Load': 2}),
    ('High (72h, load 4)', {'Duty_Hours_Per_Week': 72.0, 'Training_Load': 4}),
]
for name, updates in workload_tiers:
    r = evaluate_record(updates)
    raw_s = f"{r['raw_p'][0]:.3f}/{r['raw_p'][1]:.3f}/{r['raw_p'][2]:.3f}"
    cal_s = f"{r['cal_p'][0]:.3f}/{r['cal_p'][1]:.3f}/{r['cal_p'][2]:.3f}"
    print(f"{name:<14} | {raw_s:<24} | {cal_s:<28} | {r['risk_score']:<12.1f} | {r['category']:<12}")

# Test 4: Job Satisfaction: high -> medium -> low
print("\n--- TEST 4: JOB SATISFACTION (High -> Medium -> Low) ---")
print(f"{'Satisfaction':<14} | {'Raw Probs (L/M/H)':<24} | {'Calibrated Probs (L/M/H)':<28} | {'Risk Score':<12} | {'Category':<12}")
print("-" * 105)
for js, label in [(5, 'High (5)'), (4, 'Good (4)'), (3, 'Medium (3)'), (2, 'Low (2)'), (1, 'Very Low (1)')]:
    r = evaluate_record({'mood_score': js, 'JobSatisfaction': js})
    raw_s = f"{r['raw_p'][0]:.3f}/{r['raw_p'][1]:.3f}/{r['raw_p'][2]:.3f}"
    cal_s = f"{r['cal_p'][0]:.3f}/{r['cal_p'][1]:.3f}/{r['cal_p'][2]:.3f}"
    print(f"{label:<14} | {raw_s:<24} | {cal_s:<28} | {r['risk_score']:<12.1f} | {r['category']:<12}")

# Test 5: Mental Health Score: healthy -> moderate -> poor
print("\n--- TEST 5: MENTAL HEALTH / WELLBEING SCORE (Healthy -> Moderate -> Poor) ---")
print(f"{'Wellbeing':<14} | {'Raw Probs (L/M/H)':<24} | {'Calibrated Probs (L/M/H)':<28} | {'Risk Score':<12} | {'Category':<12}")
print("-" * 105)
mh_tiers = [
    ('Healthy (all 0)', {'discouraged_score': 0, 'concentration_score': 0, 'interest_score': 0, 'Burnout_Symptoms': 'Rarely'}),
    ('Moderate (all 1)', {'discouraged_score': 1, 'concentration_score': 1, 'interest_score': 1, 'Burnout_Symptoms': 'Sometimes'}),
    ('Poor (all 3)', {'discouraged_score': 3, 'concentration_score': 3, 'interest_score': 3, 'Burnout_Symptoms': 'Often'}),
]
for name, updates in mh_tiers:
    r = evaluate_record(updates)
    raw_s = f"{r['raw_p'][0]:.3f}/{r['raw_p'][1]:.3f}/{r['raw_p'][2]:.3f}"
    cal_s = f"{r['cal_p'][0]:.3f}/{r['cal_p'][1]:.3f}/{r['cal_p'][2]:.3f}"
    print(f"{name:<14} | {raw_s:<24} | {cal_s:<28} | {r['risk_score']:<12.1f} | {r['category']:<12}")

# Test 6: Work Experience: test whether model behaves sensibly
print("\n--- TEST 6: WORK EXPERIENCE (1 -> 5 -> 10 -> 15 -> 20 -> 25 years) ---")
print(f"{'Experience':<14} | {'Raw Probs (L/M/H)':<24} | {'Calibrated Probs (L/M/H)':<28} | {'Risk Score':<12} | {'Category':<12}")
print("-" * 105)
for exp in [1.0, 5.0, 10.0, 15.0, 20.0, 25.0]:
    r = evaluate_record({'Experience_Years': exp, 'years_of_service': exp, 'Age': int(20 + exp)})
    raw_s = f"{r['raw_p'][0]:.3f}/{r['raw_p'][1]:.3f}/{r['raw_p'][2]:.3f}"
    cal_s = f"{r['cal_p'][0]:.3f}/{r['cal_p'][1]:.3f}/{r['cal_p'][2]:.3f}"
    print(f"{exp:<14.1f} | {raw_s:<24} | {cal_s:<28} | {r['risk_score']:<12.1f} | {r['category']:<12}")

# Test 7: Consecutive Duty / Deployment variables: normal -> elevated -> extreme
print("\n--- TEST 7: CONSECUTIVE DUTY & DEPLOYMENT (Normal -> Elevated -> Extreme) ---")
print(f"{'Deployment Tier':<16} | {'Raw Probs (L/M/H)':<24} | {'Calibrated Probs (L/M/H)':<28} | {'Risk Score':<12} | {'Category':<12}")
print("-" * 105)
dep_tiers = [
    ('Normal (consec 3, dep 15d)', {'Consecutive_Duty_Days': 3, 'Deployment_Days': 15}),
    ('Elevated (consec 12, dep 90d)', {'Consecutive_Duty_Days': 12, 'Deployment_Days': 90}),
    ('Extreme (consec 25, dep 200d)', {'Consecutive_Duty_Days': 25, 'Deployment_Days': 200}),
]
for name, updates in dep_tiers:
    r = evaluate_record(updates)
    raw_s = f"{r['raw_p'][0]:.3f}/{r['raw_p'][1]:.3f}/{r['raw_p'][2]:.3f}"
    cal_s = f"{r['cal_p'][0]:.3f}/{r['cal_p'][1]:.3f}/{r['cal_p'][2]:.3f}"
    print(f"{name:<16} | {raw_s:<24} | {cal_s:<28} | {r['risk_score']:<12.1f} | {r['category']:<12}")

# Test 8: Night / Irregular duty variables: normal -> elevated -> extreme
print("\n--- TEST 8: NIGHT / IRREGULAR SHIFTS (Normal -> Elevated -> Extreme) ---")
print(f"{'Night Duty Tier':<16} | {'Raw Probs (L/M/H)':<24} | {'Calibrated Probs (L/M/H)':<28} | {'Risk Score':<12} | {'Category':<12}")
print("-" * 105)
night_tiers = [
    ('Normal (1 night/mo)', {'Night_Shifts_Per_Month': 1}),
    ('Elevated (6 nights/mo)', {'Night_Shifts_Per_Month': 6}),
    ('Extreme (16 nights/mo)', {'Night_Shifts_Per_Month': 16}),
]
for name, updates in night_tiers:
    r = evaluate_record(updates)
    raw_s = f"{r['raw_p'][0]:.3f}/{r['raw_p'][1]:.3f}/{r['raw_p'][2]:.3f}"
    cal_s = f"{r['cal_p'][0]:.3f}/{r['cal_p'][1]:.3f}/{r['cal_p'][2]:.3f}"
    print(f"{name:<16} | {raw_s:<24} | {cal_s:<28} | {r['risk_score']:<12.1f} | {r['category']:<12}")
