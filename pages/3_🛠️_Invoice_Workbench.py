# pages/3_🛠️_Invoice_Workbench.py
import streamlit as st
import api_client
import pandas as pd
import requests
try:
    from pdf2image import convert_from_bytes
except ImportError:
    st.error("pdf2image not installed. Please run: pip install pdf2image")
    convert_from_bytes = None

st.set_page_config(page_title="Invoice Workbench", layout="wide")

# Apply the same CSS theme with additional workbench-specific styling
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
    
    .workbench-header {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid var(--primary-color);
        position: sticky;
        top: 0;
        z-index: 100;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .status-needs-review {
        background: #FFF3CD;
        color: #856404;
        border: 1px solid #FFEAA7;
    }
    
    .status-approved {
        background: #D4F6D4;
        color: #155724;
        border: 1px solid #C3E6CB;
    }
    
    .status-rejected {
        background: #F8D7DA;
        color: #721C24;
        border: 1px solid #F5C6CB;
    }
    
    .action-buttons {
        display: flex;
        gap: 1rem;
        margin-top: 1rem;
        flex-wrap: wrap;
    }
    
    .btn-primary {
        background: var(--primary-color);
        color: white;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    
    .btn-primary:hover {
        background: var(--accent-color);
    }
    
    .btn-danger {
        background: var(--error-color);
        color: white;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        cursor: pointer;
    }
    
    .btn-secondary {
        background: #6C757D;
        color: white;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        cursor: pointer;
    }
    
    .match-step {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
    }
    
    .match-step.success {
        border-left: 4px solid var(--success-color);
    }
    
    .match-step.error {
        border-left: 4px solid var(--error-color);
    }
    
    .match-step.info {
        border-left: 4px solid #2196F3;
    }
    
    .step-icon {
        font-size: 1.5rem;
        margin-right: 1rem;
        min-width: 2rem;
    }
    
    .step-content {
        flex: 1;
    }
    
    .step-title {
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    
    .step-message {
        color: var(--text-color);
        opacity: 0.8;
        font-size: 0.9rem;
    }
    
    .document-metadata {
        background: #F8F9FA;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .metadata-item {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }
    
    .metadata-label {
        font-weight: 500;
        color: var(--text-color);
    }
    
    .metadata-value {
        color: var(--primary-color);
        font-weight: 600;
    }
    
    .copilot-prompt {
        background: #E3F2FD;
        border: 1px solid #BBDEFB;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        cursor: pointer;
        font-size: 0.85rem;
        transition: background-color 0.3s ease;
    }
    
    .copilot-prompt:hover {
        background: #BBDEFB;
    }
    
    .queue-item {
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    
    .queue-item:hover {
        background-color: #F0F8FF;
    }
    
    .priority-high {
        border-left: 3px solid #FF5722;
    }
    
    .priority-medium {
        border-left: 3px solid #FF9800;
    }
    
    .priority-low {
        border-left: 3px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'selected_invoice_id' not in st.session_state:
    st.session_state.selected_invoice_id = None
if 'copilot_messages' not in st.session_state:
    st.session_state.copilot_messages = []

def select_invoice(invoice_id):
    """Callback to set the selected invoice."""
    st.session_state.selected_invoice_id = invoice_id
    # Clear previous chat history when a new invoice is selected
    st.session_state.copilot_messages = []

def handle_invoice_action(action, invoice_id):
    """Handle invoice actions (approve, reject, etc.)"""
    try:
        if action == "approve":
            result = api_client.approve_invoice(invoice_id)
            if result:
                st.success(f"✅ Invoice {invoice_id} approved successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to approve invoice")
        elif action == "reject":
            result = api_client.reject_invoice(invoice_id)
            if result:
                st.warning(f"⚠️ Invoice {invoice_id} rejected")
                st.rerun()
            else:
                st.error("❌ Failed to reject invoice")
    except Exception as e:
        st.error(f"❌ Error performing action: {str(e)}")

# --- Main Layout ---
st.title("🛠️ Invoice Workbench")
st.markdown("**Power-User Workspace** - Resolve invoice exceptions with AI assistance and streamlined workflow")

col1, col2, col3 = st.columns([0.3, 0.45, 0.25])

# --- Column 1: Enhanced Work Queue ---
with col1:
    st.markdown("### 📋 Work Queue")
    
    # Enhanced filtering
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        status_filter = st.selectbox(
            "Filter by status:",
            options=["needs_review", "approved_for_payment", "pending_match", "paid"],
            index=0
        )
    
    with filter_col2:
        search_invoice = st.text_input("🔍 Search Invoice ID", placeholder="INV-...")
    
    # Get invoices with enhanced display
    invoices = api_client.get_invoices(status=status_filter)
    
    if invoices:
        df = pd.DataFrame(invoices)
        
        # Filter by search if provided
        if search_invoice:
            df = df[df['invoice_id'].str.contains(search_invoice, case=False, na=False)]
        
        if not df.empty:
            # Enhanced dataframe with visual cues
            # Add priority column based on amount (mock logic)
            df['priority'] = df['grand_total'].apply(
                lambda x: 'High' if x > 10000 else 'Medium' if x > 5000 else 'Low'
            )
            
            # Format currency
            df['grand_total_formatted'] = df['grand_total'].apply(lambda x: f"${x:,.2f}")
            
            # Display enhanced dataframe
            display_df = df[['invoice_id', 'vendor_name', 'grand_total_formatted', 'invoice_date', 'priority']]
            display_df.columns = ['Invoice ID', 'Vendor', 'Amount', 'Date', 'Priority']
            
            # Custom styling function
            def style_dataframe(df):
                def highlight_priority(row):
                    if row['Priority'] == 'High':
                        return ['background-color: #FFEBEE'] * len(row)
                    elif row['Priority'] == 'Medium':
                        return ['background-color: #FFF3E0'] * len(row)
                    else:
                        return ['background-color: #E8F5E8'] * len(row)
                
                return df.style.apply(highlight_priority, axis=1)
            
            # Display with selection
            event = st.dataframe(
                display_df,
                on_select="rerun",
                selection_mode="single-row",
                key="invoice_selector",
                use_container_width=True,
                hide_index=True
            )
            
            if event.selection['rows']:
                selected_row_index = event.selection['rows'][0]
                selected_id = df.iloc[selected_row_index]['invoice_id']
                select_invoice(selected_id)
        else:
            st.info("No invoices match the current filter criteria.")
    else:
        st.info("No invoices found for the selected status.")
    
    # Quick stats
    st.markdown("---")
    st.markdown("**📊 Queue Summary**")
    try:
        queue_stats = api_client.get_queue_stats()
        if queue_stats:
            col1_1, col1_2 = st.columns(2)
            with col1_1:
                st.metric("Total", queue_stats.get('total', 0))
            with col1_2:
                st.metric("High Priority", queue_stats.get('high_priority', 0))
    except:
        pass

# --- Column 2: Enhanced Dossier & Document Viewer ---
with col2:
    if not st.session_state.selected_invoice_id:
        st.markdown("""
        <div class="workbench-header">
            <h3>📄 Select an Invoice</h3>
            <p>Choose an invoice from the Work Queue to view its details and take action.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        invoice_id = st.session_state.selected_invoice_id
        dossier = api_client.get_invoice_dossier(invoice_id)
        
        if not dossier:
            st.error(f"Could not load details for invoice {invoice_id}.")
        else:
            summary = dossier.get("summary", {})
            
            # --- STICKY HEADER CARD ---
            status = summary.get('status', '').replace('_', ' ').title()
            status_class = f"status-{summary.get('status', '').replace('_', '-')}"
            
            st.markdown(f"""
            <div class="workbench-header">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="margin: 0;">📄 {summary.get('invoice_id', 'N/A')}</h3>
                    <span class="status-badge {status_class}">{status}</span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
                    <div>
                        <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.25rem;">VENDOR</div>
                        <div style="font-weight: 600; color: var(--text-color);">{summary.get('vendor_name', 'N/A')}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.25rem;">AMOUNT</div>
                        <div style="font-weight: 600; color: var(--primary-color); font-size: 1.1rem;">${summary.get('grand_total', 0):,.2f}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.25rem;">DATE</div>
                        <div style="font-weight: 600; color: var(--text-color);">{summary.get('invoice_date', 'N/A')}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # --- ACTION BUTTONS ---
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                if st.button("✅ Approve", use_container_width=True, type="primary"):
                    handle_invoice_action("approve", invoice_id)
            
            with action_col2:
                if st.button("❌ Reject", use_container_width=True):
                    # Show confirmation dialog
                    with st.expander("⚠️ Confirm Rejection"):
                        st.warning("Are you sure you want to reject this invoice?")
                        if st.button("Yes, Reject", type="primary"):
                            handle_invoice_action("reject", invoice_id)
            
            with action_col3:
                # More actions dropdown
                with st.popover("⋯ More Actions"):
                    if st.button("📧 Forward"):
                        st.info("Forward functionality would be implemented here")
                    if st.button("🚫 Dispute"):
                        st.info("Dispute functionality would be implemented here")
                    if st.button("⏸️ Hold"):
                        st.info("Hold functionality would be implemented here")
            
            st.markdown("---")
            
            # --- TABBED CONTENT ---
            tab_match, tab_docs, tab_data = st.tabs(["🕵️ Match Trace", "📄 Document Viewer", "📊 Raw Data"])

            with tab_match:
                if dossier.get("match_trace"):
                    st.markdown("**Validation Steps:**")
                    for step in dossier["match_trace"]:
                        status = step.get('status', 'INFO')
                        icon = "✅" if status == 'PASS' else "❌" if status == 'FAIL' else "ℹ️"
                        css_class = "success" if status == 'PASS' else "error" if status == 'FAIL' else "info"
                        
                        st.markdown(f"""
                        <div class="match-step {css_class}">
                            <div class="step-icon">{icon}</div>
                            <div class="step-content">
                                <div class="step-title">{step.get('step', 'Unknown Step')}</div>
                                <div class="step-message">{step.get('message', '')}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if status == 'FAIL' and step.get('details'):
                            with st.expander("🔍 Show Details"):
                                st.json(step.get('details', {}))
                else:
                    st.info("No match trace available for this invoice yet.")

            with tab_docs:
                st.markdown("**Original Documents**")
                docs = dossier.get("documents", {})
                
                def render_pdf_with_metadata(doc_type, doc_data):
                    if doc_data and doc_data.get('file_path'):
                        # Display metadata first
                        extracted_data = doc_data.get('data', {})
                        if extracted_data:
                            st.markdown(f"""
                            <div class="document-metadata">
                                <h5>{doc_type.upper()} - Key Fields</h5>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Show key fields based on document type
                            if doc_type == 'invoice':
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown(f"**Invoice Date:** {extracted_data.get('invoice_date', 'N/A')}")
                                    st.markdown(f"**Due Date:** {extracted_data.get('due_date', 'N/A')}")
                                with col2:
                                    st.markdown(f"**PO Number:** {extracted_data.get('po_number', 'N/A')}")
                                    st.markdown(f"**Total:** ${extracted_data.get('grand_total', 0):,.2f}")
                            
                        # Render PDF
                        if convert_from_bytes:
                            try:
                                file_url = f"{api_client.BASE_URL}/documents/file/{doc_data.get('file_path')}"
                                response = requests.get(file_url)
                                if response.status_code == 200:
                                    images = convert_from_bytes(response.content)
                                    st.image(images[0], use_column_width=True, caption=f"{doc_type.title()} Document")
                                else:
                                    st.warning(f"Could not load {doc_type} document.")
                            except Exception as e:
                                st.error(f"Error rendering {doc_type} PDF: {e}")
                        else:
                            st.info("Document not available or pdf2image not installed.")
                
                doc1, doc2 = st.columns(2)
                with doc1:
                    st.subheader("📄 Invoice")
                    render_pdf_with_metadata('invoice', docs.get('invoice'))
                
                with doc2:
                    st.subheader("📋 Purchase Order / GRN")
                    po_doc = docs.get('po') or docs.get('grn')
                    doc_type = 'po' if docs.get('po') else 'grn'
                    render_pdf_with_metadata(doc_type, po_doc)
            
            with tab_data:
                with st.expander("📄 Invoice Raw Data"):
                    st.json(dossier.get('documents', {}).get('invoice', {}).get('data', {}))
                with st.expander("📋 PO Raw Data"):
                    st.json(dossier.get('documents', {}).get('po', {}).get('data', {}))
                with st.expander("📦 GRN Raw Data"):
                    st.json(dossier.get('documents', {}).get('grn', {}).get('data', {}))

# --- Column 3: Enhanced AP Copilot ---
with col3:
    st.markdown("### 🤖 AI Assistant")
    st.markdown("*Your intelligent helper for complex queries and analysis*")
    
    # Contextual prompts
    if st.session_state.selected_invoice_id:
        st.markdown("**💡 Suggested Actions:**")
        
        prompt_suggestions = [
            "Summarize the issue",
            "Draft a dispute email",
            "Check vendor payment history",
            "Explain the matching failure",
            "Suggest resolution steps"
        ]
        
        for suggestion in prompt_suggestions:
            if st.button(suggestion, key=f"prompt_{suggestion}", use_container_width=True):
                # Add the suggestion as a user message
                st.session_state.copilot_messages.append({"role": "user", "content": suggestion})
                
                # Get response from copilot
                with st.spinner("AI Assistant thinking..."):
                    response = api_client.copilot_chat(suggestion, st.session_state.selected_invoice_id)
                
                if response:
                    response_content = response.get("responseText", "Sorry, I couldn't process that request.")
                    st.session_state.copilot_messages.append({"role": "assistant", "content": response_content})
                    
                    # Handle UI actions
                    if response.get("uiAction") == "SHOW_TOAST_SUCCESS":
                        st.toast(response_content, icon="✅")
                    
                    st.rerun()
        
        st.markdown("---")
    
    # Display chat history
    for msg in st.session_state.copilot_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("data"):
                with st.expander("📊 View Data"):
                    st.json(msg["data"])

    # Chat input
    if prompt := st.chat_input("Ask the AI Assistant..."):
        st.session_state.copilot_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("AI Assistant thinking..."):
                response = api_client.copilot_chat(prompt, st.session_state.selected_invoice_id)
            
            if response:
                message_placeholder.markdown(response.get("responseText"))
                response_data = {"role": "assistant", "content": response.get("responseText")}
                
                # Handle UI actions from the copilot
                if response.get("uiAction") == "LOAD_SINGLE_DOSSIER":
                    invoice_to_load = response.get("data", {}).get("summary", {}).get("invoice_id")
                    if invoice_to_load:
                        st.info(f"AI is loading invoice {invoice_to_load}...")
                        st.session_state.selected_invoice_id = invoice_to_load
                        st.rerun()

                elif response.get("uiAction") == "SHOW_TOAST_SUCCESS":
                    st.toast(response.get("responseText"), icon="✅")

                # Store data for display in expander if present
                if response.get("data"):
                    response_data["data"] = response.get("data")
                    
                st.session_state.copilot_messages.append(response_data)
            else:
                message_placeholder.markdown("Sorry, I encountered an error. Please try again.")
                st.session_state.copilot_messages.append({"role": "assistant", "content": "Error"})
    
    # Quick help
    with st.expander("❓ How can I help?"):
        st.markdown("""
        **I can help you with:**
        
        • Analyzing invoice discrepancies
        • Explaining matching failures
        • Suggesting resolution steps
        • Checking vendor history
        • Drafting communication
        • Automating approvals
        
        Just type your question or use the suggested prompts above!
        """) 