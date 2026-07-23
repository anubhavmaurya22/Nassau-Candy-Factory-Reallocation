import plotly.express as px
import streamlit as st

from utils import load_data, load_full_recommendations

st.set_page_config(page_title="Recommendation Dashboard", page_icon="📊", layout="wide")
st.title("📊 Recommendation Dashboard")
st.caption("Ranked reassignment suggestions across all products.")

df = load_data()

st.sidebar.header("Priority")
speed_weight = st.sidebar.slider(
    "Optimization priority (0 = profit, 1 = speed)",
    0.0, 1.0, 0.5, 0.05, key="dash_speedweight",
)

show_only_reassignments = st.sidebar.checkbox("Show only suggested reassignments", value=True)
hide_low_confidence = st.sidebar.checkbox("Hide low-confidence recommendations", value=False)

full_table = load_full_recommendations(speed_weight)
table = full_table[full_table["Reassignment Suggested"]] if show_only_reassignments else full_table
if hide_low_confidence:
    table = table[table["Confidence"] != "Low"]

col1, col2, col3 = st.columns(3)
col1.metric("Products Analyzed", len(full_table))
col2.metric("Reassignments Suggested", int(full_table["Reassignment Suggested"].sum()))
col3.metric("High-Risk Flags", int(full_table["High Risk"].sum()))

st.markdown("---")

st.dataframe(
    table.style.format({
        "Lead Time Gain (days)": "{:.2f}",
        "Profit Margin Change": "{:+.2%}",
    }).map(
        lambda v: "background-color:#ffe3e3" if v is True else "",
        subset=["High Risk"],
    ).map(
        lambda v: {"Low": "background-color:#fff3bf", "Medium": "", "High": "background-color:#ebfbee"}.get(v, ""),
        subset=["Confidence"],
    ),
    use_container_width=True,
    hide_index=True,
)
st.caption(
    "🟢 High confidence = 100+ historical orders backing this product's current factory. "
    "🟡 Low confidence = fewer than 20 — treat as directional, not conclusive."
)

st.subheader("Expected lead-time gain by product")
fig = px.bar(
    table.sort_values("Lead Time Gain (days)", ascending=True),
    x="Lead Time Gain (days)", y="Product", orientation="h",
    color="High Risk", color_discrete_map={True: "#E4572E", False: "#4C6EF5"},
    height=500,
)
st.plotly_chart(fig, use_container_width=True)

csv = table.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download recommendations as CSV", csv, "recommendations.csv", "text/csv")