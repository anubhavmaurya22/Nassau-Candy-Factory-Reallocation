"""
Generates the core EDA charts used in the research paper.
Run with: python notebooks/eda.py   (from project root)
Outputs saved to outputs/charts/
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, "src")
from reference_data import FACTORIES

OUT_DIR = "outputs/charts"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams.update({"figure.dpi": 130, "font.size": 10})


def savefig(name):
    path = f"{OUT_DIR}/{name}.png"
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"saved {path}")


def main():
    df = pd.read_csv("data/processed.csv")

    # 1. Orders by Division
    plt.figure(figsize=(6, 4))
    df["Division_clean"].value_counts().plot(kind="bar", color="#4C6EF5")
    plt.title("Order Volume by Division")
    plt.ylabel("Number of Orders")
    plt.xlabel("")
    plt.xticks(rotation=0)
    savefig("01_orders_by_division")

    # 2. Ship Mode distribution
    plt.figure(figsize=(6, 4))
    df["Ship Mode"].value_counts().plot(kind="bar", color="#2F9E44")
    plt.title("Order Volume by Ship Mode")
    plt.ylabel("Number of Orders")
    plt.xlabel("")
    plt.xticks(rotation=20)
    savefig("02_ship_mode_distribution")

    # 3. Profit margin by division (boxplot)
    plt.figure(figsize=(6, 4))
    df.boxplot(column="ProfitMargin", by="Division_clean", grid=False)
    plt.title("Profit Margin Distribution by Division")
    plt.suptitle("")
    plt.ylabel("Profit Margin")
    plt.xlabel("")
    savefig("03_profit_margin_by_division")

    # 4. Current distance-to-factory distribution
    plt.figure(figsize=(6, 4))
    df["DistanceToFactoryMiles"].dropna().plot(kind="hist", bins=30, color="#E4572E")
    plt.title("Distribution: Customer Distance to CURRENT Assigned Factory")
    plt.xlabel("Distance (miles)")
    savefig("04_current_distance_distribution")

    # 5. Average distance by factory (current assignment only)
    plt.figure(figsize=(6, 4))
    df.groupby("Factory")["DistanceToFactoryMiles"].mean().sort_values().plot(
        kind="barh", color="#845EF7"
    )
    plt.title("Avg Customer Distance by Currently-Assigned Factory")
    plt.xlabel("Average Distance (miles)")
    savefig("05_avg_distance_by_factory")

    # 6. Orders by region
    plt.figure(figsize=(6, 4))
    df["Region"].value_counts().plot(kind="bar", color="#F59F00")
    plt.title("Order Volume by Customer Region")
    plt.xticks(rotation=0)
    savefig("06_orders_by_region")

    # 7. Factory + customer-region map (scatter, no basemap needed)
    plt.figure(figsize=(7, 5))
    plt.scatter(df["cust_lon"], df["cust_lat"], s=5, alpha=0.15, color="gray", label="Customers")
    for name, coords in FACTORIES.items():
        plt.scatter(coords["lon"], coords["lat"], s=180, marker="^", label=name, edgecolor="black")
    plt.title("Factory Locations vs Customer Base")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.legend(fontsize=7, loc="lower left")
    savefig("07_factory_customer_map")

    # 8. Recommendation summary (requires models to be trained already)
    try:
        import joblib
        from optimizer import build_full_recommendation_table
        lead_pipe = joblib.load("models/lead_time_model.pkl")
        profit_pipe = joblib.load("models/profit_margin_model.pkl")
        table = build_full_recommendation_table(df, lead_pipe, profit_pipe, speed_weight=0.5)
        table.to_csv("outputs/recommendations.csv", index=False)

        plt.figure(figsize=(7, 5))
        colors = table["High Risk"].map({True: "#E4572E", False: "#4C6EF5"})
        plt.barh(table["Product"], table["Lead Time Gain (days)"], color=colors)
        plt.title("Predicted Lead-Time Gain by Product (red = high risk)")
        plt.xlabel("Lead Time Gain (days)")
        savefig("08_recommendation_summary")
    except FileNotFoundError:
        print("Models not found yet - skipping recommendation chart. Run model.py first.")

    print("\nEDA chart generation complete.")


if __name__ == "__main__":
    main()
