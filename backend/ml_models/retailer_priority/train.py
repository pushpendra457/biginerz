"""
ml_models/retailer_priority/train.py

Trains the Retailer Priority model from real CSV data.

Run from backend/ root:
    python -m ml_models.retailer_priority.train

Input CSVs (from data/):
    retailers.csv
    retailer_pos.csv
    retailer_inventory_weekly.csv
    retailer_visit_log.csv
    growers.csv

Output:
    ml_models/retailer_priority/pipeline.pkl
"""

import sys
import logging
import os
from pathlib import Path
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import KFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler


# ── Paths ──────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent.parent.parent   
DATA_DIR = REPO_ROOT / "data"
MODEL_DIR = Path(__file__).parent
ARTIFACT_PATH = MODEL_DIR / "pipeline.pkl"


print(f"DEBUG: Current file: {__file__}")
print(f"DEBUG: DATA_DIR exists: {DATA_DIR.exists()}")
if DATA_DIR.exists():
    try:
        print(f"DEBUG: Contents of DATA_DIR: {list(DATA_DIR.iterdir())}")
    except Exception as e:
        print(f"DEBUG: Could not list directory: {e}")
else:
    print("DEBUG: Contents of DATA_DIR: Folder not found")

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("train.retailer_priority")


# ── 1. LOAD & MERGE DATA ───────────────────────────────────────────────────────

def load_data() -> pd.DataFrame:
    log.info("Loading CSVs from data/...")

    retailers = pd.read_csv(DATA_DIR / "retailers.csv")
    pos = pd.read_csv(DATA_DIR / "retailer_pos.csv", parse_dates=["transaction_date"])
    inventory = pd.read_csv(DATA_DIR / "retailer_inventory_weekly.csv", parse_dates=["week_end_date"])
    visits = pd.read_csv(DATA_DIR / "retailer_visit_log.csv", parse_dates=["visit_date"])
    growers = pd.read_csv(DATA_DIR / "growers.csv")

    log.info(f"  retailers={len(retailers)}  pos={len(pos)}  inventory={len(inventory)}")

    # ── POS features per retailer ────────────────────────────
    # Use last 4 weeks of data as the training window
    max_date = pos["transaction_date"].max()
    pos_cutoff = max_date - pd.Timedelta(weeks=4)
    prev_cutoff = pos_cutoff - pd.Timedelta(weeks=4)

    # Clean boolean slices instead of repeating complex dynamic queries
    pos_recent = pos[pos["transaction_date"] >= pos_cutoff].copy()
    pos_prev = pos[(pos["transaction_date"] >= prev_cutoff) & (pos["transaction_date"] < pos_cutoff)]

    pos_recent["revenue"] = pos_recent["sku_qty"] * pos_recent["sku_price"]

    pos_agg = (
        pos_recent.groupby("retailer_id")
        .agg(
            weekly_sales_qty=("sku_qty", "sum"),
            transactions=("transaction_id", "nunique"),
            weekly_revenue=("revenue", "sum"),
        )
    )
    
    pos_agg["avg_qty_per_txn"] = pos_agg["weekly_sales_qty"] / pos_agg["transactions"].clip(lower=1)
    pos_agg["weekly_sales_qty"] /= 4
    pos_agg["transactions"] /= 4
    pos_agg["weekly_revenue"] /= 4

    # Growth rate: recent vs previous window
    prev_agg = pos_prev.groupby("retailer_id")[["sku_qty"]].sum().rename(columns={"sku_qty": "prev_qty"})
    
    # Fast index join instead of free column merge
    pos_agg = pos_agg.join(prev_agg, how="left")
    pos_agg["prev_qty"] = pos_agg["prev_qty"].fillna(pos_agg["weekly_sales_qty"] * 4)
    pos_agg["sales_growth_rate"] = (
        (pos_agg["weekly_sales_qty"] * 4 - pos_agg["prev_qty"])
        / pos_agg["prev_qty"].clip(lower=1)
    ).clip(-1, 5)

    # ── Inventory features ───────────────────────────────────
    latest_inv_date = inventory["week_end_date"].max()
    inv_latest = inventory[inventory["week_end_date"] == latest_inv_date].copy()

    # REMOVED Python Lambda Loop! Replaced with ultra fast C-vectorization mapping
    inv_latest["is_stockout"] = (inv_latest["sku_qty"] == 0).astype(int)

    inv_agg = (
        inv_latest.groupby("retailer_id")
        .agg(
            avg_inventory=("sku_qty", "mean"),
            stockout_count=("is_stockout", "sum"), # Native C speed execution
            total_skus=("sku_qty", "count"),
        )
    )
    inv_agg["stockout_ratio"] = inv_agg["stockout_count"] / inv_agg["total_skus"].clip(lower=1)

    # ── Visit features ───────────────────────────────────────
    visit_cutoff = visits["visit_date"].max()
    visit_agg = (
        visits.groupby("territory_id")
        .agg(
            weekly_visits=("visit_date", "count"),
            last_visit_date=("visit_date", "max"),
        )
    )
    visit_agg["days_since_last_visit"] = (
        visit_cutoff - visit_agg["last_visit_date"]
    ).dt.days.clip(0, 90)
    visit_agg["weekly_visits"] /= 4

    # ── Grower features per tehsil ───────────────────────────
    grower_agg = (
        growers.groupby("tehsil")
        .agg(
            avg_farm_size=("grower_farm_size", "mean"),
            avg_grower_age=("grower_age", "mean"),
            scan_rate=("product_scan", "mean"),
            campaign_attendance_rate=("offline_campaign_attended", "mean"),
        )
    )

    # ── Blazing Fast Index-Based Joins ──────────────────────
    df = retailers.join(pos_agg, on="retailer_id", how="left")
    df = df.join(inv_agg, on="retailer_id", how="left")
    df = df.join(visit_agg, on="territory_id", how="left")
    df = df.join(grower_agg, on="tehsil", how="left")

    # Fill missing retailers (no POS activity) with conservative defaults
    num_defaults = {
        "weekly_sales_qty": 0,
        "transactions": 0,
        "avg_qty_per_txn": 0,
        "weekly_revenue": 0,
        "sales_growth_rate": 0,
        "avg_inventory": 5,
        "stockout_ratio": 0.5,
        "weekly_visits": 1,
        "days_since_last_visit": 30,
        "avg_farm_size": 3,
        "avg_grower_age": 40,
        "scan_rate": 0.1,
        "campaign_attendance_rate": 0.1,
    }
    df = df.fillna(num_defaults)
    for col in ["state", "district", "tehsil"]:
        df[col] = df[col].fillna("Unknown")

    log.info(f"Merged dataset: {len(df)} rows, {df.shape[1]} cols")
    return df


