import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

from utils.theme import apply_custom_css, set_plotly_theme
from utils.data_loader import (
    generate_mock_openstat_data,
    load_open_customs_data,
    execute_openstat_api_query,
    parse_uploaded_csv,
    OPENSTAT_SCHEMAS
)

# Initialize Layout and Styling
apply_custom_css()
set_plotly_theme()

# ==========================================
# 1. Sidebar Executive Controls
# ==========================================
st.sidebar.markdown("### 🇵🇭 Macro Planner")
st.sidebar.caption("Power BI Decision Workspace")

data_source = st.sidebar.radio(
    "SELECT ENGINE DATA SOURCE:",
    ["PSA OPENSTAT SERIES", "BETTERGOV PH CUSTOMS DATA (HUGGING FACE)", "CUSTOM CSV IMPORT"]
)

uploaded_df = None
if data_source == "CUSTOM CSV IMPORT":
    file_upload = st.sidebar.file_uploader("Upload CSV Data", type=["csv"])
    if file_upload:
        parsed_data, err = parse_uploaded_csv(file_upload)
        if err:
            st.sidebar.error(err)
        else:
            uploaded_df = parsed_data
            st.sidebar.success("CSV Loaded Successfully!")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Dynamic Filters")

selected_table = "5. GDP by Industry"
selected_item = "..Gross Domestic Product"

if data_source == "PSA OPENSTAT SERIES":
    selected_table = st.sidebar.selectbox("OPENSTAT TABLE ENDPOINT:", list(OPENSTAT_SCHEMAS.keys()))
    cfg = OPENSTAT_SCHEMAS[selected_table]
    selected_item = st.sidebar.selectbox("INDICATOR SUB-CATEGORY:", cfg["items"])

valuation_type = st.sidebar.selectbox("VALUATION SERIES", ["At Constant 2018 Prices", "At Current Prices"])
frequency = st.sidebar.selectbox("REPORT FREQUENCY", ["Annual Aggregated", "Quarterly"])

# Active Engine Router
if data_source == "PSA OPENSTAT SERIES":
    with st.spinner(f"Querying OpenSTAT API ({selected_table})..."):
        raw_df = execute_openstat_api_query(selected_table, selected_item, valuation_type)
elif data_source == "BETTERGOV PH CUSTOMS DATA (HUGGING FACE)":
    with st.spinner("Streaming Parquet dataset via DuckDB HTTPFS..."):
        raw_df = load_open_customs_data()
elif data_source == "CUSTOM CSV IMPORT" and uploaded_df is not None:
    raw_df = uploaded_df
else:
    raw_df = generate_mock_openstat_data()

year_min = int(raw_df["Year"].min())
year_max = int(raw_df["Year"].max())
year_range = st.sidebar.slider("YEAR RANGE SCOPE", min_value=year_min, max_value=year_max, value=(2012, year_max))

# Filter Application
filtered_df = raw_df[(raw_df["Year"] >= year_range[0]) & (raw_df["Year"] <= year_range[1])].copy()

if "Valuation" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Valuation"] == valuation_type]

if frequency == "Annual Aggregated":
    numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns.tolist()
    agg_dict = {col: "mean" if "Rate" in col or "Growth" in col else "sum" for col in numeric_cols if col != "Year"}
    view_df = filtered_df.groupby("Year").agg(agg_dict).reset_index()
    view_df["Time_Index"] = view_df["Year"].astype(str)
else:
    view_df = filtered_df.copy()
    view_df["Time_Index"] = view_df["Year"].astype(str) + " " + view_df.get("Period", "Q1")

view_df = view_df.sort_values(by="Year")

# Sidebar Data Portals
st.sidebar.markdown("---")
st.sidebar.markdown("### 🌐 Data Portals")
st.sidebar.markdown("[📊 PSA OpenSTAT](https://openstat.psa.gov.ph/)")
st.sidebar.markdown("[🇵🇭 PH BetterGov PH Data](https://data.bettergov.ph/)")
st.sidebar.markdown("[🤗 Hugging Face Dataset](https://huggingface.co/datasets/bettergovph/open-customs-data)")

