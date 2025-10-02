"""Quick API test to verify Phase 2 model integration with the backend."""

import requests
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
SAMPLE_PDF = Path(__file__).resolve().parent / "backend" / "test_samples" / "sample_policy_compliant.pdf"

def test_api_health():
    """Test API health endpoint."""
    print("🔍 Testing API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

def test_document_upload_and_analysis():
    """Test document upload and compliance analysis with Phase 2 model."""
    print("\n📄 Testing document upload and analysis...")
    
    if not SAMPLE_PDF.exists():
        print(f"❌ Sample PDF not found at {SAMPLE_PDF}")
        return False
    
    try:
        # Upload document
        print(f"   Uploading: {SAMPLE_PDF.name}")
        with open(SAMPLE_PDF, 'rb') as f:
            files = {'file': (SAMPLE_PDF.name, f, 'application/pdf')}
            upload_response = requests.post(f"{API_BASE_URL}/api/v1/documents/upload", files=files)
        
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(f"   Error: {upload_response.text}")
            return False
        
        doc_data = upload_response.json()
        doc_id = doc_data.get('document_id')
        print(f"✅ Document uploaded successfully (ID: {doc_id})")
        
        # Analyze document
        print("   Running compliance analysis with Phase 2 model...")
        analysis_payload = {
            "document_id": doc_id,
            "analysis_type": "full",
            "include_explanation": True
        }
        analysis_response = requests.post(
            f"{API_BASE_URL}/api/v1/compliance/analyze",
            json=analysis_payload
        )
        
        if analysis_response.status_code != 200:
            print(f"❌ Analysis failed: {analysis_response.status_code}")
            print(f"   Error: {analysis_response.text}")
            return False
        
        result = analysis_response.json()
        
        print("✅ Analysis completed successfully")
        print("\n📊 Results:")
        print(f"   Classification: {result.get('classification')}")
        print(f"   Confidence: {result.get('confidence', 0):.3f}")
        print(f"   Processing Time: {result.get('processing_time', 0):.2f}s")
        
        # Show probabilities if available
        metadata = result.get('metadata', {})
        probabilities = metadata.get('probabilities', {})
        if probabilities:
            print("\n   Class Probabilities:")
            for label, prob in probabilities.items():
                print(f"      {label}: {prob:.3f}")
        
        # Show recommendations
        recommendations = result.get('recommendations', [])
        if recommendations:
            print("\n   Recommendations:")
            for rec in recommendations:
                print(f"      • {rec}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all API tests."""
    print("=" * 60)
    print("Phase 2 Model - API Integration Test")
    print("=" * 60)
    
    # Test API health
    if not test_api_health():
        print("\n❌ API is not running. Please start it with:")
        print("   cd backend && python -m uvicorn api.main:app --reload --port 8000")
        return
    
    # Test document analysis
    test_document_upload_and_analysis()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
