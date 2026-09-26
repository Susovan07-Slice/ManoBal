import pandas as pd
import numpy as np

ENGINEERED_FEATURES_INFO = [
    {
        "name": "workload_intensity_ratio",
        "formula": "(Working_Hours_per_Week + Duty_Hours_Per_Week) / 80.0",
        "reason": "Measures combined routine and duty hour burden normalized to a standard dual 40h operational baseline. Values > 1.0 reflect chronic workload strain."
    },
    {
        "name": "sleep_debt_index",
        "formula": "np.maximum(0, 8.0 - Sleep_Hours)",
        "reason": "Calculates nightly restorative sleep deficit from the healthy 8.0-hour physiological requirement. Directly correlates with cognitive fatigue and burnout."
    },
    {
        "name": "night_shift_burden",
        "formula": "Night_Shifts_Per_Month / (Consecutive_Duty_Days + 1.0)",
        "reason": "Evaluates circadian disruption density per duty cycle. Frequent night shifts combined with compressed duty intervals compound physiological stress."
    },
    {
        "name": "recovery_deficit_score",
        "formula": "Leave_Gap_Days / (Annual_Leaves_Taken + 1.0)",
        "reason": "Quantifies protracted intervals without restorative leave relative to annual leave usage. High scores flag personnel at imminent risk of exhaustion."
    },
    {
        "name": "active_recovery_ratio",
        "formula": "(Sleep_Hours + Physical_Activity_Hours_per_Week / 7.0) / (Working_Hours_per_Week / 7.0 + 1.0)",
        "reason": "Assesses daily wellness equilibrium by comparing restorative inputs (sleep + exercise) against daily work demand."
    },
    {
        "name": "deployment_fatigue_factor",
        "formula": "Deployment_Days * (Consecutive_Duty_Days / 7.0)",
        "reason": "Reflects operational endurance strain where prolonged field deployment is magnified by consecutive days without stand-down periods."
    }
]

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies domain-grounded feature engineering for personnel stress & welfare monitoring.
    Does NOT use the target column ('Stress_Level') to avoid data leakage.
    """
    df_feat = df.copy()

    # 1. Workload intensity ratio
    if 'Working_Hours_per_Week' in df_feat.columns and 'Duty_Hours_Per_Week' in df_feat.columns:
        df_feat['workload_intensity_ratio'] = (
            df_feat['Working_Hours_per_Week'] + df_feat['Duty_Hours_Per_Week']
        ) / 80.0

    # 2. Sleep debt index
    if 'Sleep_Hours' in df_feat.columns:
        df_feat['sleep_debt_index'] = np.maximum(0.0, 8.0 - df_feat['Sleep_Hours'])

    # 3. Night shift burden
    if 'Night_Shifts_Per_Month' in df_feat.columns and 'Consecutive_Duty_Days' in df_feat.columns:
        df_feat['night_shift_burden'] = df_feat['Night_Shifts_Per_Month'] / (
            df_feat['Consecutive_Duty_Days'] + 1.0
        )

    # 4. Recovery deficit score
    if 'Leave_Gap_Days' in df_feat.columns and 'Annual_Leaves_Taken' in df_feat.columns:
        df_feat['recovery_deficit_score'] = df_feat['Leave_Gap_Days'] / (
            df_feat['Annual_Leaves_Taken'] + 1.0
        )

    # 5. Active recovery ratio
    if all(col in df_feat.columns for col in ['Sleep_Hours', 'Physical_Activity_Hours_per_Week', 'Working_Hours_per_Week']):
        df_feat['active_recovery_ratio'] = (
            df_feat['Sleep_Hours'] + (df_feat['Physical_Activity_Hours_per_Week'] / 7.0)
        ) / ((df_feat['Working_Hours_per_Week'] / 7.0) + 1.0)

    # 6. Deployment fatigue factor
    if 'Deployment_Days' in df_feat.columns and 'Consecutive_Duty_Days' in df_feat.columns:
        df_feat['deployment_fatigue_factor'] = df_feat['Deployment_Days'] * (
            df_feat['Consecutive_Duty_Days'] / 7.0
        )

    return df_feat
