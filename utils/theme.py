import streamlit as st
import plotly.io as pio

POWER_BI_COLORS = [
    "#005B94",  # Power BI Primary Blue
    "#00A896",  # Teal Accent
    "#F59E0B",  # Amber Accent
    "#EF4444",  # Red Delta / Outflow
    "#10B981",  # Green Delta / Growth
    "#6366F1",  # Indigo Accent
    "#8B5CF6",  # Purple Accent
    "#64748B"   # Muted Slate
]

def apply_custom_css() -> None:
    """Injects custom CSS to replicate Power BI executive dashboard styling."""
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #F8F9FA;
            }
            [data-testid="stSidebar"] {
                background-color: #0F172A !important;
            }
            [data-testid="stSidebar"] * {
                color: #E2E8F0 !important;
            }
            [data-testid="stSidebar"] .stSelectbox label,
            [data-testid="stSidebar"] .stSlider label,
            [data-testid="stSidebar"] .stRadio label {
                color: #94A3B8 !important;
                font-weight: 600;
                font-size: 0.85rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            div[data-testid="stMetric"] {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 16px 20px;
                box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
            }
            div[data-testid="stMetric"] label {
                color: #64748B !important;
                font-size: 0.825rem !important;
                font-weight: 700 !important;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            div[data-testid="stMetricValue"] {
                color: #0F172A !important;
                font-size: 1.75rem !important;
                font-weight: 800 !important;
            }
            .header-title {
                font-size: 1.85rem;
                font-weight: 800;
                color: #0F172A;
                margin-bottom: 4px;
            }
            .header-subtitle {
                font-size: 0.925rem;
                color: #64748B;
                margin-bottom: 16px;
            }
            .timestamp-badge {
                background-color: #E2E8F0;
                color: #334155;
                font-size: 0.75rem;
                padding: 4px 10px;
                border-radius: 12px;
                font-weight: 600;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

def set_plotly_theme() -> None:
    """Configures a global Plotly template aligned with Power BI color palettes."""
    template = pio.templates["plotly_white"]
    template.layout.colorway = POWER_BI_COLORS
    template.layout.font.family = "Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, sans-serif"
    template.layout.title.font.color = "#0F172A"
    template.layout.title.font.size = 16
    template.layout.paper_bgcolor = "rgba(0,0,0,0)"
    template.layout.plot_bgcolor = "rgba(0,0,0,0)"
    template.layout.xaxis.gridcolor = "#E2E8F0"
    template.layout.yaxis.gridcolor = "#E2E8F0"
    pio.templates["power_bi"] = template
    pio.templates.default = "power_bi"
