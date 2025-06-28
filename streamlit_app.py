# streamlit_app.py
import streamlit as st

# --- SUPERVITY PRO THEME CONFIGURATION ---
st.set_page_config(
    page_title="Supervity Pro - AP Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR SUPERVITY PRO THEME ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Variables */
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
    
    /* Main App Styling */
    .main .block-container {
        font-family: 'Inter', sans-serif;
        color: var(--text-color);
        background-color: var(--background-color);
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background-color: var(--card-background);
        border-right: 2px solid var(--border-color);
    }
    
    /* Headers and Typography */
    h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: var(--primary-color);
        border-bottom: 3px solid var(--primary-color);
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }
    
    h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: var(--text-color);
    }
    
    /* Custom Cards */
    .metric-card {
        background: var(--card-background);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid var(--primary-color);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .welcome-card {
        background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .feature-card {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        margin-bottom: 1rem;
        transition: box-shadow 0.3s ease;
    }
    
    .feature-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Buttons */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        transition: background-color 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: var(--accent-color);
    }
    
    /* Status Indicators */
    .status-online {
        color: var(--success-color);
        font-weight: 600;
    }
    
    .status-offline {
        color: var(--error-color);
        font-weight: 600;
    }
    
    /* Icons */
    .nav-icon {
        font-size: 1.2rem;
        margin-right: 0.5rem;
    }
    
    /* Logo Styling */
    .logo {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 1rem;
    }
    
    .logo h2 {
        margin: 0;
        color: var(--primary-color);
        font-weight: 700;
    }
    
    .logo .tagline {
        font-size: 0.8rem;
        color: var(--text-color);
        opacity: 0.7;
        margin-top: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR BRANDING ---
with st.sidebar:
    st.markdown("""
    <div class="logo">
        <h2>⚡ Supervity Pro</h2>
        <div class="tagline">AI-Powered AP Command Center</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Navigation")
    st.markdown("""
    Use the pages in the sidebar to access different modules:
    
    **📊 Dashboard** - Executive overview and KPIs  
    **📥 Document Hub** - Upload and process documents  
    **🛠️ Workbench** - Invoice review and resolution  
    **🧠 AI Insights** - Intelligence and recommendations  
    **🔎 Data Explorer** - Advanced search and analytics  
    **⚙️ Configuration** - System settings and rules  
    """)

# --- MAIN WELCOME INTERFACE ---
st.markdown("""
<div class="welcome-card">
    <h1 style="color: white; border: none; margin-bottom: 1rem;">Welcome to Supervity Pro</h1>
    <p style="font-size: 1.1rem; margin-bottom: 0;">
        Your AI-powered partner for intelligent accounts payable management. 
        Experience unprecedented efficiency with enterprise-grade automation.
    </p>
</div>
""", unsafe_allow_html=True)

# --- SYSTEM STATUS ---
col1, col2, col3 = st.columns(3)

with col1:
    try:
        import api_client
        response = api_client.get_kpis()
        if response:
            st.markdown('<div class="status-online">🟢 Backend Status: Online</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-offline">🔴 Backend Status: Offline</div>', unsafe_allow_html=True)
    except:
        st.markdown('<div class="status-offline">🔴 Backend Status: Offline</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="status-online">🟢 AI Copilot: Ready</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="status-online">🟢 Document Processing: Active</div>', unsafe_allow_html=True)

st.markdown("---")

# --- FEATURE OVERVIEW ---
st.markdown("## Core Capabilities")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>📊 Executive Dashboard</h3>
        <p>Real-time KPIs, performance metrics, and manager's briefings. Get immediate visibility into your AP operation's health and efficiency.</p>
    </div>
    
    <div class="feature-card">
        <h3>🛠️ Invoice Workbench</h3>
        <p>Power-user workspace for exception resolution with AI assistance. Streamlined workflow for maximum efficiency.</p>
    </div>
    
    <div class="feature-card">
        <h3>🔎 Data Explorer</h3>
        <p>Advanced search and analytics across all invoice data. Flexible filtering and comprehensive reporting capabilities.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>📥 Document Hub</h3>
        <p>Intelligent document upload and processing with real-time monitoring. Automated extraction and validation.</p>
    </div>
    
    <div class="feature-card">
        <h3>🧠 AI Insights</h3>
        <p>Proactive intelligence feed with learned patterns and optimization recommendations. Continuous improvement.</p>
    </div>
    
    <div class="feature-card">
        <h3>⚙️ Configuration</h3>
        <p>Secure system settings, vendor management, and automation rule configuration. Enterprise-grade controls.</p>
    </div>
    """, unsafe_allow_html=True)

# --- QUICK ACTIONS ---
st.markdown("## Quick Actions")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📊 View Dashboard", use_container_width=True):
        st.switch_page("pages/1_📈_Executive_Dashboard.py")

with col2:
    if st.button("📥 Upload Documents", use_container_width=True):
        st.switch_page("pages/2_📥_Document_Hub.py")

with col3:
    if st.button("🛠️ Review Invoices", use_container_width=True):
        st.switch_page("pages/3_🛠️_Invoice_Workbench.py")

with col4:
    if st.button("🧠 AI Insights", use_container_width=True):
        st.switch_page("pages/4_��_AI_Insights.py") 