"""Generate synthetic orders -> SQL database -> train Random Forest -> export Power BI CSV."""
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, confusion_matrix)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.db import engine, Base
from app import models  # noqa: F401

SEED, N = 42, 1200
rng = np.random.default_rng(SEED)
CATS = {"Electronics": (15000, 120000, .18), "Fashion": (1500, 15000, .35),
        "Home and Kitchen": (2000, 30000, .28), "Beauty": (800, 8000, .40),
        "Sports": (2500, 40000, .30)}
REGION_DELAY = {"Western": 2.6, "Central": 3.6, "Southern": 3.4, "Northern": 5.0,
                "Eastern": 4.8, "North Western": 3.8}

# --- generate -------------------------------------------------------------
dates = pd.to_datetime("2025-01-01") + pd.to_timedelta(rng.integers(0, 365, N), unit="D")
month_w = np.array([1, .9, 1, 1.1, 1.1, 1, 1, 1.1, 1.1, 1.2, 1.4, 1.8])
dates = pd.Series(rng.choice(pd.date_range("2025-01-01", "2025-12-31"), N,
                  p=np.repeat(month_w, 31)[:365][:365] / np.repeat(month_w, 31)[:365].sum()))
cat = rng.choice(list(CATS), N, p=[.22, .25, .2, .17, .16])
region = rng.choice(list(REGION_DELAY), N, p=[.34, .16, .16, .1, .1, .14])
qty = rng.integers(1, 6, N)
price = np.array([round(rng.uniform(CATS[c][0], CATS[c][1]), -1) for c in cat])
disc = rng.choice([0, .05, .10, .15, .20], N, p=[.4, .2, .2, .12, .08])
sales = np.round(price * qty * (1 - disc), 2)
margin = np.array([CATS[c][2] for c in cat])
profit = np.round(sales * (margin - disc * .6) + rng.normal(0, 150, N), 2)
base = np.array([REGION_DELAY[r] for r in region]) + (qty > 3) * .6 + (cat == "Electronics") * .4
days = np.clip(np.round(base + rng.normal(0, 1.3, N)), 1, 14).astype(int)
returned = (rng.random(N) < (0.04 + (cat == "Fashion") * .08 + disc * .2)).astype(int)

df = pd.DataFrame({
    "order_id": [f"LM{100000 + i}" for i in range(N)],
    "order_date": dates.dt.date, "category": cat, "region": region, "quantity": qty,
    "unit_price": price, "discount_rate": disc, "sales_amount": sales, "profit": profit,
    "delivery_days": days, "returned": returned})

# --- data quality + label -------------------------------------------------
print("Shape:", df.shape)
print("Missing values:\n", df.isna().sum().to_string())
print("Duplicate order IDs:", df.order_id.duplicated().sum())
df = df.drop_duplicates("order_id")
df["late_delivery"] = (df.delivery_days > 5).astype(int)

# --- store in SQL ---------------------------------------------------------
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
df.to_sql("orders", engine, if_exists="append", index=False)
print(f"Inserted {len(df)} rows into SQL table 'orders'")
df.assign(month=pd.to_datetime(df.order_date).dt.to_period("M").astype(str)) \
  .to_csv("powerbi_orders.csv", index=False)

# --- model ----------------------------------------------------------------
CATEGORICAL = ["category", "region"]
NUMERIC = ["quantity", "unit_price", "discount_rate", "sales_amount", "returned"]
X, y = df[CATEGORICAL + NUMERIC], df.late_delivery
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.2, stratify=y, random_state=SEED)
pre = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), NUMERIC)])
pipe = Pipeline([("pre", pre), ("rf", RandomForestClassifier(
    n_estimators=300, min_samples_leaf=3, class_weight="balanced", random_state=SEED))])
pipe.fit(Xtr, ytr)
proba, pred = pipe.predict_proba(Xte)[:, 1], pipe.predict(Xte)
tn, fp, fn, tp = confusion_matrix(yte, pred).ravel()
metrics = {"accuracy": accuracy_score(yte, pred), "precision": precision_score(yte, pred, zero_division=0),
           "recall": recall_score(yte, pred), "f1": f1_score(yte, pred),
           "roc_auc": roc_auc_score(yte, proba), "threshold": 0.5,
           "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
           "baseline_accuracy_majority": float(1 - yte.mean()),
           "note": "Synthetic data - technical demonstration only."}
metrics = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in metrics.items()}
Path("models").mkdir(exist_ok=True)
joblib.dump(pipe, "models/late_delivery.joblib")
Path("models/metrics.json").write_text(json.dumps(metrics, indent=2))
print(json.dumps(metrics, indent=2))
