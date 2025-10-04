# 🚀 Quick Commands - RAG + LLaMA System Setup

## ✅ CURRENT STATUS (Just Completed)

**What's Ready:**
- ✅ Dependencies installed (ChromaDB, Ollama, Groq)
- ✅ Ollama server running
- ✅ All RAG + LLaMA code created
- ✅ Legal-BERT model exists
- ✅ 203 regulations ready

**What's Needed:**
- ⏳ LLaMA model (choose option below)

---

# Quick Commands for Insurance Compliance System

## 🚀 Setup (5 Minutes)

```powershell
# Navigate to backend
cd c:\Users\adity\OneDrive\Desktop\Capstone\backend

# Install dependency
pip install PyPDF2

# Test system
python test_smart_scraper.py
```

---

## ▶️ Run Scraper

### Full Scraping (All Sites)
```powershell
python smart_scraper.py
```

### Single Site Test (Recommended First)
```powershell
python -c "from smart_scraper import SmartMotorVehicleScraper; s = SmartMotorVehicleScraper(); s.scrape_site_with_smart_filtering('IRDAI_MOTOR', s.sites['IRDAI_MOTOR']); s.save_final_stats()"
```

---

## 📊 Check Results

### View Downloaded PDFs
```powershell
dir D:\smart_motor_compliance_scraper\relevant_pdfs
```

### Count Downloaded Documents
```powershell
python -c "import pandas as pd; df = pd.read_csv('D:/smart_motor_compliance_scraper/motor_vehicle_relevant_docs.csv'); print(f'Downloaded: {len(df)} PDFs')"
```

### View Statistics
```powershell
python -c "import json; stats = json.load(open('D:/smart_motor_compliance_scraper/scraping_stats.json')); print(f\"Total: {stats['total_links_found']}\"); print(f\"Downloaded: {stats['successfully_downloaded']}\"); print(f\"Success rate: {stats['successfully_downloaded']/stats['total_links_found']*100:.1f}%\")"
```

### Analyze Rejections
```powershell
python -c "import json; rejected = json.load(open('D:/smart_motor_compliance_scraper/rejected_pdfs.json')); print(f'Rejected: {len(rejected)} PDFs'); reasons = {}; [reasons.update({d['reason']: reasons.get(d['reason'], 0) + 1}) for d in rejected]; print('Top reasons:'); [print(f'  {k}: {v}') for k, v in sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:5]]"
```

---

## 🎛️ Adjust Settings

### Make Stricter (Less PDFs)
Edit `smart_scraper.py` lines 57-64:
```python
'link_score': 35,          # Change from 25
'bert_confidence': 0.75,   # Change from 0.65
```

### Make More Lenient (More PDFs)
```python
'link_score': 15,          # Change from 25
'bert_confidence': 0.55,   # Change from 0.65
```

### Disable BERT (Faster, ~80% accuracy)
Line 66:
```python
'enable_bert': False,
```

### Add Blacklist Terms
Lines 74-82:
```python
self.blacklist_terms = [
    'newsletter',
    'election notice',
    'your_new_term_here',  # Add here
]
```

---

## 🔍 Monitor GPU Usage

```powershell
# Watch GPU in real-time (new terminal)
nvidia-smi -l 1
```

Expected during BERT stage:
- GPU utilization: 40-60%
- Memory: ~2-3 GB

---

## 🧹 Clean Up / Reset

### Delete Output (Start Fresh)
```powershell
Remove-Item -Recurse -Force D:\smart_motor_compliance_scraper
```

### Keep Logs, Delete PDFs Only
```powershell
Remove-Item -Force D:\smart_motor_compliance_scraper\relevant_pdfs\*
```

---

## 🔧 Troubleshooting

### BERT Not Loading
```powershell
# Check model exists
dir backend\models\legal_bert_domain_adapted

# If missing, scraper still works (80% accuracy)
# Or update path in smart_scraper.py line 142
```

