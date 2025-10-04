# 🎯 Backend API Integration - Complete Guide

## ✅ What Was Implemented

### **New API Endpoints Created:**

#### 1. **Upload Policy** (`POST /api/v1/upload`)
- Accepts PDF file upload
- Runs RAG + LLaMA analysis automatically
- Stores policy data in memory
- Returns policy ID and status

#### 2. **Get Policy Analysis** (`GET /api/v1/policies/{id}`)
- Retrieves complete analysis for a policy
- Returns classification, violations, recommendations
- Includes RAG metadata (regulations used)

#### 3. **Get All Policies** (`GET /api/v1/policies`)
- Lists all analyzed policies
- Returns summary data for each policy
- Sorted by upload date (newest first)

#### 4. **Get Statistics** (`GET /api/v1/statistics`)
- Returns dashboard statistics
- Includes totals, averages, recent analyses
- Calculates compliance rates

#### 5. **Chat with Policy** (`POST /api/v1/chat`)
- AI-powered Q&A about policies
- Uses LLaMA for responses
- Context-aware with policy data
- Fallback responses if LLaMA unavailable

#### 6. **Delete Policy** (`DELETE /api/v1/policies/{id}`)
- Removes policy and analysis
- Deletes uploaded file

---

## 🚀 Quick Start

### **Start Backend Server:**

```bash
cd backend
python -m uvicorn api.main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
✅ RAG + LLaMA service ready!
📊 Vector Store: 112 regulations indexed
🤖 LLM Provider: ollama (llama3.1:8b)
```

### **Verify Backend is Running:**

```bash
# Open in browser or use curl
http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-10-04T10:00:00",
  "version": "1.0.0",
  "services": {
    "compliance_engine": "healthy"
  }
}
```

---

## 🧪 API Testing

### **Test 1: Upload Policy**

```bash
# Using curl
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_samples/sample_policy_compliant.pdf"

# Expected Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "sample_policy_compliant.pdf",
  "status": "completed",
  "message": "Policy uploaded and analyzed successfully"
}
```

**Frontend Integration:**
- FileUpload component → POST /api/v1/upload
- Gets policy ID → Navigate to /analysis/{id}

---

### **Test 2: Get Policy Analysis**

```bash
# Replace {id} with actual policy ID from upload
curl -X GET "http://localhost:8000/api/v1/policies/550e8400-e29b-41d4-a716-446655440000"

# Expected Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "sample_policy_compliant.pdf",
  "classification": "COMPLIANT",
  "confidence": 0.95,
  "compliance_score": 87,
  "violations": [
    {
      "severity": "HIGH",
      "type": "Coverage Gap",
      "description": "Missing flood coverage",
      "regulation_reference": "IRDAI/REG/2024/001",
      "recommendation": "Add flood coverage clause"
    }
  ],
  "recommendations": ["Add flood coverage", "Update terms"],
  "explanation": "Policy analysis summary...",
  "rag_metadata": {
    "regulations_retrieved": 5,
    "top_sources": ["IRDAI/REG/2024/001", "IRDAI/REG/2024/002"]
  },
  "created_at": "2025-10-04T10:00:00Z"
}
```

**Frontend Integration:**
- Analysis page → GET /api/v1/policies/{id}
- Displays all results with charts and cards

---

### **Test 3: Chat with Policy**

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "What violations were found?"
  }'

# Expected Response:
{
  "response": "The analysis found 3 violations in this policy:\n\n1. **HIGH - Coverage Gap**\n   Missing flood coverage...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-10-04T10:05:00Z"
}
```

**Frontend Integration:**
- ChatInterface component → POST /api/v1/chat
- Displays response in chat bubble

---

### **Test 4: Get Statistics**

```bash
curl -X GET "http://localhost:8000/api/v1/statistics"

# Expected Response:
{
  "totalPolicies": 10,
  "compliantPolicies": 6,
  "nonCompliantPolicies": 3,
  "reviewRequired": 1,
  "averageScore": 78,
  "recentAnalyses": [...]
}
```

**Frontend Integration:**
- Dashboard → GET /api/v1/statistics
- Displays stats cards and charts

---

### **Test 5: Get All Policies**

```bash
curl -X GET "http://localhost:8000/api/v1/policies"

# Expected Response:
[
  {
    "id": "uuid-1",
    "filename": "policy1.pdf",
    "status": "COMPLIANT",
    "uploadedAt": "2025-10-01T10:00:00Z",
    "lastAnalyzed": "2025-10-01T10:05:00Z",
    "score": 87
  },
  {
    "id": "uuid-2",
    "filename": "policy2.pdf",
    "status": "NON_COMPLIANT",
    "uploadedAt": "2025-10-02T10:00:00Z",
    "lastAnalyzed": "2025-10-02T10:05:00Z",
    "score": 45
  }
]
```

**Frontend Integration:**
- Dashboard → GET /api/v1/policies
- Displays PolicyGrid with all policies

---

## 🔧 Full Integration Test

### **Complete User Flow:**

```bash
# Terminal 1: Start Backend
cd backend
python -m uvicorn api.main:app --reload

