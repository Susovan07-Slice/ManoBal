import pandas as pd
import numpy as np
from typing import Dict, List, Any
from src.explain import StressModelExplainer
from src.risk_scoring import extract_operational_risk_factors

FACTOR_DESCRIPTIONS = {
    'Sleep_Hours': 'Restorative sleep deficit (< 5.5 hrs/night)',
    'sleep_debt_index': 'Nightly sleep deficit from 8-hour restorative baseline',
    'Duty_Hours_Per_Week': 'Elevated operational duty workload (> 50 hrs/week)',
    'Working_Hours_per_Week': 'High weekly routine and task workload',
    'workload_intensity_ratio': 'Severe cumulative duty and routine workload burden',
    'Night_Shifts_Per_Month': 'Frequent night-shift roster assignments',
    'night_shift_burden': 'Elevated night-shift frequency per duty cycle',
    'Consecutive_Duty_Days': 'Prolonged consecutive duty period without stand-down days',
    'Leave_Gap_Days': 'Extended interval elapsed since last sanctioned leave',
    'Annual_Leaves_Taken': 'Low annual leave entitlement utilization',
    'recovery_deficit_score': 'Acute recovery deficit (long leave gap vs. low leave taken)',
    'Deployment_Days': 'Protracted field deployment duration',
    'deployment_fatigue_factor': 'Operational deployment endurance strain',
    'Physical_Activity_Hours_per_Week': 'Low weekly physical activity and exercise',
    'active_recovery_ratio': 'Imbalance between recovery inputs and workload demand',
    'Commute_Time_Hours': 'Extended daily commute transit duration',
    'Burnout_Symptoms_Often': 'Frequent self-reported burnout symptoms',
    'Burnout_Symptoms_Sometimes': 'Occasional self-reported burnout symptoms',
    'Health_Issues_Back Pain': 'Reported musculoskeletal issue (Back Pain)',
    'Health_Issues_Hypertension': 'Reported cardiovascular indicator (Hypertension)',
    'Health_Issues_Arthritis': 'Reported joint condition (Arthritis)',
    'Health_Issues_Migraine': 'Reported chronic headache/migraine condition',
    'Operational_Exposure_High': 'High operational exposure environment',
    'Remote_Posting_Yes': 'Remote or isolated field posting',
    'OverTime_Yes': 'Consistent overtime duty schedules',
    'Experience_Years': 'Early-career or service transition factor'
}

def extract_key_factors(
    explainer: StressModelExplainer,
    record: pd.DataFrame,
    top_k: int = 4
) -> List[str]:
    """
    Extracts top model-identified risk factors formatted as clear,
    human-readable statements for welfare monitoring decision support.
    Prioritizes real operational threshold violations, augmented by SHAP contributions.
    """
    human_factors: List[str] = []

    # 1. First extract direct validated operational threshold violations
    if record is not None and not record.empty:
        record_dict = record.iloc[0].to_dict()
        op_factors = extract_operational_risk_factors(record_dict)
        for f in op_factors:
            if f not in human_factors:
                human_factors.append(f)
            if len(human_factors) >= top_k:
                return human_factors[:top_k]

    # 2. Augment with TreeSHAP model explanation factors
    try:
        explanation = explainer.explain_single_record(record)
        contributing = explanation.get('contributing_model_factors', [])
        
        for item in contributing:
            feat = item['factor']
            readable = FACTOR_DESCRIPTIONS.get(feat, None)
            if not readable:
                for prefix, desc in FACTOR_DESCRIPTIONS.items():
                    if feat.startswith(prefix):
                        readable = desc
                        break
                if not readable:
                    readable = feat.replace('_', ' ')
                    
            if readable not in human_factors:
                human_factors.append(readable)
                
            if len(human_factors) >= top_k:
                break
    except Exception:
        pass
        
    # 3. Fallback if no specific factors identified
    if len(human_factors) == 0:
        human_factors.append("General baseline operational workload")
        
    return human_factors[:top_k]
