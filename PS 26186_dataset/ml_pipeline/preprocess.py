import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

# Define the standard features common to both datasets
# These ensure compatibility between training and validation datasets
NUMERICAL_FEATURES = [
    'age',
    'sleep_hours',
    'duty_hours',
    'heart_rate_bpm',
    'fatigue_level'
]

CATEGORICAL_FEATURES = [
    'gender',
    'role',
    'location'
]

def get_preprocessor() -> ColumnTransformer:
    """
    Returns a scikit-learn ColumnTransformer that preprocesses 
    numerical and categorical features.
    """
    # Preprocessing for numerical data: 
    # Impute missing values with median, then standardize
    numerical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    # Preprocessing for categorical data: 
    # Impute missing values with most frequent, then one-hot encode
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    # Bundle preprocessing for numerical and categorical data
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, NUMERICAL_FEATURES),
            ('cat', categorical_transformer, CATEGORICAL_FEATURES)
        ],
        remainder='drop' # Drop columns not explicitly specified in features
    )

    return preprocessor

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform basic data cleaning on the dataframe (e.g. dropping complete duplicates)
    before it goes into the scikit-learn pipeline.
    """
    df_cleaned = df.copy()
    
    # Drop completely duplicated rows
    df_cleaned.drop_duplicates(inplace=True)
    
    # Ensure expected columns are present to avoid pipeline errors
    # If a feature is completely missing from a dataset, it will be imputed
    for col in NUMERICAL_FEATURES + CATEGORICAL_FEATURES:
        if col not in df_cleaned.columns:
            df_cleaned[col] = pd.NA
            
    return df_cleaned
