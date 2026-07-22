"""
Optimization logic: for every product, evaluates ALL 5 factories (not just
the currently-assigned one) by re-running the trained models with
recalculated distances, then ranks factories using a user-controlled
speed-vs-profit weight.

This is the core engine behind:
  - Factory Optimization Simulator
  - What-If Scenario Analysis
  - Recommendation Dashboard
  - Risk & Impact Panel

Run standalone with: python src/optimizer.py
"""
import math
import joblib
import numpy as np
import pandas as pd

from reference_data import FACTORIES, PRODUCT_FACTORY, PRODUCT_DIVISION, STATE_CENTROIDS

PROCESSED_PATH = "data/processed.csv"
MODEL_DIR = "models"


def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def load_models():
    lead_pipe = joblib.load(f"{MODEL_DIR}/lead_time_model.pkl")
    profit_pipe = joblib.load(f"{MODEL_DIR}/profit_margin_model.pkl")
    return lead_pipe, profit_pipe


def evaluate_product_across_factories(df, product_name, lead_pipe, profit_pipe,
                                       region_filter=None, ship_mode_filter=None):
    """
    For one product, replays its historical order rows (optionally filtered
    by region / ship mode) against EVERY factory by recalculating distance,
    then averages the model's predicted lead time & profit margin per
    factory. Returns a per-factory summary table.
    """
    rows = df[df["Product Name"] == product_name].copy()
    if region_filter:
        rows = rows[rows["Region"] == region_filter]
    if ship_mode_filter:
        rows = rows[rows["Ship Mode"] == ship_mode_filter]

    if rows.empty:
        return pd.DataFrame()

    division = PRODUCT_DIVISION.get(product_name, rows["Division_clean"].iloc[0])
    current_factory = PRODUCT_FACTORY.get(product_name)

    records = []
    for fac_name, coords in FACTORIES.items():
        sub = rows.copy()
        sub["DistanceToFactoryMiles"] = sub.apply(
            lambda r: haversine_miles(coords["lat"], coords["lon"], r["cust_lat"], r["cust_lon"])
            if pd.notna(r["cust_lat"]) else np.nan,
            axis=1,
        )
        sub["Division_clean"] = division

        feat_cols = ["Division_clean", "Ship Mode", "Region", "DistanceToFactoryMiles", "Units", "Sales"]
        sub_valid = sub.dropna(subset=["DistanceToFactoryMiles"])
        if sub_valid.empty:
            continue

        pred_lead = lead_pipe.predict(sub_valid[feat_cols])
        pred_profit = profit_pipe.predict(sub_valid[feat_cols])

        records.append({
            "Factory": fac_name,
            "IsCurrent": fac_name == current_factory,
            "AvgDistanceMiles": sub_valid["DistanceToFactoryMiles"].mean(),
            "PredictedLeadTimeDays": pred_lead.mean(),
            "PredictedProfitMargin": pred_profit.mean(),
            "OrderCount": len(sub_valid),
        })

    result = pd.DataFrame(records)
    return result


def score_factories(result_df, speed_weight: float):
    """
    speed_weight in [0, 1]: 1.0 = pure speed optimization, 0.0 = pure profit
    optimization. Scores are min-max normalized across the candidate
    factories for this product so the weight behaves consistently
    regardless of each product's absolute lead-time/profit scale.
    """
    df = result_df.copy()
    profit_weight = 1.0 - speed_weight

    lt_min, lt_max = df["PredictedLeadTimeDays"].min(), df["PredictedLeadTimeDays"].max()
    pm_min, pm_max = df["PredictedProfitMargin"].min(), df["PredictedProfitMargin"].max()

    def norm_speed(x):
        if lt_max == lt_min:
            return 1.0
        return 1 - (x - lt_min) / (lt_max - lt_min)  # lower lead time -> higher score

    def norm_profit(x):
        if pm_max == pm_min:
            return 1.0
        return (x - pm_min) / (pm_max - pm_min)  # higher margin -> higher score

    df["SpeedScore"] = df["PredictedLeadTimeDays"].apply(norm_speed)
    df["ProfitScore"] = df["PredictedProfitMargin"].apply(norm_profit)
    df["CompositeScore"] = speed_weight * df["SpeedScore"] + profit_weight * df["ProfitScore"]
    df = df.sort_values("CompositeScore", ascending=False).reset_index(drop=True)
    df["Rank"] = df.index + 1
    return df


def recommend_for_product(df, product_name, lead_pipe, profit_pipe, speed_weight=0.5,
                           region_filter=None, ship_mode_filter=None):
    result = evaluate_product_across_factories(
        df, product_name, lead_pipe, profit_pipe, region_filter, ship_mode_filter
    )
    if result.empty:
        return None
    scored = score_factories(result, speed_weight)

    current_row = scored[scored["IsCurrent"]]
    best_row = scored.iloc[0]

    summary = {
        "product": product_name,
        "current_factory": current_row["Factory"].values[0] if not current_row.empty else None,
        "recommended_factory": best_row["Factory"],
        "is_reassignment": (
            not current_row.empty and current_row["Factory"].values[0] != best_row["Factory"]
        ),
        "current_lead_time": current_row["PredictedLeadTimeDays"].values[0] if not current_row.empty else None,
        "recommended_lead_time": best_row["PredictedLeadTimeDays"],
        "current_profit_margin": current_row["PredictedProfitMargin"].values[0] if not current_row.empty else None,
        "recommended_profit_margin": best_row["PredictedProfitMargin"],
        "lead_time_gain_days": (
            current_row["PredictedLeadTimeDays"].values[0] - best_row["PredictedLeadTimeDays"]
            if not current_row.empty else None
        ),
        "profit_margin_change": (
            best_row["PredictedProfitMargin"] - current_row["PredictedProfitMargin"].values[0]
            if not current_row.empty else None
        ),
        "table": scored,
    }

    # Simple, transparent risk flag: reassignment looks good on the
    # weighted score, but would actually REDUCE profit margin -> flag it.
    summary["high_risk"] = bool(
        summary["is_reassignment"] and summary["profit_margin_change"] is not None
        and summary["profit_margin_change"] < -0.01
    )
    return summary


def build_full_recommendation_table(df, lead_pipe, profit_pipe, speed_weight=0.5):
    """Ranked list of reassignment suggestions across ALL products - powers
    the Recommendation Dashboard."""
    rows = []
    for product in df["Product Name"].unique():
        s = recommend_for_product(df, product, lead_pipe, profit_pipe, speed_weight)
        if s is None:
            continue
        rows.append({
            "Product": product,
            "Current Factory": s["current_factory"],
            "Recommended Factory": s["recommended_factory"],
            "Reassignment Suggested": s["is_reassignment"],
            "Lead Time Gain (days)": round(s["lead_time_gain_days"], 2) if s["lead_time_gain_days"] is not None else None,
            "Profit Margin Change": round(s["profit_margin_change"], 4) if s["profit_margin_change"] is not None else None,
            "High Risk": s["high_risk"],
        })
    out = pd.DataFrame(rows)
    out = out.sort_values("Lead Time Gain (days)", ascending=False)
    return out


if __name__ == "__main__":
    df = pd.read_csv(PROCESSED_PATH)
    lead_pipe, profit_pipe = load_models()
    table = build_full_recommendation_table(df, lead_pipe, profit_pipe, speed_weight=0.5)
    print(table.to_string(index=False))
    table.to_csv("outputs/recommendations.csv", index=False)
