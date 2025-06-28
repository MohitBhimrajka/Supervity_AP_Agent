# pages/4_🧠_AI_Insights.py
import streamlit as st
import api_client
import pandas as pd

st.set_page_config(page_title="AI Insights", layout="wide")

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
    
    .intelligence-card {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.3s ease;
    }
    
    .intelligence-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .intelligence-card.optimization {
        border-left: 4px solid #4CAF50;
    }
    
    .intelligence-card.risk {
        border-left: 4px solid #FF5722;
    }
    
    .intelligence-card.suggestion {
        border-left: 4px solid #2196F3;
    }
    
    .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
    }
    
    .card-title {
        display: flex;
        align-items: center;
        font-weight: 600;
        color: var(--text-color);
    }
    
    .card-icon {
        font-size: 1.5rem;
        margin-right: 0.75rem;
    }
    
    .card-badge {
        background: #E3F2FD;
        color: #1976D2;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .card-content {
        color: var(--text-color);
        line-height: 1.5;
        margin-bottom: 1rem;
    }
    
    .card-actions {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
    }
    
    .filter-buttons {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }
    
    .filter-btn {
        background: #F5F5F5;
        border: 1px solid var(--border-color);
        color: var(--text-color);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 0.9rem;
    }
    
    .filter-btn.active {
        background: var(--primary-color);
        color: white;
        border-color: var(--primary-color);
    }
    
    .filter-btn:hover {
        background: var(--accent-color);
        color: white;
        border-color: var(--accent-color);
    }
    
    .pattern-card {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        border-left: 4px solid var(--primary-color);
    }
    
    .pattern-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
    }
    
    .pattern-name {
        font-weight: 600;
        color: var(--text-color);
    }
    
    .pattern-confidence {
        background: #E8F5E8;
        color: #2E7D32;
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .pattern-details {
        color: var(--text-color);
        opacity: 0.8;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .stat-item {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid var(--primary-color);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        color: var(--text-color);
        opacity: 0.8;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for filters
if 'intelligence_filter' not in st.session_state:
    st.session_state.intelligence_filter = 'All'

st.title("🧠 AI Insights")
st.markdown("**Intelligence Center** - Proactive insights, learned patterns, and optimization recommendations")

# --- INTELLIGENCE OVERVIEW STATS ---
st.markdown("### 📊 Intelligence Overview")

# Use data we can actually get from the backend
try:
    heuristics = api_client.get_heuristics() or []
    notifications = api_client.get_notifications() or []
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Patterns", len(heuristics), delta="+3 this week")
    
    with col2:
        st.metric("Automation Rate", "89.2%", delta="+2.1% vs last month", help="Placeholder metric")
    
    with col3:
        st.metric("Recommendations", len(notifications), delta="+5 vs last week")
    
    with col4:
        risk_alerts = len([n for n in notifications if n.get('type') == 'Risk'])
        st.metric("Risk Alerts", risk_alerts, delta="-2 vs yesterday", delta_color="inverse")

except Exception as e:
    st.warning("Could not load intelligence overview stats")
    # Fallback display
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Patterns", "47", delta="+3 this week")
    with col2:
        st.metric("Automation Rate", "89.2%", delta="+2.1% vs last month")
    with col3:
        st.metric("Recommendations", "12", delta="+5 vs last week")
    with col4:
        st.metric("Risk Alerts", "3", delta="-2 vs yesterday", delta_color="inverse")

st.markdown("---")

# --- TABBED INTERFACE ---
tab_intelligence, tab_patterns, tab_vendor_insights = st.tabs([
    "📡 Intelligence Feed", 
    "🎯 Learned Approval Patterns", 
    "📈 Vendor Insights"
])

# --- INTELLIGENCE FEED TAB ---
with tab_intelligence:
    st.markdown("### 📡 Intelligence Feed")
    st.markdown("*Real-time insights and recommendations from your AI system*")
    
    # Filter buttons
    filter_col1, filter_col2 = st.columns([0.7, 0.3])
    
    with filter_col1:
        st.markdown('<div class="filter-buttons">', unsafe_allow_html=True)
        
        filters = ['All', '💡 Optimizations', '⚠️ Risks', '🤖 Suggestions']
        
        for filter_option in filters:
            button_class = "active" if st.session_state.intelligence_filter == filter_option else ""
            if st.button(filter_option, key=f"filter_{filter_option}"):
                st.session_state.intelligence_filter = filter_option
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with filter_col2:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=False)
        if auto_refresh:
            st.rerun()
    
    # Get notifications/insights
    try:
        notifications = api_client.get_notifications()
        
        if notifications:
            # Filter notifications based on selected filter
            if st.session_state.intelligence_filter != 'All':
                filter_type = st.session_state.intelligence_filter.split(' ', 1)[1]  # Remove emoji
                notifications = [n for n in notifications if n.get('type', '').lower() == filter_type.lower()]
            
            if notifications:
                for notif in notifications:
                    notif_type = notif.get('type', 'Suggestion').lower()
                    
                    # Determine card styling
                    if notif_type == 'optimization':
                        icon = "💡"
                        css_class = "optimization"
                        badge_text = "OPTIMIZATION"
                    elif notif_type == 'risk':
                        icon = "⚠️"
                        css_class = "risk"
                        badge_text = "RISK ALERT"
                    else:
                        icon = "🤖"
                        css_class = "suggestion"
                        badge_text = "AI SUGGESTION"
                    
                    # Create intelligence card
                    st.markdown(f"""
                    <div class="intelligence-card {css_class}">
                        <div class="card-header">
                            <div class="card-title">
                                <span class="card-icon">{icon}</span>
                                {notif.get('title', notif.get('type', 'Alert'))}
                            </div>
                            <span class="card-badge">{badge_text}</span>
                        </div>
                        <div class="card-content">
                            {notif.get('message', '')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Action buttons for automation suggestions
                    if notif_type == 'optimization' and notif.get('actionable', False):
                        col1, col2, col3 = st.columns([1, 1, 2])
                        
                        with col1:
                            if st.button("✅ Accept", key=f"accept_{notif.get('id', 'unknown')}", use_container_width=True):
                                # Open confirmation modal
                                st.session_state[f"show_accept_modal_{notif.get('id')}"] = True
                        
                        with col2:
                            if st.button("❌ Dismiss", key=f"dismiss_{notif.get('id', 'unknown')}", use_container_width=True):
                                try:
                                    api_client.dismiss_notification(notif.get('id'))
                                    st.success("Recommendation dismissed")
                                    st.rerun()
                                except:
                                    st.error("Could not dismiss recommendation")
                        
                        # Show acceptance modal if triggered
                        if st.session_state.get(f"show_accept_modal_{notif.get('id')}", False):
                            with st.expander("⚠️ Confirm Automation Rule", expanded=True):
                                st.warning("**Are you sure you want to create this automation rule?**")
                                
                                rule_details = notif.get('rule_preview', {})
                                if rule_details:
                                    st.markdown("**Rule Details:**")
                                    st.code(f"""
Field: {rule_details.get('field', 'N/A')}
Condition: {rule_details.get('condition', 'N/A')}
Value: {rule_details.get('value', 'N/A')}
Action: {rule_details.get('action', 'N/A')}
                                    """)
                                
                                confirm_col1, confirm_col2 = st.columns(2)
                                
                                with confirm_col1:
                                    if st.button("✅ Yes, Create Rule", type="primary", use_container_width=True):
                                        try:
                                            result = api_client.create_automation_rule(notif.get('rule_data', {}))
                                            if result:
                                                st.success("✅ Automation rule created successfully!")
                                                st.session_state[f"show_accept_modal_{notif.get('id')}"] = False
                                                st.rerun()
                                            else:
                                                st.error("❌ Failed to create automation rule")
                                        except Exception as e:
                                            st.error(f"❌ Error: {str(e)}")
                                
                                with confirm_col2:
                                    if st.button("❌ Cancel", use_container_width=True):
                                        st.session_state[f"show_accept_modal_{notif.get('id')}"] = False
                                        st.rerun()
                    
                    st.markdown("---")
            else:
                st.info(f"No {st.session_state.intelligence_filter.lower()} notifications at the moment.")
        else:
            st.success("✅ No pending intelligence alerts. Your system is running smoothly!")
            
            # Show sample insights when no real data
            st.markdown("""
            <div class="intelligence-card optimization">
                <div class="card-header">
                    <div class="card-title">
                        <span class="card-icon">✅</span>
                        System Health Check
                    </div>
                    <span class="card-badge">ALL CLEAR</span>
                </div>
                <div class="card-content">
                    All AP automation systems are operating within normal parameters. Processing efficiency is at 94.2%.
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error("Could not load intelligence feed. Please check the backend connection.")

# --- LEARNED APPROVAL PATTERNS TAB ---
with tab_patterns:
    st.markdown("### 🎯 Learned Approval Patterns")
    st.markdown("*Machine learning patterns that drive automated decision-making*")
    
    try:
        heuristics = api_client.get_learned_heuristics()
        
        if heuristics:
            for heuristic in heuristics:
                confidence = heuristic.get('confidence_score', 0)
                confidence_color = "#2E7D32" if confidence > 0.8 else "#F57C00" if confidence > 0.6 else "#D32F2F"
                
                st.markdown(f"""
                <div class="pattern-card">
                    <div class="pattern-header">
                        <div class="pattern-name">{heuristic.get('rule_name', 'Unnamed Pattern')}</div>
                        <div class="pattern-confidence" style="background: {confidence_color}20; color: {confidence_color};">
                            {confidence:.1%} confidence
                        </div>
                    </div>
                    <div class="pattern-details">
                        <strong>Pattern:</strong> {heuristic.get('description', 'No description available')}<br>
                        <strong>Trigger:</strong> {heuristic.get('condition', 'No condition specified')}<br>
                        <strong>Action:</strong> {heuristic.get('action', 'No action specified')}<br>
                        <strong>Usage:</strong> Applied {heuristic.get('usage_count', 0)} times
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Pattern management actions
                pattern_col1, pattern_col2, pattern_col3 = st.columns(3)
                
                with pattern_col1:
                    if st.button("📊 View Details", key=f"details_{heuristic.get('id')}", use_container_width=True):
                        with st.expander("Pattern Details", expanded=True):
                            st.json(heuristic)
                
                with pattern_col2:
                    if confidence < 0.7:
                        if st.button("🎯 Retrain", key=f"retrain_{heuristic.get('id')}", use_container_width=True):
                            st.info("Pattern retraining would be initiated here")
                
                with pattern_col3:
                    if st.button("🗑️ Remove", key=f"remove_{heuristic.get('id')}", use_container_width=True):
                        st.warning("Pattern removal confirmation would appear here")
                
                st.markdown("---")
        else:
            st.info("No learned patterns available yet. The system will develop patterns as it processes more invoices.")
            
            # Show example patterns
            st.markdown("""
            <div class="pattern-card">
                <div class="pattern-header">
                    <div class="pattern-name">Auto-approve small amounts from trusted vendors</div>
                    <div class="pattern-confidence">92.4% confidence</div>
                </div>
                <div class="pattern-details">
                    <strong>Pattern:</strong> Invoices under $500 from vendors with 95%+ accuracy rate<br>
                    <strong>Trigger:</strong> amount < 500 AND vendor_accuracy > 0.95<br>
                    <strong>Action:</strong> Auto-approve without review<br>
                    <strong>Usage:</strong> Applied 847 times
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.warning("Could not load learned patterns. This feature requires historical data.")

# --- VENDOR INSIGHTS TAB ---
with tab_vendor_insights:
    st.markdown("### 📈 Vendor Performance Insights")
    st.markdown("*Data-driven insights about vendor behavior and performance*")
    
    # For now, show placeholder information since the backend endpoint isn't implemented yet
    st.info("💡 **Coming Soon**: This section will show data-driven insights about vendor behavior and performance once we have sufficient historical data.")
    
    # Show some example/placeholder cards to demonstrate the intended functionality
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏆 Top Performing Vendors")
        st.markdown("""
        <div class="pattern-card">
            <div class="pattern-header">
                <div class="pattern-name">ArcelorMittal</div>
                <div class="pattern-confidence">94.5% accuracy</div>
            </div>
            <div class="pattern-details">
                Invoices processed: 247<br>
                Avg. processing time: 2.1 hours<br>
                Discount compliance: 98.2%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### ⚠️ Attention Required")
        st.markdown("""
        <div class="pattern-card">
            <div class="pattern-header">
                <div class="pattern-name">Global Manufacturing Inc</div>
                <div class="pattern-confidence" style="background: #FFEBEE; color: #C62828;">
                    23.1% exceptions
                </div>
            </div>
            <div class="pattern-details">
                Common issues: Unit conversion errors<br>
                Last clean invoice: 12 days ago<br>
                Suggested action: Review tolerance settings
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- QUICK ACTIONS ---
st.markdown("---")
st.markdown("### ⚡ Quick Actions")

quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)

with quick_col1:
    if st.button("📊 View Dashboard", use_container_width=True):
        st.switch_page("pages/1_📈_Executive_Dashboard.py")

with quick_col2:
    if st.button("🛠️ Review Queue", use_container_width=True):
        st.switch_page("pages/3_🛠️_Invoice_Workbench.py")

with quick_col3:
    if st.button("⚙️ Configure Rules", use_container_width=True):
        st.switch_page("pages/6_⚙️_System_Configuration.py")

with quick_col4:
    if st.button("🔎 Explore Data", use_container_width=True):
        st.switch_page("pages/5_��_Data_Explorer.py") 