# 🚀 How to Run the Motor Vehicle Insurance Compliance System

## 📋 Quick Start (Ready to Use!)

Your system is **already fully trained and configured**! Here's how to run it:

### 1. 🧪 Test the Core System (RECOMMENDED FIRST STEP)
```powershell
cd "D:\Capstone"

# Test all sample policies (takes ~30 seconds)
D:/Capstone/.venv/Scripts/python.exe test_pipeline.py          # ✅ Compliant policy test
D:/Capstone/.venv/Scripts/python.exe test_non_compliant.py     # ❌ Non-compliant policy test  
D:/Capstone/.venv/Scripts/python.exe test_review.py            # 🔍 Review required policy test

# Test the full system demonstration
D:/Capstone/.venv/Scripts/python.exe updated_compliance_system.py
```

**Expected Results:**
- ✅ Compliant policy: Classification = COMPLIANT, Score = 1.000
- ❌ Non-compliant policy: Classification = NON_COMPLIANT, Score = 0.000
- 🔍 Review policy: Classification varies based on content

### 2. 🌐 Start the Web Frontend (RECOMMENDED!)
```powershell
cd "D:\Capstone"

# Option 1: Quick start with launch script
.\start_frontend.ps1

# Option 2: Manual start
D:/Capstone/.venv/Scripts/python.exe -m streamlit run src/frontend/compliance_app.py
```

**Access Points:**
- **Web Interface**: http://localhost:8501 (Interactive compliance analysis)
- **Document Upload**: Drag and drop PDF files for analysis
- **Batch Processing**: Analyze multiple documents at once
- **Visual Dashboard**: Compliance metrics and system status

### 3. 🌐 Start the Web API Server (Optional)
```powershell
cd "D:\Capstone"

# Start the FastAPI server (runs on http://localhost:8000)
D:/Capstone/.venv/Scripts/python.exe -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Access Points:**
- **API Documentation**: http://localhost:8000/docs (Interactive Swagger UI)  
- **Alternative Docs**: http://localhost:8000/redoc
- **API Base URL**: http://localhost:8000

### 4. 📄 Analyze Your Own Documents

#### Quick Document Analysis (Command Line):
```powershell
# Put your PDF in test_samples folder, then run:
D:/Capstone/.venv/Scripts/python.exe -c "
from updated_compliance_system import RuleBasedComplianceEngine
from src.processing.parsers.document_parser import parse_document

engine = RuleBasedComplianceEngine()
text = parse_document('test_samples/YOUR_POLICY.pdf')  # Replace with your file
result = engine.classify_policy_text(text)

print(f'🎯 Classification: {result[\"classification\"]}')
print(f'📊 Confidence: {result[\"confidence\"]:.3f}')
print(f'📈 Score: {result[\"compliance_score\"]:.3f}')

for req in result['mandatory_compliance']:
    status = '✅' if req.get('compliant', False) else '❌'
    print(f'  {status} {req[\"rule\"]}')
"
```

#### API-Based Analysis:
```powershell
# 1. Upload document to API
curl -X POST "http://localhost:8000/upload/" -H "Content-Type: multipart/form-data" -F "file=@test_samples/sample_policy_compliant.pdf"

# 2. Analyze uploaded document (use document_id from upload response)
curl -X POST "http://localhost:8000/analysis/compliance" -H "Content-Type: application/json" -d "{\"document_id\":\"YOUR_DOCUMENT_ID\",\"analysis_type\":\"full\"}"
```

## 🎯 What The System Checks

### ✅ Mandatory Requirements Validated:
- **Third Party Liability**: Minimum Rs 15 lakh coverage
- **Personal Accident**: Coverage for owner-driver  
- **IRDAI Compliance**: Mentions of regulatory compliance
- **Coverage Types**: Comprehensive, third-party, own damage

### ❌ Violations Detected:
- Coverage below regulatory minimums
- Missing mandatory personal accident coverage  
- Explicit regulatory violations mentioned
- Non-compliance language patterns

### 💡 Recommendations Provided:
- Specific coverage amount increases needed
- Missing coverage additions required
- Regulatory compliance improvements

## 🖥️ Frontend Features

### 🔍 Document Analysis Page:
- **Upload Documents**: PDF or text files via drag & drop
- **Real-time Analysis**: Immediate compliance checking  
- **Detailed Results**: Classification, confidence scores, violations
- **Visual Charts**: Compliance gauges and confidence meters
- **Technical Breakdown**: Full analysis details and document preview

### 📊 Batch Analysis Page:
- **Multiple Documents**: Select and analyze several policies at once
- **Progress Tracking**: Real-time processing status with progress bars
- **Summary Statistics**: Overall compliance rates and distribution
- **Visual Reports**: Pie charts showing compliance breakdown
- **Export Results**: Downloadable analysis results table

### 📈 Dashboard Page:
- **System Status**: Health monitoring of all components
- **Performance Metrics**: Legal BERT accuracy (79.2%), processing stats
- **Model Information**: Training details and validation results
- **Sample Performance**: Test results on known documents

### ℹ️ System Info Page:
- **Architecture Overview**: Visual system workflow diagram
- **Component Status**: Real-time status of all system parts
- **Technical Specifications**: Model details, file locations
- **Compliance Coverage**: List of all regulatory areas checked

## 🔧 Development & Testing

### Test Individual Components:

#### 1. Document Parser Test:
```powershell
D:/Capstone/.venv/Scripts/python.exe -c "
from src.processing.parsers.document_parser import parse_document
text = parse_document('test_samples/sample_policy_compliant.pdf')
print(f'📄 Extracted {len(text)} characters')
print('📖 Preview:', text[:200])
"
```

#### 2. Legal BERT Model Test:
```powershell
D:/Capstone/.venv/Scripts/python.exe -c "
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import json

