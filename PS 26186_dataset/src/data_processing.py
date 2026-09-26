import os
import pandas as pd
from typing import Tuple, List

TARGET_COLUMN = 'Stress_Level'
PROVENANCE_COLUMNS = [
    'D3_HR_Features_Synthetic',
    'D4_Operational_Features_Synthetic'
]

def load_raw_dataset(filepath: str) -> pd.DataFrame:
    """
    Loads raw CSV dataset from specified path.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found at path: {filepath}")
    df = pd.read_csv(filepath)
    return df

def separate_features_and_target(
    df: pd.DataFrame,
    target_col: str = TARGET_COLUMN,
    drop_provenance: bool = True
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Separates the target column and removes provenance indicators and non-ML columns.
    Ensures zero target leakage.
    """
    df_clean = df.copy()

    if target_col not in df_clean.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe columns.")

    y = df_clean[target_col].copy()

    cols_to_drop = [target_col]
    if drop_provenance:
        for prov_col in PROVENANCE_COLUMNS:
            if prov_col in df_clean.columns:
                cols_to_drop.append(prov_col)

    # Check for any pure ID columns if present in future batches
    for col in df_clean.columns:
        if col.lower() in ['id', 'employee_id', 'service_id', 'personnel_id'] and col not in cols_to_drop:
            cols_to_drop.append(col)

    X = df_clean.drop(columns=cols_to_drop)

    return X, y
