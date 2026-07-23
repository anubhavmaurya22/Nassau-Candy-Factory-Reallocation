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

# ---------------------------------------------------------------------------
# Confidence tiers based on historical order count for the CURRENT factory.
# EDA showed order volume is extremely concentrated: the 5 Wonka Bar
# (Chocolate) products have 1,800-2,100 orders each, while several
# Sugar/Other products have as few as 3-4. A recommendation backed by 3
# orders is not as trustworthy as one backed by 1,800, even if the
# predicted numbers look equally clean - this tier makes that visible
# instead of hiding it.
# ---------------------------------------------------------------------------
CONFIDENCE_THRESHOLDS = {"High": 100, "Medium": 20}  # Low = below Medium threshold


def confidence_tier(order_count: int) -> str:
    if order_count >= CONFIDENCE_THRESHOLDS["High"]:
        return "High"
    if order_count >= CONFIDENCE_THRESHOLDS["Medium"]:
        return "Medium"
    return "Low"


def haversine_miles(lat1, lon1, lat2, lon2):
    """Vectorized haversine - works on scalars or numpy arrays/Series."""
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dphi = lat2 - lat1
    dlambda = lon2 - lon1
    a = np.sin(dphi / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlambda / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


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

    This is the EXPENSIVE step (model inference) and does NOT depend on the
    speed/profit slider - callers should cache this and only re-run
    score_factories() (cheap) when the slider moves.
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
        # Vectorized distance calc (no row-wise .apply - this was the main
        # source of lag, especially for high-volume products like the
        # Wonka Bars with 1,800-2,100 rows each).
        sub["DistanceToFactoryMiles"] = haversine_miles(
            coords["lat"], coords["lon"], sub["cust_lat"].values, sub["cust_lon"].values
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


def evaluate_all_products_across_factories(df, lead_pipe, profit_pipe,
                                            region_filter=None, ship_mode_filter=None):
    """
    Same as evaluate_product_across_factories, but for EVERY product at
    once. This is the single expensive computation the Recommendation
    Dashboard and Risk Panel need - callers should cache the result of
    THIS function (independent of the slider), then call score_factories()
    per-product (cheap, pure arithmetic) whenever the slider changes.

    Returns a dict: {product_name: result_dataframe}
    """
    results = {}
    for product in df["Product Name"].unique():
        r = evaluate_product_across_factories(
            df, product, lead_pipe, profit_pipe, region_filter, ship_mode_filter
        )
        if not r.empty:
            results[product] = r
    return results


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


def summarize_recommendation(product_name, result, speed_weight=0.5):
    """
    Cheap step: takes an already-computed per-factory result table (from
    evaluate_product_across_factories) and applies scoring/ranking for a
    given speed_weight. No model inference happens here - safe to call on
    every slider tick.
    """
    if result is None or result.empty:
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

    summary["high_risk"] = bool(
        summary["is_reassignment"] and summary["profit_margin_change"] is not None
        and summary["profit_margin_change"] < -0.01
    )

    # Confidence is based on how many historical orders back the CURRENT
    # factory's numbers (the reference point every comparison is made
    # against). Low order counts mean the underlying averages are noisy.
    current_order_count = (
        current_row["OrderCount"].values[0] if not current_row.empty else scored["OrderCount"].min()
    )
    summary["order_count"] = int(current_order_count)
    summary["confidence"] = confidence_tier(current_order_count)

    return summary


def recommend_for_product(df, product_name, lead_pipe, profit_pipe, speed_weight=0.5,
                           region_filter=None, ship_mode_filter=None):
    """Convenience wrapper: runs BOTH the expensive prediction step and the
    cheap scoring step for a single product. Fine for one-off calls (e.g.
    the Factory Simulator / What-If pages, which only evaluate one product
    at a time), but the Recommendation Dashboard / Risk Panel should use
    evaluate_all_products_across_factories() + summarize_recommendation()
    instead so the expensive step is only computed once and cached."""
    result = evaluate_product_across_factories(
        df, product_name, lead_pipe, profit_pipe, region_filter, ship_mode_filter
    )
    return summarize_recommendation(product_name, result, speed_weight)


def build_full_recommendation_table(all_results: dict, speed_weight=0.5):
    """
    Ranked list of reassignment suggestions across ALL products - powers
    the Recommendation Dashboard. Takes the pre-computed dict from
    evaluate_all_products_across_factories() (cheap to re-score, no model
    inference happens here) so this is safe to call on every slider move.
    """
    rows = []
    for product, result in all_results.items():
        s = summarize_recommendation(product, result, speed_weight)
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
            "Historical Orders": s["order_count"],
            "Confidence": s["confidence"],
        })
    out = pd.DataFrame(rows)
    out = out.sort_values("Lead Time Gain (days)", ascending=False)
    return out


if __name__ == "__main__":
    df = pd.read_csv(PROCESSED_PATH)
    lead_pipe, profit_pipe = load_models()
    all_results = evaluate_all_products_across_factories(df, lead_pipe, profit_pipe)
    table = build_full_recommendation_table(all_results, speed_weight=0.5)
    print(table.to_string(index=False))
    table.to_csv("outputs/recommendations.csv", index=False)