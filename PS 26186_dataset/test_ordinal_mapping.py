import os
import sys
import pandas as pd
import numpy as np

# Test ordinal mapping
burnout_map = {'rarely': 0, 'sometimes': 1, 'often': 2}
exposure_map = {'low': 0, 'medium': 1, 'high': 2}
remote_map = {'no': 0, 'yes': 1}

print("Ordinal mapping defined:")
print("Burnout:", burnout_map)
print("Exposure:", exposure_map)
print("Remote:", remote_map)