tokenizer = AutoTokenizer.from_pretrained('./models/legal_bert_rule_classification')
model = AutoModelForSequenceClassification.from_pretrained('./models/legal_bert_rule_classification')

with open('./models/legal_bert_rule_classification/rule_type_labels.json', 'r') as f:
    labels = json.load(f)
    labels = {int(k): v for k, v in labels.items()}

text = 'Third party liability coverage shall be minimum Rs 15 lakh per person'
inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
with torch.no_grad():
    outputs = model(**inputs)
    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
    predicted_class = torch.argmax(predictions, dim=-1).item()
    confidence = predictions[0][predicted_class].item()

print(f'🧠 Legal BERT Prediction: {labels[predicted_class]}')
print(f'📊 Confidence: {confidence:.3f}')
"
```

#### 3. Rule Classification Test:
```powershell
D:/Capstone/.venv/Scripts/python.exe -c "
from reclassify_rules import RuleTypeClassifier
classifier = RuleTypeClassifier()

texts = [
    'Third party liability coverage shall be minimum Rs 15 lakh per person',
    'Personal accident coverage is optional for commercial vehicles', 
    'Claims must be reported within 30 days of incident',
    'Motor vehicle means any mechanically propelled vehicle'
]

for text in texts:
    result = classifier.classify_text(text)
    print(f'📋 \"{text[:40]}...\" → {result[0]} ({result[1]:.3f})')
"
```

### Batch Processing Multiple Documents:
```powershell
D:/Capstone/.venv/Scripts/python.exe -c "
from updated_compliance_system import RuleBasedComplianceEngine
from src.processing.parsers.document_parser import parse_document
import os

engine = RuleBasedComplianceEngine()
print('🔄 BATCH PROCESSING RESULTS')
print('=' * 40)

for filename in os.listdir('test_samples/'):
    if filename.endswith('.pdf'):
        try:
            text = parse_document(f'test_samples/{filename}')
            result = engine.classify_policy_text(text)
            print(f'📄 {filename}')
            print(f'   🎯 {result[\"classification\"]} (Score: {result[\"compliance_score\"]:.3f})')
        except Exception as e:
            print(f'❌ Error with {filename}: {e}')
        print()
"
```

## 📊 System Architecture Overview

```
🏗️ SYSTEM COMPONENTS:

📋 Input: Policy Documents (PDF/Text)
    ↓
🔍 Document Parser (pdfplumber)
    ↓  
🧠 Legal BERT Rule Classifier (79.2% accuracy)
    ↓
📚 Regulatory Knowledge Base
    ↓
⚖️ Compliance Analysis Engine  
    ↓
📊 Results: COMPLIANT/NON_COMPLIANT/REQUIRES_REVIEW

🎯 TRAINED ON:
• 120 Motor Vehicle Insurance Regulations  
• IRDAI Guidelines & MoRTH Rules
• 5 Rule Types: MANDATORY, OPTIONAL, PROHIBITION, PROCEDURAL, DEFINITION
```

## 📁 Key Files You Can Interact With:

- **`updated_compliance_system.py`** - Main compliance analysis engine
- **`test_pipeline.py`** - End-to-end system testing  
- **`test_samples/`** - Sample policy documents for testing
- **`src/api/routes/compliance.py`** - API endpoints
- **`models/legal_bert_rule_classification/`** - Trained Legal BERT model

## 🚨 Troubleshooting

### Issue: "Module not found" errors
```powershell
D:/Capstone/.venv/Scripts/python.exe -m pip install torch transformers scikit-learn pandas pdfplumber fastapi uvicorn
```

### Issue: API server won't start
```powershell
# Check if main.py exists
ls src/api/main.py
# If missing, the API routes will still work with basic FastAPI setup
```

### Issue: PDF parsing fails  
```powershell
D:/Capstone/.venv/Scripts/python.exe -m pip install pdfplumber PyPDF2
```

### Issue: Model not found
```powershell
# Verify Legal BERT model files exist
ls models/legal_bert_rule_classification/
# Should show: config.json, model.safetensors, tokenizer files, etc.
```

## ✅ Success Validation Checklist

Your system is working correctly if:

- [ ] ✅ `test_pipeline.py` shows COMPLIANT classification  
- [ ] ❌ `test_non_compliant.py` shows NON_COMPLIANT with violations
- [ ] 🌐 API server starts at http://localhost:8000/docs  
- [ ] 📄 Document parser extracts text from sample PDFs
- [ ] 🧠 Legal BERT model loads and makes predictions
- [ ] 📊 Compliance engine provides detailed analysis with scores

## 🎉 You're All Set!

The **Motor Vehicle Insurance Compliance System** is **fully trained and ready to use**! 

- **79.2% accuracy** on regulatory rule classification
- **Comprehensive compliance checking** against IRDAI/MoRTH regulations  
- **Real-time analysis** of policy documents
- **Detailed explanations** and recommendations
- **Production-ready API** endpoints

Start with the Quick Start section above to see it in action! 🚀