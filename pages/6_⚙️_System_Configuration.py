# pages/6_⚙️_System_Configuration.py
import streamlit as st
import pandas as pd
import api_client
import json

st.set_page_config(page_title="System Configuration", layout="wide")

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
    
    .config-section {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .section-header {
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid var(--border-color);
    }
    
    .section-icon {
        font-size: 2rem;
        margin-right: 1rem;
        color: var(--primary-color);
    }
    
    .section-title {
        color: var(--text-color);
        font-weight: 700;
        font-size: 1.4rem;
        margin: 0;
    }
    
    .info-box {
        background: #E3F2FD;
        border: 1px solid #BBDEFB;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border-left: 4px solid #2196F3;
    }
    
    .info-title {
        font-weight: 600;
        color: #1976D2;
        margin-bottom: 0.5rem;
    }
    
    .info-content {
        color: #1976D2;
        opacity: 0.9;
        line-height: 1.5;
    }
    
    .warning-box {
        background: #FFF8E1;
        border: 1px solid #FFE082;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border-left: 4px solid #FF9800;
    }
    
    .warning-title {
        font-weight: 600;
        color: #F57C00;
        margin-bottom: 0.5rem;
    }
    
    .warning-content {
        color: #F57C00;
        opacity: 0.9;
        line-height: 1.5;
    }
    
    .help-text {
        background: #F5F5F5;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 1rem;
        margin-top: 0.5rem;
        font-size: 0.9rem;
        color: var(--text-color);
        opacity: 0.8;
    }
    
    .rule-preview {
        background: #F8F9FA;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
    
    .action-button {
        background: var(--primary-color);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 6px;
        font-weight: 600;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    
    .action-button:hover {
        background: var(--accent-color);
    }
    
    .danger-button {
        background: var(--error-color);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 6px;
        font-weight: 600;
        cursor: pointer;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .stat-card {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        border-left: 4px solid var(--primary-color);
    }
    
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        color: var(--text-color);
        opacity: 0.8;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for confirmations
if 'show_vendor_confirm' not in st.session_state:
    st.session_state.show_vendor_confirm = False

st.title("⚙️ System Configuration")
st.markdown("**Enterprise Controls** - Secure system settings, vendor management, and automation rule configuration")

# --- TABBED INTERFACE ---
tab_vendors, tab_rules = st.tabs(["🏢 Vendor Settings", "🤖 Automation Rules"])

# --- VENDOR SETTINGS TAB ---
with tab_vendors:
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown("### Current Vendor Configurations")
    
    vendor_settings = api_client.get_vendor_settings()
    
    if vendor_settings is not None:
        df = pd.DataFrame(vendor_settings)
        edited_df = st.data_editor(
            df,
            column_config={
                "vendor_name": st.column_config.TextColumn("Vendor", disabled=True),
                "price_tolerance_percent": st.column_config.NumberColumn("Price Tolerance (%)", format="%.2f"),
                "contact_email": st.column_config.TextColumn("Contact Email"),
            },
            key="vendor_editor",
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
        )

        if st.button("💾 Save Vendor Settings", type="primary"):
            st.session_state.show_vendor_confirm = True
            # Store the edited data in session state before rerun
            st.session_state.edited_vendor_settings = edited_df.to_dict('records')

    else:
        st.warning("Could not load vendor settings from the backend.")

    # Confirmation Dialog
    if st.session_state.get('show_vendor_confirm'):
        st.warning("Are you sure you want to apply these changes?")
        c1, c2 = st.columns(2)
        if c1.button("✅ Yes, Apply Changes", use_container_width=True):
            settings_to_update = st.session_state.get('edited_vendor_settings', [])
            result = api_client.update_vendor_settings(settings_to_update)
            if result:
                st.success("Vendor settings updated successfully!")
                st.session_state.show_vendor_confirm = False
                del st.session_state.edited_vendor_settings
                st.rerun()
            else:
                st.error("Failed to update settings.")

        if c2.button("❌ Cancel", use_container_width=True):
            st.session_state.show_vendor_confirm = False
            del st.session_state.edited_vendor_settings
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


# --- AUTOMATION RULES TAB ---
with tab_rules:
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown("### 📋 Current Automation Rules")
    
    automation_rules = api_client.get_automation_rules()
    if automation_rules is not None:
        st.dataframe(automation_rules, use_container_width=True)
    else:
        st.warning("Could not load automation rules from the backend.")

    st.markdown("---")
    st.markdown("### ➕ Create New Automation Rule")
    
    with st.form("new_automation_rule_form", clear_on_submit=True):
        rule_name = st.text_input("Rule Name", placeholder="e.g., Auto-approve small IT invoices")
        vendor_name = st.text_input("Vendor Name (Optional)")
        
        st.write("**Conditions (JSON format)**")
        conditions_text = st.text_area(
            "Conditions", 
            '{"field": "grand_total", "operator": "<", "value": 500}',
            help='Define conditions in JSON format, e.g., `{"field": "grand_total", "operator": "<", "value": 500}`'
        )
        action = st.selectbox("Action", ["approve", "reject", "flag_for_audit"])
        
        submitted = st.form_submit_button("🚀 Create Automation Rule", type="primary")
        if submitted:
            try:
                conditions_json = json.loads(conditions_text)
                rule_data = {
                    "rule_name": rule_name,
                    "vendor_name": vendor_name if vendor_name else None,
                    "conditions": conditions_json,
                    "action": action,
                }
                result = api_client.create_automation_rule(rule_data)
                if result:
                    st.success(f"Successfully created rule: {result.get('rule_name')}")
                    st.rerun()
                else:
                    st.error("Failed to create rule. Check backend logs.")
            except json.JSONDecodeError:
                st.error("Invalid JSON format for conditions.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

    st.markdown('</div>', unsafe_allow_html=True) 