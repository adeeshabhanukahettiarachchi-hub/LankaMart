"""All SQL lives here. Every value is passed as a bound parameter (no string-built values)."""
from .config import CATEGORY_MARGIN, LATE_THRESHOLD_DAYS


def _where(category=None, region=None):
    clauses, params = [], []
    if category:
        clauses.append("category = ?")
        params.append(category)
    if region:
        clauses.append("region = ?")
        params.append(region)
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def summary(conn, category=None, region=None):
    where, params = _where(category, region)
    r = conn.execute(
        f"""SELECT COUNT(*) AS total_orders,
                   COALESCE(SUM(sales_amount), 0) AS total_sales,
                   COALESCE(SUM(profit), 0)       AS total_profit,
                   COALESCE(AVG(sales_amount), 0) AS avg_order_value,
                   COALESCE(AVG(late_delivery), 0) AS late_rate,
                   COALESCE(AVG(returned), 0)      AS return_rate
            FROM v_orders{where}""", params).fetchone()
    return {"total_orders": r["total_orders"],
            "total_sales": round(r["total_sales"], 2),
            "total_profit": round(r["total_profit"], 2),
            "avg_order_value": round(r["avg_order_value"], 2),
            "late_delivery_rate": round(r["late_rate"], 4),
            "return_rate": round(r["return_rate"], 4)}


def monthly_sales(conn, category=None, region=None):
    where, params = _where(category, region)
    rows = conn.execute(
        f"""SELECT month, ROUND(SUM(sales_amount), 2) AS sales,
                   ROUND(SUM(profit), 2) AS profit, COUNT(*) AS orders
            FROM v_orders{where} GROUP BY month ORDER BY month""", params).fetchall()
    return [dict(r) for r in rows]


def category_sales(conn, region=None):
    where, params = _where(None, region)
    rows = conn.execute(
        f"""SELECT category, ROUND(SUM(sales_amount), 2) AS sales, ROUND(SUM(profit), 2) AS profit,
                   COUNT(*) AS orders, ROUND(AVG(returned), 4) AS return_rate
            FROM v_orders{where} GROUP BY category ORDER BY sales DESC""", params).fetchall()
    return [dict(r) for r in rows]


def region_sales(conn, category=None):
    where, params = _where(category, None)
    rows = conn.execute(
        f"""SELECT region, ROUND(SUM(sales_amount), 2) AS sales, COUNT(*) AS orders,
                   ROUND(AVG(delivery_days), 2) AS avg_delivery_days,
                   ROUND(AVG(late_delivery), 4) AS late_rate
            FROM v_orders{where} GROUP BY region ORDER BY sales DESC""", params).fetchall()
    return [dict(r) for r in rows]


def recent_orders(conn, limit=10, category=None, region=None):
    where, params = _where(category, region)
    rows = conn.execute(
        f"""SELECT order_id, order_date, category, region, quantity, sales_amount,
                   delivery_days, returned, late_delivery
            FROM v_orders{where} ORDER BY order_date DESC, order_id DESC LIMIT ?""",
        params + [limit]).fetchall()
    return [dict(r) for r in rows]


def filter_options(conn):
    return {"categories": [r[0] for r in conn.execute("SELECT name FROM categories ORDER BY name")],
            "regions": [r[0] for r in conn.execute("SELECT name FROM regions ORDER BY name")]}


def insert_order(conn, o):
    """Insert one order. `o` is a dict; sales, profit, late flag and the ID are computed here."""
    cat = conn.execute("SELECT category_id FROM categories WHERE name = ?", (o["category"],)).fetchone()
    reg = conn.execute("SELECT region_id FROM regions WHERE name = ?", (o["region"],)).fetchone()
    if cat is None or reg is None:
        raise ValueError("Unknown category or region")
    gross = o["unit_price"] * o["quantity"]
    sales = round(gross * (1 - o["discount_rate"]), 2)
    margin = CATEGORY_MARGIN.get(o["category"], 0.2)
    profit = round(-0.10 * sales, 2) if o["returned"] else round(sales - gross * (1 - margin), 2)
    nxt = conn.execute(
        "SELECT COALESCE(MAX(CAST(substr(order_id, 4) AS INTEGER)), 0) + 1 FROM orders").fetchone()[0]
    order_id = f"LM-{nxt:05d}"
    late = int(o["delivery_days"] > LATE_THRESHOLD_DAYS)
    conn.execute(
        """INSERT INTO orders(order_id, order_date, category_id, region_id, quantity, unit_price,
           discount_rate, sales_amount, profit, delivery_days, returned, late_delivery)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (order_id, str(o["order_date"]), cat[0], reg[0], o["quantity"], o["unit_price"],
         o["discount_rate"], sales, profit, o["delivery_days"], o["returned"], late))
    conn.commit()
    return {"order_id": order_id, "sales_amount": sales, "profit": profit, "late_delivery": late}


def log_prediction(conn, f, sales_amount, probability, label):
    conn.execute(
        """INSERT INTO prediction_log(category, region, quantity, unit_price, discount_rate,
           sales_amount, returned, probability, risk_label) VALUES (?,?,?,?,?,?,?,?,?)""",
        (f["category"], f["region"], f["quantity"], f["unit_price"], f["discount_rate"],
         sales_amount, f["returned"], probability, label))
    conn.commit()


def list_predictions(conn, limit=8):
    rows = conn.execute(
        """SELECT id, created_at, category, region, quantity, sales_amount, probability, risk_label
           FROM prediction_log ORDER BY id DESC LIMIT ?""", (limit,)).fetchall()
    return [dict(r) for r in rows]
