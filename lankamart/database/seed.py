"""Create the SQLite database and fill it with 1,200 SYNTHETIC LankaMart orders.

Usage:  python database/seed.py [--reset]
"""
import csv
import sqlite3
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DB_PATH = HERE / "lankamart.db"

# name: (min price LKR, max price LKR, gross margin)
CATEGORIES = {
    "Electronics": (15000, 90000, 0.12),
    "Fashion": (2500, 15000, 0.30),
    "Home and Kitchen": (3000, 25000, 0.22),
    "Beauty": (1500, 9000, 0.35),
    "Sports": (3500, 30000, 0.25),
}
CATEGORY_WEIGHTS = [0.22, 0.25, 0.20, 0.18, 0.15]
# name: effect on the log-odds of a late delivery
REGIONS = {"Western": -0.45, "Central": 0.0, "Southern": -0.05,
           "Northern": 0.55, "Eastern": 0.40, "North Western": 0.10}
REGION_WEIGHTS = [0.34, 0.14, 0.14, 0.08, 0.10, 0.20]
MONTH_WEIGHTS = np.array([8, 7, 8, 11, 8, 7, 8, 8, 8, 9, 11, 14], dtype=float)


def generate(n=1200, seed=42):
    rng = np.random.default_rng(seed)
    cats, regs = list(CATEGORIES), list(REGIONS)
    months = rng.choice(12, size=n, p=MONTH_WEIGHTS / MONTH_WEIGHTS.sum()) + 1
    days = rng.integers(1, 29, size=n)
    dates = sorted(f"2025-{m:02d}-{d:02d}" for m, d in zip(months, days))
    rows = []
    for i, date in enumerate(dates, start=1):
        cat = str(rng.choice(cats, p=CATEGORY_WEIGHTS))
        reg = str(rng.choice(regs, p=REGION_WEIGHTS))
        lo, hi, margin = CATEGORIES[cat]
        qty = int(rng.choice([1, 2, 3, 4, 5], p=[0.5, 0.25, 0.12, 0.08, 0.05]))
        price = float(round(rng.uniform(lo, hi) / 50) * 50)
        disc = float(rng.choice([0, 0.05, 0.10, 0.15, 0.20, 0.30],
                                p=[0.35, 0.20, 0.20, 0.12, 0.08, 0.05]))
        gross = price * qty
        sales = round(gross * (1 - disc), 2)
        profit = round(sales - gross * (1 - margin), 2)
        returned = int(rng.random() < (0.11 if cat == "Fashion" else 0.06))
        if returned:
            profit = round(-0.10 * sales, 2)
        logit = (-2.0 + 1.6 * REGIONS[reg] + (0.6 if cat == "Electronics" else 0.0)
                 + 0.35 * (qty - 1) + 3.0 * disc + rng.normal(0, 0.3))
        late = int(rng.random() < 1 / (1 + np.exp(-logit)))
        delivery = int(rng.integers(6, 10) if late else rng.integers(2, 6))
        rows.append((f"LM-{i:05d}", date, cat, reg, qty, price, disc, sales,
                     profit, delivery, returned, late))
    return rows


def build(db_path=DB_PATH, reset=False, n=1200):
    db_path = Path(db_path)
    if reset and db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.executescript((HERE / "schema.sql").read_text())
    if conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
        conn.executemany("INSERT OR IGNORE INTO categories(name) VALUES (?)", [(c,) for c in CATEGORIES])
        conn.executemany("INSERT OR IGNORE INTO regions(name) VALUES (?)", [(r,) for r in REGIONS])
        cat_id = dict(conn.execute("SELECT name, category_id FROM categories"))
        reg_id = dict(conn.execute("SELECT name, region_id FROM regions"))
        conn.executemany(
            """INSERT INTO orders(order_id, order_date, category_id, region_id, quantity,
               unit_price, discount_rate, sales_amount, profit, delivery_days, returned, late_delivery)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            [(o, d, cat_id[c], reg_id[r], q, p, di, s, pr, dd, ret, late)
             for (o, d, c, r, q, p, di, s, pr, dd, ret, late) in generate(n)])
        conn.commit()
    export_csv(conn)
    conn.close()


def export_csv(conn):
    cur = conn.execute("SELECT * FROM v_orders ORDER BY order_date, order_id")
    header = [c[0] for c in cur.description]
    rows = cur.fetchall()
    for target in (ROOT / "data" / "orders_sample.csv", ROOT / "data" / "powerbi_orders.csv"):
        target.parent.mkdir(exist_ok=True)
        with open(target, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)


if __name__ == "__main__":
    build(reset="--reset" in sys.argv)
    print(f"Database ready: {DB_PATH}")
