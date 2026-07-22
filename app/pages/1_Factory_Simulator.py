import pandas as pd
import plotly.express as px
import streamlit as st

from utils import (
    load_data,
    load_models,
    sidebar_filters,
    evaluate_product_across_factories,
    score_factories,
)

st.set_page_config(page_title="Factory Simulator", page_icon="📦", layout="wide")
st.title("📦 Factory Optimization Simulator")
st.caption("Select a product and see predicted performance across every factory.")

df = load_data()
lead_pipe, profit_pipe = load_models()

product, region, ship_mode, speed_weight = sidebar_filters(df, key_prefix="sim")

result = evaluate_product_across_factories(
    df, product, lead_pipe, profit_pipe, region_filter=region, ship_mode_filter=ship_mode
)

if result.empty:
    st.warning("No historical orders match this product + filter combination.")
    st.stop()

scored = score_factories(result, speed_weight)

st.subheader(f"Predicted performance: {product}")

display = scored[[
    "Rank", "Factory", "IsCurrent", "PredictedLeadTimeDays",
    "PredictedProfitMargin", "AvgDistanceMiles", "CompositeScore",
]].rename(columns={
    "IsCurrent": "Current Factory?",
    "PredictedLeadTimeDays": "Predicted Lead Time (days)",
    "PredictedProfitMargin": "Predicted Profit Margin",
    "AvgDistanceMiles": "Avg Distance (mi)",
    "CompositeScore": "Score",
})
st.dataframe(
    display.style.format({
        "Predicted Lead Time (days)": "{:.2f}",
        "Predicted Profit Margin": "{:.1%}",
        "Avg Distance (mi)": "{:.0f}",
        "Score": "{:.3f}",
    }),
    use_container_width=True,
    hide_index=True,
)

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(
        scored, x="Factory", y="PredictedLeadTimeDays",
        color="IsCurrent", title="Predicted Lead Time by Factory",
        labels={"PredictedLeadTimeDays": "Lead Time (days)"},
        color_discrete_map={True: "#E4572E", False: "#4C6EF5"},
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig2 = px.bar(
        scored, x="Factory", y="PredictedProfitMargin",
        color="IsCurrent", title="Predicted Profit Margin by Factory",
        labels={"PredictedProfitMargin": "Profit Margin"},
        color_discrete_map={True: "#E4572E", False: "#2F9E44"},
    )
    fig2.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig2, use_container_width=True)

best = scored.iloc[0]
st.success(
    f"**Top recommendation:** {best['Factory']} — "
    f"predicted lead time {best['PredictedLeadTimeDays']:.2f} days, "
    f"profit margin {best['PredictedProfitMargin']:.1%}."
)
