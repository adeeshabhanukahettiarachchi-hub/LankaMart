"""Run from the project root:  python -m unittest discover backend/tests -p "test_queries.py" """
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app import queries  # noqa: E402


def make_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript((ROOT / "database" / "schema.sql").read_text())
    conn.executemany("INSERT INTO categories(name) VALUES (?)", [("Electronics",), ("Fashion",)])
    conn.executemany("INSERT INTO regions(name) VALUES (?)", [("Western",), ("Northern",)])
    return conn


ORDER = dict(order_date="2025-03-10", category="Electronics", region="Western", quantity=2,
             unit_price=10000.0, discount_rate=0.1, returned=0, delivery_days=7)


class QueryTests(unittest.TestCase):
    def test_insert_computes_sales_and_late_flag(self):
        r = queries.insert_order(make_db(), ORDER)
        self.assertEqual(r["order_id"], "LM-00001")
        self.assertEqual(r["sales_amount"], 18000.0)   # 10000 x 2 x (1 - 0.1)
        self.assertEqual(r["late_delivery"], 1)         # 7 days > 5

    def test_summary_and_filters(self):
        conn = make_db()
        queries.insert_order(conn, ORDER)
        queries.insert_order(conn, {**ORDER, "category": "Fashion", "region": "Northern", "delivery_days": 3})
        self.assertEqual(queries.summary(conn)["total_orders"], 2)
        self.assertEqual(queries.summary(conn, category="Fashion")["total_orders"], 1)
        self.assertEqual(queries.summary(conn, region="Western")["late_delivery_rate"], 1.0)
        self.assertEqual(len(queries.monthly_sales(conn)), 1)

    def test_unknown_category_rejected(self):
        with self.assertRaises(ValueError):
            queries.insert_order(make_db(), {**ORDER, "category": "Toys"})

    def test_sql_injection_text_is_just_a_value(self):
        conn = make_db()
        queries.insert_order(conn, ORDER)
        self.assertEqual(queries.summary(conn, category="x' OR '1'='1")["total_orders"], 0)

    def test_check_constraint_blocks_bad_discount(self):
        with self.assertRaises(sqlite3.IntegrityError):
            queries.insert_order(make_db(), {**ORDER, "discount_rate": 0.9})


if __name__ == "__main__":
    unittest.main()
