import joblib
from src.welfare_risk_engine_v2 import PersonnelWelfareRiskEngineV2

engine = joblib.load('models/welfare_risk_engine_v2.pkl')
scenarios = {
    '1. Healthy': {
        'duty_hours_per_week': 40, 'sleep_hours': 7.5, 'consecutive_duty_days': 2,
        'night_shifts_per_month': 2, 'physical_fatigue': 1, 'mood_score': 5,
        'burnout_symptoms': 'Rarely', 'physical_activity_hours_per_week': 6.0
    },
    '2. Mild concern': {
        'duty_hours_per_week': 48, 'sleep_hours': 6.5, 'consecutive_duty_days': 5,
        'night_shifts_per_month': 3, 'physical_fatigue': 2, 'mood_score': 4,
        'burnout_symptoms': 'Rarely', 'physical_activity_hours_per_week': 4.0
    },
    '3. Moderate concern': {
        'duty_hours_per_week': 56, 'sleep_hours': 6.0, 'consecutive_duty_days': 8,
        'night_shifts_per_month': 6, 'physical_fatigue': 3, 'mood_score': 3,
        'burnout_symptoms': 'Sometimes', 'physical_activity_hours_per_week': 3.0
    },
    '4. High concern': {
        'duty_hours_per_week': 72, 'sleep_hours': 4.5, 'consecutive_duty_days': 14,
        'night_shifts_per_month': 10, 'physical_fatigue': 4, 'mood_score': 2,
        'burnout_symptoms': 'Often', 'operational_exposure': 'High'
    },
    '5. Severe/critical concern': {
        'duty_hours_per_week': 86, 'sleep_hours': 3.5, 'consecutive_duty_days': 21,
        'night_shifts_per_month': 14, 'physical_fatigue': 5, 'mood_score': 1,
        'burnout_symptoms': 'Often', 'discouraged_score': 3, 'operational_exposure': 'High'
    }
}

for name, s in scenarios.items():
    res = engine.assess(s)
    print(f"Profile: {name}")
    print(f"  Risk Score: {res['risk_score']} / 100")
    print(f"  Risk Category: {res['risk_category']}")
    print(f"  Probabilities: {res['probabilities']}")
    print(f"  Confidence: {res['confidence']}")
    print(f"  Top Risk Factors: {res['top_risk_factors']}")
    print(f"  Protective Factors: {res['protective_factors']}")
    print()

print("--- Work-hours sweep (40 to 90) ---")
base = scenarios['1. Healthy'].copy()
for h in [40, 50, 60, 70, 80, 90]:
    base['duty_hours_per_week'] = h
    res = engine.assess(base)
    print(f"  Hours={h:2d} -> Score={res['risk_score']:4.1f} | Category={res['risk_category']:8s} | Probs={res['probabilities']}")

print("\n--- Work-hours sweep under Strained Conditions (40 to 90) ---")
base_strained = {
    'duty_hours_per_week': 40, 'sleep_hours': 5.5, 'consecutive_duty_days': 6,
    'night_shifts_per_month': 4, 'physical_fatigue': 3, 'mood_score': 3,
    'burnout_symptoms': 'Sometimes', 'physical_activity_hours_per_week': 2.0
}
for h in [40, 50, 60, 70, 80, 90]:
    base_strained['duty_hours_per_week'] = h
    res = engine.assess(base_strained)
    print(f"  Hours={h:2d} -> Score={res['risk_score']:4.1f} | Category={res['risk_category']:8s} | Probs={res['probabilities']}")

print("\n--- Missing Data Completeness Test ---")
incomplete_record = {'duty_hours_per_week': 50}
res_incomplete = engine.assess(incomplete_record)
print(f"  Incomplete record result: {res_incomplete}")

