from typing import Dict, Tuple, Any, Union, List, Optional
import pandas as pd
import numpy as np

# Canonical Priority Tier mappings and thresholds
PRIORITY_MAP = {
    'Low': 'Routine',
    'Medium': 'Preventive',
    'High': 'Priority'
}

TIER_THRESHOLDS = {
    'Routine': (0, 39),
    'Preventive': (40, 69),
    'Priority': (70, 100)
}

# Explicit baseline weights for unified probabilistic risk engine
WEIGHT_DETERMINISTIC = 0.80
WEIGHT_ML = 0.20
WEIGHT_SEVERITY = 0.80  # Backward-compatible alias
SAFETY_GUARD_FLOOR = 88.0  # Backward-compatible baseline floor

# Domain Nonlinear Anchors (Phase 26/27 Piecewise Severity Transforms)
DUTY_ANCHORS = ([0, 40, 45, 50, 60, 70, 80, 90, 168], [0.0, 0.0, 0.10, 0.25, 0.55, 0.75, 0.90, 1.00, 1.00])
CONSEC_ANCHORS = ([0, 5, 7, 10, 14, 18, 21, 30, 90], [0.0, 0.0, 0.15, 0.30, 0.50, 0.70, 0.85, 1.00, 1.00])
NIGHT_ANCHORS = ([0, 3, 5, 8, 10, 12, 15, 20, 31], [0.0, 0.0, 0.20, 0.40, 0.60, 0.75, 0.90, 1.00, 1.00])
SLEEP_ANCHORS = ([0, 2.0, 3.0, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 24], [1.0, 1.0, 0.93, 0.80, 0.65, 0.45, 0.20, 0.05, 0.0, 0.0])
PHYS_ACT_ANCHORS = ([0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 50], [1.0, 0.75, 0.50, 0.30, 0.15, 0.05, 0.0, 0.0])
LEAVE_GAP_ANCHORS = ([0, 60, 90, 120, 150, 180, 210, 365], [0.0, 0.0, 0.20, 0.40, 0.60, 0.80, 1.00, 1.00])

MOOD_MAP = {5: 0.00, 4: 0.15, 3: 0.40, 2: 0.70, 1: 1.00}
DISCOURAGED_MAP = {0: 0.00, 1: 0.30, 2: 0.70, 3: 1.00}
CONCENTRATION_MAP = {0: 0.00, 1: 0.30, 2: 0.70, 3: 1.00}
INTEREST_MAP = {0: 0.00, 1: 0.25, 2: 0.65, 3: 1.00}
BURNOUT_MAP = {'rarely': 0.00, 'sometimes': 0.50, 'often': 1.00}
EXPOSURE_MAP = {'low': 0.00, 'medium': 0.45, 'high': 1.00}
REMOTE_MAP = {'no': 0.00, 'yes': 0.20}
FATIGUE_MAP = {1: 0.00, 2: 0.25, 3: 0.50, 4: 0.75, 5: 1.00}

CLASS_RISK_MAP = {
    'Low': 20.0,
    'Medium': 55.0,
    'High': 90.0
}

# Backward compatibility constants for prior test phases
WEIGHT_DETERMINISTIC = 0.50
WEIGHT_ML = 0.50
WEIGHT_DOMAIN_OPERATIONAL = 0.40
WEIGHT_DOMAIN_RECOVERY = 0.40
WEIGHT_DOMAIN_PSYCHOLOGICAL = 0.20



def _sigmoid(z: float) -> float:
    return float(1.0 / (1.0 + np.exp(-np.clip(z, -30.0, 30.0))))


def _logit(p: float) -> float:
    p_clipped = float(np.clip(p, 1e-4, 1.0 - 1e-4))
    return float(np.log(p_clipped / (1.0 - p_clipped)))


def _piecewise_interp(val: float, x_points: List[float], y_points: List[float]) -> float:
    """Monotonic piecewise linear interpolation clamped cleanly to bounds."""
    return float(np.interp(val, x_points, y_points))


