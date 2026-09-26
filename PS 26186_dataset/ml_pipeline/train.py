import os
import sys

# Add parent directory to path so root modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from train_models import main

if __name__ == '__main__':
    main()
