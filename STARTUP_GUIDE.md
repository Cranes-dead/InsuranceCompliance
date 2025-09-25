# Motor Vehicle Insurance Compliance System - Startup Guide

## 🚀 Complete Setup and Training Sequence

This guide provides the exact order of**🎯 Goal:** Organize scraped IRDAI motor vehicle insurance regulations and rules to train the AI model for compliance monitoring.

**🚗 Focus:** This system is specifically designed for **Motor Vehicle Insurance Compliance** monitoring.

**🎯 Comprehensive Motor Vehicle Compliance Categories Available:**

**1. 🏛️ MANDATORY COMPLIANCE (IRDAI/GOVT MANDATED)**
```
• Third Party Liability Insurance (Rs. 15L minimum for private cars)
• Personal Accident Cover for Owner-Driver (Rs. 15L)
• Goods Carrying Vehicle Third Party Coverage
• Passenger Carrying Vehicle Liability
• Compulsory Insurance Certificate (CIC) requirements
```

**2. 💼 COMMERCIAL VEHICLE COMPLIANCE**
```
• Heavy Commercial Vehicle (HCV) Requirements
• Light Commercial Vehicle (LCV) Guidelines  
• Passenger Service Vehicle (PSV) Regulations
• Goods Service Vehicle (GSV) Mandates
• Fleet Insurance Compliance
• Commercial Vehicle Fitness Certificate validation
```

**3. 🏠 PRIVATE VEHICLE CATEGORIES**
```
• Private Car Insurance (4-wheelers)
• Two-Wheeler Insurance Compliance
• Three-Wheeler/Auto-Rickshaw Rules
• Vintage/Classic Vehicle Insurance (25+ years old)
• Electric Vehicle (EV) Special Requirements
• CNG/LPG Vehicle Insurance Modifications
```

**4. 📋 POLICY FEATURE COMPLIANCE**
```
• Add-on Cover Validation (Zero Depreciation, Engine Protection)
• No Claim Bonus (NCB) Rules (20%-50% discount structure)
• Voluntary Deductible Compliance
• Policy Term and Renewal Guidelines (15 days cooling off)
• Multi-year Policy Compliance (2-3 year policies)
```

**5. 💰 PRICING & PREMIUM COMPLIANCE**
```
• IRDAI Motor Tariff Adherence
• Premium Calculation Validation
• Discount and Loading Guidelines
• Anti-Rebating Compliance (no cash back violations)
• GST Application on Motor Insurance (18% GST)
• Age-based premium calculations
```

**6. 🚨 CLAIM & SETTLEMENT COMPLIANCE**
```
• Third Party Motor Tariff (TPMT) Rates
• Cashless Settlement Procedures
• Survey and Loss Assessment Guidelines
• Hit and Run Case Procedures (SOLATIUM fund)
• Total Loss/Constructive Total Loss (>75% damage)
• Claim Intimation Requirements (48 hours for theft)
```

**7. 📱 DIGITAL & MODERN COMPLIANCE**
```
• Digital Policy Compliance
• QR Code Requirements on Physical Policies
• Mobile Claim Processing Validation
• Telematics/Usage-Based Insurance (UBI)
• Online Renewal Compliance
• Digital Payment Gateway Requirements
```

**8. ⚖️ LEGAL & REGULATORY UPDATES**
```
• Motor Vehicles Act 2019 Compliance
• IRDAI Motor Insurance Guidelines Updates
• Supreme Court Judgments Impact
• State-wise Variations (road tax, registration)
• MoRTH Notifications Compliance
• Insurance Ombudsman Procedures
```

**9. 🌍 SPECIAL CATEGORIES & REGIONAL COMPLIANCE**
```
• Border Area Vehicle Insurance
• Defense Personnel Vehicle Insurance Benefits
• Diplomatic Corps Vehicle Insurance
• Tourist/Visitor Vehicle Insurance
• Inter-state Vehicle Movement Compliance
• Vintage Car Club Approved Vehicles
```

