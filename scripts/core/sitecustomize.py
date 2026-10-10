import os
import sys

# Add the "scripts" directory to the Python import path so that modules moved there can be imported
scripts_path = os.path.join(os.path.dirname(__file__), "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)
