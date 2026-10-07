import sys
from pathlib import Path

# Add the project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import the existing handler and expose it as `handler` for Vercel
from web_app import NexusContactAPIHandler as handler
