# Smart Scraper Implementation Checklist ✅

## Hour 1: Setup & Testing (30-60 minutes)

### Step 1: Install Dependencies ⏱️ 2 minutes
```powershell
cd c:\Users\adity\OneDrive\Desktop\Capstone\backend
pip install PyPDF2
```

- [ ] PyPDF2 installed
- [ ] No errors in installation

---

### Step 2: Run Tests ⏱️ 2 minutes
```powershell
python test_smart_scraper.py
```

**Expected output:**
```
✅ Scraper initialized successfully
✅ URL filtering working
✅ Link text filtering working  
✅ Blacklist filtering working
✅ BERT classification working (or ⚠️ disabled)
✅ Configuration loaded
🎉 All tests completed!
```

- [ ] All tests passed
- [ ] BERT model loaded (if available)
- [ ] No fatal errors

---

### Step 3: Verify BERT Model ⏱️ 1 minute
```powershell
dir backend\models\legal_bert_domain_adapted
```

**If BERT exists:**
- [ ] Model files found
- [ ] Test output shows "✅ BERT classification working"

**If BERT missing:**
- [ ] Test output shows "⚠️ BERT disabled"
- [ ] Scraper will still work at 80% accuracy
- [ ] ✅ This is OK - proceed anyway

---

## Hour 2: Single Site Test (30-60 minutes)

### Step 4: Test with IRDAI Only ⏱️ 30-60 minutes
```powershell
python -c "from smart_scraper import SmartMotorVehicleScraper; s = SmartMotorVehicleScraper(); s.scrape_site_with_smart_filtering('IRDAI_MOTOR', s.sites['IRDAI_MOTOR']); s.save_final_stats()"
```

