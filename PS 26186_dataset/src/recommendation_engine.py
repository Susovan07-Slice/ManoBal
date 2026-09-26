from typing import List, Dict, Any
import pandas as pd

class WelfareRecommendationEngine:
    """
    Modular, transparent decision-support engine for personnel stress and welfare.
    Produces supportive, early-intervention recommendations based on:
      1. Stress Risk Level (Low, Medium, High)
      2. Key Contributing Operational & Clinical Factors
      3. Specific Threshold Signals in Raw Telemetry
    
    CRITICAL PRINCIPLE: All recommendations are supportive and intended for
    decision support; none are punitive, disciplinary, or diagnostic.
    """
    def __init__(self):
        self.base_tier_recommendations = {
            'Low': [
                "Continue routine welfare monitoring and periodic voluntary check-ins.",
                "Maintain healthy restorative sleep habits and unit physical conditioning.",
                "Encourage participation in ongoing wellness and resilience workshops."
            ],
            'Medium': [
                "Review workload pacing and upcoming roster assignments with section lead.",
                "Encourage adequate nightly rest and prioritize scheduled duty breaks.",
                "Offer a voluntary peer-support check-in this week.",
                "Monitor night-shift cadence to prevent continuous circadian strain."
            ],
            'High': [
                "Schedule a prioritized, confidential welfare interview within 48 hours.",
                "Conduct an immediate operational workload and recovery requirements audit.",
                "Recommend an authorized sanctioned leave block (5+ days) within 2 weeks.",
                "Rotate personnel out of high-intensity night-shift rosters for next cycle."
            ]
        }

    def generate_recommendations(
        self,
        risk_level: str,
        key_factors: List[str],
        record: pd.DataFrame = None,
        max_recommendations: int = 4
    ) -> List[str]:
        """
        Generates contextualized welfare recommendations tailored to tier and risk factors.
        """
        recommendations = []
        
        # 1. Start with core tier-specific baseline action
        base_recs = self.base_tier_recommendations.get(risk_level, self.base_tier_recommendations['Low'])
        recommendations.append(base_recs[0])
        
        # 2. Extract record-level metrics if available for factor triggers
        record_dict = {}
        if record is not None and not record.empty:
            record_dict = record.iloc[0].to_dict()
            
        factors_text = " ".join(key_factors).lower()
        
        # Rule A: Sleep Deficit Trigger
        sleep_val = float(record_dict.get('Sleep_Hours', 7.0))
        if 'sleep' in factors_text or sleep_val < 5.5:
            rec = "Enforce mandatory minimum rest windows between shifts to support sleep recovery."
            if rec not in recommendations:
                recommendations.append(rec)
                
        # Rule B: Duty & Workload Strain Trigger
        duty_hours = float(record_dict.get('Duty_Hours_Per_Week', 40.0))
        work_hours = float(record_dict.get('Working_Hours_per_Week', 40.0))
        if 'duty' in factors_text or 'workload' in factors_text or duty_hours > 55.0 or work_hours > 52.0:
            rec = "Review secondary task allocations and balance shift workload across section personnel."
            if rec not in recommendations:
                recommendations.append(rec)
                
        # Rule C: Night Shift Burden Trigger
        night_shifts = float(record_dict.get('Night_Shifts_Per_Month', 2.0))
        if 'night' in factors_text or night_shifts >= 6.0:
            rec = "Introduce circadian decompression intervals following consecutive night rotations."
            if rec not in recommendations:
                recommendations.append(rec)
                
        # Rule D: Consecutive Duty & Stand-down Days
        consec_days = float(record_dict.get('Consecutive_Duty_Days', 4.0))
        if 'consecutive' in factors_text or consec_days >= 8.0:
            rec = "Schedule an immediate 48-hour stand-down rest period following extended duty cycle."
            if rec not in recommendations:
                recommendations.append(rec)
                
        # Rule E: Leave Gap & Entitlement Recovery
        leave_gap = float(record_dict.get('Leave_Gap_Days', 30.0))
        if 'leave' in factors_text or leave_gap > 90.0:
            rec = "Expedite pending annual leave application; personnel exceeds recommended duty interval without leave."
            if rec not in recommendations:
                recommendations.append(rec)
                
        # Rule F: Deployment Strain Trigger
        dep_days = float(record_dict.get('Deployment_Days', 0.0))
        if 'deployment' in factors_text or dep_days > 120.0:
            rec = "Conduct post-deployment decompression assessment and assess readiness for rotation."
            if rec not in recommendations:
                recommendations.append(rec)
                
        # Rule G: Physical Health Indicators
        health_issue = str(record_dict.get('Health_Issues', ''))
        if health_issue and health_issue.lower() not in ['nan', '', 'none']:
            rec = f"Coordinate clinical follow-up with unit medical officer for reported health condition ({health_issue})."
            if rec not in recommendations:
                recommendations.append(rec)

        # 3. Fill remaining slots from tier recommendations if needed
        for rec in base_recs[1:]:
            if len(recommendations) < max_recommendations and rec not in recommendations:
                recommendations.append(rec)
                
        return recommendations[:max_recommendations]