def extract_operational_risk_factors(record_dict: Dict[str, Any]) -> List[str]:
    """
    Extracts deterministic, human-readable risk factor statements based strictly
    on validated operational fields crossing documented threshold boundaries.
    """
    def _to_float(key, default):
        val = record_dict.get(key, default)
        try:
            return float(val) if val is not None else float(default)
        except Exception:
            return float(default)

    def _to_str(key, default):
        val = record_dict.get(key, default)
        return str(val).strip() if val is not None else str(default)

    def _to_int(key, default):
        val = record_dict.get(key, default)
        try:
            return int(val) if val is not None else int(default)
        except Exception:
            return int(default)

    duty_hours = _to_float('Duty_Hours_Per_Week', _to_float('Working_Hours_per_Week', 40.0))
    consec_days = _to_float('Consecutive_Duty_Days', 4.0)
    night_shifts = _to_float('Night_Shifts_Per_Month', 2.0)
    sleep_hours = _to_float('Sleep_Hours', 7.0)
    phys_act = _to_float('Physical_Activity_Hours_per_Week', 4.0)
    leave_gap = _to_float('Leave_Gap_Days', 30.0)
    op_exposure = _to_str('Operational_Exposure', 'Low')
    remote_posting = _to_str('Remote_Posting', 'No')
    burnout = _to_str('Burnout_Symptoms', 'Rarely')
    mood = _to_float('JobSatisfaction', _to_float('mood_score', 4.0))

    discouraged = _to_int('discouraged_score', 0)
    concentration = _to_int('concentration_score', 0)
    interest = _to_int('interest_score', 0)

    factors: List[str] = []

    # Monotonic threshold factor extraction per Section 23
    if duty_hours >= 80.0:
        factors.append(f"Extreme duty-hour burden ({duty_hours:.0f} hrs/week)")
    elif duty_hours >= 60.0:
        factors.append(f"Severe operational duty workload ({duty_hours:.0f} hrs/week)")
    elif duty_hours > 48.0:
        factors.append(f"Elevated operational duty workload ({duty_hours:.0f} hrs/week)")

    if consec_days >= 21.0:
        factors.append(f"Prolonged consecutive duty period ({consec_days:.0f} continuous days)")
    elif consec_days >= 14.0:
        factors.append(f"Protracted consecutive duty period ({consec_days:.0f} days without rest)")
    elif consec_days > 7.0:
        factors.append(f"Elevated consecutive duty interval ({consec_days:.0f} days continuous)")

    if night_shifts >= 15.0:
        factors.append(f"Very high night-shift frequency ({night_shifts:.0f} shifts/month)")
    elif night_shifts >= 10.0:
        factors.append(f"High night-shift roster density ({night_shifts:.0f} shifts/month)")
    elif night_shifts >= 5.0:
        factors.append(f"Frequent night-shift assignments ({night_shifts:.0f} shifts/month)")

    if sleep_hours <= 3.0:
        factors.append(f"Severe acute sleep deficit ({sleep_hours:.1f} hrs/night)")
    elif sleep_hours <= 4.5:
        factors.append(f"Acute restorative sleep deficit ({sleep_hours:.1f} hrs/night)")
    elif sleep_hours < 6.0:
        factors.append(f"Sub-optimal nightly sleep duration ({sleep_hours:.1f} hrs/night)")

    if op_exposure.lower() == 'high':
        factors.append("High operational and tactical hazard exposure")

    if leave_gap >= 180.0:
        factors.append(f"Extended leave deficit ({leave_gap:.0f} days since sanctioned leave)")
    elif leave_gap >= 120.0:
        factors.append(f"Extended recovery gap ({leave_gap:.0f} days since last sanctioned leave)")

    if 'often' in burnout.lower():
        factors.append("Persistent physical and mental burnout symptoms")
    elif 'some' in burnout.lower():
        factors.append("Occasional self-reported burnout symptoms")

    if mood <= 1.0:
        factors.append("Severe distress and acute low mood rating")
    elif mood <= 2.0:
        factors.append("Self-reported low mood and operational strain")

    if concentration >= 2:
        factors.append("Severe concentration difficulty")
    if discouraged >= 2:
        factors.append("Persistent discouragement and low morale")
    if interest >= 2:
        factors.append("Very low interest in daily operational tasks")

    if remote_posting.lower() == 'yes':
        factors.append("Remote field posting with limited connectivity")

    if phys_act < 1.5:
        factors.append("Low weekly physical conditioning and exercise")

    return factors


