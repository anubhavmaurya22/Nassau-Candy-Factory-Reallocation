import plotly.graph_objects as go
import streamlit as st

from utils import load_data, load_models, sidebar_filters, recommend_for_product

st.set_page_config(page_title="What-If Analysis", page_icon="🔀", layout="wide")
st.title("🔀 What-If Scenario Analysis")
st.caption("Current assignment vs. recommended assignment, side by side.")

df = load_data()
lead_pipe, profit_pipe = load_models()

product, region, ship_mode, speed_weight = sidebar_filters(df, key_prefix="whatif")

summary = recommend_for_product(
    df, product, lead_pipe, profit_pipe, speed_weight,
    region_filter=region, ship_mode_filter=ship_mode,
)

if summary is None:
    st.warning("No historical orders match this product + filter combination.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Current Factory", summary["current_factory"])
col2.metric(
    "Recommended Factory", summary["recommended_factory"],
    delta="Reassignment suggested" if summary["is_reassignment"] else "No change needed",
    delta_color="normal" if summary["is_reassignment"] else "off",
)
col3.metric(
    "Lead Time Improvement",
    f"{summary['lead_time_gain_days']:.2f} days" if summary["lead_time_gain_days"] else "0 days",
)

if summary["high_risk"]:
    st.error(
        "⚠️ **High risk reassignment.** This move improves the weighted "
        "score but would REDUCE profit margin by "
        f"{abs(summary['profit_margin_change']):.1%}. Review before acting."
    )
elif summary["is_reassignment"]:
    st.success(
        f"✅ Reassigning improves profit margin by "
        f"{summary['profit_margin_change']:.1%} and lead time by "
        f"{summary['lead_time_gain_days']:.2f} days."
    )
else:
    st.info("Current factory is already optimal under this priority setting.")

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    fig = go.Figure(data=[
        go.Bar(name="Current", x=["Lead Time (days)"], y=[summary["current_lead_time"]], marker_color="#E4572E"),
        go.Bar(name="Recommended", x=["Lead Time (days)"], y=[summary["recommended_lead_time"]], marker_color="#4C6EF5"),
    ])
    fig.update_layout(title="Lead Time: Current vs Recommended", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig2 = go.Figure(data=[
        go.Bar(name="Current", x=["Profit Margin"], y=[summary["current_profit_margin"]], marker_color="#E4572E"),
        go.Bar(name="Recommended", x=["Profit Margin"], y=[summary["recommended_profit_margin"]], marker_color="#2F9E44"),
    ])
    fig2.update_layout(title="Profit Margin: Current vs Recommended", barmode="group", yaxis_tickformat=".0%")
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Full factory ranking for this scenario")
st.dataframe(
    summary["table"][[
        "Rank", "Factory", "IsCurrent", "PredictedLeadTimeDays",
        "PredictedProfitMargin", "CompositeScore",
    ]].rename(columns={
        "IsCurrent": "Current?",
        "PredictedLeadTimeDays": "Lead Time (days)",
        "PredictedProfitMargin": "Profit Margin",
        "CompositeScore": "Score",
    }).style.format({"Lead Time (days)": "{:.2f}", "Profit Margin": "{:.1%}", "Score": "{:.3f}"}),
    use_container_width=True,
    hide_index=True,
)
