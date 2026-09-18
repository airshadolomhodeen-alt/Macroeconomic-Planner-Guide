import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

from utils.theme import apply_custom_css, set_plotly_theme
from utils.data_loader import generate_mock_openstat_data, parse_uploaded_csv

# Initialize Theme & Layout Settings
apply_custom_css()
set_plotly_theme()

# ==========================================
# 1. Sidebar Executive Controls
# ==========================================
st.sidebar.markdown("### 🇵🇭 Macro Planner")
st.sidebar.caption("Power BI Decision Workspace")

data_source = st.sidebar.radio(
    "Data Engine Source:",
    ["PSA OpenSTAT (Mock Series)", "Custom CSV Import"]
)

uploaded_df = None
if data_source == "Custom CSV Import":
    file_upload = st.sidebar.file_uploader(
        "Upload CSV Data",
        type=["csv"],
        help="Upload datasets structured with standard macro series headers."
    )
    if file_upload:
        parsed_data, err = parse_uploaded_csv(file_upload)
        if err:
            st.sidebar.error(err)
        else:
            uploaded_df = parsed_data
            st.sidebar.success("CSV Loaded Successfully!")

# Load Active Dataset
if uploaded_df is not None:
    raw_df = uploaded_df
else:
    raw_df = generate_mock_openstat_data()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Dynamic Filters")

year_range = st.sidebar.slider(
    "Year Range Scope",
    min_value=int(raw_df["Year"].min()),
    max_value=int(raw_df["Year"].max()),
    value=(2010, 2026)
)

frequency = st.sidebar.selectbox(
    "Report Frequency",
    ["Quarterly", "Annual Aggregated"]
)

valuation_type = st.sidebar.selectbox(
    "Valuation Series",
    ["At Constant 2018 Prices", "At Current Prices"]
)

# Apply Dataset Filtering
filtered_df = raw_df[
    (raw_df["Year"] >= year_range[0]) &
    (raw_df["Year"] <= year_range[1]) &
    (raw_df["Valuation"] == valuation_type)
].copy()

if frequency == "Annual Aggregated":
    group_cols = ["Year", "Valuation"]
    agg_dict = {
        "GDP_Growth": "mean",
        "Inflation_Rate": "mean",
        "Policy_Rate": "mean",
        "Per_Capita_GDP": "mean",
        "Household_Consumption": "sum",
        "Gov_Spending": "sum",
        "Capital_Formation": "sum",
        "Exports": "sum",
        "Imports": "sum",
        "Agriculture": "sum",
        "Industry": "sum",
        "Services": "sum",
        "Net_Primary_Income": "sum"
    }
    view_df = filtered_df.groupby(group_cols).agg(agg_dict).reset_index()
    view_df["Time_Index"] = view_df["Year"].astype(str)
else:
    view_df = filtered_df.copy()
    view_df["Time_Index"] = view_df["Year"].astype(str) + " " + view_df["Period"]

# Sort chronological order
view_df = view_df.sort_values(by=["Year"] + ([] if frequency == "Annual Aggregated" else ["Period"]))

# ==========================================
# 2. Main Dashboard Header
# ==========================================
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown('<div class="header-title">Philippine Macroeconomic Planner</div>', unsafe_allow_html=True)
    st.markdown('<div class="header-subtitle">Cross-filtering analytics based on PSA OpenSTAT National Accounts and BSP Financial Series.</div>', unsafe_allow_html=True)
with header_col2:
    st.markdown(f'<div style="text-align: right; padding-top: 10px;"><span class="timestamp-badge">Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</span></div>', unsafe_allow_html=True)

# ==========================================
# 3. Power BI Card Grid (KPI Scorecards)
# ==========================================
if len(view_df) >= 2:
    curr = view_df.iloc[-1]
    prev = view_df.iloc[-2]
    
    gdp_delta = np.round(curr["GDP_Growth"] - prev["GDP_Growth"], 2)
    inf_delta = np.round(curr["Inflation_Rate"] - prev["Inflation_Rate"], 2)
    pol_delta = np.round(curr["Policy_Rate"] - prev["Policy_Rate"], 2)
    cap_delta = np.round(((curr["Per_Capita_GDP"] - prev["Per_Capita_GDP"]) / prev["Per_Capita_GDP"]) * 100, 2)
