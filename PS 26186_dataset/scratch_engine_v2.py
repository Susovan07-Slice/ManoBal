import numpy as np
from scipy.special import expit

class PersonnelWelfareRiskEngineV2:
    def __init__(self):
        self.version = "risk_engine_v2"
        
    def evaluate(self, record, past_history=None):
        # 1. Assessment Completeness Check
        required_fields = ['duty_hours_per_week', 'sleep_hours', 'mood_score', 'physical_fatigue']
        present = sum(1 for f in required_fields if record.get(f) is not None)
        completeness = round(present / len(required_fields), 2)
        if completeness < 0.5:
            return {
                "error": "Insufficient assessment evidence",
                "completeness": completeness,
                "risk_score": None,
                "risk_category": "Insufficient Evidence"
            }

        # Safe extraction of Jawan assessment inputs
        duty = float(record.get('duty_hours_per_week', record.get('Duty_Hours_Per_Week', 44.0)))
        sleep = float(record.get('sleep_hours', record.get('Sleep_Hours', 7.0)))
        consec = float(record.get('consecutive_duty_days', record.get('Consecutive_Duty_Days', 4.0)))
        night = float(record.get('night_shifts_per_month', record.get('Night_Shifts_Per_Month', 2.0)))
        op_exp = str(record.get('operational_exposure', record.get('Operational_Exposure', 'Low'))).capitalize()
        leave_gap = float(record.get('leave_gap_days', record.get('Leave_Gap_Days', 30.0)))
        remote = str(record.get('remote_posting', record.get('Remote_Posting', 'No'))).capitalize()

        fatigue = float(record.get('physical_fatigue', 2.0))
        mood = float(record.get('mood_score', record.get('JobSatisfaction', 4.0)))
        burnout = str(record.get('burnout_symptoms', record.get('Burnout_Symptoms', 'Rarely'))).capitalize()
        interest = float(record.get('interest_score', 0.0))
        discouraged = float(record.get('discouraged_score', 0.0))
        concentration = float(record.get('concentration_score', 0.0))
        phys_act = float(record.get('physical_activity_hours_per_week', record.get('Physical_Activity_Hours_per_Week', 4.0)))

        # 2. Latent Current Welfare State Model (theta_state)
        # Normalized item scales [0, 1]
        z_fatigue = np.clip((fatigue - 1.0) / 4.0, 0.0, 1.0)
        z_sleep_def = np.clip((8.0 - sleep) / 5.0, 0.0, 1.0)
        z_mood_def = np.clip((5.0 - mood) / 4.0, 0.0, 1.0)
        z_burnout = 1.0 if burnout == 'Often' else (0.5 if burnout == 'Sometimes' else 0.0)
        z_interest = np.clip(interest / 3.0, 0.0, 1.0)
        z_discouraged = np.clip(discouraged / 3.0, 0.0, 1.0)
        z_concentration = np.clip(concentration / 3.0, 0.0, 1.0)
        z_protective_act = np.clip(phys_act / 8.0, 0.0, 1.0)

        # Psychometric latent factor aggregation:
        # Demoralization shares mood, discouraged, interest, concentration
        demoralization = 0.35 * z_mood_def + 0.25 * z_discouraged + 0.20 * z_interest + 0.20 * z_concentration
        # Somatic exhaustion shares fatigue and sleep deficit
        somatic = 0.55 * z_fatigue + 0.45 * z_sleep_def
        
        # Combined Latent Current State
        theta_state = 0.45 * somatic + 0.35 * demoralization + 0.25 * z_burnout - 0.12 * z_protective_act

        # 3. Operational Exposure Model (theta_exposure)
        z_duty = np.clip((duty - 36.0) / 54.0, 0.0, 1.0)
        z_consec = np.clip((consec - 2.0) / 24.0, 0.0, 1.0)
        z_night = np.clip(night / 16.0, 0.0, 1.0)
        z_op_exp = 1.0 if op_exp == 'High' else (0.45 if op_exp == 'Medium' else 0.0)
        z_leave_gap = np.clip((leave_gap - 14.0) / 180.0, 0.0, 1.0)
        z_remote = 0.20 if remote == 'Yes' else 0.0

        # Physiological circadian strain and recovery deficit interactions
        circadian_strain = z_night * (1.0 + 0.5 * z_consec)
        recovery_deficit = z_consec * z_leave_gap

        theta_exposure = (
            0.35 * z_duty +
            0.20 * z_consec +
            0.20 * circadian_strain +
            0.15 * z_op_exp +
            0.10 * recovery_deficit +
            z_remote
        )

        # 4. Risk Fusion Layer
        compound_interaction = theta_state * theta_exposure
        eta = 1.65 * theta_state + 1.25 * theta_exposure + 0.85 * compound_interaction - 0.75

        # 5. Ordinal Cumulative Probabilities (Proportional Odds)
        # Cutpoints tau for Moderate, Elevated, High, Critical
        tau = [-0.35, 0.40, 1.25, 2.10]
        scale = 1.8
        
        G = [expit(scale * (eta - t)) for t in tau]
        p_ge_mod = G[0]
        p_ge_elev = G[1]
        p_ge_high = G[2]
        p_ge_crit = G[3]

        p_low = max(0.0, 1.0 - p_ge_mod)
        p_mod = max(0.0, p_ge_mod - p_ge_elev)
        p_elev = max(0.0, p_ge_elev - p_ge_high)
        p_high = max(0.0, p_ge_high - p_ge_crit)
        p_crit = max(0.0, p_ge_crit)

        total_p = p_low + p_mod + p_elev + p_high + p_crit
        p_low /= total_p
        p_mod /= total_p
        p_elev /= total_p
        p_high /= total_p
        p_crit /= total_p

        probs = {
            'low': round(float(p_low), 3),
            'moderate': round(float(p_mod), 3),
            'elevated': round(float(p_elev), 3),
            'high': round(float(p_high), 3),
            'critical': round(float(p_crit), 3)
        }

        # 6. Continuous 0-100 Risk Score
        # Continuous cumulative integral across risk bands:
        # Band 0 (Low): [0, 25]
        # Band 1 (Moderate): [25, 45]
        # Band 2 (Elevated): [45, 65]
        # Band 3 (High): [65, 82]
        # Band 4 (Critical): [82, 100]
        continuous_score = (
            12.0 + 
            13.0 * expit(scale * eta) + 
            20.0 * p_ge_mod + 
            20.0 * p_ge_elev + 
            18.0 * p_ge_high + 
            17.0 * p_ge_crit
        )
        risk_score = round(float(np.clip(continuous_score, 0.0, 100.0)), 1)

        # 7. Category Mapping according to Initial Interpretation Bands:
        # 0-20: Very Low / Low
        # 20-40: Low
        # 40-60: Moderate
        # 60-75: Elevated
        # 75-90: High
        # 90-100: Critical
        if risk_score >= 85.0: category = 'Critical'
        elif risk_score >= 70.0: category = 'High'
        elif risk_score >= 55.0: category = 'Elevated'
        elif risk_score >= 35.0: category = 'Moderate'
        else: category = 'Low'

        # 8. Uncertainty & Confidence
        p_arr = np.array([p_low, p_mod, p_elev, p_high, p_crit])
        p_arr = np.clip(p_arr, 1e-6, 1.0)
        entropy = -np.sum(p_arr * np.log(p_arr)) / np.log(5.0)
        confidence = round(float(np.clip((1.0 - (entropy * 0.55)) * completeness, 0.1, 1.0)), 2)

        # 9. Dynamic Explainability: Contributing Evidence & Protective Factors
        top_risk_factors = []
        protective_factors = []

        if duty >= 52.0: top_risk_factors.append(f"Elevated duty schedule: {int(duty)} hrs/week")
        if sleep <= 6.0: top_risk_factors.append(f"Restricted restorative sleep: {sleep:.1f} hrs/night")
        if fatigue >= 3.0: top_risk_factors.append(f"Reported physical fatigue level: {int(fatigue)} / 5")
        if consec >= 7: top_risk_factors.append(f"Extended continuous duty: {int(consec)} days without 24h rest")
        if night >= 4: top_risk_factors.append(f"High night-shift frequency: {int(night)} shifts/month")
        if burnout in ['Often', 'Sometimes']: top_risk_factors.append(f"Burnout / overwhelm symptoms reported: {burnout}")
        if mood <= 2.0: top_risk_factors.append(f"Distressed morale / low mood: {int(mood)} / 5")
        if discouraged >= 2: top_risk_factors.append("Frequent feelings of discouragement / mental exhaustion")
        if concentration >= 2: top_risk_factors.append("Concentration difficulties on operational tasks")
        if op_exp in ['High', 'Medium']: top_risk_factors.append(f"Operational hazard exposure level: {op_exp}")

        if phys_act >= 4.0: protective_factors.append(f"Regular physical conditioning: {int(phys_act)} hrs/week")
        if sleep >= 7.0: protective_factors.append(f"Adequate restorative sleep: {sleep:.1f} hrs/night")
        if mood >= 4.0: protective_factors.append(f"Resilient morale & positive state: {int(mood)} / 5")
        if duty <= 46.0: protective_factors.append(f"Standard operational pacing: {int(duty)} hrs/week")
        if fatigue <= 2.0: protective_factors.append("Low baseline physical fatigue")

        return {
            'risk_score': risk_score,
            'risk_category': category,
            'probabilities': probs,
            'confidence': confidence,
            'assessment_completeness': completeness,
            'top_risk_factors': top_risk_factors[:4],
            'protective_factors': protective_factors[:3],
            'model_version': self.version
        }

