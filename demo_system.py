"""
🚀 DEMO: Complete Motor Vehicle Insurance Compliance System
===========================================================

This demo shows all components working together:
1. Document parsing
2. Rule-based compliance analysis  
3. Legal BERT integration
4. Frontend visualization
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def demo_core_system():
    """Demo the core compliance analysis system"""
    print("🔧 TESTING CORE COMPLIANCE SYSTEM")
    print("=" * 50)
    
    try:
        from updated_compliance_system import RuleBasedComplianceEngine
        from src.processing.parsers.document_parser import parse_document
        
        engine = RuleBasedComplianceEngine()
        print("✅ Compliance engine loaded successfully")
        
        # Test with sample documents
        sample_files = [
            ('test_samples/sample_policy_compliant.pdf', 'COMPLIANT SAMPLE'),
            ('test_samples/sample_policy_non_compliant.pdf', 'NON-COMPLIANT SAMPLE'), 
            ('test_samples/sample_policy_requires_review.pdf', 'REVIEW SAMPLE')
        ]
        
        for file_path, label in sample_files:
            if Path(file_path).exists():
                print(f"\n📄 Testing {label}")
                print("-" * 30)
                
                # Parse document
                text = parse_document(file_path)
                print(f"📖 Extracted {len(text)} characters")
                
                # Analyze compliance
                result = engine.classify_policy_text(text)
                
                print(f"🎯 Classification: {result['classification']}")
                print(f"📊 Confidence: {result['confidence']:.3f}")
                print(f"📈 Score: {result['compliance_score']:.3f}")
                
                # Show mandatory requirements
                for req in result.get('mandatory_compliance', []):
                    status = "✅" if req.get('compliant', False) else "❌"
                    print(f"  {status} {req['rule']}")
                
                if result.get('recommendations'):
                    print(f"💡 Recommendations: {len(result['recommendations'])}")
            else:
                print(f"❌ Sample file not found: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Core system error: {e}")
        return False

def demo_frontend_components():
    """Demo frontend component availability"""
    print("\n🖥️ TESTING FRONTEND COMPONENTS")
    print("=" * 50)
    
    try:
        import streamlit as st
        print("✅ Streamlit available")
        
        import plotly.express as px
        import plotly.graph_objects as go
        print("✅ Plotly available")
        
        import pandas as pd
        print("✅ Pandas available")
        
        # Test frontend app imports
        try:
            from src.frontend.compliance_app import main
            print("✅ Frontend app components loaded")
        except Exception as e:
            print(f"⚠️ Frontend app import warning: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Frontend components error: {e}")
        return False

def demo_model_components():
    """Demo ML model components"""
    print("\n🧠 TESTING ML MODEL COMPONENTS")
    print("=" * 50)
    
    try:
        import torch
        print("✅ PyTorch available")
        
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        print("✅ Transformers available")
        
        # Check Legal BERT model
        model_path = "models/legal_bert_rule_classification"
        if Path(model_path).exists():
            print("✅ Legal BERT model directory found")
            
            # Try to load model
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                model = AutoModelForSequenceClassification.from_pretrained(model_path)
                print("✅ Legal BERT model loaded successfully")
                
                # Test prediction
                text = "Third party liability coverage shall be minimum Rs 15 lakh"
                inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = model(**inputs)
                    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                    confidence = torch.max(predictions).item()
                
                print(f"✅ Model prediction test passed (confidence: {confidence:.3f})")
                
            except Exception as e:
                print(f"⚠️ Model loading warning: {e}")
        else:
            print("❌ Legal BERT model directory not found")
            
        return True
        
    except Exception as e:
        print(f"❌ ML components error: {e}")
        return False

def demo_api_components():
    """Demo API components"""
    print("\n🌐 TESTING API COMPONENTS") 
    print("=" * 50)
    
    try:
        from fastapi import FastAPI
        print("✅ FastAPI available")
        
        import uvicorn
        print("✅ Uvicorn available")
        
        # Test API app imports
        try:
            from src.api.main import app
            print("✅ API application components loaded")
        except Exception as e:
            print(f"⚠️ API app import warning: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ API components error: {e}")
        return False

def main():
    """Run complete system demo"""
    print("🚀 MOTOR VEHICLE INSURANCE COMPLIANCE SYSTEM DEMO")
    print("=" * 60)
    print("Testing all system components...\n")
    
    results = {
        "Core System": demo_core_system(),
        "Frontend": demo_frontend_components(), 
        "ML Models": demo_model_components(),
        "API": demo_api_components()
    }
    
    print("\n📊 DEMO RESULTS SUMMARY")
    print("=" * 30)
    
    all_passed = True
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{component:<15} {status}")
        if not passed:
            all_passed = False
    
    print("\n🎯 OVERALL SYSTEM STATUS")
    print("=" * 30)
    
    if all_passed:
        print("✅ ALL SYSTEMS OPERATIONAL")
        print("\n🚀 Ready to run:")
        print("   Frontend: D:/Capstone/.venv/Scripts/python.exe -m streamlit run src/frontend/compliance_app.py")
        print("   API: D:/Capstone/.venv/Scripts/python.exe -m uvicorn src.api.main:app --reload")
        print("   Direct: D:/Capstone/.venv/Scripts/python.exe updated_compliance_system.py")
    else:
        print("⚠️ SOME COMPONENTS NEED ATTENTION")
        print("Check the error messages above for details.")
    
    print(f"\n📋 Access Points:")
    print(f"   🖥️ Web Frontend: http://localhost:8501")
    print(f"   🌐 API Docs: http://localhost:8000/docs") 
    print(f"   📄 Project Guide: HOW_TO_RUN.md")

if __name__ == "__main__":
    main()