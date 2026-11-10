import json
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Order

MODEL_PATH = Path("models/late_delivery.joblib")
METRICS_PATH = Path("models/metrics.json")
model = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None

app = FastAPI(title="LankaMart Decision Support API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["GET", "POST"], allow_headers=["*"])

Category = Literal["Electronics", "Fashion", "Home and Kitchen", "Beauty", "Sports"]
Region = Literal["Western", "Central", "Southern", "Northern", "Eastern", "North Western"]


class PredictIn(BaseModel):
    category: Category
    region: Region
    quantity: int = Field(ge=1, le=50)
    unit_price: float = Field(gt=0, le=1_000_000)
    discount_rate: float = Field(ge=0, le=0.5)
    returned: int = Field(0, ge=0, le=1)

from fastapi import FastAPI

app = FastAPI(
    title="Order Analytics API",
    description="API for order analytics project",
    version="1.0.0"
)

@app.get("/")
def home():
    return {"message": "Order Analytics API is running"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "message": "API is running successfully"
    }

@app.get("/orders")
def get_orders():
    return {
        "message": "Orders endpoint is working"
    }

@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok", "model_loaded": model is not None}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "API is running successfully"
    }

@app.get("/api/summary")
def summary(db: Session = Depends(get_db)):
    n, sales, profit, late, ret = db.execute(select(
        func.count(), func.coalesce(func.sum(Order.sales_amount), 0),
        func.coalesce(func.sum(Order.profit), 0),
        func.coalesce(func.avg(Order.late_delivery), 0),
        func.coalesce(func.avg(Order.returned), 0))).one()
    return {"total_orders": n, "total_sales": round(sales, 2), "total_profit": round(profit, 2),
            "avg_order_value": round(sales / n, 2) if n else 0,
            "late_rate": round(late * 100, 1), "return_rate": round(ret * 100, 1)}


@app.get("/api/monthly-sales")
def monthly(db: Session = Depends(get_db)):
    m = func.substr(Order.order_date, 1, 7).label("month")
    rows = db.execute(select(m, func.sum(Order.sales_amount), func.sum(Order.profit))
                      .group_by(m).order_by(m)).all()
    return [{"month": r[0], "sales": round(r[1], 2), "profit": round(r[2], 2)} for r in rows]


def _group(db: Session, col):
    rows = db.execute(select(col, func.sum(Order.sales_amount), func.sum(Order.profit),
                             func.avg(Order.late_delivery), func.avg(Order.returned))
                      .group_by(col).order_by(func.sum(Order.sales_amount).desc())).all()
    return [{"name": r[0], "sales": round(r[1], 2), "profit": round(r[2], 2),
             "late_rate": round(r[3] * 100, 1), "return_rate": round(r[4] * 100, 1)} for r in rows]


@app.get("/api/category-sales")
def category_sales(db: Session = Depends(get_db)):
    return _group(db, Order.category)


@app.get("/api/region-sales")
def region_sales(db: Session = Depends(get_db)):
    return _group(db, Order.region)


@app.get("/api/recent-orders")
def recent(limit: int = 10, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100))
    rows = db.scalars(select(Order).order_by(Order.order_date.desc(), Order.order_id.desc()).limit(limit)).all()
    return [{c.name: (str(getattr(o, c.name)) if c.name == "order_date" else getattr(o, c.name))
             for c in Order.__table__.columns} for o in rows]


@app.get("/api/model-metrics")
def model_metrics():
    if not METRICS_PATH.exists():
        raise HTTPException(404, "Run seed_and_train.py first")
    return json.loads(METRICS_PATH.read_text())


@app.post("/api/predict-late-delivery")
def predict(body: PredictIn):
    if model is None:
        raise HTTPException(503, "Model not trained. Run seed_and_train.py")
    row = body.model_dump()
    row["sales_amount"] = round(row["unit_price"] * row["quantity"] * (1 - row["discount_rate"]), 2)
    p = float(model.predict_proba(pd.DataFrame([row]))[0, 1])
    label = "High" if p >= 0.5 else "Medium" if p >= 0.3 else "Low"
    return {"probability": round(p, 3), "risk_label": label,
            "note": "Decision-support estimate only, not a guarantee. A staff member should review before acting."}
