import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from utils.theme import apply_power_bi_theme, configure_plotly_chart
from utils.live_connectors import (
    fetch_bsp_rates,
    fetch_psa_openstat_macro,
    fetch_dbm_budget_data,
    fetch_bettergov_customs_data,
    fetch_oecd_trade_benchmarks
)

# 1. Page Configuration
st.set_page_config(
    page_title="PH Macro & Economic Zone Portal",
    page_icon="🇵🇭",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_power_bi_theme()

# 2. Live Data Acquisition
with st.spinner("Executing live scrapers and DuckDB queries against official portals..."):
    df_bsp = fetch_bsp_rates()
    df_psa = fetch_psa_openstat_macro()
    df_dbm = fetch_dbm_budget_data()
    df_customs = fetch_bettergov_customs_data()
    df_oecd = fetch_oecd_trade_benchmarks()

# 3. Dynamic Sidebar Slicers (Bound directly to live database values)
st.sidebar.markdown("### 🇵🇭 Power BI Live Slicer")

available_ports = ["All Districts / EcoZones"]
if not df_customs.empty and "Customs_District" in df_customs.columns:
    unique_ports = sorted([str(p) for p in df_customs["Customs_District"].unique() if p])
    available_ports.extend(unique_ports)

selected_port = st.sidebar.selectbox("ECONOMIC ZONE / CUSTOMS PORT", available_ports)

min_year = int(df_customs["Year"].min()) if not df_customs.empty else 2018
max_year = int(df_customs["Year"].max()) if not df_customs.empty else 2026
selected_years = st.sidebar.slider("YEAR SCOPE", min_value=min_year, max_value=max_year, value=(min_year, max_year))

# Filter Customs Data dynamically
df_customs_filtered = df_customs.copy()
if not df_customs_filtered.empty:
    df_customs_filtered = df_customs_filtered[
        (df_customs_filtered["Year"] >= selected_years[0]) & 
        (df_customs_filtered["Year"] <= selected_years[1])
    ]
    if selected_port != "All Districts / EcoZones":
        df_customs_filtered = df_customs_filtered[df_customs_filtered["Customs_District"] == selected_port]

# 4. Top Header Action Bar
head_col1, head_col2 = st.columns([3, 1])
with head_col1:
    st.markdown("<h2 style='margin-bottom:0px; color:#0F172A; font-weight:800;'>Philippine Economic Zone & Macro Portal</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B; font-size:0.95rem;'>Live Data Feed | BSP, PSA OpenSTAT, DBM, BetterGov Customs & OECD</p>", unsafe_allow_html=True)

with head_col2:
    st.markdown("<div style='text-align: right; margin-top: 10px;'>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Live Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown(f"<span style='font-size:0.75rem; color:#0369A1;'>Last Ping: {datetime.now().strftime('%H:%M:%S')}</span></div>", unsafe_allow_html=True)

st.markdown("---")

# 5. Executive KPI Ribbon
k1, k2, k3, k4 = st.columns(4)

bsp_val = f"{df_bsp['Value_Pct'].iloc[0]}%" if not df_bsp.empty else "N/A"
bsp_lbl = df_bsp['Metric'].iloc[0] if not df_bsp.empty else "BSP Policy Rate"

psa_val = f"{df_psa['GDP_Growth_Rate'].iloc[-1]}%" if not df_psa.empty else "N/A"
psa_year = f"Year {df_psa['Year'].iloc[-1]}" if not df_psa.empty else "PSA Series"

cust_landed = f"₱{round(df_customs_filtered['Import_Landed_Cost_Billion'].sum(), 2)}B" if not df_customs_filtered.empty else "₱0B"
cust_duties = f"₱{round(df_customs_filtered['Duty_Collected_Billion'].sum(), 2)}B" if not df_customs_filtered.empty else "₱0B"

with k1:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>{bsp_lbl}</div><div class='kpi-value'>{bsp_val}</div><div class='kpi-sub'>Official Central Bank Rate</div></div>", unsafe_allow_html=True)

with k2:
    st.markdown(f"<div class='kpi-card' style='border-left-color: #00A896;'><div class='kpi-title'>Latest PSA GDP Growth</div><div class='kpi-value'>{psa_val}</div><div class='kpi-sub'>{psa_year} Real Indicator</div></div>", unsafe_allow_html=True)

with k3:
    st.markdown(f"<div class='kpi-card' style='border-left-color: #F59E0B;'><div class='kpi-title'>Total Landed Cost</div><div class='kpi-value'>{cust_landed}</div><div class='kpi-sub'>{selected_port}</div></div>", unsafe_allow_html=True)

with k4:
    st.markdown(f"<div class='kpi-card' style='border-left-color: #10B981;'><div class='kpi-title'>Duties Collected</div><div class='kpi-value'>{cust_duties}</div><div class='kpi-sub'>BetterGov Customs Dataset</div></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 6. Tabbed Analytics Canvas
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Customs & District Imports",
    "🏦 Official BSP & PSA Macro Series",
    "🏛️ DBM Budget & OECD Benchmarks",
    "🔍 Active Raw Dataset Explorer"
])

with tab1:
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("<div class='pbi-card'><b>Import Landed Cost by District & Year (₱ Billion)</b>", unsafe_allow_html=True)
        if not df_customs_filtered.empty:
            df_chart1 = df_customs_filtered.groupby("Year")["Import_Landed_Cost_Billion"].sum().reset_index()
            fig1 = px.bar(df_chart1, x="Year", y="Import_Landed_Cost_Billion", text_auto=True)
            st.plotly_chart(configure_plotly_chart(fig1, height=450), use_container_width=True)
        else:
            st.info("No customs data available for the selected parameters.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='pbi-card'><b>Customs Duties Collected vs Landed Cost Ratio</b>", unsafe_allow_html=True)
        if not df_customs_filtered.empty:
            fig2 = px.scatter(
                df_customs_filtered,
                x="Import_Landed_Cost_Billion",
                y="Duty_Collected_Billion",
                color="Customs_District",
                size="Total_Declarations" if "Total_Declarations" in df_customs_filtered.columns else None,
                hover_name="Year"
            )
            st.plotly_chart(configure_plotly_chart(fig2, height=450), use_container_width=True)
        else:
            st.info("No customs data available for scatter plot.")
        st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    m1, m2 = st.columns([1, 1])
    with m1:
        st.markdown("<div class='pbi-card'><b>Official PSA GDP Growth Rate Trend (%)</b>", unsafe_allow_html=True)
        if not df_psa.empty:
            fig_psa = px.line(df_psa, x="Year", y="GDP_Growth_Rate", markers=True)
            st.plotly_chart(configure_plotly_chart(fig_psa, height=450), use_container_width=True)
        else:
            st.warning("PSA OpenSTAT API connection pending response.")
        st.markdown("</div>", unsafe_allow_html=True)

    with m2:
        st.markdown("<div class='pbi-card'><b>Scraped BSP Target Rates Summary</b>", unsafe_allow_html=True)
        if not df_bsp.empty:
            st.dataframe(df_bsp, use_container_width=True, hide_index=True)
        else:
            st.warning("BSP Web Scraper returned no rows.")
        st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    d1, d2 = st.columns([1, 1])
    with d1:
        st.markdown("<div class='pbi-card'><b>DBM GAA / NEP Budget Document Index</b>", unsafe_allow_html=True)
        if not df_dbm.empty:
            st.dataframe(df_dbm, use_container_width=True, hide_index=True)
        else:
            st.info("DBM budget tables not parsed.")
        st.markdown("</div>", unsafe_allow_html=True)

    with d2:
        st.markdown("<div class='pbi-card'><b>OECD Economic Zone Releases Feed</b>", unsafe_allow_html=True)
        if not df_oecd.empty:
            st.dataframe(df_oecd, use_container_width=True, hide_index=True)
        else:
            st.info("OECD search query yielded no structured tables.")
        st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.markdown("### 🔍 Live Dataset Inspector")
    active_dataset = st.selectbox("Select Active Engine:", ["BetterGov Customs Parquet", "PSA GDP Growth API", "BSP Rates Scraper", "DBM Budget Scraper"])
    
    if active_dataset == "BetterGov Customs Parquet":
        st.dataframe(df_customs_filtered, use_container_width=True, hide_index=True)
    elif active_dataset == "PSA GDP Growth API":
        st.dataframe(df_psa, use_container_width=True, hide_index=True)
    elif active_dataset == "BSP Rates Scraper":
        st.dataframe(df_bsp, use_container_width=True, hide_index=True)
    else:
        st.dataframe(df_dbm, use_container_width=True, hide_index=True)
