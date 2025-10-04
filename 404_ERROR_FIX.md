# 404 Error Fix - Policy Not Found After Server Restart

## 🐛 **Problem: 404 Error When Loading Analysis**

### **Error Messages**
```
❌ API Error: "/api/v1/policies/72942763-e035-4622-98b9-c9180ee04adb" 
"Request failed with status code 404"

AxiosError: Request failed with status code 404
```

### **Why This Happens**

The backend uses **in-memory storage** (`policies_store` dictionary) which means:
- ❌ **Data is lost when server restarts**
- ❌ **Policies don't persist between sessions**
- ❌ **Old policy IDs become invalid**

This is **expected behavior** for development. In production, you'd use a database (PostgreSQL/MongoDB).

---

## ✅ **Solutions**

### **Option 1: Re-upload the Policy** (Quick Fix)
1. Go to http://localhost:3000/upload
2. Upload your policy PDF again
3. Wait for analysis (2-4 minutes)
4. Use the **new policy ID** from the results

### **Option 2: Keep Server Running** (Development)
- Don't restart the backend server
- Data persists as long as server is running
- Use `--reload` only when needed

### **Option 3: Add Database** (Production)
See section below for database integration

---

## 🛠️ **What We Fixed**

### **1. Better Error Messages**
**Before:**
```
Failed to load analysis
```

**After:**
```
Policy not found. It may have been deleted or the server was restarted.

💡 Why did this happen?
• The server was restarted (policies are stored in memory)
• The policy was deleted
• The policy ID is incorrect
```

### **2. Improved Error UI**

Added a helpful error page with:
- ✅ Clear explanation of what happened
- ✅ Why it happened (3 common reasons)
- ✅ Two action buttons:
  - **Upload New Policy** (primary action)
  - **Back to Dashboard** (secondary)

### **3. 404-Specific Handling**

```typescript
catch (err: any) {
  const errorMessage = err.response?.status === 404 
    ? 'Policy not found. It may have been deleted or the server was restarted.'
    : err.response?.data?.detail || 'Failed to load analysis';
  setError(errorMessage);
  toast.error(errorMessage);
}
```

---

## 📊 **Current System Architecture**

```
Frontend (Next.js)
    ↓ HTTP Request with Policy ID
Backend (FastAPI)
    ↓ Lookup in Memory
policies_store = {
  "policy-id-1": {...},
  "policy-id-2": {...}
}  ← ⚠️ LOST ON RESTART!
```

---

## 🚀 **Production Solution: Add Database**

### **Option A: PostgreSQL (Recommended)**

#### **Install Dependencies**
```bash
cd backend
pip install sqlalchemy psycopg2-binary alembic
```

#### **Create Database Models**
```python
# backend/app/db/models.py
from sqlalchemy import Column, String, Float, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    classification = Column(String, nullable=False)
    confidence = Column(Float)
    compliance_score = Column(Float)
    violations = Column(JSON)
    recommendations = Column(JSON)
    explanation = Column(String)
    rag_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    last_analyzed = Column(DateTime, default=datetime.utcnow)
```

#### **Database Connection**
```python
# backend/app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:password@localhost/insurance_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### **Update Endpoints**
```python
# backend/api/v1/endpoints/policies.py
from app.db.database import get_db
from app.db.models import Policy

@router.post("/upload")
async def upload_policy(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # ... analysis code ...
    
    # Save to database instead of memory
    policy = Policy(
        id=policy_id,
        filename=file.filename,
        classification=result.classification,
        # ... other fields
    )
    db.add(policy)
    db.commit()
    
    return {"id": policy_id, ...}

@router.get("/policies/{policy_id}")
async def get_policy(
    policy_id: str,
    db: Session = Depends(get_db)
):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy
```

---

### **Option B: MongoDB (Alternative)**

#### **Install Dependencies**
```bash
pip install motor pymongo
```

#### **Connection**
```python
# backend/app/db/mongodb.py
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.insurance_db
policies_collection = db.policies
```

#### **CRUD Operations**
```python
# Save policy
await policies_collection.insert_one(policy_data)

# Get policy
policy = await policies_collection.find_one({"id": policy_id})

# Update policy
await policies_collection.update_one(
    {"id": policy_id},
    {"$set": updated_data}
)

# Delete policy
await policies_collection.delete_one({"id": policy_id})
```

---

## 🎯 **Quick Reference**

### **Development (Current)**
- ✅ Fast iteration
- ✅ No database setup needed
- ❌ Data lost on restart
- ❌ Not production-ready

### **Production (With Database)**
- ✅ Data persists
- ✅ Server can restart safely
- ✅ Supports multiple instances
- ✅ Production-ready
- ⚠️ Requires database setup

---

## 📝 **Workaround for Now**

### **Keep Server Running**
```bash
# Start backend (don't restart unless needed)
cd backend
python -m uvicorn api.main:app --reload

# Frontend can restart freely
cd frontend-nextjs
npm run dev
```

### **When You Need to Restart Backend**
1. Note: All policies will be lost
2. Re-upload test policies after restart
3. Use new policy IDs generated

---

## 🔧 **Files Modified**

### **frontend-nextjs/src/app/analysis/[id]/page.tsx**
- ✅ Better 404 error handling
- ✅ Helpful error message with explanation
- ✅ Two action buttons (Upload / Dashboard)

### **Frontend Changes**
```typescript
// Detect 404 specifically
const errorMessage = err.response?.status === 404 
  ? 'Policy not found. It may have been deleted or the server was restarted.'
  : err.response?.data?.detail || 'Failed to load analysis';

// Show helpful error UI
<div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
  <p className="font-medium">💡 Why did this happen?</p>
  <ul className="list-disc list-inside">
    <li>The server was restarted</li>
    <li>The policy was deleted</li>
    <li>The policy ID is incorrect</li>
  </ul>
</div>
```

---

## ✅ **Status**

### **Immediate Fix: ✅ Complete**
- Better error messages
- Helpful UI with explanations
- Clear next actions for users

### **Long-term Fix: ⏳ Optional**
- Database integration (PostgreSQL/MongoDB)
- Required for production deployment
- Can be done later before going live

---

## 🎉 **Result**

Users now get:
1. ✅ **Clear error message** explaining what happened
2. ✅ **Why it happened** (3 common reasons)
3. ✅ **What to do next** (Upload or go to Dashboard)
4. ✅ **Better UX** during development

The system continues to work perfectly for development. For production, add database integration when ready to deploy! 🚀
