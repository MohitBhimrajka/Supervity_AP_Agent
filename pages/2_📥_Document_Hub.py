# pages/2_📥_Document_Hub.py
import streamlit as st
import api_client
import time

st.set_page_config(page_title="Document Hub", layout="wide")

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
    
    .step-container {
        background: var(--card-background);
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
        border-left: 4px solid var(--primary-color);
    }
    
    .step-header {
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
    }
    
    .step-number {
        background: var(--primary-color);
        color: white;
        width: 3rem;
        height: 3rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1.2rem;
        margin-right: 1rem;
    }
    
    .step-title {
        color: var(--text-color);
        font-weight: 600;
        font-size: 1.4rem;
        margin: 0;
    }
    
    .upload-zone {
        border: 2px dashed var(--border-color);
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        background: #FAFAFA;
        transition: border-color 0.3s ease;
    }
    
    .upload-zone:hover {
        border-color: var(--primary-color);
        background: #F0F8FF;
    }
    
    .file-info {
        background: #E8F4FD;
        border: 1px solid #B3D9F0;
        border-radius: 6px;
        padding: 1rem;
        margin-top: 1rem;
    }
    
    .processing-metrics {
        display: flex;
        justify-content: space-around;
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-top: 1rem;
    }
    
    .metric-item {
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--primary-color);
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: var(--text-color);
        opacity: 0.8;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processing_job_id' not in st.session_state:
    st.session_state.processing_job_id = None
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

st.title("📥 Document Hub")
st.markdown("**Intelligent Document Processing** - Upload and process invoices, POs, and GRNs with AI-powered extraction")

