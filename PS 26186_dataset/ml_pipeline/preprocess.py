import os
import sys
import pandas as pd
from sklearn.compose import ColumnTransformer

# Add parent directory to path so src can be resolved
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.feature_engineering import engineer_features
from src.data_processing import separate_features_and_target, PROVENANCE_COLUMNS, TARGET_COLUMN
from src.preprocessing import identify_feature_types, build_preprocessor

def get_preprocessor(numerical_features=None, categorical_features=None) -> ColumnTransformer:
    """
    Returns an sklearn ColumnTransformer that preprocesses numerical and categorical features.
    """
    if numerical_features is None or categorical_features is None:
        # If not supplied, construct using default training feature set
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'FINAL_MAIN_STRESS_DATASET.csv')
        if not os.path.exists(data_path):
            data_path = os.path.join(os.path.dirname(__file__), '..', 'final_dataset.csv')
        sample_df = pd.read_csv(data_path)
        X, _ = separate_features_and_target(sample_df)
        X_fe = engineer_features(X)
        numerical_features, categorical_features = identify_feature_types(X_fe)
        
    return build_preprocessor(numerical_features, categorical_features)

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans data, removes provenance indicators, and executes domain feature engineering.
    """
    df_cleaned = df.copy()
    df_cleaned.drop_duplicates(inplace=True)
    
    # Drop provenance columns if present
    for prov_col in PROVENANCE_COLUMNS:
        if prov_col in df_cleaned.columns:
            df_cleaned.drop(columns=[prov_col], inplace=True)
            
    # Apply feature engineering
    df_cleaned = engineer_features(df_cleaned)
    return df_cleaned