### ChromeDriver Issues
```powershell
pip install --upgrade webdriver-manager
```

### Out of Memory
Edit `smart_scraper.py` line 66:
```python
'enable_bert': False,
```

---

## 📈 Compare Old vs New

```powershell
# Old scraper stats
python -c "import pandas as pd; df = pd.read_csv('D:/motor_compliance_scraper/motor_vehicle_compliance_documents.csv'); high = (df['motor_vehicle_relevance']=='HIGH').sum(); low = (df['motor_vehicle_relevance']=='LOW').sum(); print(f'Old: Total={len(df)}, HIGH={high} ({high/len(df)*100:.1f}%), LOW={low} ({low/len(df)*100:.1f}%)')"

# New scraper stats
python -c "import pandas as pd; df = pd.read_csv('D:/smart_motor_compliance_scraper/motor_vehicle_relevant_docs.csv'); print(f'New: Total={len(df)} (all should be relevant)')"
```

---

## 🎯 Recommended Workflow

### Day 1 (Today - 4-5 hours)

**Hour 1: Setup**
```powershell
pip install PyPDF2
python test_smart_scraper.py
```

**Hour 2: Test Run**
```powershell
# Single site first
python -c "from smart_scraper import SmartMotorVehicleScraper; s = SmartMotorVehicleScraper(); s.scrape_site_with_smart_filtering('IRDAI_MOTOR', s.sites['IRDAI_MOTOR']); s.save_final_stats()"
```

**Hour 3-4: Full Scraping**
```powershell
python smart_scraper.py
# Let it run, monitor terminal
```

**Hour 5: Analysis**
```powershell
# Check results
dir D:\smart_motor_compliance_scraper\relevant_pdfs

# Review rejections
python -c "import json; data = json.load(open('D:/smart_motor_compliance_scraper/rejected_pdfs.json')); print(f'Rejected: {len(data)}'); print('Sample reasons:'); [print(f\"  - {d['reason']}\") for d in data[:10]]"

# Adjust thresholds if needed
```

### Day 2 (Next - RAG Integration)
- Index documents in vector database
- Set up LLaMA for reasoning
- Build chat interface

---

## 💾 Output Files

| File | Purpose | Size |
|------|---------|------|
| `relevant_pdfs/*.pdf` | Downloaded PDFs | Varies |
| `motor_vehicle_relevant_docs.csv` | Dataset with metadata | ~1-5 MB |
| `processed_urls.txt` | Avoid duplicates | ~10 KB |
| `rejected_pdfs.json` | Audit log | ~50-200 KB |
| `scraping_stats.json` | Performance metrics | ~2 KB |

---

## 🎉 Success Indicators

You'll know it's working when you see:

```
✅ Stage 1 passed: URL score = 40
✅ Stage 2 passed: Link score = 75
✅ Stage 2.5 passed: No blacklist terms
✅ Stage 3 passed: Metadata relevant
✅ Stage 4 passed: BERT score = 0.823
🎉 ALL CHECKS PASSED - Downloading full PDF...
✅ Successfully downloaded: motor_insurance_guidelines_2023.pdf
```

And final stats show:
```
📊 PROGRESS STATISTICS
Total links evaluated: 150
✅ Successfully downloaded: 8 (5.3%)
❌ Filtered: 142 (94.7%)
```

**5-10% download rate = Excellent!** (Old scraper would download 100%)

---

## 📞 Quick Help

**Scraper too slow?**
→ Disable BERT: `'enable_bert': False`

**Too many PDFs?**
→ Increase thresholds: `'link_score': 35`

**Too few PDFs?**
→ Decrease thresholds: `'link_score': 15`

**Want to add blacklist?**
→ Edit lines 74-82 in `smart_scraper.py`

**BERT not working?**
→ Scraper still works at 80% accuracy

---

**Ready? Run:** `python test_smart_scraper.py` 🚀