**10. 🔧 TECHNICAL & SAFETY COMPLIANCE**
```
• Vehicle Safety Standards Compliance
• Pollution Under Control (PUC) Certificate
• Fitness Certificate for Commercial Vehicles
• Speed Limiters and Safety Device Requirements
• Airbag and Safety Feature Impact on Premium
• Vehicle Modification Disclosure Requirements
```erations to set up, train, and run the Motor Vehicle Insurance Compliance System from scratch.

**🚗 System Focus:** Automated compliance monitoring specifically for Motor Vehicle Insurance policies against IRDAI and MoRTH regulations.

---

## Phase 1: Initial Environment Setup

### Step 1: Python Environment Setup

```bash
# 1. Navigate to project directory
cd D:\Capstone

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment (CHOOSE ONE METHOD)
# 🔧 If you get "execution policy" error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# ✅ RECOMMENDED - PowerShell:
.venv\Scripts\Activate.ps1

# 🔄 ALTERNATIVE - Command Prompt (if PowerShell fails):
# .venv\Scripts\activate.bat

# ✅ Verify activation (you should see (.venv) in your prompt)
# Your prompt should now show: (.venv) PS D:\Capstone>

# 4. Upgrade pip and install build tools
python -m pip install --upgrade pip setuptools wheel

# 5. Install all dependencies (may take 5-10 minutes)
pip install -r requirements.txt

# 6. Install spaCy language model
python -m spacy download en_core_web_sm
```

**Important Notes:**
- If step 5 fails with torch or numpy errors, see "Issue 0.1" in troubleshooting section
- The virtual environment must stay activated for all subsequent commands
- Look for `(.venv)` at the start of your command prompt to confirm activation

### Step 2: Ollama Installation and Setup

```bash
# 1. Download Ollama from https://ollama.ai and install

# 2. Check if Ollama is already running (common after installation)
curl http://localhost:11434/api/tags

# 3. If step 2 shows an error, start Ollama service
ollama serve

# 4. If step 2 shows "models not found" or empty list, pull the language model
# ⚠️ LARGE DOWNLOAD (~4.9GB) - Will take 1-3 hours depending on internet speed
ollama pull llama3.1

# 5. Verify model is installed
ollama list

# 6. Test Ollama is working with the model
curl http://localhost:11434/api/tags
```

**Common Issues & Solutions:**
- **"bind: Only one usage" error**: Ollama is already running, skip step 3
- **"models not found"**: Run step 4 to download the model
- **Slow download**: This is normal, the model is 4.9GB

**Success Indicators:**
- `ollama list` shows "llama3.1" in the list
- `curl` command returns JSON with model information

### Step 3: Directory Structure Creation

```bash
# Create necessary directories
mkdir data\uploads, data\processed, data\training, data\raw, models, logs
```

### ✅ Phase 1 Verification

Before proceeding to data collection, verify your setup is complete:

```bash
# Test Python environment and packages
python -c "import torch, transformers, fastapi, streamlit, spacy; print('✅ All Python packages working!')"

# Test spaCy model
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('✅ spaCy model loaded!')"

# Test Ollama service
curl http://localhost:11434/api/tags

# Check if model is available
ollama list
```

**Expected Results:**
- All Python packages import without errors
- spaCy model loads successfully  
- curl returns JSON response
- ollama list shows "llama3.1"

**If any test fails, refer to the troubleshooting section before continuing.**

---

## Phase 2: Motor Insurance Regulatory Data Collection & Training Setup

### Step 4: Run Document Scraper (Collect Motor Insurance Regulatory Data)

**🎯 Goal:** Download IRDAI motor vehicle insurance regulations, MoRTH rules, and related compliance guidelines to train the compliance monitoring model.

**🚗 Focus:** Collecting regulations specifically for **Motor Vehicle Insurance Compliance**.

```bash
# Run the main scraper to collect motor insurance regulatory documents
python scraper.py

# OR run the streamlined version
python scraper_streamlined.py
```

**Expected Output:**
- Downloads motor insurance regulatory PDFs to `D:/motor_compliance_scraper/motor_insurance_pdfs/`
- Creates `motor_vehicle_compliance_documents.csv` with extracted regulatory text
- Generates `processed_motor_urls.txt` for tracking processed URLs
- **🎯 NEW**: Prioritizes documents with HIGH motor vehicle relevance

