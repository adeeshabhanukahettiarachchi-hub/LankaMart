"""Train the Random Forest from the SQL database:  python backend/train_model.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.db import connect, ensure_database  # noqa: E402
from app.ml import train  # noqa: E402

if __name__ == "__main__":
    ensure_database()
    conn = connect()
    _, metrics = train(conn)
    conn.close()
    print(json.dumps(metrics, indent=2))
