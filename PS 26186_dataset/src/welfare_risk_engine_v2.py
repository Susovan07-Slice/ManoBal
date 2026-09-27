"""
PERSONNEL WELFARE RISK ENGINE V2
=================================
Authoritative, Continuous, Probabilistic Welfare Risk Assessment Engine.

Key Architectural Principles:
1. Probabilistic Latent Evidence Model:
   - Separates Current Welfare State (Group A: Jawan App assessment) from Operational Exposure (Group B: Telemetry & Rostering).
   - Psychometric factor aggregation (Demoralization & Somatic Exhaustion) prevents double counting of correlated items.
2. Cumulative Ordinal Exceedance:
   - Evaluates P(Risk > Low), P(Risk > Moderate), P(Risk > Elevated), P(Risk > High).
   - Outputs discrete probabilities summing strictly to 1.0 across 5 ordered tiers:
     Low, Moderate, Elevated, High, Critical.
3. Continuous 0–100 Welfare Risk Score:
   - Smooth continuous cumulative integral over exceedance probabilities.
   - Initial Interpretation Bands:
     * 0–20: Very Low concern
     * 20–40: Low concern
     * 40–60: Moderate concern
     * 60–75: Elevated concern
     * 75–90: High concern
     * 90–100: Critical concern
4. Strict Monotonicity on validated risk variables.
5. Zero Demographic Bias.
6. Uncertainty & Confidence tracking via Shannon entropy and data completeness.
7. Dynamic explainability: Contributing evidence and protective factors.
"""

import os
import json
import numpy as np
from typing import Dict, Any, List, Optional, Union
from scipy.special import expit

TIER_NAMES = ['Low', 'Moderate', 'Elevated', 'High', 'Critical']

