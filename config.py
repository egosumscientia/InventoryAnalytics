import os
from pathlib import Path

# Root of the project
BASE_DIR = Path(__file__).resolve().parent

# Allow overriding paths via environment variables for portability
DATA_PATH = Path(os.getenv("INVENTORY_DATA_PATH", BASE_DIR / "data"))
REPORTS_PATH = Path(os.getenv("INVENTORY_REPORTS_PATH", BASE_DIR / "reports"))
