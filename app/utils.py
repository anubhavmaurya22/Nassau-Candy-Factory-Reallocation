"""Shared helpers for the Streamlit app: path setup, cached data/model loading."""
import os
import sys

import joblib
import pandas as pd
import streamlit as st

# Make src/ importable from the app
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(APP_DIR)
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from reference_data import FACTORIES, PRODUCT_FACTORY, PRODUCT_DIVISION  # noqa: E402
from optimizer import (  # noqa: E402
    evaluate_product_across_factories,
    evaluate_all_products_across_factories,
    score_factories,
    summarize_recommendation,
    recommend_for_product,
    build_full_recommendation_table,
)

PROCESSED_PATH = os.path.join(ROOT_DIR, "data", "processed.csv")
MODEL_DIR = os.path.join(ROOT_DIR, "models")


@st.cache_data
def load_data():
    return pd.read_csv(PROCESSED_PATH)


@st.cache_resource
def load_models():
    lead_pipe = joblib.load(os.path.join(MODEL_DIR, "lead_time_model.pkl"))
    profit_pipe = joblib.load(os.path.join(MODEL_DIR, "profit_margin_model.pkl"))
    return lead_pipe, profit_pipe


@st.cache_data
def load_all_predictions(region_filter=None, ship_mode_filter=None):
    """
    THE EXPENSIVE STEP: runs both ML models across every (product, factory)
    pair. Cached independent of the speed/profit slider, so moving the
    slider never re-triggers model inference - only the cheap scoring step
    (build_full_recommendation_table) re-runs, which is pure arithmetic on
    a ~75-row table and is effectively instant.
    """
    df = load_data()
    lead_pipe, profit_pipe = load_models()
    return evaluate_all_products_across_factories(
        df, lead_pipe, profit_pipe, region_filter=region_filter, ship_mode_filter=ship_mode_filter
    )


def load_full_recommendations(speed_weight: float, region_filter=None, ship_mode_filter=None):
    """Cheap re-scoring step - safe to call on every slider tick."""
    all_results = load_all_predictions(region_filter, ship_mode_filter)
    return build_full_recommendation_table(all_results, speed_weight)


@st.cache_data
def evaluate_product_cached(product_name, region_filter=None, ship_mode_filter=None):
    """Cached expensive step for a single product (used by the Factory
    Simulator and What-If Analysis pages). Cached independent of the
    speed/profit slider - only re-runs when product/region/ship-mode
    filters actually change."""
    df = load_data()
    lead_pipe, profit_pipe = load_models()
    return evaluate_product_across_factories(
        df, product_name, lead_pipe, profit_pipe, region_filter, ship_mode_filter
    )


def sidebar_filters(df: pd.DataFrame, key_prefix: str = ""):
    """Shared sidebar controls: product, region, ship mode, speed/profit slider."""
    st.sidebar.header("Filters")

    products = sorted(df["Product Name"].unique())
    product = st.sidebar.selectbox("Product", products, key=f"{key_prefix}_product")

    regions = ["All"] + sorted(df["Region"].unique())
    region = st.sidebar.selectbox("Region", regions, key=f"{key_prefix}_region")
    region = None if region == "All" else region

    ship_modes = ["All"] + sorted(df["Ship Mode"].unique())
    ship_mode = st.sidebar.selectbox("Ship Mode", ship_modes, key=f"{key_prefix}_shipmode")
    ship_mode = None if ship_mode == "All" else ship_mode

    st.sidebar.markdown("---")
    speed_weight = st.sidebar.slider(
        "Optimization priority",
        min_value=0.0, max_value=1.0, value=0.5, step=0.05,
        key=f"{key_prefix}_speedweight",
        help="0 = pure profit optimization, 1 = pure speed optimization",
    )
    col1, col2 = st.sidebar.columns(2)
    col1.caption("⬅ Profit")
    col2.markdown("<div style='text-align:right'>Speed ➡</div>", unsafe_allow_html=True)

    return product, region, ship_mode, speed_weight