**📚 What Gets Scraped (Motor Insurance Focus):**
- **IRDAI Motor Insurance Regulations:** Third party liability rules, coverage mandates
- **MoRTH Vehicle Insurance Rules:** Mandatory insurance requirements for vehicles
- **Premium Guidelines:** IRDAI approved motor insurance tariffs
- **Coverage Standards:** Minimum coverage requirements, add-on regulations
- **Claim Settlement Rules:** Motor insurance claim compliance procedures

**🎯 Training Use:** These regulatory documents will be used to train the AI model to understand motor vehicle insurance compliance patterns.

### Step 5: Prepare Training Data for Motor Vehicle Insurance Compliance

**🎯 Goal:** Organize scraped IRDAI motor vehicle insurance regulations and rules to train the AI model for compliance monitoring.

**� Focus:** This system is specifically designed for **Motor Vehicle Insurance Compliance** monitoring.

#### Using Regulatory Documents for Training

```bash
# Organize scraped regulatory documents for motor insurance training
python -c "
import pandas as pd
import os
import shutil

# Check if scraper data exists
scraper_file = 'D:/motor_compliance_scraper/motor_vehicle_compliance_documents.csv'
if not os.path.exists(scraper_file):
    print('⚠️  Scraper data not found. Run Step 4 first to collect IRDAI motor insurance regulations.')
    print('   Need regulatory documents before training the model.')
else:
    # Read scraped regulatory data
    df = pd.read_csv(scraper_file)
    
    # Create training directory structure for regulatory documents
    folders = ['data/training/motor_regulations', 'data/training/irdai_guidelines', 'data/training/mort_rules']
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    
    print(f'✅ Found {len(df)} regulatory documents')
    print('📚 These regulations will be used to train the compliance model:')
    print('   - IRDAI motor insurance regulations')
    print('   - MoRTH vehicle insurance requirements') 
    print('   - Government insurance guidelines')
    print()
    print('📁 Training folders created at: data/training/')
    print('🎯 Model will learn compliance patterns from these regulations')
"
```

#### Manual Organization of Regulatory Documents (Optional)

If you want to organize the scraped documents by type:

```bash
# Create organized structure for different types of regulations
python -c "
import os

# Create specific folders for different regulation types
regulation_folders = [
    'data/training/motor_insurance_regulations',
    'data/training/third_party_liability_rules', 
    'data/training/premium_guidelines',
    'data/training/coverage_mandates',
    'data/training/claim_procedures'
]

for folder in regulation_folders:
    os.makedirs(folder, exist_ok=True)
    
print('✅ Regulation-specific training folders created!')
print('� You can optionally organize scraped documents by regulation type:')
print('   - Motor Insurance Regulations (general rules)')
print('   - Third Party Liability Rules (mandatory coverage)')
print('   - Premium Guidelines (IRDAI approved rates)')
print('   - Coverage Mandates (required covers)')
print('   - Claim Procedures (compliance processes)')
print()
print('📚 Source documents location: D:/motor_compliance_scraper/motor_insurance_pdfs/')
print('🎯 Organized documents help the model learn specific compliance areas')
"
```

#### Quick Setup for Testing (No Manual Organization)

```bash
# Simple setup - use all scraped regulations for training
python -c "
import os
import pandas as pd

# Create single training folder for all regulations
os.makedirs('data/training/all_regulations', exist_ok=True)

# Check scraped data
scraper_file = 'D:/motor_compliance_scraper/motor_vehicle_compliance_documents.csv'
if os.path.exists(scraper_file):
    df = pd.read_csv(scraper_file)
    print(f'✅ Ready to train with {len(df)} motor insurance regulations')
    print('📁 Training folder: data/training/all_regulations/')
    print('📚 Model will learn from all IRDAI motor insurance rules')
    print('🚗 Focus: Motor Vehicle Insurance Compliance')
else:
    print('⚠️  Run Step 4 first to collect regulatory documents')

print()
print('🔍 Training Process:')
print('   1. Model reads IRDAI motor insurance regulations')
print('   2. Learns patterns of compliant vs non-compliant language')
print('   3. Can then check new motor policies against these learned patterns')
"
```

