"""
Data preparation pipeline for the Nassau Candy Distributor project.

Run with:  python src/data_prep.py

Reads:  data/Nassau_Candy_Distributor.csv
Writes: data/processed.csv
"""
import math
import pandas as pd

from reference_data import (
    FACTORIES,
    PRODUCT_FACTORY,
    PRODUCT_DIVISION,
    SHIP_MODE_LEAD_DAYS,
    STATE_CENTROIDS,
    MILES_PER_EXTRA_DAY,
    SHIPPING_COST_PER_UNIT_PER_100_MILES,
)

RAW_PATH = "data/Nassau_Candy_Distributor.csv"
OUT_PATH = "data/processed.csv"


def haversine_miles(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points, in miles."""
    R = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def load_raw(path: str = RAW_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Basic hygiene
    df = df.drop_duplicates()
    df["Product Name"] = df["Product Name"].str.strip()

    # Assign current factory + division from the reference mapping
    df["Factory"] = df["Product Name"].map(PRODUCT_FACTORY)
    df["Division_clean"] = df["Product Name"].map(PRODUCT_DIVISION)

    unmapped = df[df["Factory"].isna()]["Product Name"].unique()
    if len(unmapped):
        print(f"WARNING: {len(unmapped)} product(s) have no factory mapping: {unmapped}")

    # Standardized lead time proxy from Ship Mode (see reference_data.py note
    # on why raw Order/Ship Date columns are not usable)
    df["LeadTimeProxyDays"] = df["Ship Mode"].map(SHIP_MODE_LEAD_DAYS)

    # Profit margin (target for the "profit" side of the optimization)
    df["ProfitMargin"] = df["Gross Profit"] / df["Sales"].replace(0, pd.NA)

    return df


def add_geo_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Customer location centroid (state/province level)
    df["cust_lat"] = df["State/Province"].map(lambda s: STATE_CENTROIDS.get(s, (None, None))[0])
    df["cust_lon"] = df["State/Province"].map(lambda s: STATE_CENTROIDS.get(s, (None, None))[1])

    missing_state = df[df["cust_lat"].isna()]["State/Province"].unique()
    if len(missing_state):
        print(f"WARNING: {len(missing_state)} state(s) missing centroid: {missing_state}")

    # Distance from the CURRENT assigned factory to the customer
    def dist_to_current_factory(row):
        fac = FACTORIES.get(row["Factory"])
        if fac is None or pd.isna(row["cust_lat"]):
            return None
        return haversine_miles(fac["lat"], fac["lon"], row["cust_lat"], row["cust_lon"])

    df["DistanceToFactoryMiles"] = df.apply(dist_to_current_factory, axis=1)

    # Distance-adjusted targets (see reference_data.py for assumptions)
    df["AdjustedLeadTimeDays"] = df["LeadTimeProxyDays"] + (
        df["DistanceToFactoryMiles"] / MILES_PER_EXTRA_DAY
    )
    df["ShippingCostEst"] = (
        df["Units"] * (df["DistanceToFactoryMiles"] / 100.0) * SHIPPING_COST_PER_UNIT_PER_100_MILES
    )
    df["AdjustedGrossProfit"] = df["Gross Profit"] - df["ShippingCostEst"]
    df["AdjustedProfitMargin"] = df["AdjustedGrossProfit"] / df["Sales"].replace(0, pd.NA)

    return df


def add_all_factory_distances(df: pd.DataFrame) -> pd.DataFrame:
    """Add distance-to-EVERY-factory columns. These are the features the
    trained model will use at inference time to score hypothetical
    (product, factory) reassignments it never saw historically."""
    df = df.copy()
    for fac_name, coords in FACTORIES.items():
        col = f"dist_{fac_name.replace(chr(39), '').replace(' ', '_')}"
        df[col] = df.apply(
            lambda r: haversine_miles(coords["lat"], coords["lon"], r["cust_lat"], r["cust_lon"])
            if pd.notna(r["cust_lat"]) else None,
            axis=1,
        )
    return df


def run(raw_path: str = RAW_PATH, out_path: str = OUT_PATH) -> pd.DataFrame:
    df = load_raw(raw_path)
    df = clean(df)
    df = add_geo_features(df)
    df = add_all_factory_distances(df)
    df.to_csv(out_path, index=False)
    print(f"Processed {len(df)} rows -> {out_path}")
    return df


if __name__ == "__main__":
    run()
