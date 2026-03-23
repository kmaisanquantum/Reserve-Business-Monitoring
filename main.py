import os
import sys
import importlib.util

# This is a proxy to allow Render to find the FastAPI app
# when the root directory is set to the repository root.
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))

# Add backend to path for internal imports to work (e.g. import config)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Load the actual main.py from the backend directory using a unique module name
# to avoid circular imports with the root-level main.py
spec = importlib.util.spec_from_file_location("backend_actual_main", os.path.join(backend_dir, "main.py"))
backend_actual_main = importlib.util.module_from_spec(spec)
sys.modules["backend_actual_main"] = backend_actual_main
spec.loader.exec_module(backend_actual_main)

app = backend_actual_main.app