**� What the Model Will Learn:**

From the scraped IRDAI and MoRTH documents, the model will understand:
- **Minimum Coverage Requirements** (Third party liability amounts)
- **Mandatory Covers** (Personal accident, etc.)
- **Premium Rate Guidelines** (IRDAI approved tariffs)
- **Policy Terms Compliance** (Required clauses and exclusions)
- **Claim Settlement Rules** (Process compliance)

**✅ Verification:**
```bash
# Check if regulatory training data is ready
python -c "
import os
import pandas as pd

# Check scraped regulatory data
scraper_file = 'D:/motor_compliance_scraper/motor_vehicle_compliance_documents.csv'
training_folders = ['data/training/motor_regulations', 'data/training/all_regulations']

if os.path.exists(scraper_file):
    df = pd.read_csv(scraper_file)
    print(f'� Regulatory Documents Available: {len(df)}')
    print('📁 Source: D:/motor_compliance_scraper/motor_insurance_pdfs/')
    
    # Check training folders
    total_ready = 0
    for folder in training_folders:
        if os.path.exists(folder):
            total_ready += 1
            
    if total_ready > 0:
        print('✅ Training folders ready!')
        print('🚗 Ready to train Motor Vehicle Insurance Compliance Model')
    else:
        print('⚠️  No training folders found. Run setup commands above.')
else:
    print('⚠️  No scraped regulatory data found.')
    print('   Run Step 4 (scraper) first to collect IRDAI motor insurance regulations')

print()
print('🎯 Training Approach: Regulations → Model → Policy Compliance Checking')
"
```

**🚗 Motor Vehicle Insurance Compliance Areas:**

**📋 Mandatory Coverage Requirements:**
- Third Party Insurance compliance (minimum Rs. 15L coverage for private vehicles)
- Personal Accident Cover requirements (Rs. 15L for owner-driver)
- Passenger Legal Liability (for commercial vehicles)
- Goods Carrying Vehicle compliance (different liability limits)

**💰 Premium & Pricing Compliance:**
- Premium calculation validation against IRDAI tariffs
- No Cash Discount violations (anti-rebating provisions)
- Proper application of No Claim Bonus (NCB)
- Age and vehicle type-based premium compliance

**📑 Policy Terms & Conditions:**
- Standard policy wordings compliance
- Proper exclusions and inclusions as per IRDAI guidelines
- Cooling-off period compliance (15 days for new policies)
- Policy renewal notice requirements (45 days advance notice)

**🔧 Add-on Coverage Compliance:**
- Zero Depreciation cover guidelines
- Engine Protection cover validity
- Return to Invoice (RTI) compliance
- Road Side Assistance (RSA) terms
- Key Replacement and Lock Repair compliance

**🚛 Vehicle Type-Specific Compliance:**
- Two-wheeler specific requirements
- Private car vs Commercial vehicle differentiation
- Heavy Commercial Vehicle (HCV) regulations
- Passenger Carrying Vehicle (PCV) requirements
- Goods Carrying Vehicle (GCV) mandates
- Vintage and Classic car insurance rules

**📋 Documentation & Process Compliance:**
- Proper vehicle registration verification
- Valid Driving License requirements
- Fitness Certificate compliance (for commercial vehicles)
- Pollution Under Control (PUC) certificate validation
- Previous insurance history verification

**💸 Claim Settlement Compliance:**
- Cashless claim settlement procedures
- Third Party Motor Tariff (TPMT) compliance
- Survey and assessment guidelines
- Claim intimation timeframes
- Total Loss/Constructive Total Loss procedures

**📊 Regulatory Filing & Reporting:**
- IRDAI return filing compliance
- Motor Third Party data reporting
- Claim settlement ratio reporting
- Grievance handling compliance
- Ombudsman reference procedures

**🌍 Regional & Special Cases:**
- Border area vehicle insurance
- Defense personnel vehicle insurance
- Diplomatic corps vehicle insurance
- Electric Vehicle (EV) insurance compliance
- CNG/LPG vehicle insurance requirements