# Terminal 2: Start Frontend
cd frontend-nextjs
npm run dev

# Browser: Test the flow
1. Go to http://localhost:3000
2. Click "Start Analysis"
3. Upload test_samples/sample_policy_compliant.pdf
4. Wait for analysis (5-10 seconds)
5. View results at /analysis/{id}
6. Click "Chat about this policy"
7. Ask: "What violations were found?"
8. Go to Dashboard
9. See statistics and policy grid
```

---

## 📊 API Documentation

### **Interactive Docs:**

```bash
# Swagger UI
http://localhost:8000/docs

# ReDoc
http://localhost:8000/redoc

# OpenAPI JSON
http://localhost:8000/openapi.json
```

---

## 🎨 Frontend-Backend Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                     INTEGRATION FLOW                         │
└─────────────────────────────────────────────────────────────┘

Upload Page (Next.js)
  │
  └─→ POST /api/v1/upload (FastAPI)
      │
      ├─→ Save PDF file
      ├─→ Run RAG + LLaMA analysis
      └─→ Return policy ID
  
  ↓ Navigate to /analysis/{id}

Analysis Page (Next.js)
  │
  └─→ GET /api/v1/policies/{id} (FastAPI)
      │
      └─→ Return complete analysis
  
  ↓ Click "Chat about policy"

Chat Page (Next.js)
  │
  └─→ POST /api/v1/chat (FastAPI)
      │
      ├─→ Get policy context
      ├─→ Generate LLaMA response
      └─→ Return answer
  
  ↓ Navigate to Dashboard

Dashboard Page (Next.js)
  │
  ├─→ GET /api/v1/statistics (FastAPI)
  │   └─→ Return stats
  │
  └─→ GET /api/v1/policies (FastAPI)
      └─→ Return all policies
```

---

## ⚠️ Important Notes

### **Data Storage:**
- Currently uses **in-memory storage** (dictionary)
- Data is lost when server restarts
- **TODO:** Add database (PostgreSQL/MongoDB) for production

### **File Storage:**
- PDFs saved to `backend/data/uploads/`
- Named with UUID (e.g., `uuid.pdf`)
- **TODO:** Add cloud storage (S3/Azure Blob) for production

### **CORS:**
- Already configured for `http://localhost:3000`
- Works with Next.js dev server
- Update for production domains

### **Error Handling:**
- Graceful fallbacks if analysis fails
- Policies still stored with error status
- Chat has fallback responses if LLaMA unavailable

---

## 🐛 Troubleshooting

### **Issue 1: Backend won't start**
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F

# Restart backend
python -m uvicorn api.main:app --reload
```

### **Issue 2: Upload fails with 500 error**
```bash
# Check if LLaMA (Ollama) is running
ollama list

# Start Ollama if needed
ollama serve

# Check logs
tail -f backend/logs/compliance_system.log
```

### **Issue 3: CORS errors**
```bash
# Verify CORS configuration
# File: backend/app/core/config.py
BACKEND_CORS_ORIGINS: List[str] = [
    "http://localhost:3000"
]
```

### **Issue 4: Analysis takes too long**
```bash
# Check LLaMA timeout
# File: backend/app/ml/llm/llama_engine.py
timeout: float = 300.0  # 5 minutes

# Monitor terminal for logs
# Should see "Analysis completed for document {id}"
```

---

## 📝 Next Steps

### **Completed ✅**
- [x] Upload endpoint
- [x] Analysis retrieval
- [x] Chat endpoint
- [x] Statistics endpoint
- [x] Policy listing
- [x] CORS configuration
- [x] Error handling
- [x] Fallback responses

### **Production TODOs ⏳**
- [ ] Add PostgreSQL database
- [ ] Implement user authentication
- [ ] Add rate limiting
- [ ] Set up Redis for caching
- [ ] Add cloud file storage
- [ ] Implement websockets for real-time updates
- [ ] Add comprehensive logging
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Add unit tests for endpoints
- [ ] Add integration tests

---

## 🎯 Success Criteria

✅ **You'll know it's working when:**

1. **Upload Test:**
   - Upload PDF → Get policy ID
   - Analysis completes in <10 seconds
   - No errors in terminal

2. **Analysis Test:**
   - Navigate to /analysis/{id}
   - See all data displayed
   - Charts render correctly

3. **Chat Test:**
   - Send message → Get response in <5 seconds
   - Responses are contextual
   - Chat history persists

4. **Dashboard Test:**
   - Statistics show real numbers
   - Charts display data
   - Policy grid shows uploaded policies

---

**Last Updated:** October 4, 2025  
**Status:** ✅ Backend Integration Complete  
**API Docs:** http://localhost:8000/docs
