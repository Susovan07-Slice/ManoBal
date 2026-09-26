import os
import sys

# Add parent directory to path so src modules can be resolved
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.explain import StressModelExplainer

def get_explainer():
    """
    Returns an initialized instance of StressModelExplainer for the champion pipeline.
    """
    return StressModelExplainer()

if __name__ == '__main__':
    explainer = get_explainer()
    print("TreeSHAP Explainer successfully loaded and ready for inference explanations.")