**📱 Digital & Modern Compliance:**
- Digital policy issuance compliance
- QR code requirements on policies
- Mobile app-based claim compliance
- Telematics and Usage-Based Insurance (UBI)
- Online policy renewal compliance

**⚖️ Legal & Regulatory Updates:**
- Motor Vehicles Act 2019 compliance
- Hit and Run case coverage
- Golden Hour treatment compliance
- Compulsory insurance violation penalties
- Court awarded compensation limits

---

## Phase 3: Database Setup

### Step 6: Initialize Database

```bash
# Run database initialization
python -c "
from src.data.database import create_tables, engine
create_tables()
print('Database tables created successfully!')
"
```

---

## Phase 4: Model Training

### Step 7: Train Legal BERT Model

```bash
# Navigate to training directory
cd src\ml\training

# Run the training script
python train_legal_bert.py --data-dir ..\..\..\data\training --epochs 3 --batch-size 8

# Training will save model to: ../../../models/legal_bert_compliance/
```

**Training Output:**
- Model files saved in `models/legal_bert_compliance/`
- Training logs in `logs/training.log`
- Model metrics and validation scores

### Step 8: Test Model Loading

```bash
# Test if model loads correctly
python -c "
import sys
sys.path.append('src')
from ml.models.legal_bert import LegalBERTClassifier

model = LegalBERTClassifier()
model.load_model('models/legal_bert_compliance')
print('Model loaded successfully!')
"
```

---

## Phase 5: Service Startup

### Step 9: Start API Backend (Terminal 1)

```bash
# Navigate to API directory
cd src\api

# Start FastAPI server
python main.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Verify API is running:** Open http://localhost:8000/docs in browser

### Step 10: Start Streamlit Frontend (Terminal 2)

```bash
# Open new terminal/PowerShell window
cd D:\Capstone
.venv\Scripts\Activate.ps1

# Navigate to frontend directory  
cd src\frontend

# Start Streamlit app
streamlit run app.py
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
Network URL: http://192.168.1.x:8501
```

---

## Phase 6: System Testing and Validation

### Step 11: Test Complete System

#### Test API Endpoints:
```bash
# Test health check
curl http://localhost:8000/health

# Test document upload (with a sample PDF)
curl -X POST "http://localhost:8000/documents/upload" -H "Content-Type: multipart/form-data" -F "file=@sample_policy.pdf"
```

#### Test Web Interface:
1. Open http://localhost:8501
2. Navigate to "Document Upload" page
3. Upload a sample insurance document
4. Go to "Document Analysis" page
5. Analyze the uploaded document
6. Check "Dashboard" for results

### Step 12: Verify Model Training Results

```bash
# Check model performance
python -c "
import sys
sys.path.append('src')
from ml.models.legal_bert import LegalBERTClassifier

model = LegalBERTClassifier()
model.load_model('models/legal_bert_compliance')

# Test with sample text
sample_text = 'This policy complies with IRDAI regulations for motor insurance coverage.'
result = model.predict([sample_text])
print(f'Sample prediction: {result}')
"
```

---

## File Execution Order Summary

### Required Order:
1. **Environment Setup** → `pip install -r requirements.txt`
2. **Ollama Setup** → `ollama serve` & `ollama pull llama3.1`
3. **Regulatory Data Collection** → `python scraper.py` (downloads IRDAI rules as reference)
4. **Training Data Preparation** → Collect & label actual insurance policies in `data/training/`
5. **Database Setup** → Initialize database tables
6. **Model Training** → `python src/ml/training/train_legal_bert.py`
7. **API Server** → `python src/api/main.py`
8. **Frontend** → `streamlit run src/frontend/app.py`

### Critical Dependencies:
- **Ollama must be running** before starting API server
- **Model must be trained** before running compliance analysis
- **Database must be initialized** before uploading documents
- **API server must be running** before using frontend features

---

## Troubleshooting Common Issues

### Issue 0: PowerShell Execution Policy Error
```bash
# ERROR: Scripts disabled on this system
# SOLUTION 1: Change execution policy (recommended)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# SOLUTION 2: Use Command Prompt instead of PowerShell
cmd
.venv\Scripts\activate.bat