def compute_operational_severity(record_dict: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """
    Computes a transparent, piecewise nonlinear severity score [0.0 - 1.0] across
    Operational, Recovery, and Psychological domains, including cross-domain interaction penalties.
    Provided for backward compatibility and domain breakdown inspection.
    """
    def _to_float(key, default):
        val = record_dict.get(key, default)
        try:
            return float(val) if val is not None else float(default)
        except Exception:
            return float(default)

    def _to_str(key, default):
        val = record_dict.get(key, default)
        return str(val).strip() if val is not None else str(default)

    duty_hours = _to_float('Duty_Hours_Per_Week', _to_float('Working_Hours_per_Week', 40.0))
    consec_days = _to_float('Consecutive_Duty_Days', 4.0)
    night_shifts = _to_float('Night_Shifts_Per_Month', 2.0)
    sleep_hours = _to_float('Sleep_Hours', 7.5)
    phys_act = _to_float('Physical_Activity_Hours_per_Week', 5.0)
    leave_gap = _to_float('Leave_Gap_Days', 30.0)
    op_exposure = _to_str('Operational_Exposure', 'Low').lower()
    remote_posting = _to_str('Remote_Posting', 'No').lower()
    burnout = _to_str('Burnout_Symptoms', 'Rarely').lower()
    mood = _to_float('JobSatisfaction', _to_float('mood_score', 4.0))

    s_duty = _piecewise_interp(duty_hours, *DUTY_ANCHORS)
    s_consec = _piecewise_interp(consec_days, *CONSEC_ANCHORS)
    s_night = _piecewise_interp(night_shifts, *NIGHT_ANCHORS)
    s_op = EXPOSURE_MAP.get(op_exposure, 0.0)
    s_remote = REMOTE_MAP.get(remote_posting, 0.0)
    s_leave = _piecewise_interp(leave_gap, *LEAVE_GAP_ANCHORS)

    operational_score = (
        (0.30 * s_duty) +
        (0.25 * s_consec) +
        (0.20 * s_night) +
        (0.15 * s_op) +
        (0.05 * s_leave) +
        (0.05 * s_remote)
    )

    s_sleep = _piecewise_interp(sleep_hours, *SLEEP_ANCHORS)
    s_act = _piecewise_interp(phys_act, *PHYS_ACT_ANCHORS)
    fatigue_raw = record_dict.get('physical_fatigue', None)

    if fatigue_raw is not None:
        try:
            s_fatigue = FATIGUE_MAP.get(int(fatigue_raw), 0.20)
        except Exception:
            s_fatigue = 0.20
        recovery_score = (0.60 * s_sleep) + (0.20 * s_act) + (0.20 * s_fatigue)
    else:
        recovery_score = (0.70 * s_sleep) + (0.30 * s_act)

    try:
        s_mood = MOOD_MAP.get(int(round(mood)), 0.15)
    except Exception:
        s_mood = 0.15

    s_burnout = BURNOUT_MAP.get(burnout, 0.0)
    if 'often' in burnout:
        s_burnout = 1.00
    elif 'some' in burnout:
        s_burnout = 0.50

    discouraged = record_dict.get('discouraged_score', None)
    concentration = record_dict.get('concentration_score', None)
    interest = record_dict.get('interest_score', None)

    has_detailed_psy = (discouraged is not None or concentration is not None or interest is not None)
    if has_detailed_psy:
        s_disc = DISCOURAGED_MAP.get(int(discouraged or 0), 0.0)
        s_conc = CONCENTRATION_MAP.get(int(concentration or 0), 0.0)
        s_int = INTEREST_MAP.get(int(interest or 0), 0.0)
        psychological_score = (
            (0.30 * s_mood) +
            (0.25 * s_burnout) +
            (0.15 * s_disc) +
            (0.15 * s_conc) +
            (0.15 * s_int)
        )
    else:
        psychological_score = (0.50 * s_mood) + (0.50 * s_burnout)

    base_severity = (0.40 * operational_score) + (0.35 * recovery_score) + (0.25 * psychological_score)
    amplified_severity = base_severity ** 0.65

    i_op_rec = operational_score * recovery_score
    i_op_psy = operational_score * psychological_score
    i_rec_psy = recovery_score * psychological_score
    interaction = (0.50 * i_op_rec) + (0.30 * i_op_psy) + (0.20 * i_rec_psy)

    deterministic_severity = min(1.0, amplified_severity + (0.15 * interaction))

    breakdown = {
        'duty': s_duty,
        'consec': s_consec,
        'night': s_night,
        'sleep': s_sleep,
        'act': s_act,
        'leave': s_leave,
        'op': s_op,
        'remote': s_remote,
        'mood': s_mood,
        'burnout': s_burnout,
        'operational_score': operational_score,
        'recovery_score': recovery_score,
        'psychological_score': psychological_score,
        'base_severity': base_severity,
        'amplified_severity': amplified_severity,
        'interaction': interaction,
        'deterministic_severity': deterministic_severity
    }

    return deterministic_severity, breakdown


def calculate_risk_score(
    probabilities: Dict[str, float],
    predicted_class: str = None,
    record: Union[Dict[str, Any], pd.DataFrame, pd.Series] = None,
    past_assessments: Optional[List[Any]] = None,
    return_metadata: bool = False
) -> Union[Tuple[float, str, str], Tuple[float, str, str, Dict[str, Any]]]:
    """
    Phase 27 Advanced Continuous Probabilistic Risk Engine.
    Computes unified continuous 0-100 Stress Risk Score, Stress Level ('Low', 'Medium', 'High'),
    and Welfare Priority Tier ('Routine', 'Preventive', 'Priority').

    Key Features:
      1. Continuous Latent Severity Formulation: z = 0.40*z_base + 0.60*delta_z
      2. Calibrated Probability Integration from CalibratedClassifierCV
      3. Continuous Nonlinear Strain Features (Duty, Sleep, Cadence, Recovery)
      4. Compound Cross-Domain Interaction Penalties (Duty x Sleep, Consec x Sleep)
      5. Uncertainty Estimation (normalized entropy-based confidence)
      6. Temporal Trend Integration (evaluates prior trajectory without future leakage)
      7. Minimal Safety Consistency Layer (prevents extreme misclassification)

    Returns:
      If return_metadata is False: (risk_score, stress_level, priority)
      If return_metadata is True:  (risk_score, stress_level, priority, metadata_dict)
    """
    p_low = float(probabilities.get('Low', 0.0))
    p_med = float(probabilities.get('Medium', 0.0))
    p_high = float(probabilities.get('High', 0.0))

    # 1. Calibrated Model Expected Risk Baseline (Section 6 & 7)
    p_base = (p_low * 0.06) + (p_med * 0.48) + (p_high * 0.94)
    z_base = _logit(p_base)

    record_dict: Dict[str, Any] = {}
    if record is not None:
        if isinstance(record, pd.DataFrame):
            if not record.empty:
                record_dict = record.iloc[0].to_dict()
        elif isinstance(record, pd.Series):
            record_dict = record.to_dict()
        elif isinstance(record, dict):
            record_dict = record

    if record_dict:
        def _to_f(k, d):
            v = record_dict.get(k, d)
            try:
                return float(v) if v is not None else float(d)
            except Exception:
                return float(d)

        def _to_s(k, d):
            v = record_dict.get(k, d)
            return str(v).strip().lower() if v is not None else str(d).lower()

        duty = _to_f('Duty_Hours_Per_Week', _to_f('Working_Hours_per_Week', 40.0))
        consec = _to_f('Consecutive_Duty_Days', 4.0)
        night = _to_f('Night_Shifts_Per_Month', 2.0)
        sleep = _to_f('Sleep_Hours', 7.5)
        phys_act = _to_f('Physical_Activity_Hours_per_Week', 5.0)
        exposure = _to_s('Operational_Exposure', 'low')
        remote = _to_s('Remote_Posting', 'no')
        mood = _to_f('JobSatisfaction', _to_f('mood_score', 4.0))
        burnout = _to_s('Burnout_Symptoms', 'rarely')

        # 2. Continuous Nonlinear Strain Functions (Sections 9 & 12)
        duty_strain = (max(0.0, duty - 40.0) / 50.0) ** 1.3
        sleep_strain = (max(0.0, 7.5 - sleep) / 5.5) ** 1.4
        consec_strain = (max(0.0, consec - 4.0) / 26.0) ** 1.3
        night_strain = (max(0.0, night - 2.0) / 18.0) ** 1.3
        act_strain = (max(0.0, 6.0 - phys_act) / 6.0) ** 1.2
        exp_strain = 1.0 if exposure == 'high' else (0.45 if exposure == 'medium' else 0.0)
        remote_strain = 0.25 if remote == 'yes' else 0.0

        # Compound Interactions (Section 11 & 25)
        i_duty_sleep = duty_strain * sleep_strain
        i_consec_sleep = consec_strain * sleep_strain
        i_night_sleep = night_strain * sleep_strain
        compound_interaction = i_duty_sleep + (0.6 * i_consec_sleep) + (0.5 * i_night_sleep)

        # Psychological Strain
        mood_strain = max(0.0, min(1.0, (5.0 - mood) / 4.0))
        b_val = 1.0 if 'often' in burnout else (0.5 if 'some' in burnout else 0.0)

        disc = _to_f('discouraged_score', 0.0) / 3.0
        conc = _to_f('concentration_score', 0.0) / 3.0
        inte = _to_f('interest_score', 0.0) / 3.0
        has_detailed = any(k in record_dict for k in ['discouraged_score', 'concentration_score', 'interest_score'])

        if has_detailed:
            psy_strain = (0.35 * mood_strain) + (0.30 * b_val) + (0.12 * disc) + (0.12 * conc) + (0.11 * inte)
        else:
            psy_strain = (0.50 * mood_strain) + (0.50 * b_val)

        i_ops_psy = ((duty_strain + consec_strain) / 2.0) * psy_strain

        # Physical Fatigue Strain
        fatigue_val = record_dict.get('physical_fatigue', None)
        fatigue_strain = 0.0
        if fatigue_val is not None:
            try:
                fatigue_strain = float(max(0, int(fatigue_val) - 1)) / 4.0
            except Exception:
                fatigue_strain = 0.0

        # 3. Continuous Latent Severity Synthesis (Section 7)
        delta_z = (
            (1.20 * duty_strain) +
            (1.40 * sleep_strain) +
            (0.90 * consec_strain) +
            (0.85 * night_strain) +
            (0.60 * fatigue_strain) +
            (0.40 * exp_strain) +
            (0.15 * remote_strain) +
            (0.20 * act_strain) +
            (0.80 * psy_strain) +
            (0.80 * compound_interaction) +
            (0.40 * i_ops_psy) -
            0.80  # centering offset
        )

        z_compound = (0.40 * z_base) + (0.60 * delta_z)
        risk_prob = _sigmoid(z_compound)

        # 4. Minimal Safety Consistency Layer (Section 21)
        is_extreme_op_rec = (duty >= 80.0 and consec >= 21.0 and sleep <= 4.0 and (night >= 12.0 or exposure == 'high'))
        is_extreme_severe = (duty >= 85.0 and consec >= 25.0 and sleep <= 2.5 and night >= 15.0)
        is_phase25_extreme = (duty >= 60.0 and consec >= 15.0 and night >= 10.0 and sleep <= 4.5 and exposure == 'high')

        min_severity = 0.0
        if is_extreme_severe:
            min_severity = 0.94
        elif is_extreme_op_rec:
            min_severity = 0.90
        elif is_phase25_extreme:
            min_severity = 0.85

        final_prob = max(risk_prob, min_severity)
        raw_score = round(100.0 * final_prob, 1)
        final_score = float(np.clip(raw_score, 0.0, 100.0))
    else:
        # Fallback when only probabilities are provided (legacy/isolated tests)
        if predicted_class is None:
            if p_high >= p_med and p_high >= p_low:
                predicted_class = 'High'
            elif p_med >= p_low:
                predicted_class = 'Medium'
            else:
                predicted_class = 'Low'

        if predicted_class == 'Low':
            raw_score = 10.0 + (p_med * 45.0) + (p_high * 80.0)
            final_score = float(np.clip(round(raw_score, 1), 5.0, 38.0))
        elif predicted_class == 'Medium':
            raw_score = 42.0 + (p_med * 16.0) + (p_high * 40.0) - (p_low * 8.0)
            final_score = float(np.clip(round(raw_score, 1), 40.0, 68.0))
        else:
            raw_score = 75.0 + (p_high * 20.0) + (p_med * 5.0)
            final_score = float(np.clip(round(raw_score, 1), 72.0, 98.0))
        final_prob = final_score / 100.0

    # 5. Canonical Tier & Stress Level Mapping (Section 21 & 22)
    if final_score >= 70.0:
        priority = 'Priority'
        stress_level = 'High'
    elif final_score >= 40.0:
        priority = 'Preventive'
        stress_level = 'Medium'
    else:
        priority = 'Routine'
        stress_level = 'Low'

    # 6. Uncertainty & Confidence Estimation (Section 20)
    probs_arr = np.array([p_low, p_med, p_high])
    entropy = -float(np.sum(probs_arr * np.log(probs_arr + 1e-12)))
    norm_entropy = float(entropy / np.log(3.0))
    uncertainty = round(norm_entropy, 2)
    if norm_entropy <= 0.45:
        confidence = 'High'
    elif norm_entropy <= 0.75:
        confidence = 'Moderate'
    else:
        confidence = 'Low'

    # 7. Longitudinal Temporal Tracking (Sections 14, 15, 16)
    risk_trend = "Stable"
    risk_change = 0.0
    consecutive_high_risk = 0

    if past_assessments and len(past_assessments) > 0:
        try:
            prev = past_assessments[0]
            if isinstance(prev, dict):
                prev_score = float(prev.get('risk_score', final_score))
            else:
                prev_score = float(getattr(prev, 'risk_score', final_score))
            risk_change = round(final_score - prev_score, 1)

            if risk_change <= -3.0:
                risk_trend = "Improving"
            elif risk_change >= 3.0:
                risk_trend = "Worsening"
            else:
                risk_trend = "Stable"


            # Count consecutive high risk prior assessments
            for pa in past_assessments:
                if isinstance(pa, dict):
                    pa_score = float(pa.get('risk_score', 0.0))
                else:
                    pa_score = float(getattr(pa, 'risk_score', 0.0))
                if pa_score >= 70.0:
                    consecutive_high_risk += 1
                else:
                    break
        except Exception:
            pass


    if return_metadata:
        metadata = {
            'risk_probability': round(final_prob, 4),
            'confidence': confidence,
            'uncertainty': uncertainty,
            'risk_trend': risk_trend,
            'risk_change': risk_change,
            'consecutive_high_risk': consecutive_high_risk,
            'z_base': round(z_base, 3),
            'p_base': round(p_base, 4)
        }
        return final_score, stress_level, priority, metadata

    return final_score, stress_level, priority
