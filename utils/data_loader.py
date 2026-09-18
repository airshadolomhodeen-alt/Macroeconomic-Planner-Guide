import streamlit as st
import pandas as pd
import numpy as np
from typing import Tuple, Optional

REQUIRED_COLUMNS = [
    "Year", "Period", "Valuation", "GDP_Growth", "Inflation_Rate",
    "Policy_Rate", "Per_Capita_GDP", "Household_Consumption",
    "Gov_Spending", "Capital_Formation", "Exports", "Imports",
    "Agriculture", "Industry", "Services", "Net_Primary_Income"
]

@st.cache_data(ttl=3600)
def generate_mock_openstat_data() -> pd.DataFrame:
    """Generates synthetic data matching 13 official PSA OpenSTAT series specs (2000–2026)."""
    np.random.seed(42)
    records = []
    years = list(range(2000, 2027))
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    valuations = ["At Current Prices", "At Constant 2018 Prices"]

    for yr in years:
        for qtr in quarters:
            for val in valuations:
                multiplier = 1.0 if val == "At Constant 2018 Prices" else (1.0 + (yr - 2000) * 0.035)
                
                # Base Macro Metrics
                if yr == 2020:
                    gdp_growth = np.round(np.random.normal(-9.5, 1.5), 2)
                elif yr == 2021:
                    gdp_growth = np.round(np.random.normal(5.7, 1.0), 2)
                else:
                    gdp_growth = np.round(np.random.normal(6.2, 0.8), 2)

                inflation = np.round(np.random.uniform(2.0, 5.8), 2)
                policy_rate = np.round(inflation + np.random.uniform(0.5, 2.5), 2)
                per_capita_gdp = np.round((140000 + (yr - 2000) * 6500) * multiplier, 2)

                # Sectoral & Expenditure Breakdown (in Billion PHP)
                base_gdp = (4000 + (yr - 2000) * 450) * multiplier
                agri = np.round(base_gdp * 0.09, 2)
                ind = np.round(base_gdp * 0.29, 2)
                srv = np.round(base_gdp * 0.62, 2)

                hfce = np.round(base_gdp * 0.72, 2)
                gfce = np.round(base_gdp * 0.15, 2)
                gcf = np.round(base_gdp * 0.23, 2)
                exp = np.round(base_gdp * 0.27, 2)
                imp = np.round(base_gdp * 0.37, 2)

                npi = np.round((250 + (yr - 2000) * 20) * multiplier, 2)

                records.append({
                    "Year": yr,
                    "Period": qtr,
                    "Valuation": val,
                    "GDP_Growth": gdp_growth,
                    "Inflation_Rate": inflation,
                    "Policy_Rate": policy_rate,
                    "Per_Capita_GDP": per_capita_gdp,
                    "Household_Consumption": hfce,
                    "Gov_Spending": gfce,
                    "Capital_Formation": gcf,
                    "Exports": exp,
                    "Imports": imp,
                    "Agriculture": agri,
                    "Industry": ind,
                    "Services": srv,
                    "Net_Primary_Income": npi
                })

    return pd.DataFrame(records)

@st.cache_data(ttl=600)
def parse_uploaded_csv(uploaded_file) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Parses and validates user-uploaded CSV datasets against expected macro schema."""
    try:
        df = pd.read_csv(uploaded_file)
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        
        if missing_cols:
            return None, f"Uploaded CSV missing required columns: {', '.join(missing_cols)}"
        
        df["Year"] = df["Year"].astype(int)
        return df, None
    except Exception as e:
        return None, f"Error processing file: {str(e)}"
