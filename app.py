import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ==========================================
# Page Configuration
# ==========================================
st.set_page_config(
    page_title="Macroeconomic Planner Guide | PH",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# Data Loading & Caching
# ==========================================
@st.cache_data
def load_mock_data():
    """
    Generates mock macroeconomic data mimicking PSA, BSP, and DBM datasets.
    In production, replace this with pd.read_csv() reading from your uploaded datasets.
    """
    years = np.arange(2010, 2025)
    
    # Simulate Philippine Macroeconomic indicators
    # Base trends with some random noise to simulate real-world economic cycles
    gdp_growth = np.random.normal(loc=6.0, scale=1.5, size=len(years))
    gdp_growth[10] = -9.5 # 2020 COVID dip simulation
    
    inflation_rate = np.random.normal(loc=3.5, scale=1.2, size=len(years))
    inflation_rate[12] = 5.8 # 2022 inflation spike simulation
    
    policy_rate = inflation_rate * 0.8 + np.random.normal(loc=1.0, scale=0.5, size=len(years))
    
    gov_spending_budget = np.linspace(1500, 5700, len(years)) + np.random.normal(0, 100, len(years))
    
    data = pd.DataFrame({
        "Year": years,
        "GDP Growth (%)": np.round(gdp_growth, 1),
        "Inflation Rate (%)": np.round(inflation_rate, 1),
        "Policy Rate (%)": np.round(policy_rate, 1),
        "Gov Spending (B PHP)": np.round(gov_spending_budget, 1)
    })
    
    # Sectoral Data for Bar Chart
    sectors = ['Agriculture', 'Industry', 'Services']
    sector_data = []
    for year in years:
        for sector in sectors:
            base_val = 100 if sector == 'Agriculture' else (300 if sector == 'Industry' else 500)
            growth = np.random.normal(1.05, 0.02)
            sector_data.append({
                "Year": year,
                "Sector": sector,
                "Gross Value Added": round(base_val * (growth ** (year - 2009)), 1)
            })
            
    df_macro = data
    df_sector = pd.DataFrame(sector_data)
    
    return df_macro, df_sector

# Load data
df_macro, df_sector = load_mock_data()

# ==========================================
# Sidebar Navigation & Filters
# ==========================================
st.sidebar.title("⚙️ Dashboard Controls")
st.sidebar.markdown("Filter the macroeconomic data below.")

# 1. File Uploader for custom datasets
uploaded_file = st.sidebar.file_uploader("Upload Custom CSV (Optional)", type=['csv'])
if uploaded_file is not None:
    try:
        df_macro = pd.read_csv(uploaded_file)
        st.sidebar.success("Custom data loaded successfully!")
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")

# 2. Year Range Slider
min_year, max_year = int(df_macro["Year"].min()), int(df_macro["Year"].max())
selected_years = st.sidebar.slider(
    "Select Year Range:",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

# 3. Metric Selector
available_metrics = [col for col in df_macro.columns if col != "Year"]
selected_metrics = st.sidebar.multiselect(
    "Select Metrics for Line Chart:",
    options=available_metrics,
    default=["GDP Growth (%)", "Inflation Rate (%)"]
)

st.sidebar.markdown("---")
st.sidebar.info("Data Sources Context: PSA, BSP, DBM, Open Data PH.")

# ==========================================
# Data Filtering
# ==========================================
filtered_macro = df_macro[
    (df_macro["Year"] >= selected_years[0]) & 
    (df_macro["Year"] <= selected_years[1])
].reset_index(drop=True)

filtered_sector = df_sector[
    (df_sector["Year"] >= selected_years[0]) & 
    (df_sector["Year"] <= selected_years[1])
].reset_index(drop=True)

# ==========================================
# Main Dashboard Layout
# ==========================================
st.title("🇵🇭 Macroeconomic Planner Guide")
st.markdown("A unified dashboard for analyzing Philippine economic indicators, fiscal policy, and sectoral growth.")

# --- KPI HEADER (Scorecard) ---
if not filtered_macro.empty:
    latest_year = filtered_macro["Year"].max()
    latest_data = filtered_macro[filtered_macro["Year"] == latest_year].iloc[0]
    
    # Get previous year for delta calculations
    prev_data = df_macro[df_macro["Year"] == (latest_year - 1)]
    
    def get_delta(metric):
        if not prev_data.empty:
            return round(latest_data[metric] - prev_data.iloc[0][metric], 2)
        return None

    # Layout for KPIs
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.metric(label=f"GDP Growth ({latest_year})", 
                  value=f"{latest_data.get('GDP Growth (%)', 0)}%", 
                  delta=f"{get_delta('GDP Growth (%)')}% YoY" if get_delta('GDP Growth (%)') is not None else None)
    with kpi2:
        # Inverse delta color for inflation (higher is usually worse)
        st.metric(label=f"Inflation Rate ({latest_year})", 
                  value=f"{latest_data.get('Inflation Rate (%)', 0)}%", 
                  delta=f"{get_delta('Inflation Rate (%)')}% YoY" if get_delta('Inflation Rate (%)') is not None else None,
                  delta_color="inverse")
    with kpi3:
        st.metric(label=f"Policy Rate ({latest_year})", 
                  value=f"{latest_data.get('Policy Rate (%)', 0)}%", 
                  delta=f"{get_delta('Policy Rate (%)')}% YoY" if get_delta('Policy Rate (%)') is not None else None,
                  delta_color="off")
    with kpi4:
        st.metric(label=f"Gov Spending ({latest_year})", 
                  value=f"₱{latest_data.get('Gov Spending (B PHP)', 0):,.1f} B", 
                  delta=f"₱{get_delta('Gov Spending (B PHP)')} B YoY" if get_delta('Gov Spending (B PHP)') is not None else None)
else:
    st.warning("No data available for the selected date range.")

st.markdown("---")

# --- INTERACTIVE VISUALIZATIONS ---

col_left, col_right = st.columns(2)

# 1. Line Chart: Historical Trends
with col_left:
    st.subheader("Historical Economic Trends")
    if selected_metrics and not filtered_macro.empty:
        fig_line = px.line(
            filtered_macro, 
            x="Year", 
            y=selected_metrics,
            markers=True,
            title="Selected Macroeconomic Indicators Over Time",
            template="plotly_white"
        )
        fig_line.update_layout(legend_title_text='Indicators', xaxis=dict(dtick=1))
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Please select at least one metric from the sidebar.")

# 2. Bar Chart: Sectoral Breakdown
with col_right:
    st.subheader("Sectoral Gross Value Added")
    if not filtered_sector.empty:
        fig_bar = px.bar(
            filtered_sector, 
            x="Year", 
            y="Gross Value Added", 
            color="Sector", 
            barmode="stack",
            title="Economic Contribution by Sector (Mock GVA)",
            template="plotly_white"
        )
        fig_bar.update_layout(xaxis=dict(dtick=1))
        st.plotly_chart(fig_bar, use_container_width=True)

# 3. Scatter Plot: Correlation
st.subheader("Correlation: Inflation vs. Policy Rate")
if not filtered_macro.empty and "Inflation Rate (%)" in filtered_macro.columns and "Policy Rate (%)" in filtered_macro.columns:
    fig_scatter = px.scatter(
        filtered_macro, 
        x="Inflation Rate (%)", 
        y="Policy Rate (%)", 
        size="Gov Spending (B PHP)",
        color="GDP Growth (%)",
        hover_name="Year",
        title="Bubble Size = Gov Spending | Color = GDP Growth",
        template="plotly_white",
        trendline="ols" # Requires statsmodels, omitted for base streamlit unless installed
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.warning("Scatter plot requires 'Inflation Rate (%)' and 'Policy Rate (%)' columns.")

st.markdown("---")

# --- RAW DATA TABLE ---
st.subheader("Raw Data View")
with st.expander("View and Export Underlying Data", expanded=False):
    st.dataframe(filtered_macro, use_container_width=True)
    
    # Allow CSV download
    csv = filtered_macro.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Data as CSV",
        data=csv,
        file_name='macro_data_ph.csv',
        mime='text/csv',
    )
