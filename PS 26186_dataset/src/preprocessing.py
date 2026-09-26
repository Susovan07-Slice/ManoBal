import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

def identify_feature_types(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """
    Identifies numerical and categorical features automatically.
    """
    numerical_features = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_features = df.select_dtypes(include=['object', 'category']).columns.tolist()
    return numerical_features, categorical_features

def build_preprocessor(
    numerical_features: List[str],
    categorical_features: List[str]
) -> ColumnTransformer:
    """
    Constructs an sklearn ColumnTransformer pipeline:
    - Numerical: Median imputation -> StandardScaler
    - Categorical: Most frequent imputation -> OneHotEncoder (handle_unknown='ignore')
    """
    num_pipeline = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    cat_pipeline = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', num_pipeline, numerical_features),
            ('cat', cat_pipeline, categorical_features)
        ],
        remainder='drop'
    )
    return preprocessor

def prepare_train_test_data(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Executes:
    1. Stratified train/test split.
    2. Feature type identification from X_train.
    3. Pipeline construction.
    4. Fitting preprocessor ONLY on X_train to prevent data leakage.
    5. Transforming X_train and X_test.
    """
    # 1. Stratified train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        stratify=y,
        random_state=random_state
    )

    # 2. Identify feature types
    num_features, cat_features = identify_feature_types(X_train)

    # 3. Build preprocessing pipeline
    preprocessor = build_preprocessor(num_features, cat_features)

    # 4. Fit ONLY on X_train
    X_train_processed = preprocessor.fit_transform(X_train)

    # 5. Transform X_test (no fitting)
    X_test_processed = preprocessor.transform(X_test)

    # 6. Extract processed feature names
    cat_encoder = preprocessor.named_transformers_['cat'].named_steps['encoder']
    cat_feature_names = cat_encoder.get_feature_names_out(cat_features).tolist()
    all_processed_feature_names = num_features + cat_feature_names

    return {
        "X_train_raw": X_train,
        "X_test_raw": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "X_train_processed": X_train_processed,
        "X_test_processed": X_test_processed,
        "numerical_features": num_features,
        "categorical_features": cat_features,
        "processed_feature_names": all_processed_feature_names,
        "preprocessor": preprocessor
    }
