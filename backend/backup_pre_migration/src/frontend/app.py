import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List
import time

# Configure Streamlit page
st.set_page_config(
    page_title="Insurance Compliance System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

class ComplianceSystemUI:
    def __init__(self):
        self.api_base = API_BASE_URL
        
    def check_api_health(self) -> bool:
        """Check if API is available"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def upload_document(self, uploaded_file) -> Dict:
        """Upload document to API"""
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            response = requests.post(f"{self.api_base}/documents/upload", files=files)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_document(self, document_id: str, analysis_type: str = "full") -> Dict:
        """Analyze document for compliance"""
        try:
            data = {
                "document_id": document_id,
                "analysis_type": analysis_type,
                "include_explanation": True
            }
            response = requests.post(f"{self.api_base}/analysis/compliance", json=data)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_documents(self) -> List[Dict]:
        """Get list of uploaded documents"""
        try:
            response = requests.get(f"{self.api_base}/documents/")
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except:
            return []
    
    def start_batch_analysis(self, document_ids: List[str]) -> Dict:
        """Start batch analysis"""
        try:
            data = {
                "document_ids": document_ids,
                "analysis_type": "full",
                "include_explanations": True
            }
            response = requests.post(f"{self.api_base}/analysis/batch", json=data)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_batch_status(self, batch_id: str) -> Dict:
        """Get batch analysis status"""
        try:
            response = requests.get(f"{self.api_base}/analysis/batch/{batch_id}")
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

def main():
    ui = ComplianceSystemUI()
    
    # Header
    st.title("🏛️ Insurance Compliance System")
    st.markdown("AI-powered compliance monitoring for insurance documents")
    
    # Check API health
    if not ui.check_api_health():
        st.error("⚠️ API service is not available. Please ensure the backend is running.")
        st.info("Start the API server with: `python -m src.api.main`")
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Document Upload", "Single Analysis", "Batch Analysis", "Dashboard", "Document Library"]
    )
    
    if page == "Document Upload":
        document_upload_page(ui)
    elif page == "Single Analysis":
        single_analysis_page(ui)
    elif page == "Batch Analysis":
        batch_analysis_page(ui)
    elif page == "Dashboard":
        dashboard_page(ui)
    elif page == "Document Library":
        document_library_page(ui)

def document_upload_page(ui: ComplianceSystemUI):
    st.header("📤 Document Upload")
    st.markdown("Upload insurance documents for compliance analysis")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose files",
        accept_multiple_files=True,
        type=['pdf', 'txt', 'docx'],
        help="Upload PDF, TXT, or DOCX files (max 50MB each)"
    )
    
    if uploaded_files:
        st.subheader("Upload Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        uploaded_docs = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Uploading {uploaded_file.name}...")
            
            result = ui.upload_document(uploaded_file)
            
            if result["success"]:
                uploaded_docs.append(result["data"])
                st.success(f"✅ {uploaded_file.name} uploaded successfully")
            else:
                st.error(f"❌ Failed to upload {uploaded_file.name}: {result['error']}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.text("Upload complete!")
        
        if uploaded_docs:
            st.subheader("Uploaded Documents")
            df = pd.DataFrame(uploaded_docs)
            st.dataframe(df)

def single_analysis_page(ui: ComplianceSystemUI):
    st.header("🔍 Single Document Analysis")
    
    # Get available documents
    documents = ui.get_documents()
    
    if not documents:
        st.warning("No documents available. Please upload documents first.")
        return
    
    # Document selection
    doc_options = {doc["filename"]: doc["document_id"] for doc in documents}
    selected_doc = st.selectbox("Select document to analyze", options=list(doc_options.keys()))
    
    # Analysis options
    analysis_type = st.selectbox(
        "Analysis type",
        ["full", "quick", "specific"],
        help="Full: Complete compliance check, Quick: Basic check, Specific: Targeted analysis"
    )
    
    if st.button("🚀 Start Analysis", type="primary"):
        document_id = doc_options[selected_doc]
        
        with st.spinner(f"Analyzing {selected_doc}..."):
            result = ui.analyze_document(document_id, analysis_type)
        
        if result["success"]:
            display_analysis_results(result["data"])
        else:
            st.error(f"Analysis failed: {result['error']}")

def display_analysis_results(analysis_data: Dict):
    """Display compliance analysis results"""
    st.subheader("📊 Analysis Results")
    
    # Classification and confidence
    col1, col2, col3 = st.columns(3)
    
    with col1:
        classification = analysis_data["classification"]
        if classification == "COMPLIANT":
            st.success(f"✅ {classification}")
        elif classification == "NON_COMPLIANT":
            st.error(f"❌ {classification}")
        else:
            st.warning(f"⚠️ {classification}")
    
    with col2:
        confidence = analysis_data["confidence"]
        st.metric("Confidence Score", f"{confidence:.2%}")
    
    with col3:
        processing_time = analysis_data.get("processing_time", 0)
        st.metric("Processing Time", f"{processing_time:.1f}s")
    
    # Confidence gauge
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = confidence * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Confidence Score"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"},
                {'range': [80, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Violations
    violations = analysis_data.get("violations", [])
    if violations:
        st.subheader("🚨 Compliance Violations")
        for i, violation in enumerate(violations, 1):
            with st.expander(f"Violation {i}: {violation['type']}"):
                st.write(f"**Severity:** {violation['severity']}")
                st.write(f"**Description:** {violation['description']}")
                if violation.get('regulation_reference'):
                    st.write(f"**Regulation:** {violation['regulation_reference']}")
                if violation.get('suggested_fix'):
                    st.write(f"**Suggested Fix:** {violation['suggested_fix']}")
    
    # Recommendations
    recommendations = analysis_data.get("recommendations", [])
    if recommendations:
        st.subheader("💡 Recommendations")
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")
    
    # AI Explanation
    explanation = analysis_data.get("explanation")
    if explanation:
        st.subheader("🤖 AI Explanation")
        st.write(explanation)

def batch_analysis_page(ui: ComplianceSystemUI):
    st.header("📊 Batch Analysis")
    st.markdown("Analyze multiple documents simultaneously")
    
    documents = ui.get_documents()
    
    if not documents:
        st.warning("No documents available. Please upload documents first.")
        return
    
    # Document selection
    st.subheader("Select Documents")
    selected_docs = []
    
    for doc in documents:
        if st.checkbox(f"{doc['filename']} ({doc['file_size']} bytes)", key=doc['document_id']):
            selected_docs.append(doc['document_id'])
    
    if not selected_docs:
        st.info("Please select documents to analyze")
        return
    
    st.write(f"Selected {len(selected_docs)} documents for analysis")
    
    if st.button("🚀 Start Batch Analysis", type="primary"):
        result = ui.start_batch_analysis(selected_docs)
        
        if result["success"]:
            batch_data = result["data"]
            batch_id = batch_data["batch_id"]
            
            st.success(f"Batch analysis started! Batch ID: {batch_id}")
            
            # Progress tracking
            progress_container = st.container()
            
            with progress_container:
                status_col, progress_col = st.columns([1, 3])
                
                while True:
                    status_result = ui.get_batch_status(batch_id)
                    
                    if status_result["success"]:
                        batch_status = status_result["data"]
                        
                        with status_col:
                            st.metric("Status", batch_status["status"].title())
                            st.metric("Completed", f"{batch_status['completed']}/{batch_status['total_documents']}")
                        
                        with progress_col:
                            progress = batch_status["completed"] / batch_status["total_documents"]
                            st.progress(progress)
                        
                        if batch_status["status"] == "completed":
                            st.success("✅ Batch analysis completed!")
                            
                            # Display results summary
                            if batch_status.get("summary"):
                                st.subheader("📈 Summary")
                                st.text(batch_status["summary"])
                            
                            # Display individual results
                            results = batch_status.get("results", [])
                            if results:
                                display_batch_results(results)
                            
                            break
                        
                        elif batch_status["status"] == "failed":
                            st.error("❌ Batch analysis failed")
                            break
                        
                        time.sleep(2)  # Wait before next status check
                    else:
                        st.error(f"Failed to get batch status: {status_result['error']}")
                        break
        else:
            st.error(f"Failed to start batch analysis: {result['error']}")

def display_batch_results(results: List[Dict]):
    """Display batch analysis results"""
    st.subheader("📋 Batch Results")
    
    # Summary statistics
    total = len(results)
    compliant = sum(1 for r in results if r["classification"] == "COMPLIANT")
    non_compliant = sum(1 for r in results if r["classification"] == "NON_COMPLIANT")
    needs_review = sum(1 for r in results if r["classification"] == "REQUIRES_REVIEW")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Documents", total)
    with col2:
        st.metric("Compliant", compliant, delta=f"{compliant/total*100:.1f}%")
    with col3:
        st.metric("Non-Compliant", non_compliant, delta=f"{non_compliant/total*100:.1f}%", delta_color="inverse")
    with col4:
        st.metric("Needs Review", needs_review, delta=f"{needs_review/total*100:.1f}%")
    
    # Visualization
    fig = px.pie(
        values=[compliant, non_compliant, needs_review],
        names=["Compliant", "Non-Compliant", "Needs Review"],
        title="Compliance Distribution",
        color_discrete_map={
            "Compliant": "green",
            "Non-Compliant": "red", 
            "Needs Review": "orange"
        }
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed results table
    results_df = pd.DataFrame([
        {
            "Document ID": r["document_id"][:8] + "...",
            "Classification": r["classification"],
            "Confidence": f"{r['confidence']:.2%}",
            "Violations": len(r.get("violations", [])),
            "Analysis Time": f"{r['processing_time']:.1f}s"
        }
        for r in results
    ])
    
    st.dataframe(results_df, use_container_width=True)

def dashboard_page(ui: ComplianceSystemUI):
    st.header("📈 Compliance Dashboard")
    st.markdown("Overview of compliance status and trends")
    
    # Placeholder for dashboard metrics
    # In a real implementation, this would fetch aggregated data
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Documents", "156", delta="12")
    with col2:
        st.metric("Compliance Rate", "73.2%", delta="2.1%")
    with col3:
        st.metric("Violations Found", "42", delta="-5", delta_color="inverse")
    with col4:
        st.metric("Avg Processing Time", "2.3s", delta="-0.2s", delta_color="inverse")
    
    # Compliance trends (mock data)
    st.subheader("Compliance Trends")
    
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
    compliance_rates = [70 + 5 * (i % 7) + (i * 0.1) for i in range(30)]
    
    fig = px.line(
        x=dates,
        y=compliance_rates,
        title="Daily Compliance Rate",
        labels={"x": "Date", "y": "Compliance Rate (%)"}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent violations (mock data)
    st.subheader("Recent Violations")
    violations_data = [
        {"Document": "Policy_001.pdf", "Type": "Regulation Breach", "Severity": "High", "Date": "2024-01-15"},
        {"Document": "Claim_042.pdf", "Type": "Missing Information", "Severity": "Medium", "Date": "2024-01-14"},
        {"Document": "Policy_023.pdf", "Type": "Format Issue", "Severity": "Low", "Date": "2024-01-13"},
    ]
    
    violations_df = pd.DataFrame(violations_data)
    st.dataframe(violations_df, use_container_width=True)

def document_library_page(ui: ComplianceSystemUI):
    st.header("📚 Document Library")
    st.markdown("Manage your uploaded documents")
    
    documents = ui.get_documents()
    
    if not documents:
        st.info("No documents in library. Upload some documents to get started.")
        return
    
    # Documents table
    df = pd.DataFrame(documents)
    df['upload_timestamp'] = pd.to_datetime(df['upload_timestamp'])
    df['file_size_mb'] = df['file_size'] / (1024 * 1024)
    
    # Display options
    st.sidebar.subheader("Filter Options")
    doc_type_filter = st.sidebar.selectbox(
        "Document Type",
        ["All"] + list(df['document_type'].unique())
    )
    
    # Apply filters
    filtered_df = df
    if doc_type_filter != "All":
        filtered_df = df[df['document_type'] == doc_type_filter]
    
    # Display table
    display_columns = ['filename', 'document_type', 'file_size_mb', 'upload_timestamp', 'status']
    column_config = {
        'filename': 'File Name',
        'document_type': 'Type',
        'file_size_mb': st.column_config.NumberColumn('Size (MB)', format="%.2f"),
        'upload_timestamp': 'Upload Date',
        'status': 'Status'
    }
    
    st.dataframe(
        filtered_df[display_columns],
        column_config=column_config,
        use_container_width=True
    )
    
    st.info(f"Showing {len(filtered_df)} of {len(df)} documents")

if __name__ == "__main__":
    main()