# ==========================================
# 2. Main Dashboard Header & KPI Grid
# ==========================================
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown('<div class="header-title">Philippine Macroeconomic & Trade Planner</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="header-subtitle">Active Engine Source: <b>{data_source}</b> | Target: <b>{selected_item}</b></div>', unsafe_allow_html=True)
with header_col2:
    st.markdown(f'<div style="text-align: right; padding-top: 10px;"><span class="timestamp-badge">Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</span></div>', unsafe_allow_html=True)

if len(view_df) >= 2:
    curr = view_df.iloc[-1]
    prev = view_df.iloc[-2]
    gdp_delta = np.round(curr.get("GDP_Growth", 0) - prev.get("GDP_Growth", 0), 2)
    inf_delta = np.round(curr.get("Inflation_Rate", 0) - prev.get("Inflation_Rate", 0), 2)
    pol_delta = np.round(curr.get("Policy_Rate", 0) - prev.get("Policy_Rate", 0), 2)
    cap_delta = np.round(((curr.get("Per_Capita_GDP", 1) - prev.get("Per_Capita_GDP", 1)) / max(prev.get("Per_Capita_GDP", 1), 1)) * 100, 2)
else:
    curr = view_df.iloc[-1] if len(view_df) > 0 else {}
    gdp_delta, inf_delta, pol_delta, cap_delta = 0, 0, 0, 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("LATEST GDP GROWTH", f"{curr.get('GDP_Growth', 0):.1f}%", f"{gdp_delta:+.2f}% vs prev")
kpi2.metric("INFLATION RATE", f"{curr.get('Inflation_Rate', 0):.1f}%", f"{inf_delta:+.2f}% vs prev", delta_color="inverse")
kpi3.metric("BSP POLICY RATE", f"{curr.get('Policy_Rate', 0):.2f}%", f"{pol_delta:+.2f}% vs prev", delta_color="inverse")
kpi4.metric("PER CAPITA GDP", f"₱{curr.get('Per_Capita_GDP', 0):,.0f}", f"{cap_delta:+.2f}% vs prev")

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 3. Dynamic Visualizations
# ==========================================
tab1, tab2, tab3 = st.tabs(["📈 Historical Trends", "📊 Sectoral & Expenditure Shares", "🔄 Macro Correlations"])

with tab1:
    st.markdown(f"**Historical Trajectory: {selected_item}**")
    y_cols = ["Selected_Value"] if "Selected_Value" in view_df.columns else ["GDP_Growth", "Inflation_Rate"]
    fig_trends = px.line(view_df, x="Time_Index", y=y_cols, markers=True, labels={"Time_Index": "Timeline Period", "value": "Value"})
    fig_trends.update_layout(height=420)
    st.plotly_chart(fig_trends, use_container_width=True)

with tab2:
    col_sec1, col_sec2 = st.columns(2)
    with col_sec1:
        st.markdown("**Gross Value Added by Industry (Billion ₱)**")
        fig_industry = px.bar(view_df, x="Time_Index", y=["Agriculture", "Industry", "Services"], barmode="stack")
        fig_industry.update_layout(height=400)
        st.plotly_chart(fig_industry, use_container_width=True)

    with col_sec2:
        st.markdown("**Expenditure / Trade Breakdown (Billion ₱)**")
        fig_expenditure = px.bar(view_df, x="Time_Index", y=["Household_Consumption", "Gov_Spending", "Capital_Formation", "Exports"], barmode="group")
        fig_expenditure.update_layout(height=400)
        st.plotly_chart(fig_expenditure, use_container_width=True)

with tab3:
    st.markdown("**Macroeconomic Correlation Engine**")
    fig_corr = px.scatter(view_df, x="Inflation_Rate", y="Policy_Rate", size="Per_Capita_GDP", color="GDP_Growth", trendline="ols")
    fig_corr.update_layout(height=420)
    st.plotly_chart(fig_corr, use_container_width=True)

# ==========================================
# 4. Filtered Data Explorer
# ==========================================
st.markdown("---")
with st.expander("🔍 Tabular Data Explorer & Export Engine", expanded=False):
    st.dataframe(view_df, use_container_width=True, hide_index=True)
    st.download_button(
        label="📥 Export Filtered Dataset (CSV)",
        data=view_df.to_csv(index=False).encode("utf-8"),
        file_name=f"openstat_export_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
