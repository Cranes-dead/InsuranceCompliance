"""
Simple Streamlit Frontend for Compliance System
Works with the current FastAPI backend
"""

import streamlit as st
import requests
import json
from pathlib import Path
import tempfile
import os

# Configure page
st.set_page_config(
    page_title="Insurance Compliance System",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

def main():
    st.title("🚗 Motor Vehicle Insurance Compliance System")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Navigation")
        page = st.radio(
            "Choose a page:",
            ["Document Analysis", "System Status", "About"]
        )
    
    if page == "Document Analysis":
        document_analysis_page()
    elif page == "System Status":
        system_status_page()
    elif page == "About":
        about_page()

def document_analysis_page():
    st.header("📄 Document Compliance Analysis")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Policy Document",
        type=['pdf', 'txt'],
        help="Upload a motor vehicle insurance policy document for compliance analysis"
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if uploaded_file is not None:
            st.success(f"File uploaded: {uploaded_file.name}")
            
            # Analysis button
            if st.button("🔍 Analyze Compliance", type="primary"):
                with st.spinner("Analyzing document..."):
                    try:
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                            tmp_file.write(uploaded_file.read())
                            tmp_path = tmp_file.name
                        
                        # Upload to API
                        with open(tmp_path, 'rb') as f:
                            files = {'file': (uploaded_file.name, f, uploaded_file.type)}
                            response = requests.post(f"{API_BASE_URL}/api/v1/documents/upload", files=files)
                        
                        if response.status_code == 200:
                            doc_data = response.json()
                            doc_id = doc_data['document_id']
                            
                            # Analyze document
                            analysis_response = requests.post(
                                f"{API_BASE_URL}/api/v1/compliance/analyze",
                                json={
                                    "document_id": doc_id,
                                    "analysis_type": "full",
                                    "include_explanation": True
                                }
                            )
                            
                            if analysis_response.status_code == 200:
                                analysis_result = analysis_response.json()
                                display_analysis_result(analysis_result)
                            else:
                                st.error(f"Analysis failed: {analysis_response.text}")
                        else:
                            st.error(f"Upload failed: {response.text}")
                        
                        # Cleanup
                        os.unlink(tmp_path)
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        else:
            st.info("👆 Please upload a document to begin analysis")
    
    with col2:
        st.markdown("### 📊 Quick Stats")
        try:
            # Get system stats
            stats_response = requests.get(f"{API_BASE_URL}/health")
            if stats_response.status_code == 200:
                stats = stats_response.json()
                st.metric("System Status", "🟢 Online")
                st.metric("API Version", "v1.0")
            else:
                st.metric("System Status", "🔴 Offline")
        except:
            st.metric("System Status", "🔴 Offline")

def display_analysis_result(result):
    """Display the analysis result in a nice format."""
    st.markdown("---")
    st.header("📊 Analysis Results")
    
    # Classification result
    classification = result.get('classification', 'UNKNOWN')
    confidence = result.get('confidence', 0.0)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if classification == 'COMPLIANT':
            st.success(f"✅ {classification}")
        elif classification == 'NON_COMPLIANT':
            st.error(f"❌ {classification}")
        else:
            st.warning(f"⚠️ {classification}")
    
    with col2:
        st.metric("Confidence", f"{confidence:.1%}")
    
    with col3:
        st.metric("Processing Time", f"{result.get('processing_time', 0):.2f}s")
    
    # Violations
    violations = result.get('violations', [])
    if violations:
        st.subheader("🚨 Violations Found")
        for i, violation in enumerate(violations, 1):
            with st.expander(f"Violation {i}: {violation.get('type', 'Unknown')}"):
                st.write(f"**Severity:** {violation.get('severity', 'Unknown')}")
                st.write(f"**Description:** {violation.get('description', 'No description')}")
                if violation.get('suggested_action'):
                    st.write(f"**Suggested Action:** {violation.get('suggested_action')}")
    
    # Recommendations
    recommendations = result.get('recommendations', [])
    if recommendations:
        st.subheader("💡 Recommendations")
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")
    
    # Explanation
    explanation = result.get('explanation')
    if explanation:
        st.subheader("🤖 AI Explanation")
        st.write(explanation)

def system_status_page():
    st.header("🔧 System Status")
    
    try:
        # Health check
        health_response = requests.get(f"{API_BASE_URL}/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            
            st.success("✅ Backend API is running")
            
            col1, col2 = st.columns(2)
            with col1:
                st.json(health_data)
            
            with col2:
                st.markdown("### 🚀 Available Features")
                st.write("- Document upload and parsing")
                st.write("- Compliance analysis")
                st.write("- Violation detection")
                st.write("- Recommendation generation")
                
                st.markdown("### 🔮 Advanced AI Features")
                st.info("Advanced AI features (Legal BERT + Ollama) can be enabled by running `python setup_advanced_ai.py`")
        else:
            st.error("❌ Backend API is not responding")
    
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend API")
        st.markdown("### 🚀 Start the Backend")
        st.code("python -m uvicorn api.main:app --reload --port 8000")

def about_page():
    st.header("ℹ️ About")
    
    st.markdown("""
    ## 🚗 Motor Vehicle Insurance Compliance System
    
    This system helps analyze motor vehicle insurance policies for regulatory compliance.
    
    ### 🎯 Key Features:
    - **Document Analysis**: Upload and analyze policy documents
    - **Compliance Classification**: Automated compliance assessment
    - **Violation Detection**: Identify specific compliance issues
    - **Smart Recommendations**: Get actionable improvement suggestions
    - **Dual AI Architecture**: Simple models + Advanced AI options
    
    ### 🛠️ Technology Stack:
    - **Backend**: FastAPI + Python
    - **Frontend**: Streamlit
    - **ML Models**: Simple ML + Legal BERT + Ollama (optional)
    - **Document Processing**: PyPDF2, Text extraction
    
    ### 📊 Current Status:
    - ✅ Core system functional
    - ✅ Simple ML models active
    - 🔮 Advanced AI available (requires setup)
    
    ### 🚀 Getting Started:
    1. Upload a policy document
    2. Click "Analyze Compliance"
    3. Review results and recommendations
    
    For advanced AI features, run: `python setup_advanced_ai.py`
    """)

if __name__ == "__main__":
    main()