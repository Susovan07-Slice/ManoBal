from typing import Dict, Tuple

PRIORITY_MAP = {
    'Low': 'Routine',
    'Medium': 'Preventive',
    'High': 'Priority'
}

def calculate_risk_score(probabilities: Dict[str, float], predicted_class: str = None) -> Tuple[int, str, str]:
    """
    Computes a standardized Stress Risk Score (0-100) and operational Welfare Priority.
    
    Tiers:
      0 - 39  : Low Risk    -> Priority: Routine
      40 - 69 : Medium Risk -> Priority: Preventive
      70 - 100: High Risk   -> Priority: Priority
    
    The score is calibrated continuously based on model predicted class probabilities.
    """
    p_low = float(probabilities.get('Low', 0.0))
    p_med = float(probabilities.get('Medium', 0.0))
    p_high = float(probabilities.get('High', 0.0))
    
    if predicted_class is None:
        if p_high >= p_med and p_high >= p_low:
            predicted_class = 'High'
        elif p_med >= p_low:
            predicted_class = 'Medium'
        else:
            predicted_class = 'Low'
            
    if predicted_class == 'Low':
        # Calibrated 5 - 38 based on certainty and distance to medium
        raw_score = 10.0 + (p_med * 45.0) + (p_high * 80.0)
        score = int(round(max(5.0, min(38.0, raw_score))))
        level = 'Low'
    elif predicted_class == 'Medium':
        # Calibrated 42 - 68 based on median certainty and high probability buffer
        raw_score = 42.0 + (p_med * 16.0) + (p_high * 40.0) - (p_low * 8.0)
        score = int(round(max(40.0, min(68.0, raw_score))))
        level = 'Medium'
    else:  # High
        # Calibrated 75 - 98 reflecting critical intervention need
        raw_score = 75.0 + (p_high * 20.0) + (p_med * 5.0)
        score = int(round(max(72.0, min(98.0, raw_score))))
        level = 'High'
        
    priority = PRIORITY_MAP[level]
    return score, level, priority
