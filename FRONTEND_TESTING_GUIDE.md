# Frontend Testing Guide - Phase 2 Model

## Current Status ✅
- **Backend**: Running on http://localhost:8000 with Phase 2 model loaded
- **Frontend**: Running on http://localhost:8501
- **Model**: Phase 2 Legal-BERT (domain-adapted + classifier)

## How to Test the Frontend

### 1. Access the Frontend
Open your browser to: **http://localhost:8501**

### 2. Navigate to Document Analysis
- The sidebar shows "Document Analysis" (default page)
- You should see the upload interface

### 3. Upload a Test Document
**Option A: Use sample from project**
- Navigate to: `backend/test_samples/`
- Upload any of these files:
  - `sample_policy_compliant.pdf`
  - `sample_policy_non_compliant.pdf`
  - `sample_policy_requires_review.pdf`

**Option B: Use your own PDF**
- Upload any motor vehicle insurance policy document (PDF or TXT)

### 4. Run Analysis
- Click the **"🔍 Analyze Compliance"** button
- Wait 5-10 seconds for Phase 2 model to process
- Results will appear with:
  - Classification (COMPLIANT / NON_COMPLIANT / REQUIRES_REVIEW)
  - Confidence score
  - Class probabilities
  - Mandatory requirements checklist
  - Recommendations
  - Violations (if any)

### 5. Expected Results for Sample Files

#### sample_policy_compliant.pdf
```
Classification: REQUIRES_REVIEW
Confidence: 95.4%
Probabilities:
  - COMPLIANT: 3.3%
  - NON_COMPLIANT: 1.2%
  - REQUIRES_REVIEW: 95.4%
```

## Verification Steps

### Backend Verification
```bash
# Test API health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "services": {
    "compliance_engine": "healthy"
  }
}
```

### Check Backend Logs
Look for this confirmation in the backend terminal:
```
✅ Loaded Phase 2 Legal-BERT compliance model from .../models/legal_bert_compliance_final
Compliance service initialized successfully
```

### Frontend Features to Test

1. **Document Upload**
   - ✅ File upload accepts PDF/TXT
   - ✅ Shows file name after upload
   - ✅ Displays file size

2. **Analysis Results**
   - ✅ Classification displayed prominently
   - ✅ Confidence score shown
   - ✅ Color-coded result (green/yellow/red)
   - ✅ Detailed probabilities for all classes

3. **Mandatory Requirements**
   - ✅ Third Party Liability Coverage status
   - ✅ Personal Accident Cover status
   - ✅ Coverage amounts shown

4. **Recommendations**
   - ✅ List of action items
   - ✅ Specific to classification result

5. **Violations** (if NON_COMPLIANT)
   - ✅ Violation type
   - ✅ Severity level
   - ✅ Suggested actions

## Troubleshooting

### Frontend Not Loading
```bash
# Restart Streamlit
cd c:/Users/adity/OneDrive/Desktop/Capstone
streamlit run frontend/frontend_app.py --server.port 8501
```

### Backend Not Responding
```bash
# Restart FastAPI
cd backend
python -m uvicorn api.main:app --reload --port 8000
```

### Upload Fails
- Check that backend is running
- Verify file size < 50MB
- Ensure file extension is .pdf or .txt

### Analysis Takes Too Long
- Phase 2 model needs ~5 seconds on CPU
- This is normal for BERT-based models
- GPU would speed this up significantly

## API Endpoints Used by Frontend

1. **Health Check**
   - `GET /health`
   - Verifies backend is running

2. **Document Upload**
   - `POST /api/v1/documents/upload`
   - Accepts multipart form data
   - Returns document_id

3. **Compliance Analysis**
   - `POST /api/v1/compliance/analyze`
   - Body: `{"document_id": "...", "analysis_type": "full"}`
   - Returns full analysis result

## Performance Metrics

- **Upload Speed**: < 1 second
- **Analysis Time**: ~5 seconds (Phase 2 model on CPU)
- **Total Workflow**: ~6-7 seconds end-to-end

## Next Steps

1. **Test with Different Documents**
   - Try various policy types
   - Test with non-compliant policies
   - Upload edge cases (very short/long documents)

2. **Compare Models**
   - Switch to simple model (see PHASE2_INTEGRATION_SUMMARY.md)
   - Compare results and speed
   - Decide which model fits your needs better

3. **Customize Frontend**
   - Add more visualizations
   - Display model confidence thresholds
   - Add batch document processing

## Notes

- The Phase 2 model tends to be more conservative than the simple model
- High confidence in REQUIRES_REVIEW reflects training data distribution
- Model performance can be improved with more balanced training data
- Frontend uses Streamlit for rapid prototyping - can migrate to React/Next.js later
