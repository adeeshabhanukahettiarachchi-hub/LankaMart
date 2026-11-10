import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.getenv("LANKAMART_DB", ROOT / "database" / "lankamart.db"))
SCHEMA_PATH = ROOT / "database" / "schema.sql"
SEED_PATH = ROOT / "database" / "seed.py"
MODEL_PATH = ROOT / "backend" / "models" / "late_delivery_rf.joblib"
METRICS_PATH = ROOT / "backend" / "models" / "metrics.json"
ALLOWED_ORIGINS = os.getenv("LANKAMART_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

CATEGORY_MARGIN = {"Electronics": 0.12, "Fashion": 0.30, "Home and Kitchen": 0.22,
                   "Beauty": 0.35, "Sports": 0.25}
LATE_THRESHOLD_DAYS = 5
