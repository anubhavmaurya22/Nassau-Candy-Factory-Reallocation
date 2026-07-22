import streamlit as st
from utils import load_data, load_models

st.set_page_config(
    page_title="Nassau Candy | Factory Optimization",
    page_icon="🏭",
    layout="wide",
)

st.title("🏭 Nassau Candy Distributor — Factory Optimization Dashboard")

st.markdown("""
This dashboard moves Nassau Candy Distributor from **descriptive analytics**
to **intelligent decision-making**: it predicts shipping performance for
every product across all 5 factories and recommends reassignments that
improve delivery speed without sacrificing profit.

### Use the pages in the sidebar to explore:

**📦 Factory Optimization Simulator**
Pick any product and see predicted lead time & profit margin across all
5 factories.

**🔀 What-If Scenario Analysis**
Compare the current factory assignment against the recommended one,
side by side.

**📊 Recommendation Dashboard**
Ranked list of every product's reassignment suggestion, sorted by
expected efficiency gain.

**⚠️ Risk & Impact Panel**
Flags reassignments that look good on paper but carry real profit risk.

---
""")

df = load_data()
lead_pipe, profit_pipe = load_models()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Orders Analyzed", f"{len(df):,}")
col2.metric("Products", df["Product Name"].nunique())
col3.metric("Factories", 5)
col4.metric("Regions Served", df["Region"].nunique())

st.info(
    "⚠️ **Data note:** the raw Order Date / Ship Date columns in this "
    "dataset are corrupted by anonymization (Order IDs show 2021-2024, "
    "Order Date shows 2024-2025, Ship Date shows 2026-2030 — three "
    "inconsistent timelines). Lead time is instead estimated from Ship "
    "Mode plus a disclosed distance-based transit assumption. "
    "See the research paper for full methodology.",
    icon="ℹ️",
)
