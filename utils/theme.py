import streamlit as st

POWER_BI_COLORS = ["#005B94", "#00A896", "#F59E0B", "#EF4444", "#10B981", "#6366F1", "#8B5CF6", "#64748B"]

def apply_power_bi_theme():
    """Injects custom CSS to enforce a full-width Power BI layout without padding."""
    st.markdown(
        """
        <style>
            .block-container {
                padding: 1rem 1.5rem !important;
                max-width: 100% !important;
            }
            .stApp {
                background-color: #F8FAFC;
            }
            [data-testid="stSidebar"] {
                background-color: #0F172A !important;
                border-right: 1px solid #1E293B;
            }
            [data-testid="stSidebar"] * {
                color: #E2E8F0 !important;
            }
            .pbi-card {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 16px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
                margin-bottom: 12px;
            }
            .kpi-card {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-left: 5px solid #005B94;
                border-radius: 8px;
                padding: 14px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            }
            .kpi-title {
                color: #64748B;
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 4px;
            }
            .kpi-value {
                color: #0F172A;
                font-size: 1.65rem;
                font-weight: 800;
                line-height: 1.2;
            }
            .kpi-sub {
                color: #64748B;
                font-size: 0.8rem;
                font-weight: 500;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

def configure_plotly_chart(fig, height=480):
    """Formats Plotly charts to match Power BI card styling with transparent backgrounds."""
    fig.update_layout(
        autosize=True,
        height=height,
        margin=dict(l=15, r=15, t=40, b=15),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Segoe UI, sans-serif", size=12, color="#334155"),
        colorway=POWER_BI_COLORS,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor="#E2E8F0", showline=True, linecolor="#CBD5E1"),
        yaxis=dict(gridcolor="#E2E8F0", showline=True, linecolor="#CBD5E1")
    )
    return fig
