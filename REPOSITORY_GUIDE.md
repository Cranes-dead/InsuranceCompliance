# 🗂️ Repository File Management Guide

## ✅ **Essential Files (KEEP in Git)**

### 🚀 **Core System Files**
- `updated_compliance_system.py` - Main compliance analysis engine
- `reclassify_rules.py` - Rule type classification logic
- `demo_system.py` - System demonstration and testing
- `requirements.txt` - Python dependencies

### 🖥️ **Frontend & API**
- `src/frontend/compliance_app.py` - Streamlit web interface
- `src/api/` - FastAPI backend components
- `src/processing/` - Document processing utilities

### 🧪 **Testing**
- `test_pipeline.py` - Main system testing
- `test_non_compliant.py` - Non-compliant sample testing
- `test_review.py` - Review sample testing
- `test_samples/` - Sample policy documents

### 📋 **Configuration & Docs**
- `HOW_TO_RUN.md` - Main usage guide
- `SOLUTION_SUMMARY.md` - Complete solution overview
- `readme.md` - Project overview
- `start_frontend.ps1` / `start_frontend.bat` - Launch scripts

### 🧠 **Model Configuration (Small Files)**
- `models/legal_bert_rule_classification/config.json`
- `models/legal_bert_rule_classification/tokenizer*.json`
- `models/legal_bert_rule_classification/rule_type_labels.json`
- `models/legal_bert_rule_classification/vocab.txt`

### 📊 **Training Data (Essential)**
- `data/training/motor_vehicle_rules_classification.csv` - Rule classifications

## 🚫 **Ignored Files (NOT in Git)**

### 💾 **Large Binary Files**
- `models/*/model.safetensors` - Large model weights (100MB+)
- `models/*/pytorch_model.bin` - PyTorch model binaries
- `models/*/checkpoint-*/` - Training checkpoints
- `*.bin`, `*.safetensors` - All binary model files

### 📁 **Runtime/Generated Files**
- `.venv/` - Python virtual environment
- `__pycache__/` - Python cache files
- `logs/` - Runtime log files
- `motor_vehicle_compliance.db` - Database file
- `temp_uploads/` - Temporary file uploads

### 📄 **Data Files**
- `data/uploads/*.pdf` - Uploaded documents
- `data/raw/*` - Raw scraped data
- `data/processed/*` - Processed data outputs

### 🔧 **Development Files (Optional)**
- `analyze_*.py` - Development analysis scripts
- `fix_*.py` - Development fix scripts
- `generate_*.py` - Development generation scripts
- `train_*.py` - Development training scripts
- `simple_*.py` - Development utility scripts
- `working_*.py` - Development workspace files

### 📋 **Documentation Drafts**
- `project idea.txt` - Initial project notes
- `DESIGN_DOCUMENT.md` - Design documentation
- `STARTUP_GUIDE.md` - Detailed startup guide
- `FRONTEND_SUCCESS.md` - Development notes

### 🛠️ **System Files**
- `OllamaSetup.exe` - Installation executable
- `*.tmp`, `*.temp`, `*.bak` - Temporary files

## 🎯 **Repository Size Optimization**

### Before .gitignore:
- **Estimated size**: 200MB+ (with model binaries)
- **Files**: 500+ (including all cache, models, data)

### After .gitignore:
- **Repository size**: ~20MB (essential files only)
- **Files**: ~50 (core system files only)

## 🔄 **What Happens When Someone Clones**

### ✅ **Available Immediately:**
- Complete source code
- Frontend interface  
- API endpoints
- Configuration files
- Sample documents
- Documentation

### 🔧 **Generated on First Run:**
- Virtual environment (`.venv/`)
- Model binaries (downloaded/trained)
- Cache files (`__pycache__/`)
- Log files (`logs/`)
- Database files (`*.db`)

## 📋 **Setup Commands for New Users**

```powershell
# 1. Clone repository
git clone https://github.com/Cranes-dead/Capstone.git
cd Capstone

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run system (will auto-generate missing components)
python demo_system.py

# 5. Start frontend
python -m streamlit run src/frontend/compliance_app.py
```

## 💡 **Benefits of This Approach**

✅ **Small Repository**: Fast clone and download times  
✅ **Essential Files Only**: Focus on code, not data  
✅ **Auto-Regeneration**: Missing files created on first run  
✅ **Clean Commits**: No large binary files in git history  
✅ **Easy Collaboration**: Developers get clean, focused codebase  

The system will work perfectly after cloning because all essential configuration and code files are included!