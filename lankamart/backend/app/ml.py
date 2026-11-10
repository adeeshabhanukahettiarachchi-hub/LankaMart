import json

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import METRICS_PATH, MODEL_PATH

CAT_FEATURES = ["category", "region"]
NUM_FEATURES = ["quantity", "unit_price", "discount_rate", "sales_amount", "returned"]


def load_training_frame(conn):
    return pd.read_sql_query(
        "SELECT category, region, quantity, unit_price, discount_rate, sales_amount, returned, "
        "late_delivery FROM v_orders", conn)


def build_pipeline():
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_FEATURES),
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")),
                          ("scale", StandardScaler())]), NUM_FEATURES)])
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=3, class_weight="balanced",
                                random_state=42, n_jobs=-1)
    return Pipeline([("prep", pre), ("model", rf)])


def train(conn, threshold=0.5):
    df = load_training_frame(conn)
    X, y = df[CAT_FEATURES + NUM_FEATURES], df["late_delivery"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    pipe = build_pipeline().fit(X_tr, y_tr)
    proba = pipe.predict_proba(X_te)[:, 1]
    pred = (proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_te, pred).ravel()
    metrics = {"rows": int(len(df)), "test_rows": int(len(y_te)), "threshold": threshold,
               "accuracy": round(accuracy_score(y_te, pred), 3),
               "precision": round(precision_score(y_te, pred, zero_division=0), 3),
               "recall": round(recall_score(y_te, pred), 3),
               "f1": round(f1_score(y_te, pred), 3),
               "roc_auc": round(roc_auc_score(y_te, proba), 3),
               "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
               "note": "Synthetic data: demonstration only, not real-world performance."}
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    return pipe, metrics


def load_model():
    return joblib.load(MODEL_PATH)


def predict_proba(model, f):
    row = pd.DataFrame([{k: f[k] for k in CAT_FEATURES + NUM_FEATURES}])
    return float(model.predict_proba(row)[0, 1])


def risk_label(p):
    return "High" if p >= 0.5 else "Medium" if p >= 0.3 else "Low"
