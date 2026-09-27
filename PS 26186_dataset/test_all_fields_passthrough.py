import joblib
import pandas as pd
import numpy as np

v2 = joblib.load('models/stress_risk_ensemble_v2.pkl')
with open('check_hours.py') as f:
    exec(f.read().split('print')[0])

fields = [
    ('duty_hours_per_week', [35.0, 40.0, 50.0, 60.0, 75.0]),
    ('night_shifts_per_month', [0, 2, 5, 10, 15]),
    ('consecutive_duty_days', [2, 4, 7, 14, 21]),
    ('leave_gap_days', [15, 30, 60, 120, 180]),
    ('sleep_hours', [8.0, 7.0, 6.0, 5.0, 4.0]),
    ('physical_activity_hours_per_week', [0.0, 2.0, 4.0, 6.0, 8.0]),
    ('operational_exposure', ['Low', 'Medium', 'High']),
    ('remote_posting', ['No', 'Yes']),
    ('mood_score', [5, 4, 3, 2, 1]),
    ('burnout_symptoms', ['Rarely', 'Sometimes', 'Often']),
    ('physical_fatigue', [1, 2, 3, 4, 5]),
    ('interest_score', [0, 1, 2, 3]),
    ('discouraged_score', [0, 1, 2, 3]),
    ('concentration_score', [0, 1, 2, 3])
]

print(f"{'Field':<35} | {'Val':<8} | {'Score':<6} | {'P(Low)':<6} | {'P(Med)':<6} | {'P(High)':<7}")
print('-' * 78)
for f_name, vals in fields:
    for val in vals:
        rec = dict(base)
        rec[f_name] = val
        if f_name == 'duty_hours_per_week':
            rec['Duty_Hours_Per_Week'] = val
            rec['Working_Hours_per_Week'] = val
        elif f_name == 'night_shifts_per_month':
            rec['Night_Shifts_Per_Month'] = val
        elif f_name == 'consecutive_duty_days':
            rec['Consecutive_Duty_Days'] = val
            rec['consecutive_days_on_duty'] = val
        elif f_name == 'leave_gap_days':
            rec['Leave_Gap_Days'] = val
            rec['leave_balance_days'] = val
        elif f_name == 'sleep_hours':
            rec['Sleep_Hours'] = val
        elif f_name == 'physical_activity_hours_per_week':
            rec['Physical_Activity_Hours_per_Week'] = val
        elif f_name == 'operational_exposure':
            rec['Operational_Exposure'] = val
        elif f_name == 'remote_posting':
            rec['Remote_Posting'] = val
        elif f_name == 'mood_score':
            rec['JobSatisfaction'] = val
            rec['RelationshipSatisfaction'] = val
        elif f_name == 'burnout_symptoms':
            rec['Burnout_Symptoms'] = val
            
        res = v2.assess(rec)
        print(f"{f_name:<35} | {str(val):<8} | {res['risk_score']:<6.1f} | {res['probabilities']['Low']:<6.3f} | {res['probabilities']['Medium']:<6.3f} | {res['probabilities']['High']:<7.3f}")
