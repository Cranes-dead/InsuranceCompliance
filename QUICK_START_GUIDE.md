# 🚀 Quick Start Guide - Frontend + Backend

## Prerequisites
- ✅ Backend running on `http://localhost:8000`
- ✅ Frontend Next.js installed
- ✅ Python 3.11+ for backend
- ✅ Node.js 18+ for frontend

---

## 🏃 Quick Start Commands

### **Terminal 1 - Backend (FastAPI)**
```bash
cd backend
python -m uvicorn api.main:app --reload
```
**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### **Terminal 2 - Frontend (Next.js)**
```bash
cd frontend-nextjs
npm run dev
```
**Expected Output:**
```
  ▲ Next.js 15.5.4
  - Local:        http://localhost:3000
  - Network:      http://192.168.x.x:3000
  
  ✓ Ready in 2.1s
```

---

## 🧪 Test Each Page

### **1. Landing Page**
```
URL: http://localhost:3000

✅ Test:
- Click "Start Analysis" → Goes to /upload
- Click "View Dashboard" → Goes to /dashboard
- See 6 feature cards
- See stats (92% accuracy, <5s, 203 regulations)
```

### **2. Upload Page**
```
URL: http://localhost:3000/upload

✅ Test:
- Drag & drop PDF file
- Or click to browse
- See file name and size
- Click "Analyze Policy"
- Should navigate to /analysis/{id}

⚠️ Requires backend endpoint:
POST /api/v1/upload
```

### **3. Analysis Results Page**
```
URL: http://localhost:3000/analysis/test-123

✅ Test:
- See status badge (COMPLIANT/NON_COMPLIANT/REQUIRES_REVIEW)
- See confidence score
- See animated compliance gauge
- See violations list (colored by severity)
- See recommendations
- See source regulations
- Click "Chat about this policy" → Goes to /chat/test-123

⚠️ Requires backend endpoint:
GET /api/v1/policies/test-123
```

### **4. Chat Page**
```
URL: http://localhost:3000/chat/test-123

✅ Test:
- See welcome message
- Type a message
- Press Enter to send
- See loading spinner
- Get AI response
- Scroll auto-scrolls to bottom

⚠️ Requires backend endpoint:
POST /api/v1/chat
Body: { "session_id": "test-123", "message": "What violations?" }
```

### **5. Dashboard**
```
URL: http://localhost:3000/dashboard

✅ Test:
- See 4 stat cards (Total, Compliant, Non-Compliant, Review)
- See compliance gauge chart
- See status pie chart
- See violation bar chart
- See recent analyses table
- See policy grid
- Click policy card → Goes to /analysis/{id}

⚠️ Requires backend endpoints:
GET /api/v1/statistics
GET /api/v1/policies
```

---

## 🛠️ Backend Endpoints Needed

### **Priority 1: Essential Endpoints**

#### 1. Upload Policy
```python
# File: backend/api/v1/endpoints/upload.py

@router.post("/upload")
async def upload_policy(file: UploadFile = File(...)):
    # Save file
    policy_id = str(uuid4())
    file_path = f"data/uploads/{policy_id}.pdf"
    
    # Run analysis
    analysis_result = await analyze_policy(file_path)
    
    return {
        "id": policy_id,
        "filename": file.filename,
        "status": "completed",
        "analysis": analysis_result
    }
```

#### 2. Get Analysis by ID
```python
# File: backend/api/v1/endpoints/policies.py

@router.get("/policies/{policy_id}")
async def get_policy_analysis(policy_id: str):
    # Fetch from database or file storage
    analysis = fetch_analysis(policy_id)
    
    return {
        "id": policy_id,
        "filename": "policy.pdf",
        "classification": "COMPLIANT",
        "confidence": 0.95,
        "compliance_score": 87,
        "violations": [...],
        "recommendations": [...],
        "explanation": "...",
        "rag_metadata": {
            "regulations_retrieved": 5,
            "top_sources": [...]
        },
        "created_at": "2025-10-04T10:00:00Z"
    }
```

#### 3. Chat with Policy
```python
# File: backend/api/v1/endpoints/chat.py

@router.post("/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id
    message = request.message
    
    # Get policy context
    policy = fetch_policy(session_id)
    
    # Generate response using LLaMA
    response = await llama_chat(message, policy)
    
    return {
        "response": response,
        "session_id": session_id
    }
```

### **Priority 2: Dashboard Endpoints**

#### 4. Get Statistics
```python
@router.get("/statistics")
async def get_statistics():
    # Calculate from database
    return {
        "totalPolicies": 10,
        "compliantPolicies": 6,
        "nonCompliantPolicies": 3,
        "reviewRequired": 1,
        "averageScore": 78,
        "recentAnalyses": [...]
    }
```

