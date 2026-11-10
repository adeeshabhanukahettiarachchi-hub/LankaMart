PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS regions (
    region_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL UNIQUE
);

-- One row per synthetic order. No customer names, phones or addresses are stored.
CREATE TABLE IF NOT EXISTS orders (
    order_id      TEXT PRIMARY KEY,
    order_date    TEXT NOT NULL CHECK (order_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    category_id   INTEGER NOT NULL REFERENCES categories(category_id),
    region_id     INTEGER NOT NULL REFERENCES regions(region_id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    REAL    NOT NULL CHECK (unit_price > 0),
    discount_rate REAL    NOT NULL CHECK (discount_rate BETWEEN 0 AND 0.5),
    sales_amount  REAL    NOT NULL CHECK (sales_amount >= 0),
    profit        REAL    NOT NULL,
    delivery_days INTEGER NOT NULL CHECK (delivery_days >= 0),
    returned      INTEGER NOT NULL CHECK (returned IN (0, 1)),
    late_delivery INTEGER NOT NULL CHECK (late_delivery IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_orders_date     ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_category ON orders(category_id);
CREATE INDEX IF NOT EXISTS idx_orders_region   ON orders(region_id);

-- Audit trail of delivery-risk estimates requested from the dashboard.
CREATE TABLE IF NOT EXISTS prediction_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    category      TEXT NOT NULL,
    region        TEXT NOT NULL,
    quantity      INTEGER NOT NULL,
    unit_price    REAL NOT NULL,
    discount_rate REAL NOT NULL,
    sales_amount  REAL NOT NULL,
    returned      INTEGER NOT NULL,
    probability   REAL NOT NULL CHECK (probability BETWEEN 0 AND 1),
    risk_label    TEXT NOT NULL
);

-- Flat, readable view used by the API, notebook and Power BI export.
DROP VIEW IF EXISTS v_orders;
CREATE VIEW v_orders AS
SELECT o.order_id,
       o.order_date,
       substr(o.order_date, 1, 7) AS month,
       c.name AS category,
       r.name AS region,
       o.quantity, o.unit_price, o.discount_rate, o.sales_amount, o.profit,
       o.delivery_days, o.returned, o.late_delivery
FROM orders o
JOIN categories c ON c.category_id = o.category_id
JOIN regions r    ON r.region_id   = o.region_id;