if __name__ == '__main__':
    engine = PersonnelWelfareRiskEngineV2()
    print("=== 5 CANONICAL CONTROLLED PROFILES ===")
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
        '5. Critical concern': {
            'duty_hours_per_week': 86, 'sleep_hours': 3.5, 'consecutive_duty_days': 21,
            'night_shifts_per_month': 14, 'physical_fatigue': 5, 'mood_score': 1,
            'burnout_symptoms': 'Often', 'discouraged_score': 3, 'operational_exposure': 'High'
        }
    }

    for name, s in scenarios.items():
        res = engine.evaluate(s)
        print(f"\n{name}:")
        print(f"  Risk Score   : {res['risk_score']} / 100")
        print(f"  Category     : {res['risk_category']}")
        print(f"  Confidence   : {res['confidence']}")
        print(f"  Probabilities: {res['probabilities']}")
        print(f"  Top Factors  : {res['top_risk_factors']}")
        print(f"  Protective   : {res['protective_factors']}")

    # Monotonicity test: Work Hours
    print("\n=== MONOTONICITY: WORK HOURS (40 -> 90) ===")
    base = scenarios['1. Healthy'].copy()
    for h in [40, 50, 60, 70, 80, 90]:
        base['duty_hours_per_week'] = h
        res = engine.evaluate(base)
        print(f"  Hours={h:2d} -> Score={res['risk_score']:4.1f} | Category={res['risk_category']:<9} | Probs={res['probabilities']}")

    # Monotonicity test: Sleep
    print("\n=== MONOTONICITY: SLEEP HOURS (8 -> 4) ===")
    base = scenarios['1. Healthy'].copy()
    for s in [8.0, 7.0, 6.0, 5.0, 4.0]:
        base['sleep_hours'] = s
        res = engine.evaluate(base)
        print(f"  Sleep={s:3.1f} -> Score={res['risk_score']:4.1f} | Category={res['risk_category']:<9} | Probs={res['probabilities']}")