else:
    curr = view_df.iloc[-1] if len(view_df) > 0 else {}
    gdp_delta, inf_delta, pol_delta, cap_delta = 0, 0, 0, 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Latest GDP Growth", f"{curr.get('GDP_Growth', 0):.1f}%", f"{gdp_delta:+.2f}% vs prev")
kpi2.metric("Inflation Rate", f"{curr.get('Inflation_Rate', 0):.1f}%", f"{inf_delta:+.2f}% vs prev", delta_color="inverse")
kpi3.metric("BSP Policy Rate", f"{curr.get('Policy_Rate', 0):.2f}%", f"{pol_delta:+.2f}% vs prev", delta_color="inverse")
kpi4.metric("Per Capita GDP", f"₱{curr.get('Per_Capita_GDP', 0):,.0f}", f"{cap_delta:+.2f}% vs prev")

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 4. Interactive Visual Analytics Workspace
# ==========================================
tab1, tab2, tab3 = st.tabs(["📈 Historical Trends", "📊 Sectoral & Expenditure Shares", "🔄 Macro Correlations"])

with tab1:
    st.markdown("**GDP Growth Rate vs Inflation Trajectory**")
    fig_trends = px.line(
        view_df,
        x="Time_Index",
        y=["GDP_Growth", "Inflation_Rate", "Policy_Rate"],
        labels={"value": "Percentage (%)", "Time_Index": "Timeline Period", "variable": "Indicator"},
        markers=True
    )
    fig_trends.update_traces(hovertemplate="%{x}<br>%{series.name}: <b>%{y:.2f}%</b>")
    fig_trends.update_layout(height=420, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_trends, use_container_width=True)

with tab2:
    col_sec1, col_sec2 = st.columns(2)
    
    with col_sec1:
        st.markdown("**Gross Value Added by Industry (Billion ₱)**")
        fig_industry = px.bar(
            view_df,
            x="Time_Index",
            y=["Agriculture", "Industry", "Services"],
            labels={"value": "Billion PHP", "Time_Index": "Timeline Period", "variable": "Sector"},
            barmode="stack"
        )
        fig_industry.update_layout(height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_industry, use_container_width=True)

    with col_sec2:
        st.markdown("**GDP Expenditure Breakdown (Billion ₱)**")
        fig_expenditure = px.bar(
            view_df,
            x="Time_Index",
            y=["Household_Consumption", "Gov_Spending", "Capital_Formation", "Exports"],
            labels={"value": "Billion PHP", "Time_Index": "Timeline Period", "variable": "Component"},
            barmode="group"
        )
        fig_expenditure.update_layout(height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_expenditure, use_container_width=True)

with tab3:
    st.markdown("**Policy Rate vs Inflation Rate Dynamics**")
    fig_corr = px.scatter(
        view_df,
        x="Inflation_Rate",
        y="Policy_Rate",
        size="Per_Capita_GDP",
        color="GDP_Growth",
        hover_name="Time_Index",
        trendline="ols",
        labels={
            "Inflation_Rate": "Inflation Rate (%)",
            "Policy_Rate": "BSP Policy Rate (%)",
            "GDP_Growth": "GDP Growth (%)",
            "Per_Capita_GDP": "Per Capita GDP"
        },
        color_continuous_scale="Blues"
    )
    fig_corr.update_layout(height=420)
    st.plotly_chart(fig_corr, use_container_width=True)

# ==========================================
# 5. Filtered Data Explorer
# ==========================================
st.markdown("---")
with st.expander("🔍 Tabular Data Explorer & Export Engine", expanded=False):
    st.markdown("Filter and export the processed macroeconomic series.")
    
    # Column selector
    available_cols = [c for c in view_df.columns if c not in ["Valuation", "Time_Index"]]
    selected_cols = st.multiselect("Select Display Columns:", available_cols, default=["Year", "Period", "GDP_Growth", "Inflation_Rate", "Policy_Rate", "Per_Capita_GDP"] if frequency != "Annual Aggregated" else ["Year", "GDP_Growth", "Inflation_Rate", "Policy_Rate", "Per_Capita_GDP"])
    
    display_df = view_df[selected_cols] if selected_cols else view_df
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    csv_bytes = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Filtered Dataset (CSV)",
        data=csv_bytes,
        file_name=f"ph_macro_planner_export_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