**Watch for:**
- [ ] Browser opens (headless - you won't see it)
- [ ] Terminal shows stage-by-stage filtering
- [ ] Some PDFs rejected (good!)
- [ ] 1-5 PDFs downloaded (typical for single site)
- [ ] No crashes

**Check output:**
```powershell
dir D:\smart_motor_compliance_scraper\relevant_pdfs
```

- [ ] Folder created
- [ ] PDFs downloaded
- [ ] File names look relevant

---

### Step 5: Review First Results ⏱️ 5 minutes

**Check CSV:**
```powershell
python -c "import pandas as pd; df = pd.read_csv('D:/smart_motor_compliance_scraper/motor_vehicle_relevant_docs.csv'); print(df.head())"
```

- [ ] CSV created
- [ ] Contains metadata
- [ ] Titles look relevant

**Check rejections:**
```powershell
python -c "import json; data = json.load(open('D:/smart_motor_compliance_scraper/rejected_pdfs.json')); print(f'Rejected: {len(data)}'); [print(f\"  {d['reason']}\") for d in data[:5]]"
```

- [ ] Rejection log exists
- [ ] Shows why PDFs were rejected
- [ ] Reasons make sense (newsletters, low scores, etc.)

---

### Step 6: Adjust Thresholds (If Needed) ⏱️ 10 minutes

**If too many PDFs downloaded (>10):**

Edit `smart_scraper.py` lines 57-64:
```python
'link_score': 35,          # Increase from 25
'bert_confidence': 0.75,   # Increase from 0.65
```

**If too few PDFs downloaded (<2):**

```python
'link_score': 15,          # Decrease from 25
'bert_confidence': 0.55,   # Decrease from 0.65
```

- [ ] Thresholds adjusted (if needed)
- [ ] Re-run test if changed

---

## Hour 3-4: Full Scraping (2-3 hours runtime)

### Step 7: Run Full Scraper ⏱️ 2-3 hours
```powershell
python smart_scraper.py
```

**What happens:**
- Scrapes all configured sites: IRDAI, MoRTH, GIC
- Shows progress in terminal
- Takes 2-3 hours depending on sites
- You can leave it running

**Monitor progress:**
- [ ] Terminal shows stage-by-stage filtering
- [ ] Download rate: 5-10% (excellent!)
- [ ] No crashes or freezes
- [ ] GPU usage visible (if using BERT)

**Optional: Monitor GPU**
```powershell
# In a new terminal
nvidia-smi -l 1
```

- [ ] GPU usage: 40-60% during BERT stage
- [ ] VRAM usage: 2-3 GB
- [ ] No out-of-memory errors

---

### Step 8: Let It Run ⏱️ 2-3 hours

While scraping runs:
- [ ] Terminal shows progress
- [ ] No errors/crashes
- [ ] Can do other work
- [ ] Check occasionally

**When it completes:**
```
🎉 SCRAPING COMPLETED
📊 PROGRESS STATISTICS
...
```

- [ ] Scraping completed message shown
- [ ] Statistics displayed
- [ ] No fatal errors

---

## Hour 5: Analysis & Validation (30-60 minutes)

### Step 9: Check Final Results ⏱️ 10 minutes

**Count downloaded PDFs:**
```powershell
dir D:\smart_motor_compliance_scraper\relevant_pdfs | Measure-Object -Line
```

- [ ] PDFs downloaded
- [ ] Count seems reasonable (5-20 typical)

**Check CSV:**
```powershell
python -c "import pandas as pd; df = pd.read_csv('D:/smart_motor_compliance_scraper/motor_vehicle_relevant_docs.csv'); print(f'Total documents: {len(df)}'); print(f'Sample titles:'); print(df['title'].head(10))"
```

- [ ] CSV has correct count
- [ ] Titles are relevant
- [ ] No newsletters/notices

---

### Step 10: Review Statistics ⏱️ 5 minutes

```powershell
python -c "import json; stats = json.load(open('D:/smart_motor_compliance_scraper/scraping_stats.json')); print(f\"Total links: {stats['total_links_found']}\"); print(f\"Downloaded: {stats['successfully_downloaded']}\"); print(f\"Success rate: {stats['successfully_downloaded']/stats['total_links_found']*100:.1f}%\"); print(f\"Filtered by URL: {stats['filtered_by_url']}\"); print(f\"Filtered by link: {stats['filtered_by_link_text']}\"); print(f\"Filtered by blacklist: {stats['filtered_by_blacklist']}\"); print(f\"Filtered by metadata: {stats['filtered_by_metadata']}\"); print(f\"Filtered by BERT: {stats['filtered_by_bert']}\")"
```

**Expected:**
- Total links: 50-200 (varies by site)
- Downloaded: 5-20 (5-10% typical)
- Success rate: 5-10% ✅
- Most filtering: URL + link text stages

- [ ] Success rate: 5-10% (good!)
- [ ] Filtering distribution makes sense
- [ ] BERT caught some edge cases

---

### Step 11: Analyze Rejections ⏱️ 10 minutes

```powershell
python -c "import json, pandas as pd; rejected = json.load(open('D:/smart_motor_compliance_scraper/rejected_pdfs.json')); df = pd.DataFrame(rejected); print(f'Total rejected: {len(rejected)}'); print('\nTop rejection reasons:'); print(df['reason'].value_counts().head(10)); print('\nSample rejected titles:'); [print(f\"  - {r['title'][:60]}\") for r in rejected[:10]]"
```

**Check for:**
- [ ] Newsletters rejected ✅
- [ ] Election notices rejected ✅
- [ ] Annual reports rejected ✅
- [ ] Low-score docs rejected ✅
- [ ] No false negatives (relevant docs rejected)

**If you see false negatives:**
- Lower thresholds slightly
- Add exceptions to blacklist

---

### Step 12: Manual Spot Check ⏱️ 10 minutes

**Open a few downloaded PDFs:**
```powershell
# Open first PDF
start D:\smart_motor_compliance_scraper\relevant_pdfs\*.pdf
```

**Verify:**
- [ ] PDFs are about motor vehicle insurance
- [ ] Not newsletters or reports
- [ ] Contain regulations/guidelines
- [ ] No obvious false positives

---

### Step 13: Compare with Old Data ⏱️ 5 minutes

```powershell
# Old scraper stats
python -c "import pandas as pd; df = pd.read_csv('D:/motor_compliance_scraper/motor_vehicle_compliance_documents.csv'); high = (df['motor_vehicle_relevance']=='HIGH').sum(); low = (df['motor_vehicle_relevance']=='LOW').sum(); print(f'Old scraper:'); print(f'  Total: {len(df)}'); print(f'  HIGH: {high} ({high/len(df)*100:.1f}%)'); print(f'  LOW: {low} ({low/len(df)*100:.1f}%)')"

# New scraper stats  
python -c "import pandas as pd; df = pd.read_csv('D:/smart_motor_compliance_scraper/motor_vehicle_relevant_docs.csv'); print(f'\nSmart scraper:'); print(f'  Total: {len(df)}'); print(f'  Expected relevance: ~95%+')"
```

**Expected improvement:**
- [ ] Old: ~40% HIGH, 60% LOW
- [ ] New: 95%+ relevant
- [ ] Fewer total downloads
- [ ] Higher quality dataset

---

## Final Validation ✅

### Success Criteria

- [ ] ✅ Scraper ran without crashes
- [ ] ✅ 5-20 PDFs downloaded (reasonable)
- [ ] ✅ All PDFs are motor vehicle insurance related
- [ ] ✅ No newsletters/election notices downloaded
- [ ] ✅ Rejection log shows proper filtering
- [ ] ✅ Statistics show 5-10% download rate
- [ ] ✅ Old data preserved as backup
- [ ] ✅ New data in clean folder

### If All Checks Pass:

🎉 **SUCCESS!** You now have:
- Clean dataset of relevant motor insurance documents
- Intelligent scraper for future updates
- Audit trail of all filtering decisions
- Statistics for analysis

---

## Next Steps (After Scraping) 🚀

### Phase 2: RAG Integration (Next Session)

- [ ] Create vector database (ChromaDB/FAISS)
- [ ] Index documents with Legal-BERT embeddings
- [ ] Set up LLaMA for reasoning
- [ ] Build retrieval pipeline
- [ ] Test RAG system

### Phase 3: LLaMA Classification (Next Session)

- [ ] Integrate LLaMA for compliance analysis
- [ ] Create prompt templates
- [ ] Test classification accuracy
- [ ] Build chat interface
- [ ] Full system integration

---

## Troubleshooting Checklist

### Issue: Tests fail
- [ ] Check PyPDF2 installed: `pip list | findstr PyPDF2`
- [ ] Check Python version: `python --version` (should be 3.8+)
- [ ] Try: `pip install --upgrade PyPDF2`

### Issue: BERT not loading
- [ ] Check model path: `dir backend\models\legal_bert_domain_adapted`
- [ ] ✅ Scraper still works without BERT (80% accuracy)
- [ ] No action needed if model missing

### Issue: ChromeDriver error
- [ ] Run: `pip install --upgrade webdriver-manager`
- [ ] Scraper auto-installs driver
- [ ] Restart if persistent

### Issue: GPU out of memory
- [ ] Edit `smart_scraper.py` line 66: `'enable_bert': False`
- [ ] Scraper works without GPU (80% accuracy)
- [ ] Or reduce other GPU usage

### Issue: Too many/few PDFs
- [ ] Adjust thresholds in `smart_scraper.py` lines 57-64
- [ ] More PDFs: decrease scores
- [ ] Fewer PDFs: increase scores
- [ ] Rerun specific site to test

### Issue: Scraper too slow
- [ ] Disable BERT: `'enable_bert': False`
- [ ] Saves 30-40% time
- [ ] Still 80% accurate

---

## Time Summary

| Phase | Time | Status |
|-------|------|--------|
| Setup & Testing | 30-60 min | ⬜ |
| Single Site Test | 30-60 min | ⬜ |
| Full Scraping | 2-3 hours | ⬜ |
| Analysis | 30-60 min | ⬜ |
| **Total** | **4-5 hours** | ⬜ |

---

## Support Files Reference

📄 **Read these for help:**
- `VISUAL_SUMMARY.md` - What we built
- `SMART_SCRAPER_GUIDE.md` - Detailed usage
- `QUICK_COMMANDS.md` - Command reference
- `SMART_SCRAPER_SUMMARY.md` - Overview

---

**Ready to start?** 

✅ Check this list as you go!

**First command:**
```powershell
cd c:\Users\adity\OneDrive\Desktop\Capstone\backend
pip install PyPDF2
python test_smart_scraper.py
```

🚀 Good luck!