# SOLUTION 3: Bypass policy for single session
powershell -ExecutionPolicy Bypass

# SOLUTION 4: Use batch file activation
.venv\Scripts\activate.bat
```

### Issue 0.1: Package Version Conflicts & Build Errors
```bash
# ERROR: Could not find a version that satisfies the requirement torch==2.1.1
# ERROR: Cannot import 'setuptools.build_meta'
# SOLUTION 1: Install build tools first, then packages
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# SOLUTION 2: Install critical packages individually
pip install --upgrade pip setuptools wheel
pip install numpy>=1.26.0  # Python 3.12 compatible version
pip install torch>=2.2.0 torchvision>=0.17.0
pip install transformers>=4.35.0
pip install fastapi uvicorn streamlit
pip install -r requirements.txt

# SOLUTION 3: Clear everything and start fresh
pip cache purge
pip uninstall -y numpy torch torchvision transformers
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# SOLUTION 4: If still failing, install one by one
pip install setuptools wheel
pip install numpy
pip install torch torchvision
pip install transformers
pip install scikit-learn
pip install fastapi uvicorn
pip install streamlit
pip install spacy
pip install sqlalchemy
pip install selenium webdriver-manager
pip install pdfplumber langdetect
pip install python-dotenv pydantic loguru
pip install ollama
```

### Issue 1: Ollama Connection Failed
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve
```

### Issue 1.1: Ollama Port Already in Use
```bash
# ERROR: listen tcp 127.0.0.1:11434: bind: Only one usage of each socket address
# This means Ollama is already running!

# SOLUTION 1: Check if Ollama is running
netstat -ano | findstr :11434
curl http://localhost:11434/api/tags

# SOLUTION 2: If Ollama is running but no models, pull the model
ollama list  # Check installed models
ollama pull llama3.1  # Download the model (large download ~4.9GB)

# SOLUTION 3: If you need to restart Ollama service
# Find the process ID (PID) from netstat command above
taskkill /PID <PID_NUMBER> /F
ollama serve

# SOLUTION 4: Check Ollama status
ollama list  # Should show llama3.1 after download completes
```

### Issue 2: Model Not Found
```bash
# Verify model directory exists
ls models/legal_bert_compliance/

# If missing, retrain:
python src/ml/training/train_legal_bert.py --data-dir data/training --epochs 3
```

### Issue 3: Import Errors
```bash
# Ensure you're in the right directory and virtual environment is active
pwd  # Should be D:\Capstone
python -c "import sys; print(sys.executable)"  # Should point to .venv
```

### Issue 4: Port Already in Use
```bash
# Find what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :8501

# Kill the process if needed
taskkill /PID <PID_NUMBER> /F
```

---

## Quick Start Commands (After Initial Setup)

Once everything is set up, you can start the system with these commands:

**Terminal 1 - API Server:**
```bash
cd D:\Capstone && .venv\Scripts\activate.bat && cd src\api && python main.py
```

**Terminal 2 - Frontend:**
```bash
cd D:\Capstone && .venv\Scripts\activate.bat && cd src\frontend && streamlit run app.py
```

**Terminal 3 - Ollama (if not running as service):**
```bash
ollama serve
```

---

## Success Indicators

✅ **Environment Setup Complete:**
- Virtual environment activated
- All packages installed without errors
- spaCy model downloaded

✅ **Data Collection Complete:**
- PDF files in `D:/compliance_scraper/scraped_pdfs/`
- CSV file with extracted text created
- Training data organized in labeled folders

✅ **Model Training Complete:**
- Model files in `models/legal_bert_compliance/`
- Training completed without errors
- Model can be loaded successfully

✅ **Services Running:**
- API server responding at http://localhost:8000
- Frontend accessible at http://localhost:8501
- Ollama service running at http://localhost:11434

✅ **System Integration:**
- Documents can be uploaded through web interface
- Compliance analysis returns results
- AI explanations are generated
- Dashboard shows analytics

You're now ready to use the complete Insurance Compliance System! 🎉