# --- STEP 1: UPLOAD DOCUMENTS ---
st.markdown("""
<div class="step-container">
    <div class="step-header">
        <div class="step-number">1</div>
        <h3 class="step-title">Upload Documents</h3>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([0.7, 0.3])

with col1:
    st.markdown("""
    <div class="upload-zone">
        <h4>📄 Drop your documents here</h4>
        <p>Supported formats: PDF, PNG, JPG<br>
        Maximum size: 10MB per file</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Choose files",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
        
        # Display file information
        for i, file in enumerate(uploaded_files):
            file_size_mb = file.size / (1024 * 1024)
            st.markdown(f"""
            <div class="file-info">
                <strong>📄 {file.name}</strong><br>
                Size: {file_size_mb:.2f} MB | Type: {file.type}
            </div>
            """, unsafe_allow_html=True)

with col2:
    st.markdown("### 📋 Processing Guidelines")
    st.info("""
    **For best results:**
    
    • Ensure documents are clearly readable
    • Upload complete document sets when possible
    • Include both invoices and corresponding POs/GRNs
    • Use high-resolution scans for better OCR accuracy
    """)
    
    st.markdown("### 📊 Recent Activity")
    # Mock recent processing stats
    st.markdown("""
    <div class="processing-metrics">
        <div class="metric-item">
            <div class="metric-value">47</div>
            <div class="metric-label">Today</div>
        </div>
        <div class="metric-item">
            <div class="metric-value">312</div>
            <div class="metric-label">This Week</div>
        </div>
        <div class="metric-item">
            <div class="metric-value">98.2%</div>
            <div class="metric-label">Success Rate</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Process button
if uploaded_files:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Processing", type="primary", use_container_width=True):
            # Initiate processing
            with st.spinner("Uploading files..."):
                try:
                    result = api_client.upload_documents(uploaded_files)
                    if result and result.get("id"):
                        st.session_state.processing_job_id = result["id"]
                        st.success(f"✅ Upload successful! Job ID: {result['id']}")
                        st.rerun()
                    else:
                        st.error("❌ Upload failed. Please try again.")
                except Exception as e:
                    st.error(f"❌ Error during upload: {str(e)}")

# --- STEP 2: MONITOR PROCESSING ---
if st.session_state.processing_job_id or uploaded_files:
    st.markdown("---")
    st.markdown("""
    <div class="step-container">
        <div class="step-header">
            <div class="step-number">2</div>
            <h3 class="step-title">Monitor Processing Job</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.processing_job_id:
        # Enhanced job monitoring with st.status
        with st.status("Processing documents...", expanded=True) as status:
            job_id = st.session_state.processing_job_id
            
            # Simulate progressive status updates
            st.write("🔍 Analyzing document structure...")
            time.sleep(1)
            
            st.write("📖 Extracting text with OCR...")
            time.sleep(1)
            
            st.write("🧠 Running AI field extraction...")
            time.sleep(1)
            
            # Get actual job status
            try:
                job_status = api_client.get_job_status(job_id)
                
                if job_status:
                    if job_status.get("status") == "completed":
                        st.write("✅ Document processing completed successfully!")
                        status.update(label="Processing complete!", state="complete", expanded=False)
                        
                        # Display results
                        results = job_status.get("results", {})
                        processed_count = results.get("processed_documents", 0)
                        success_count = results.get("successful_extractions", 0)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📄 Documents Processed", processed_count)
                        with col2:
                            st.metric("✅ Successful Extractions", success_count)
                        with col3:
                            success_rate = (success_count / processed_count * 100) if processed_count > 0 else 0
                            st.metric("📊 Success Rate", f"{success_rate:.1f}%")
                        
                        # Action buttons
                        st.markdown("### 🎯 Next Steps")
                        action_col1, action_col2, action_col3 = st.columns(3)
                        
                        with action_col1:
                            if st.button("🛠️ Review in Workbench", use_container_width=True):
                                st.switch_page("pages/3_🛠️_Invoice_Workbench.py")
                        
                        with action_col2:
                            if st.button("📊 View Dashboard", use_container_width=True):
                                st.switch_page("pages/1_📈_Executive_Dashboard.py")
                        
                        with action_col3:
                            if st.button("🔄 Process More", use_container_width=True):
                                st.session_state.processing_job_id = None
                                st.session_state.uploaded_files = []
                                st.rerun()
                        
                    elif job_status.get("status") == "failed":
                        error_msg = job_status.get("error", "Unknown error occurred")
                        st.write(f"❌ Processing failed: {error_msg}")
                        status.update(label="Processing failed", state="error", expanded=False)
                        
                        st.error("Document processing encountered an error. Please check the files and try again.")
                        
                        if st.button("🔄 Try Again"):
                            st.session_state.processing_job_id = None
                            st.rerun()
                    
                    else:  # still processing
                        st.write("⏳ Processing in progress...")
                        progress = job_status.get("progress", {})
                        
                        if progress:
                            current_step = progress.get("current_step", "Unknown")
                            completed_files = progress.get("completed_files", 0)
                            total_files = progress.get("total_files", 1)
                            
                            st.write(f"Current step: {current_step}")
                            st.progress(completed_files / total_files)
                            st.write(f"Files: {completed_files}/{total_files}")
                        
                        # Auto-refresh
                        time.sleep(2)
                        st.rerun()
                
                else:
                    st.write("❌ Could not retrieve job status")
                    status.update(label="Status unavailable", state="error")
                    
            except Exception as e:
                st.write(f"❌ Error checking status: {str(e)}")
                status.update(label="Error checking status", state="error")
    
    else:
        st.info("👆 Upload documents above to start processing")

# --- RECENT PROCESSING HISTORY ---
st.markdown("---")
st.markdown("### 📈 Recent Processing History")

try:
    # Get recent jobs from the backend
    recent_jobs = api_client.get_jobs()
    
    if recent_jobs:
        # Display as a clean table
        import pandas as pd
        df = pd.DataFrame(recent_jobs)
        
        # Format the dataframe for display
        if not df.empty:
            display_columns = ['timestamp', 'job_id', 'status', 'documents_count', 'success_rate']
            available_columns = [col for col in display_columns if col in df.columns]
            
            if available_columns:
                df_display = df[available_columns].head(10)  # Show last 10 jobs
                
                # Format columns for better display
                if 'timestamp' in df_display.columns:
                    df_display['timestamp'] = pd.to_datetime(df_display['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No recent processing history available")
    else:
        st.info("No recent processing jobs found")
        
except Exception as e:
    st.warning("Could not load recent processing history")

# --- HELP & DOCUMENTATION ---
with st.expander("📚 Help & Documentation"):
    st.markdown("""
    ### Document Types Supported
    
    **📄 Invoices**
    - Vendor invoices in PDF format
    - Scanned invoice images (PNG, JPG)
    - Multi-page invoices
    
    **📋 Purchase Orders**
    - Internal PO documents
    - Vendor acknowledgments
    - Change orders and amendments
    
    **📦 Goods Receipt Notes (GRNs)**
    - Delivery confirmations
    - Inspection reports
    - Quality certificates
    
    ### Processing Steps
    
    1. **Document Upload** - Files are securely uploaded and validated
    2. **OCR Extraction** - Text is extracted using advanced OCR technology
    3. **AI Analysis** - Machine learning models identify and extract key fields
    4. **Validation** - Extracted data is cross-referenced and validated
    5. **Matching** - Documents are automatically matched with existing records
    
    ### Troubleshooting
    
    - **Poor OCR results?** Ensure documents are high-resolution and clearly readable
    - **Processing fails?** Check file formats and sizes are within limits
    - **Fields missing?** Some document formats may require manual review
    """) 