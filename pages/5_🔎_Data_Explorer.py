# pages/5_🔎_Data_Explorer.py
import streamlit as st
import api_client
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Data Explorer", layout="wide")

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
    
    .search-summary {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .summary-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;
    }
    
    .stat-item {
        text-align: center;
        padding: 1rem;
        background: #F8F9FA;
        border-radius: 8px;
        border-left: 3px solid var(--primary-color);
    }
    
    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--primary-color);
        margin-bottom: 0.25rem;
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: var(--text-color);
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .filter-section {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .filter-header {
        font-weight: 600;
        color: var(--text-color);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    .recent-activity {
        background: #E3F2FD;
        border: 1px solid #BBDEFB;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .activity-header {
        font-weight: 600;
        color: #1976D2;
        margin-bottom: 0.5rem;
    }
    
    .export-section {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'search_executed' not in st.session_state:
    st.session_state.search_executed = False
if 'search_results' not in st.session_state:
    st.session_state.search_results = None

st.title("🔎 Data Explorer")
st.markdown("**Advanced Analytics** - Flexible search and comprehensive reporting across all invoice data")

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    st.markdown('<div class="filter-header">🔍 Search Filters</div>', unsafe_allow_html=True)
    
    # Basic Filters
    st.markdown("**Basic Criteria**")
    status_filter = st.multiselect(
        "Invoice Status",
        options=["needs_review", "approved_for_payment", "pending_match", "paid"],
        default=[]
    )
    
    vendor_filter = st.text_input("Vendor Name (contains)", placeholder="Enter vendor name...")
    invoice_id_filter = st.text_input("Invoice ID", placeholder="INV-...")
    
    # Date Range
    st.markdown("**Date Range**")
    date_option = st.selectbox(
        "Date Filter",
        ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"]
    )
    
    date_from = None
    date_to = None
    
    if date_option == "Custom Range":
        col1, col2 = st.columns(2)
        with col1:
            date_from = st.date_input("From Date")
        with col2:
            date_to = st.date_input("To Date")
    elif date_option != "All Time":
        days_back = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}[date_option]
        date_from = datetime.now() - timedelta(days=days_back)
        date_to = datetime.now()
    
    # Amount Range
    st.markdown("**Amount Range**")
    amount_filter = st.selectbox(
        "Amount Range",
        ["All Amounts", "Under $1,000", "$1,000 - $10,000", "$10,000 - $50,000", "Over $50,000", "Custom"]
    )
    
    min_amount = None
    max_amount = None
    
    if amount_filter == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            min_amount = st.number_input("Min Amount ($)", min_value=0.0, step=100.0)
        with col2:
            max_amount = st.number_input("Max Amount ($)", min_value=0.0, step=100.0)
    elif amount_filter != "All Amounts":
        amount_ranges = {
            "Under $1,000": (0, 1000),
            "$1,000 - $10,000": (1000, 10000),
            "$10,000 - $50,000": (10000, 50000),
            "Over $50,000": (50000, None)
        }
        min_amount, max_amount = amount_ranges[amount_filter]
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Search Button
    st.markdown("---")
    if st.button("🔍 Execute Search", type="primary", use_container_width=True):
        st.session_state.search_executed = True
        st.rerun()
    
    if st.button("🔄 Reset Filters", use_container_width=True):
        st.session_state.search_executed = False
        st.session_state.search_results = None
        st.rerun()
    
    # Recent Activity
    st.markdown("---")
    st.markdown('<div class="recent-activity">', unsafe_allow_html=True)
    st.markdown('<div class="activity-header">📈 Recent Activity</div>', unsafe_allow_html=True)
    st.markdown("""
    **Today:** 47 invoices processed  
    **This Week:** 312 invoices  
    **Avg. Processing Time:** 4.2 hours  
    **Exception Rate:** 12.3%
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN CONTENT AREA ---

# Default view or search results
if not st.session_state.search_executed:
    # Show default recent invoices view
    st.markdown("### 📋 Recent Invoices")
    st.markdown("*Showing the last 25 processed invoices. Use the sidebar filters to search for specific data.*")
    
    try:
        # Get recent invoices
        recent_invoices = api_client.get_recent_invoices(limit=25)
        
        if recent_invoices:
            df = pd.DataFrame(recent_invoices)
            
            # Display summary
            total_count = len(df)
            total_amount = df['grand_total'].sum() if 'grand_total' in df.columns else 0
            avg_amount = df['grand_total'].mean() if 'grand_total' in df.columns else 0
            
            st.markdown(f"""
            <div class="search-summary">
                <div class="summary-stats">
                    <div class="stat-item">
                        <div class="stat-value">{total_count}</div>
                        <div class="stat-label">Recent Invoices</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${total_amount:,.0f}</div>
                        <div class="stat-label">Total Value</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${avg_amount:,.0f}</div>
                        <div class="stat-label">Average Amount</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{len(df[df['status'] == 'needs_review']) if 'status' in df.columns else 0}</div>
                        <div class="stat-label">Need Review</div>
                    </div>
                </div>
                <p style="margin: 0; color: var(--text-color); opacity: 0.8;">
                    <strong>Recent Activity:</strong> Showing invoices from the last 30 days, sorted by processing date.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display the dataframe
            display_columns = ['invoice_id', 'vendor_name', 'grand_total', 'status', 'invoice_date']
            available_columns = [col for col in display_columns if col in df.columns]
            
            if available_columns:
                df_display = df[available_columns].copy()
                
                # Format columns for better display
                if 'grand_total' in df_display.columns:
                    df_display['grand_total'] = df_display['grand_total'].apply(lambda x: f"${x:,.2f}")
                if 'status' in df_display.columns:
                    df_display['status'] = df_display['status'].str.replace('_', ' ').str.title()
                
                # Rename columns for display
                column_renames = {
                    'invoice_id': 'Invoice ID',
                    'vendor_name': 'Vendor',
                    'grand_total': 'Amount',
                    'status': 'Status',
                    'invoice_date': 'Date'
                }
                df_display = df_display.rename(columns=column_renames)
                
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("No data columns available for display")
        else:
            st.info("No recent invoices found. Upload some documents to get started!")
            
    except Exception as e:
        st.error(f"Could not load recent invoices: {str(e)}")
        st.info("Please ensure the backend API is running and accessible.")

else:
    # Execute search with filters
    st.markdown("### 🔍 Search Results")
    
    with st.spinner("Searching invoices..."):
        try:
            # Build search parameters
            search_params = {}
            
            if status_filter:
                search_params['status'] = status_filter
            if vendor_filter:
                search_params['vendor_name'] = vendor_filter
            if invoice_id_filter:
                search_params['invoice_id'] = invoice_id_filter
            if date_from:
                search_params['date_from'] = date_from.isoformat()
            if date_to:
                search_params['date_to'] = date_to.isoformat()
            if min_amount is not None:
                search_params['min_amount'] = min_amount
            if max_amount is not None:
                search_params['max_amount'] = max_amount
            
            # Build search filters for the API
            filters = []
            if search_params.get('status'):
                filters.append({"field": "status", "operator": "in", "value": search_params['status']})
            if search_params.get('vendor_name'):
                filters.append({"field": "vendor_name", "operator": "contains", "value": search_params['vendor_name']})
            if search_params.get('invoice_id'):
                filters.append({"field": "invoice_id", "operator": "contains", "value": search_params['invoice_id']})
            if search_params.get('date_from'):
                filters.append({"field": "invoice_date", "operator": "gte", "value": search_params['date_from']})
            if search_params.get('date_to'):
                filters.append({"field": "invoice_date", "operator": "lte", "value": search_params['date_to']})
            if search_params.get('min_amount') is not None:
                filters.append({"field": "grand_total", "operator": "gte", "value": search_params['min_amount']})
            if search_params.get('max_amount') is not None:
                filters.append({"field": "grand_total", "operator": "lte", "value": search_params['max_amount']})
            
            # Get search results
            search_results = api_client.search_invoices(filters)
            st.session_state.search_results = search_results
            
            if search_results:
                df = pd.DataFrame(search_results)
                
                # Calculate summary statistics
                total_count = len(df)
                total_amount = df['grand_total'].sum() if 'grand_total' in df.columns else 0
                avg_amount = df['grand_total'].mean() if 'grand_total' in df.columns else 0
                unique_vendors = df['vendor_name'].nunique() if 'vendor_name' in df.columns else 0
                
                # Display search summary
                st.markdown(f"""
                <div class="search-summary">
                    <div class="summary-stats">
                        <div class="stat-item">
                            <div class="stat-value">{total_count}</div>
                            <div class="stat-label">Invoices Found</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${total_amount:,.0f}</div>
                            <div class="stat-label">Total Value</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${avg_amount:,.0f}</div>
                            <div class="stat-label">Average Amount</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{unique_vendors}</div>
                            <div class="stat-label">Unique Vendors</div>
                        </div>
                    </div>
                    <p style="margin: 0; color: var(--text-color); opacity: 0.8;">
                        <strong>Search completed:</strong> Found {total_count} invoices matching your criteria totaling ${total_amount:,.2f}.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Display results table
                display_columns = ['invoice_id', 'vendor_name', 'grand_total', 'status', 'invoice_date', 'due_date']
                available_columns = [col for col in display_columns if col in df.columns]
                
                if available_columns:
                    df_display = df[available_columns].copy()
                    
                    # Format columns for better display
                    if 'grand_total' in df_display.columns:
                        df_display['grand_total'] = df_display['grand_total'].apply(lambda x: f"${x:,.2f}")
                    if 'status' in df_display.columns:
                        df_display['status'] = df_display['status'].str.replace('_', ' ').str.title()
                    
                    # Rename columns for display
                    column_renames = {
                        'invoice_id': 'Invoice ID',
                        'vendor_name': 'Vendor',
                        'grand_total': 'Amount',
                        'status': 'Status',
                        'invoice_date': 'Invoice Date',
                        'due_date': 'Due Date'
                    }
                    df_display = df_display.rename(columns=column_renames)
                    
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Export options
                    st.markdown('<div class="export-section">', unsafe_allow_html=True)
                    st.markdown("### 📊 Export Results")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        csv_data = df_display.to_csv(index=False)
                        st.download_button(
                            label="📄 Download CSV",
                            data=csv_data,
                            file_name=f"invoice_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    with col2:
                        if st.button("📧 Email Report", use_container_width=True):
                            st.info("Email report functionality would be implemented here")
                    
                    with col3:
                        if st.button("📊 Create Dashboard", use_container_width=True):
                            st.info("Dashboard creation functionality would be implemented here")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                else:
                    st.warning("No data columns available for display")
            else:
                st.warning("No invoices found matching your search criteria.")
                st.markdown("""
                **Suggestions:**
                - Try broadening your search criteria
                - Check if the date range includes processed invoices
                - Verify vendor names are spelled correctly
                - Remove amount filters to see all invoices
                """)
                
        except Exception as e:
            st.error(f"Search failed: {str(e)}")
            st.info("Please check your search criteria and try again.")

# --- QUICK ACTIONS ---
st.markdown("---")
st.markdown("### ⚡ Quick Actions")

action_col1, action_col2, action_col3, action_col4 = st.columns(4)

with action_col1:
    if st.button("📊 View Dashboard", use_container_width=True):
        st.switch_page("pages/1_📈_Executive_Dashboard.py")

with action_col2:
    if st.button("🛠️ Review Queue", use_container_width=True):
        st.switch_page("pages/3_🛠️_Invoice_Workbench.py")

with action_col3:
    if st.button("🧠 AI Insights", use_container_width=True):
        st.switch_page("pages/4_🧠_AI_Insights.py")

with action_col4:
    if st.button("⚙️ Configuration", use_container_width=True):
        st.switch_page("pages/6_⚙️_System_Configuration.py") 