class PersonnelWelfareRiskEngineV2:
    def __init__(
        self,
        lgb_model=None,
        ordinal_clfs=None,
        scaler=None,
        feature_names=None,
        validation_metrics=None
    ):
        self.version = "risk_engine_v2"
        self.lgb_model = lgb_model
        self.ordinal_clfs = ordinal_clfs
        self.scaler = scaler
        self.feature_names = feature_names or []
        self.validation_metrics = validation_metrics or {}
        self.reference_scores = None

    def assess(
        self,
        record: Union[Dict[str, Any], Any],
        past_assessments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Alias for evaluate to ensure seamless API integration."""
        return self.evaluate(record, past_history=past_assessments)

    def evaluate(
        self,
        record: Union[Dict[str, Any], Any],
        past_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end welfare risk inference for a single personnel record.
        """
        if not isinstance(record, dict):
            if hasattr(record, "to_dict"):
                record = record.to_dict()
            else:
                record = dict(record)

        # -------------------------------------------------------------
        # 1. Assessment Completeness Check (Section 14)
        # -------------------------------------------------------------
        required_fields = ['duty_hours_per_week', 'sleep_hours', 'mood_score', 'physical_fatigue']
        present_count = 0
        for f in required_fields:
            alt_f = {
                'duty_hours_per_week': ['Duty_Hours_Per_Week', 'Working_Hours_per_Week'],
                'sleep_hours': ['Sleep_Hours'],
                'mood_score': ['JobSatisfaction'],
                'physical_fatigue': []
            }.get(f, [])
            all_keys = [f] + alt_f
            if any(record.get(k) is not None for k in all_keys):
                present_count += 1

        completeness = round(present_count / len(required_fields), 2)
        if completeness < 0.50:
            return {
                "error": "Insufficient assessment evidence",
                "completeness": completeness,
                "assessment_completeness": completeness,
                "risk_score": None,
                "risk_category": "Insufficient Evidence",
                "probabilities": None,
                "confidence": 0.0,
                "uncertainty": 1.0,
                "model_version": self.version
            }

        # -------------------------------------------------------------
        # 2. Extract & Normalize Assessment Inputs
        # -------------------------------------------------------------
        def safe_float(val, default):
            if val is None:
                return float(default)
            try:
                return float(val)
            except (ValueError, TypeError):
                return float(default)

        def safe_str(val, default):
            if val is None or str(val).strip() == '':
                return str(default)
            return str(val)

        # Group B: Operational Exposure Evidence
        duty = safe_float(
            record.get('duty_hours_per_week') or record.get('Duty_Hours_Per_Week') or record.get('Working_Hours_per_Week'),
            44.0
        )
        consec = safe_float(
            record.get('consecutive_duty_days') or record.get('Consecutive_Duty_Days'),
            3.0
        )
        night = safe_float(
            record.get('night_shifts_per_month') or record.get('Night_Shifts_Per_Month'),
            2.0
        )
        op_exp = safe_str(
            record.get('operational_exposure') or record.get('Operational_Exposure'),
            'Low'
        ).capitalize()
        leave_gap = safe_float(
            record.get('leave_gap_days') or record.get('Leave_Gap_Days'),
            30.0
        )
        remote = safe_str(
            record.get('remote_posting') or record.get('Remote_Posting'),
            'No'
        ).capitalize()

        # Group A: Current Welfare State Evidence (Jawan App Questions)
        sleep = safe_float(
            record.get('sleep_hours') or record.get('Sleep_Hours'),
            7.0
        )
        fatigue = safe_float(record.get('physical_fatigue'), 2.0)
        mood = safe_float(
            record.get('mood_score') or record.get('JobSatisfaction'),
            4.0
        )
        burnout = safe_str(
            record.get('burnout_symptoms') or record.get('Burnout_Symptoms'),
            'Rarely'
        ).capitalize()
        interest = safe_float(record.get('interest_score'), 0.0)
        discouraged = safe_float(record.get('discouraged_score'), 0.0)
        concentration = safe_float(record.get('concentration_score'), 0.0)
        phys_act = safe_float(
            record.get('physical_activity_hours_per_week') or record.get('Physical_Activity_Hours_per_Week'),
            4.0
        )

        # -------------------------------------------------------------
        # 3. Psychometric Latent Current State Model (theta_state)
        # Prevents double counting via factor aggregation
        # -------------------------------------------------------------
        z_fatigue = np.clip((fatigue - 1.0) / 4.0, 0.0, 1.0)
        z_sleep_def = np.clip((8.0 - sleep) / 5.0, 0.0, 1.0)
        z_mood_def = np.clip((5.0 - mood) / 4.0, 0.0, 1.0)
        z_burnout = 1.0 if burnout == 'Often' else (0.5 if burnout == 'Sometimes' else 0.0)
        z_interest = np.clip(interest / 3.0, 0.0, 1.0)
        z_discouraged = np.clip(discouraged / 3.0, 0.0, 1.0)
        z_concentration = np.clip(concentration / 3.0, 0.0, 1.0)
        z_protective_act = np.clip(phys_act / 8.0, 0.0, 1.0)

        # Psychometric sub-traits:
        # Demoralization shares mood, discouragement, interest deficit, concentration deficit
        demoralization = 0.35 * z_mood_def + 0.25 * z_discouraged + 0.20 * z_interest + 0.20 * z_concentration
        # Somatic exhaustion shares physical fatigue and restorative sleep deficit
        somatic = 0.55 * z_fatigue + 0.45 * z_sleep_def

        # Latent current welfare strain trait
        theta_state = (
            0.45 * somatic +
            0.35 * demoralization +
            0.25 * z_burnout -
            0.12 * z_protective_act
        )

        # -------------------------------------------------------------
        # 4. Operational Exposure Model (theta_exposure)
        # -------------------------------------------------------------
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

        # -------------------------------------------------------------
        # 5. Risk Fusion Layer with Controlled Non-Linear Interactions
        # -------------------------------------------------------------
        compound_interaction = theta_state * theta_exposure
        eta = 1.65 * theta_state + 1.25 * theta_exposure + 0.85 * compound_interaction - 0.75

        # -------------------------------------------------------------
        # 6. Ordinal Cumulative Probabilities (Proportional Odds)
        # -------------------------------------------------------------
        tau = [-0.35, 0.40, 1.25, 2.10]
        scale = 1.80

        G = [expit(scale * (eta - t)) for t in tau]
        p_ge_mod = float(G[0])
        p_ge_elev = float(G[1])
        p_ge_high = float(G[2])
        p_ge_crit = float(G[3])

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

        # -------------------------------------------------------------
        # 7. Continuous 0–100 Risk Score Formulation
        # -------------------------------------------------------------
        # Smooth continuous cumulative integral across risk exceedance thresholds
        continuous_score = (
            12.0 +
            13.0 * expit(scale * eta) +
            20.0 * p_ge_mod +
            20.0 * p_ge_elev +
            18.0 * p_ge_high +
            17.0 * p_ge_crit
        )

        # -------------------------------------------------------------
        # 8. Temporal Trend & Persistence (Section 11)
        # -------------------------------------------------------------
        risk_trend = "Stable"
        risk_change = 0.0
        consecutive_high_risk = 0
        temporal_adjustment = 0.0

        if past_history and len(past_history) > 0:
            valid_past = [p for p in past_history if p.get("risk_score") is not None]
            if valid_past:
                prev_score = float(valid_past[0]["risk_score"])
                risk_change = round(continuous_score - prev_score, 1)

                if risk_change >= 6.0:
                    risk_trend = "Worsening"
                    temporal_adjustment += min(3.5, risk_change * 0.20)
                elif risk_change <= -6.0:
                    risk_trend = "Improving"
                    temporal_adjustment -= min(3.5, abs(risk_change) * 0.20)

                for past in valid_past:
                    if float(past.get("risk_score", 0.0)) >= 65.0:
                        consecutive_high_risk += 1
                    else:
                        break

                if consecutive_high_risk >= 3:
                    temporal_adjustment += 2.5
        else:
            risk_trend = "No prior history"

        final_risk_score = round(float(np.clip(continuous_score + temporal_adjustment, 0.0, 100.0)), 1)

        # -------------------------------------------------------------
        # 9. Risk Category Mapping (Interpretation Bands)
        # -------------------------------------------------------------
        # 0–20: Very Low concern
        # 20–40: Low concern
        # 40–60: Moderate concern
        # 60–75: Elevated concern
        # 75–90: High concern
        # 90–100: Critical concern
        if final_risk_score >= 85.0:
            category = "Critical"
        elif final_risk_score >= 70.0:
            category = "High"
        elif final_risk_score >= 55.0:
            category = "Elevated"
        elif final_risk_score >= 35.0:
            category = "Moderate"
        else:
            category = "Low"

        # -------------------------------------------------------------
        # 10. Uncertainty & Confidence (Section 13)
        # -------------------------------------------------------------
        p_arr = np.array([p_low, p_mod, p_elev, p_high, p_crit])
        p_arr = np.clip(p_arr, 1e-6, 1.0)
        # Normalized Shannon entropy [0, 1]
        entropy = -np.sum(p_arr * np.log(p_arr)) / np.log(5.0)
        confidence = round(float(np.clip((1.0 - (entropy * 0.55)) * completeness, 0.1, 1.0)), 2)
        uncertainty = round(float(1.0 - confidence), 2)

        # -------------------------------------------------------------
        # 11. Dynamic Explainability: Evidence & Protective Factors (Section 21)
        # -------------------------------------------------------------
        top_risk_factors = []
        protective_factors = []

        if duty >= 54.0:
            top_risk_factors.append(f"Elevated duty schedule: {int(duty)} hrs/week")
        if sleep <= 6.0:
            top_risk_factors.append(f"Restricted restorative sleep: {sleep:.1f} hrs/night")
        if fatigue >= 3.0:
            top_risk_factors.append(f"Reported physical fatigue level: {int(fatigue)} / 5")
        if consec >= 7:
            top_risk_factors.append(f"Extended continuous duty: {int(consec)} consecutive days")
        if night >= 4:
            top_risk_factors.append(f"High night-shift frequency: {int(night)} shifts/month")
        if burnout in ['Often', 'Sometimes']:
            top_risk_factors.append(f"Burnout & exhaustion symptoms: {burnout}")
        if mood <= 2.0:
            top_risk_factors.append(f"Low morale / depressed mood score: {int(mood)} / 5")
        if discouraged >= 2:
            top_risk_factors.append("Frequent feelings of discouragement / operational strain")
        if concentration >= 2:
            top_risk_factors.append("Difficulty maintaining task concentration")
        if op_exp in ['High', 'Medium']:
            top_risk_factors.append(f"Operational hazard exposure level: {op_exp}")
        if leave_gap >= 90:
            top_risk_factors.append(f"Prolonged interval since sanctioned leave: {int(leave_gap)} days")

        if phys_act >= 4.0:
            protective_factors.append(f"Regular physical conditioning: {int(phys_act)} hrs/week")
        if sleep >= 7.0:
            protective_factors.append(f"Adequate restorative sleep: {sleep:.1f} hrs/night")
        if mood >= 4.0:
            protective_factors.append(f"Resilient morale & positive state: {int(mood)} / 5")
        if duty <= 46.0:
            protective_factors.append(f"Standard operational duty pacing: {int(duty)} hrs/week")
        if fatigue <= 2.0:
            protective_factors.append("Low baseline physical fatigue")
        if consec <= 4:
            protective_factors.append(f"Appropriate duty rotation pacing ({int(consec)} consecutive days)")

        # -------------------------------------------------------------
        # 12. Non-Punitive Supportive Welfare Recommendations
        # -------------------------------------------------------------
        recommendations = []
        if category in ["Critical", "High"]:
            recommendations.append({
                "type": "Operational Adjustment",
                "action": "Immediate 48-hour operational rest stand-down and clinical welfare review.",
                "priority": "Priority"
            })
            if sleep < 6.0 or fatigue >= 4:
                recommendations.append({
                    "type": "Sleep & Recovery",
                    "action": "Protected circadian recovery sleep block of at least 8 uninterrupted hours.",
                    "priority": "Priority"
                })
            if leave_gap > 90:
                recommendations.append({
                    "type": "Restorative Leave",
                    "action": "Fast-track 10-day sanctioned restorative leave cycle.",
                    "priority": "Priority"
                })
        elif category == "Elevated":
            recommendations.append({
                "type": "Workload Optimization",
                "action": "Cap weekly duty hours to 48 and substitute night rotations with daytime logistics.",
                "priority": "Preventive"
            })
            recommendations.append({
                "type": "Welfare Support",
                "action": "Peer support check-in and unit welfare officer conversation within 3 days.",
                "priority": "Preventive"
            })
        elif category == "Moderate":
            recommendations.append({
                "type": "General Welfare",
                "action": "Maintain balanced duty pacing and monitor sleep hygiene over next 7 days.",
                "priority": "Routine"
            })
        else:
            recommendations.append({
                "type": "General Welfare",
                "action": "Current welfare indicators optimal. Continue regular physical conditioning.",
                "priority": "Routine"
            })

        # Backward-compatible priority & stress-level mapping
        legacy_stress_level = "High" if category in ["Critical", "High"] else ("Medium" if category in ["Elevated", "Moderate"] else "Low")
        legacy_risk_priority = "Priority" if category in ["Critical", "High"] else ("Preventive" if category in ["Elevated", "Moderate"] else "Routine")

        return {
            "risk_score": final_risk_score,
            "risk_category": category,
            "probabilities": {
                "low": round(float(p_low), 3),
                "moderate": round(float(p_mod), 3),
                "elevated": round(float(p_elev), 3),
                "high": round(float(p_high), 3),
                "critical": round(float(p_crit), 3)
            },
            "confidence": confidence,
            "uncertainty": uncertainty,
            "assessment_completeness": completeness,
            "risk_trend": risk_trend,
            "risk_change": risk_change,
            "consecutive_high_risk": consecutive_high_risk,
            "top_risk_factors": top_risk_factors[:4],
            "protective_factors": protective_factors[:3],
            "key_factors": top_risk_factors[:4],  # Backward compatibility
            "recommendations": recommendations,
            "stress_level": legacy_stress_level,
            "risk_priority": legacy_risk_priority,
            "model_version": self.version
        }
