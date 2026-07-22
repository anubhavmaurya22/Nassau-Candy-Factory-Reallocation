"""
Trains two models on the processed dataset:
  1. Lead time proxy predictor  (regression, target = LeadTimeProxyDays)
  2. Profit margin predictor    (regression, target = ProfitMargin)

Both are trained on general shipping/order features (distance to assigned
factory, division, ship mode, region, units, sales) so that, at inference
time, we can feed in a HYPOTHETICAL factory (via its distance) and get a
predicted lead time / profit for a (product, factory) pair that never
happened historically. This is what makes the "what if we reassigned this
product to another factory" analysis possible.

Run with: python src/model.py
"""
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

PROCESSED_PATH = "data/processed.csv"
MODEL_DIR = "models"

CATEGORICAL = ["Division_clean", "Ship Mode", "Region"]
NUMERIC = ["DistanceToFactoryMiles", "Units", "Sales"]


def build_pipeline(estimator):
    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
            ("num", "passthrough", NUMERIC),
        ]
    )
    return Pipeline(steps=[("pre", pre), ("model", estimator)])


def train_and_eval(df, target_col, label):
    data = df.dropna(subset=[target_col, "DistanceToFactoryMiles"])
    X = data[CATEGORICAL + NUMERIC]
    y = data[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    results = {}
    for name, est in [
        ("Ridge (baseline)", Ridge(alpha=1.0)),
        ("RandomForest", RandomForestRegressor(n_estimators=300, max_depth=8, random_state=42)),
    ]:
        pipe = build_pipeline(est)
        pipe.fit(X_train, y_train)
        preds = pipe.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        results[name] = {"pipe": pipe, "mae": mae, "r2": r2}
        print(f"[{label}] {name:20s}  MAE={mae:.4f}   R2={r2:.4f}")

    # pick the better model by R2
    best_name = max(results, key=lambda k: results[k]["r2"])
    print(f"[{label}] -> best model: {best_name}\n")
    return results[best_name]["pipe"], results


def run():
    df = pd.read_csv(PROCESSED_PATH)

    lead_pipe, lead_results = train_and_eval(df, "AdjustedLeadTimeDays", "LeadTime")
    profit_pipe, profit_results = train_and_eval(df, "AdjustedProfitMargin", "ProfitMargin")

    joblib.dump(lead_pipe, f"{MODEL_DIR}/lead_time_model.pkl")
    joblib.dump(profit_pipe, f"{MODEL_DIR}/profit_margin_model.pkl")
    print(f"Saved models to {MODEL_DIR}/")

    return lead_pipe, profit_pipe


if __name__ == "__main__":
    run()
