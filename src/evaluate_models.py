"""
Generates model evaluation visuals expected in an ML project submission:
  - Predicted vs Actual scatter plots (lead time + profit margin models)
  - Feature importance chart (Random Forest profit margin model)

Run with: python src/evaluate_models.py   (from project root)
Outputs saved to outputs/charts/
"""
import os
import sys

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import CATEGORICAL, NUMERIC  # noqa: E402

OUT_DIR = "outputs/charts"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "font.size": 10})


def savefig(name):
    path = f"{OUT_DIR}/{name}.png"
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"saved {path}")


def predicted_vs_actual(pipe, X_test, y_test, title, filename, color):
    preds = pipe.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    plt.figure(figsize=(5.5, 5.5))
    plt.scatter(y_test, preds, alpha=0.3, s=12, color=color)
    lims = [min(y_test.min(), preds.min()), max(y_test.max(), preds.max())]
    plt.plot(lims, lims, "k--", linewidth=1, label="Perfect prediction")
    plt.xlabel("Actual")
    plt.ylabel("Predicted")
    plt.title(f"{title}\nMAE={mae:.4f}   R²={r2:.4f}")
    plt.legend()
    savefig(filename)


def feature_importance(pipe, title, filename, top_n=15):
    model = pipe.named_steps["model"]
    if not hasattr(model, "feature_importances_"):
        print(f"{title}: model has no feature_importances_, skipping")
        return

    pre = pipe.named_steps["pre"]
    cat_encoder = pre.named_transformers_["cat"]
    cat_names = list(cat_encoder.get_feature_names_out(CATEGORICAL))
    feature_names = cat_names + NUMERIC

    importances = model.feature_importances_
    order = np.argsort(importances)[::-1][:top_n]

    plt.figure(figsize=(6, 5))
    plt.barh(
        [feature_names[i] for i in order][::-1],
        [importances[i] for i in order][::-1],
        color="#845EF7",
    )
    plt.title(title)
    plt.xlabel("Importance")
    savefig(filename)


def main():
    df = pd.read_csv("data/processed.csv")
    lead_pipe = joblib.load("models/lead_time_model.pkl")
    profit_pipe = joblib.load("models/profit_margin_model.pkl")

    feat_cols = CATEGORICAL + NUMERIC

    # Lead time model eval
    lead_data = df.dropna(subset=["AdjustedLeadTimeDays", "DistanceToFactoryMiles"])
    X = lead_data[feat_cols]
    y = lead_data["AdjustedLeadTimeDays"]
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    predicted_vs_actual(
        lead_pipe, X_test, y_test,
        "Lead Time Model: Predicted vs Actual",
        "09_lead_time_pred_vs_actual", "#4C6EF5",
    )

    # Profit margin model eval
    profit_data = df.dropna(subset=["AdjustedProfitMargin", "DistanceToFactoryMiles"])
    X = profit_data[feat_cols]
    y = profit_data["AdjustedProfitMargin"]
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    predicted_vs_actual(
        profit_pipe, X_test, y_test,
        "Profit Margin Model: Predicted vs Actual",
        "10_profit_margin_pred_vs_actual", "#2F9E44",
    )

    # Feature importance (Random Forest is the profit margin model)
    feature_importance(
        profit_pipe,
        "Feature Importance: Profit Margin Model (Random Forest)",
        "11_profit_margin_feature_importance",
    )

    print("\nModel evaluation chart generation complete.")


if __name__ == "__main__":
    main()