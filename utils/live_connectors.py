import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import duckdb
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

@st.cache_data(ttl=600)
def fetch_bsp_rates() -> pd.DataFrame:
    """Scrapes official key target rates directly from the Bangko Sentral ng Pilipinas statistics page."""
    url = "https://www.bsp.gov.ph/SitePages/Statistics/Statistics.aspx"
    records = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            tables = soup.find_all("table")
            for table in tables:
                for row in table.find_all("tr"):
                    cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                    if len(cols) >= 2:
                        label, val = cols[0], cols[1]
                        if any(k in label.lower() for k in ["policy rate", "target reverse repurchase", "overnight", "inflation", "reserve requirement"]):
                            nums = re.findall(r"[-+]?\d*\.\d+|\d+", val)
                            if nums:
                                records.append({"Metric": label, "Value_Pct": float(nums[0])})
    except Exception as e:
        st.warning(f"BSP Scraping Note: {e}")
    
    return pd.DataFrame(records) if records else pd.DataFrame(columns=["Metric", "Value_Pct"])

@st.cache_data(ttl=600)
def fetch_psa_openstat_macro() -> pd.DataFrame:
    """Queries official PSA OpenSTAT API endpoint for Philippine national GDP growth series."""
    api_url = "https://openstat.psa.gov.ph/api/v1/data/National%20Accounts/GDP_Growth"
    try:
        res = requests.get(api_url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if "data" in data:
                df = pd.DataFrame(data["data"])
                df.rename(columns={"Year": "Year", "Value": "GDP_Growth_Rate"}, inplace=True)
                df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
                df["GDP_Growth_Rate"] = pd.to_numeric(df["GDP_Growth_Rate"], errors="coerce")
                return df.dropna().sort_values("Year")
    except Exception:
        pass
    
    return pd.DataFrame(columns=["Year", "GDP_Growth_Rate"])

@st.cache_data(ttl=600)
def fetch_dbm_budget_data() -> pd.DataFrame:
    """Scrapes national budget and expenditure summaries from DBM portal tables."""
    url = "https://www.dbm.gov.ph/"
    records = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                if any(k in a.text.lower() for k in ["gaa", "nep", "budget", "expenditure"]):
                    nums = re.findall(r"\b20\d{2}\b", a.text)
                    if nums:
                        records.append({"Year": int(nums[0]), "Document_Title": a.text.strip(), "Link": a["href"]})
    except Exception:
        pass
    
    return pd.DataFrame(records) if records else pd.DataFrame(columns=["Year", "Document_Title", "Link"])

@st.cache_data(ttl=1200)
def fetch_bettergov_customs_data() -> pd.DataFrame:
    """Queries real customs port transactions directly from BetterGov Hugging Face Parquet using DuckDB HTTPFS."""
    hf_parquet_url = "https://huggingface.co/datasets/bettergovph/open-customs-data/resolve/main/combined.parquet"
    try:
        conn = duckdb.connect()
        conn.execute("INSTALL httpfs; LOAD httpfs;")
        query = f"""
            SELECT 
                CAST(YEAR(TRY_CAST(date AS DATE)) AS INT) as Year,
                COALESCE(port_of_entry, 'Other District Port') as Customs_District,
                ROUND(SUM(TRY_CAST(total_landed_cost AS DOUBLE)) / 1e9, 2) as Import_Landed_Cost_Billion,
                ROUND(SUM(TRY_CAST(duty_paid AS DOUBLE)) / 1e9, 2) as Duty_Collected_Billion,
                COUNT(*) as Total_Declarations
            FROM '{hf_parquet_url}'
            WHERE date IS NOT NULL
            GROUP BY 1, 2
            HAVING Year BETWEEN 2015 AND 2026
            ORDER BY Year ASC, Import_Landed_Cost_Billion DESC
        """
        df = conn.execute(query).df()
        return df if not df.empty else pd.DataFrame(columns=["Year", "Customs_District", "Import_Landed_Cost_Billion", "Duty_Collected_Billion", "Total_Declarations"])
    except Exception as e:
        st.error(f"Customs Data Load Failure: {e}")
        return pd.DataFrame(columns=["Year", "Customs_District", "Import_Landed_Cost_Billion", "Duty_Collected_Billion", "Total_Declarations"])

@st.cache_data(ttl=1200)
def fetch_oecd_trade_benchmarks() -> pd.DataFrame:
    """Scrapes live OECD data catalog tables matching economic zones and FDI releases."""
    url = "https://www.oecd.org/en/search/data.html?orderBy=mostRelevant&page=0&facetTags=oecd-languages%3Aen%2Coecd-content-types%3Adata%2Fstatistical-release&q=economic+zone"
    records = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for item in soup.find_all(["div", "article", "li"]):
                text = item.get_text(separator=" ", strip=True)
                if "economic zone" in text.lower() or "trade" in text.lower():
                    records.append({"Source": "OECD Release", "Details": text[:180]})
    except Exception:
        pass
    
    return pd.DataFrame(records[:15]) if records else pd.DataFrame(columns=["Source", "Details"])
