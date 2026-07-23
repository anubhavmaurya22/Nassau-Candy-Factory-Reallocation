import plotly.express as px
import streamlit as st

from utils import load_data, load_full_recommendations

st.set_page_config(page_title="Risk & Impact Panel", page_icon="⚠️", layout="wide")
st.title("⚠️ Risk & Impact Panel")
st.caption("Profit impact alerts and high-risk reassignment warnings.")

df = load_data()

speed_weight = st.sidebar.slider(
    "Optimization priority (0 = profit, 1 = speed)",
    0.0, 1.0, 0.5, 0.05, key="risk_speedweight",
)

table = load_full_recommendations(speed_weight)
risky = table[table["High Risk"]]
safe_reassignments = table[table["Reassignment Suggested"] & ~table["High Risk"]]
profit_losses = table[table["Profit Margin Change"] < 0]
low_confidence_reassignments = table[table["Reassignment Suggested"] & (table["Confidence"] == "Low")]

col1, col2, col3, col4 = st.columns(4)
col1.metric("🔴 High-Risk Reassignments", len(risky))
col2.metric("🟢 Safe Reassignments", len(safe_reassignments))
col3.metric("📉 Any Profit Decline", len(profit_losses))
col4.metric("🟡 Low-Confidence Reassignments", len(low_confidence_reassignments))

st.markdown("---")

if len(low_confidence_reassignments):
    st.subheader("🟡 Low-Confidence Reassignments")
    st.markdown(
        "These products have **fewer than 20 historical orders** backing "
        "their current-factory numbers. The recommendation may be directionally "
        "correct, but shouldn't be treated as statistically conclusive - "
        "collect more shipment data before acting."
    )
    st.dataframe(
        low_confidence_reassignments.style.format({
            "Lead Time Gain (days)": "{:.2f}",
            "Profit Margin Change": "{:+.2%}",
        }),
        use_container_width=True, hide_index=True,
    )
    st.markdown("---")

if len(risky):
    st.subheader("🔴 High-Risk Reassignments")
    st.markdown(
        "These reassignments score well on the composite (speed+profit) "
        "metric, but would **reduce profit margin by more than 1 point** — "
        "review manually before implementing."
    )
    st.dataframe(
        risky.style.format({
            "Lead Time Gain (days)": "{:.2f}",
            "Profit Margin Change": "{:+.2%}",
        }),
        use_container_width=True, hide_index=True,
    )
else:
    st.success("No high-risk reassignments flagged at this priority setting.")

st.markdown("---")
st.subheader("Profit impact across all products")
fig = px.scatter(
    table, x="Lead Time Gain (days)", y="Profit Margin Change",
    color="High Risk", size=table["Lead Time Gain (days)"].abs() + 0.1,
    hover_name="Product",
    color_discrete_map={True: "#E4572E", False: "#4C6EF5"},
    title="Lead-Time Gain vs Profit Impact (bottom-right = fast but costly)",
)
fig.add_hline(y=0, line_dash="dash", line_color="gray")
fig.add_vline(x=0, line_dash="dash", line_color="gray")
fig.update_yaxes(tickformat=".0%")
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Top-right quadrant = win-win reassignments (faster AND more "
    "profitable). Bottom-right = fast but erodes margin — treat with "
    "caution even if not formally flagged as high-risk."
)