#### 5. Get All Policies
```python
@router.get("/policies")
async def get_all_policies():
    policies = fetch_all_policies()
    return [
        {
            "id": p.id,
            "filename": p.filename,
            "status": p.status,
            "uploadedAt": p.uploaded_at,
            "lastAnalyzed": p.analyzed_at,
            "score": p.compliance_score
        }
        for p in policies
    ]
```

---

## 🔧 CORS Setup (Required!)

**File: `backend/api/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware BEFORE routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Then add your routes
app.include_router(...)
```

---

## 📝 Component File Structure

```
frontend-nextjs/src/
├── app/
│   ├── page.tsx                    ✅ Landing page
│   ├── upload/
│   │   └── page.tsx                ✅ Upload page
│   ├── analysis/
│   │   └── [id]/
│   │       └── page.tsx            ✅ Analysis results (NEW)
│   ├── chat/
│   │   └── [id]/
│   │       └── page.tsx            ✅ Chat page (NEW)
│   └── dashboard/
│       └── page.tsx                ✅ Dashboard with charts (NEW)
│
├── components/
│   ├── landing/
│   │   ├── HeroSection.tsx         ✅
│   │   └── FeaturesSection.tsx     ✅
│   ├── upload/
│   │   └── FileUpload.tsx          ✅
│   ├── results/
│   │   ├── StatusBadge.tsx         ✅ (NEW)
│   │   ├── ScoreGauge.tsx          ✅ (NEW)
│   │   ├── ViolationCard.tsx       ✅ (NEW)
│   │   └── RecommendationList.tsx  ✅ (NEW)
│   ├── chat/
│   │   └── ChatInterface.tsx       ✅ (NEW)
│   └── dashboard/
│       ├── Charts.tsx              ✅ (NEW)
│       └── PolicyGrid.tsx          ✅ (NEW)
│
└── lib/
    ├── api.ts                       ✅ API client
    ├── types.ts                     ✅ TypeScript types
    └── utils.ts                     ✅ Helper functions
```

---

## 🎯 Test Checklist

### Frontend Tests (Without Backend):
- [x] Landing page renders
- [x] Upload page shows dropzone
- [x] Analysis page shows "Not Found" error gracefully
- [x] Chat page loads with welcome message
- [x] Dashboard shows empty state

### Integration Tests (With Backend):
- [ ] Upload PDF → Get analysis ID → Navigate to results
- [ ] Analysis page fetches data from backend
- [ ] Chat sends messages → Receives AI responses
- [ ] Dashboard shows real statistics
- [ ] Policy grid shows uploaded policies
- [ ] Charts render with real data

---

## 🚨 Troubleshooting

### **Problem: CORS Error**
```
Access to XMLHttpRequest blocked by CORS policy
```
**Solution:** Add CORS middleware to FastAPI (see above)

### **Problem: API Call Fails (404)**
```
GET http://localhost:8000/api/v1/policies/123 404 Not Found
```
**Solution:** Implement the backend endpoint

### **Problem: Charts Not Rendering**
```
Error: Module not found: recharts
```
**Solution:**
```bash
cd frontend-nextjs
npm install recharts
```

### **Problem: Upload Fails**
```
POST http://localhost:8000/api/v1/upload 415 Unsupported Media Type
```
**Solution:** Ensure backend accepts `multipart/form-data`

---

## 📊 Progress Tracking

**Implementation Status:**

| Component | Status | Test URL |
|-----------|--------|----------|
| Landing Page | ✅ Complete | http://localhost:3000 |
| Upload Page | ✅ Complete | http://localhost:3000/upload |
| Analysis Results | ✅ Complete | http://localhost:3000/analysis/[id] |
| AI Chat | ✅ Complete | http://localhost:3000/chat/[id] |
| Dashboard | ✅ Complete | http://localhost:3000/dashboard |

**Backend Integration:**

| Endpoint | Required | Implemented |
|----------|----------|-------------|
| POST /api/v1/upload | ✅ Yes | ⏳ Pending |
| GET /api/v1/policies/{id} | ✅ Yes | ⏳ Pending |
| POST /api/v1/chat | ✅ Yes | ⏳ Pending |
| GET /api/v1/statistics | ✅ Yes | ⏳ Pending |
| GET /api/v1/policies | ✅ Yes | ⏳ Pending |

---

## 🎉 Success Criteria

✅ **You'll know it's working when:**

1. **Upload Flow:**
   - Upload PDF → See progress bar
   - Analysis completes → Navigate to results page
   - Results show classification, score, violations

2. **Chat Flow:**
   - Ask question → See loading spinner
   - Get AI response in <5 seconds
   - Messages persist in session

3. **Dashboard Flow:**
   - See real statistics (not 0s)
   - Charts render with data
   - Click policy → View analysis
   - Upload button works

---

**Last Updated:** October 4, 2025  
**Status:** ✅ Frontend Complete | ⏳ Awaiting Backend Integration
