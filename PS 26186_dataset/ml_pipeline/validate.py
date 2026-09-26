import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_processing import load_raw_dataset
from src.external_validation import load_and_inspect_d2, run_external_validation
from sklearn.model_selection import train_test_split

def main():
    print("=" * 70)
    print(" EXTERNAL VALIDATION (D2_cleaned.csv) ")
    print("=" * 70)
    
    main_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'FINAL_MAIN_STRESS_DATASET.csv')
    if not os.path.exists(main_path):
        main_path = os.path.join(os.path.dirname(__file__), '..', 'final_dataset.csv')
    main_df = load_raw_dataset(main_path)
    
    d2_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'D2_cleaned.csv')
    d2_df, d2_info = load_and_inspect_d2(d2_path)
    
    # Split Main dataset into Train/Test to guarantee zero contamination
    main_train, _ = train_test_split(main_df, test_size=0.2, stratify=main_df['Stress_Level'], random_state=42)
    
    print("Training Common-Feature Generalization Benchmark on Main training set...")
    results = run_external_validation(main_train, d2_df)
    
    print(f"\nD2 External Accuracy:     {results['accuracy']:.4f}")
    print(f"D2 External Macro F1:     {results['macro_f1']:.4f}")
    print(f"D2 High-Stress Recall:    {results['high_stress_recall']:.4f}")
    print(f"D2 High-Stress Precision: {results['high_stress_precision']:.4f}")
    print("\nClassification Report:")
    print(results['classification_report_text'])

if __name__ == '__main__':
    main()