# ── 2. FEATURE ENGINEERING ────────────────────────────────────────────────────

NUMERIC_FEATURES = [
    "weekly_sales_qty",
    "transactions",
    "avg_qty_per_txn",
    "sales_growth_rate",
    "avg_inventory",
    "stockout_ratio",
    "weekly_visits",
    "days_since_last_visit",
    "avg_farm_size",
    "avg_grower_age",
    "scan_rate",
    "campaign_attendance_rate",
    # Engineered
    "revenue_proxy",
    "visit_recency_score",
    "engagement_index",
    "inventory_pressure",
]

CATEGORICAL_FEATURES = ["state", "district", "tehsil"]
TARGET = "weekly_revenue"


def engineer_features(X: pd.DataFrame) -> pd.DataFrame:
    X = X.copy()
    X["revenue_proxy"] = X["weekly_sales_qty"] * X["avg_qty_per_txn"]
    X["visit_recency_score"] = 1 / (1 + X["days_since_last_visit"])
    X["engagement_index"] = (X["scan_rate"] + X["campaign_attendance_rate"]) / 2
    X["inventory_pressure"] = X["stockout_ratio"] / (X["avg_inventory"].clip(lower=1) + 1)
    return X


# ── 3. PIPELINE ───────────────────────────────────────────────────────────────

def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    model = GradientBoostingRegressor(
        n_estimators=400,
        learning_rate=0.04,
        max_depth=5,
        subsample=0.8,
        min_samples_leaf=8,
        random_state=42,
    )
    from ml_models.retailer_priority.train import engineer_features
    return Pipeline([
        ("feature_engineering", FunctionTransformer(engineer_features)),
        ("preprocessor", preprocessor),
        ("model", model),
    ])


# ── 4. TRAIN & EVALUATE ───────────────────────────────────────────────────────

