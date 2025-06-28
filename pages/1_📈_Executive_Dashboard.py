# pages/1_📈_Executive_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import api_client

st.set_page_config(page_title="Executive Dashboard", layout="wide")

# Apply the same CSS theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary-color: #008080;
        --accent-color: #0047AB;
        --background-color: #F0F2F6;
        --text-color: #31333F;
        --card-background: #FFFFFF;
        --success-color: #2E8B57;
        --error-color: #DC143C;
        --warning-color: #FF8C00;
        --border-color: #E0E0E0;
    }
    
    .metric-card {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid var(--primary-color);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .notification-card {
        background: var(--card-background);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        margin-bottom: 0.75rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .notification-card.optimization {
        border-left: 4px solid #4CAF50;
    }
    
    .notification-card.risk {
        border-left: 4px solid #FF5722;
    }
    
    .notification-card.suggestion {
        border-left: 4px solid #2196F3;
    }
    
    .section-header {
        color: var(--primary-color);
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--border-color);
    }
    
    .kpi-group {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }
    
    .chart-container {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Executive Dashboard")
st.markdown("**Manager's Briefing** - Real-time overview of AP operation health and performance")

# Fetch data from the backend
kpi_data = api_client.get_kpis()
notifications = api_client.get_notifications()

if not kpi_data:
    st.error("⚠️ Could not fetch KPI data from the backend. Please ensure the API is running.")
    st.stop()

# --- LIVE AP HEALTH SECTION ---
st.markdown('<h2 class="section-header">🟢 Live AP Health</h2>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="kpi-group"><h3>Operational Efficiency</h3>', unsafe_allow_html=True)
    
    op_eff = kpi_data.get("operational_efficiency", {})
    
    # Enhanced KPIs with context and deltas
    touchless_rate = op_eff.get("touchless_invoice_rate_percent", 0)
    col1_1, col1_2 = st.columns(2)
    
    with col1_1:
        st.metric(
            "Touchless Rate", 
            f"{touchless_rate:.1f}%",
            delta=f"+{touchless_rate-85:.1f}% vs target",  # Assuming 85% target
            help="Percentage of invoices processed without manual review"
        )
        # Progress bar
        st.progress(min(touchless_rate/100, 1.0))
    
    with col1_2:
        in_review_count = op_eff.get("invoices_in_review_queue", 0)
        st.metric(
            "Invoices for Review", 
            str(in_review_count),
            delta=f"-{max(0, 50-in_review_count)} vs avg",  # Assuming avg of 50
            help="Current number of invoices requiring manual attention"
        )
        if in_review_count > 75:
            st.error("🚨 High review queue")
        elif in_review_count > 50:
            st.warning("⚠️ Elevated review queue")
        else:
            st.success("✅ Normal review queue")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="kpi-group"><h3>Financial Health</h3>', unsafe_allow_html=True)
    
    fin_opt = kpi_data.get("financial_optimization", {})
    
    col2_1, col2_2, col2_3 = st.columns(3)
    
    with col2_1:
        discounts_captured = fin_opt.get("discounts_captured", "$0")
        st.metric(
            "Discounts Captured",
            discounts_captured,
            delta="+12% vs last month",
            help="Value of early payment discounts successfully taken"
        )
    
    with col2_2:
        discounts_missed = fin_opt.get("discounts_missed", "$0")
        st.metric(
            "Discounts Missed",
            discounts_missed,
            delta="-8% vs last month",
            delta_color="inverse",
            help="Value of missed early payment discounts"
        )
    
    with col2_3:
        dpo = fin_opt.get("days_payable_outstanding_proxy", 0)
        st.metric(
            "Avg. Payment Time",
            f"{dpo} Days",
            delta=f"-{max(0, 30-dpo)} vs target",
            help="Average days to pay invoices after receipt"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- PERFORMANCE ANALYSIS SECTION ---
st.markdown('<h2 class="section-header">📈 Performance Analysis</h2>', unsafe_allow_html=True)

col1, col2 = st.columns([0.6, 0.4])

with col1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("Invoice Status Funnel")
    
    # Create mock funnel data (in real implementation, this would come from the backend)
    funnel_data = {
        "Total Ingested": 1000,
        "Successfully Matched": 850,
        "Auto-Approved": 720,
        "Paid": 680,
        "Needs Review": 130  # Branch from Total Ingested
    }
    
    # Create funnel chart
    fig = go.Figure()
    
    # Main funnel flow
    fig.add_trace(go.Funnel(
        y = ["Total Ingested", "Successfully Matched", "Auto-Approved", "Paid"],
        x = [funnel_data["Total Ingested"], funnel_data["Successfully Matched"], 
             funnel_data["Auto-Approved"], funnel_data["Paid"]],
        textposition = "inside",
        texttemplate = "%{label}<br>%{value}",
        textfont = {"family": "Inter", "size": 12},
        marker = {"color": ["#008080", "#20B2AA", "#48D1CC", "#E0FFFF"]},
        connector = {"line": {"color": "#008080", "dash": "solid", "width": 2}}
    ))
    
    fig.update_layout(
        title={
            "text": "Invoice Processing Efficiency Flow",
            "font": {"family": "Inter", "size": 16}
        },
        font={"family": "Inter"},
        height=400,
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add efficiency metrics below the chart
    efficiency_rate = (funnel_data["Auto-Approved"] / funnel_data["Total Ingested"]) * 100
    review_rate = (funnel_data["Needs Review"] / funnel_data["Total Ingested"]) * 100
    
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("Processing Efficiency", f"{efficiency_rate:.1f}%")
    with metric_col2:
        st.metric("Review Rate", f"{review_rate:.1f}%")
    with metric_col3:
        st.metric("Payment Rate", f"{(funnel_data['Paid']/funnel_data['Auto-Approved']*100):.1f}%")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("Manager's Briefing")
    
    if notifications:
        # Categorize notifications
        optimizations = [n for n in notifications if n.get('type') == 'Optimization']
        risks = [n for n in notifications if n.get('type') == 'Risk']
        suggestions = [n for n in notifications if n.get('type') != 'Optimization' and n.get('type') != 'Risk']
        
        # Display categorized notifications
        for category, items, icon, css_class in [
            ("💡 Optimizations", optimizations, "💡", "optimization"),
            ("⚠️ Risks", risks, "🚨", "risk"),
            ("🤖 Suggestions", suggestions, "🧠", "suggestion")
        ]:
            if items:
                st.markdown(f"**{category}**")
                for notif in items[:3]:  # Show top 3 per category
                    st.markdown(f'''
                    <div class="notification-card {css_class}">
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                            <span style="font-size: 1.2rem; margin-right: 0.5rem;">{icon}</span>
                            <strong>{notif.get('type', 'Alert')}</strong>
                        </div>
                        <p style="margin: 0; color: var(--text-color);">{notif.get('message', '')}</p>
                        <div style="margin-top: 0.5rem;">
                            <button style="background: none; border: none; color: var(--primary-color); cursor: pointer; font-size: 0.9rem;">
                                → Take Action
                            </button>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.success("✅ No high-priority notifications at the moment.")
        st.markdown("""
        <div class="notification-card optimization">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">✅</span>
                <strong>System Health</strong>
            </div>
            <p style="margin: 0; color: var(--text-color);">All systems operating normally. AP automation is running smoothly.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- QUICK NAVIGATION ---
st.markdown("---")
st.markdown("### Quick Navigation")

nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

with nav_col1:
    if st.button("🛠️ Review Exceptions", use_container_width=True):
        st.switch_page("pages/3_🛠️_Invoice_Workbench.py")

with nav_col2:
    if st.button("📥 Upload Documents", use_container_width=True):
        st.switch_page("pages/2_📥_Document_Hub.py")

with nav_col3:
    if st.button("🧠 View AI Insights", use_container_width=True):
        st.switch_page("pages/4_🧠_AI_Insights.py")

with nav_col4:
    if st.button("🔎 Explore Data", use_container_width=True):
        st.switch_page("pages/5_��_Data_Explorer.py") 