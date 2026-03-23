import sys
import os

# Add backend directory to path so imports inside backend work
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.append(backend_path)

from main import app
