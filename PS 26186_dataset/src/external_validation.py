import os
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)
from lightgbm import LGBMClassifier

from src.model_training import CLASS_NAMES, LABEL_TO_INT, INT_TO_LABEL

# Common feature definitions between Main and D2
COMMON_FEATURE_MAP_MAIN = {
    'Age': 'Age',
    'Gender': 'Gender',
    'Department': 'Department',
    'Job_Role': 'Job_Role',
    'Remote_Work': 'Remote_Work',
    'Sleep_Hours': 'Sleep_Hours',
    'Working_Hours_per_Week': 'Work_Hours_per_Week',
    'Physical_Activity_Hours_per_Week': 'Physical_Activity_Hrs',
    'Experience_Years': 'Work_Experience',
    'JobSatisfaction': 'Job_Satisfaction'
}

COMMON_NUMERICAL = [
    'Age',
    'Sleep_Hours',
    'Working_Hours_per_Week',
    'Physical_Activity_Hours_per_Week',
    'Experience_Years',
    'JobSatisfaction'
]

COMMON_CATEGORICAL = [
    'Gender',
    'Department',
    'Job_Role',
    'Remote_Work'
]

def load_and_inspect_d2(filepath: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Loads and inspects the external validation dataset D2_cleaned.csv.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"D2 dataset not found at: {filepath}")
        
    df_d2 = pd.read_csv(filepath)
    inspection_info = {
        "shape": df_d2.shape,
        "columns": df_d2.columns.tolist(),
        "missing_values": df_d2.isnull().sum().to_dict(),
        "duplicates": int(df_d2.duplicated().sum()),
        "stress_level_summary": df_d2['Stress_Level'].describe().to_dict()
    }
    return df_d2, inspection_info

def build_common_feature_pipeline(params: dict = None) -> Pipeline:
    """
    Builds an isolated preprocessing and model pipeline anchored strictly
    to features shared between Main and D2.
    """
    if params is None:
        params = {
            'class_weight': 'balanced',
            'random_state': 42,
            'verbose': -1,
            'learning_rate': 0.12,
            'max_depth': 4,
            'n_estimators': 200,
            'num_leaves': 15
        }
        
    num_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    cat_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', num_pipeline, COMMON_NUMERICAL),
            ('cat', cat_pipeline, COMMON_CATEGORICAL)
        ],
        remainder='drop'
    )
    
    model = LGBMClassifier(**params)
    
    return Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', model)
    ])

def prepare_common_data(main_train_df: pd.DataFrame, d2_df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray, pd.DataFrame, np.ndarray]:
    """
    Extracts common features and aligns target labels.
    D2 target is categorized using distribution-matched cutoffs (Low: <=5.1, Med: 5.1-6.7, High: >6.7).
    """
    # Main training features
    X_main_common = main_train_df[list(COMMON_FEATURE_MAP_MAIN.keys())].copy()
    y_main = main_train_df['Stress_Level'].copy()
    y_main_encoded = np.array([LABEL_TO_INT[v] for v in y_main])
    
    # Map D2 features to common names
    d2_aligned = d2_df.copy()
    # Invert mapping: D2 column -> Common Main name
    inv_map = {v: k for k, v in COMMON_FEATURE_MAP_MAIN.items()}
    d2_aligned.rename(columns=inv_map, inplace=True)
    X_d2_common = d2_aligned[list(COMMON_FEATURE_MAP_MAIN.keys())].copy()
    
    # Bin continuous Stress_Level in D2
    # Distribution matching Main (42.2% Low, 37.2% Med, 20.6% High)
    d2_stress = d2_df['Stress_Level']
    cut_low = float(d2_stress.quantile(0.422))
    cut_high = float(d2_stress.quantile(0.794))
    
    binned_d2 = pd.cut(
        d2_stress,
        bins=[-np.inf, cut_low, cut_high, np.inf],
        labels=['Low', 'Medium', 'High']
    )
    y_d2_encoded = np.array([LABEL_TO_INT[v] for v in binned_d2])
    
    return X_main_common, y_main_encoded, X_d2_common, y_d2_encoded

def run_external_validation(
    main_train_df: pd.DataFrame,
    d2_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Trains common-feature model strictly on Main Training data,
    evaluates strictly on unseen external D2 dataset.
    """
    X_tr, y_tr, X_val, y_val = prepare_common_data(main_train_df, d2_df)
    
    pipeline = build_common_feature_pipeline()
    pipeline.fit(X_tr, y_tr)
    
    preds = np.asarray(pipeline.predict(X_val)).ravel()
    
    acc = accuracy_score(y_val, preds)
    macro_f1 = f1_score(y_val, preds, average='macro', zero_division=0)
    weighted_f1 = f1_score(y_val, preds, average='weighted', zero_division=0)
    macro_prec = precision_score(y_val, preds, average='macro', zero_division=0)
    macro_rec = recall_score(y_val, preds, average='macro', zero_division=0)
    cm = confusion_matrix(y_val, preds, labels=[0, 1, 2])
    
    report_dict = classification_report(
        y_val,
        preds,
        labels=[0, 1, 2],
        target_names=CLASS_NAMES,
        output_dict=True,
        zero_division=0
    )
    report_text = classification_report(
        y_val,
        preds,
        labels=[0, 1, 2],
        target_names=CLASS_NAMES,
        zero_division=0
    )
    
    return {
        "pipeline": pipeline,
        "accuracy": acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "macro_precision": macro_prec,
        "macro_recall": macro_rec,
        "high_stress_precision": report_dict['High']['precision'],
        "high_stress_recall": report_dict['High']['recall'],
        "high_stress_f1": report_dict['High']['f1-score'],
        "confusion_matrix": cm,
        "classification_report_text": report_text,
        "classification_report_dict": report_dict
    }
