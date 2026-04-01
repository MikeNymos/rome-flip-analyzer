"""Launcher script that patches os.getcwd for sandboxed environments."""
import os
import sys

# Patch os.getcwd to avoid PermissionError in sandboxed environments
PROJECT_DIR = "/Users/Mike/Desktop/Sandbox/rome-flip-analyzer"
os.chdir(PROJECT_DIR)

_original_getcwd = os.getcwd
def _safe_getcwd():
    try:
        return _original_getcwd()
    except PermissionError:
        return PROJECT_DIR
os.getcwd = _safe_getcwd

# Also add project dir to sys.path
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# Launch streamlit
from streamlit.web.cli import main
sys.argv = ["streamlit", "run", os.path.join(PROJECT_DIR, "app.py"),
            "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
main()