def train(df: pd.DataFrame) -> dict:
    X = df[CATEGORICAL_FEATURES + [f for f in NUMERIC_FEATURES if f not in
           ["revenue_proxy", "visit_recency_score", "engagement_index", "inventory_pressure"]]]
    y = df[TARGET]

    log.info(f"Training on {len(X)} samples, target='{TARGET}'")

    pipeline = build_pipeline()

    # 5-fold CV
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_results = cross_validate(
        pipeline, X, y, cv=cv,
        scoring={"r2": "r2", "neg_mae": "neg_mean_absolute_error", "neg_rmse": "neg_root_mean_squared_error"},
        return_train_score=True,
    )

    mae   = -cv_results["test_neg_mae"]
    rmse  = -cv_results["test_neg_rmse"]
    r2    = cv_results["test_r2"]
    tr_r2 = cv_results["train_r2"]

    log.info("=" * 50)
    log.info("CROSS-VALIDATION RESULTS")
    log.info(f"  MAE   {mae.mean():.2f} ± {mae.std():.2f}")
    log.info(f"  RMSE  {rmse.mean():.2f} ± {rmse.std():.2f}")
    log.info(f"  R²    {r2.mean():.4f} ± {r2.std():.4f}")
    log.info(f"  Overfit gap (train R² - test R²): {(tr_r2.mean()-r2.mean()):.4f}")
    log.info("=" * 50)

    # Final fit on full data
    pipeline.fit(X, y)

    # Calibration: revenue percentiles for 0-100 normalization
    y_pred = pipeline.predict(X)
    p5  = float(np.percentile(y_pred, 5))
    p95 = float(np.percentile(y_pred, 95))
    log.info(f"Calibration: revenue P5={p5:.1f}  P95={p95:.1f}")

    return {
        "pipeline": pipeline,
        "revenue_p5": p5,
        "revenue_p95": p95,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "target": TARGET,
        "metadata": {
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "n_samples": len(X),
            "cv_mae_mean": float(mae.mean()),
            "cv_mae_std": float(mae.std()),
            "cv_rmse_mean": float(rmse.mean()),
            "cv_rmse_std": float(rmse.std()),
            "cv_r2_mean": float(r2.mean()),
            "cv_r2_std": float(r2.std()),
        },
    }


# ── 5. ENTRYPOINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        df = load_data()
    except FileNotFoundError as e:
        log.error(f"CSV not found: {e}")
        log.info("Generating synthetic data for development...")
        # ── Synthetic fallback so you can develop without CSVs ──
        import numpy as np
        np.random.seed(42)
        N = 2000
        df = pd.DataFrame({
            "state": np.random.choice(["Uttar Pradesh","Madhya Pradesh","Rajasthan"], N),
            "district": np.random.choice(["Lucknow","Kanpur","Agra","Jaipur"], N),
            "tehsil": np.random.choice(["Malihabad","Bijnor","Sadar","Sanganer"], N),
            "weekly_sales_qty": np.random.exponential(80, N).clip(0, 500),
            "transactions": np.random.poisson(30, N).clip(1, 200).astype(float),
            "avg_qty_per_txn": np.random.uniform(1.5, 8.0, N),
            "sales_growth_rate": np.random.normal(0.10, 0.25, N).clip(-0.5, 1.5),
            "avg_inventory": np.random.exponential(25, N).clip(2, 200),
            "stockout_ratio": np.random.beta(2, 10, N),
            "weekly_visits": np.random.randint(1, 8, N).astype(float),
            "days_since_last_visit": np.random.exponential(7, N).clip(1, 60),
            "avg_farm_size": np.random.lognormal(1.5, 0.7, N).clip(0.5, 50),
            "avg_grower_age": np.random.normal(44, 8, N).clip(22, 70),
            "scan_rate": np.random.beta(3, 7, N),
            "campaign_attendance_rate": np.random.beta(2, 8, N),
        })
        df["weekly_revenue"] = (
            df["weekly_sales_qty"] * df["avg_qty_per_txn"] * np.random.uniform(8, 14, N)
            + df["sales_growth_rate"] * 200
            + df["scan_rate"] * 150
            - df["stockout_ratio"] * 300
            + np.random.normal(0, 50, N)
        ).clip(0, 10000)

    artifacts = train(df)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifacts, ARTIFACT_PATH)
    log.info(f"\nSaved → {ARTIFACT_PATH}")