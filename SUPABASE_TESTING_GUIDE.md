# Quick Testing Guide - Supabase Database Migration

## 🚀 Quick Start

### 1. Install Dependencies
```powershell
cd backend
pip install supabase
```

### 2. Start Backend
```powershell
cd backend
python -m uvicorn api.main:app --reload --timeout-keep-alive 300
```

### 3. Start Frontend
```powershell
cd frontend-nextjs
npm run dev
```

---

## ✅ Verification Checklist

### Test 1: Policy Upload & Persistence
**Steps**:
1. Open http://localhost:3000
2. Upload `test_samples/sample_policy_compliant.pdf`
3. Wait for analysis to complete (~30 seconds with Groq)
4. Note the policy ID from URL

**Expected**:
- ✅ Upload successful
- ✅ Analysis completes
- ✅ Results displayed
- ✅ No errors in console

**Verify Database**:
```powershell
# Restart backend server (Ctrl+C, then restart)
# Policy should still be there!
```

---

### Test 2: File Validation
**Steps**:
1. Try uploading a large file (>50MB) → Should fail
2. Try uploading empty file → Should fail
3. Try uploading non-PDF → Should fail

**Expected**:
- ✅ Error message displayed
- ✅ File rejected before upload
- ✅ No corrupted data in database

---

### Test 3: Chat Persistence
**Steps**:
1. Upload a policy
2. Click "Chat about policy"
3. Send message: "Why was my policy classified this way?"
4. Wait for response
5. Note the response

**Verify Database**:
```powershell
# Restart backend server
# Navigate to same policy
# Chat history should still be there!
```

---

### Test 4: Chat Message Length Validation
**Steps**:
1. Try sending a very long message (>10,000 characters)

**Expected**:
- ✅ Error: "Message exceeds maximum length"
- ✅ Message not sent
- ✅ User informed of limit

---

### Test 5: Statistics Calculation
**Steps**:
1. Upload 3 different policies:
   - `sample_policy_compliant.pdf`
   - `sample_policy_non_compliant.pdf`
   - `sample_policy_requires_review.pdf`
2. Navigate to Dashboard
3. Check statistics

**Expected**:
- ✅ Total Policies: 3
- ✅ Compliant: 1
- ✅ Non-Compliant: 1
- ✅ Review Required: 1
- ✅ Average score calculated
- ✅ Recent analyses listed

---

### Test 6: Policy Deletion
**Steps**:
1. Upload a policy
2. Chat with the policy (send 2-3 messages)
3. Delete the policy
4. Check database

**Expected**:
- ✅ Policy deleted from list
- ✅ Chat history also deleted (cascade)
- ✅ PDF file deleted from disk
- ✅ Statistics updated

---

### Test 7: Server Restart Persistence
**Critical Test!**

**Steps**:
1. Upload 2 policies
2. Chat with both policies
3. Stop backend server (Ctrl+C)
4. Restart backend server
5. Refresh frontend
6. Check if policies are still there

**Expected**:
- ✅ All policies visible
- ✅ Chat history preserved
- ✅ Statistics correct
- ✅ No data loss!

---

## 🐛 Common Issues & Fixes

### Issue 1: `ModuleNotFoundError: No module named 'supabase'`
**Fix**:
```powershell
cd backend
pip install supabase
```

### Issue 2: Database Connection Error
**Check**:
1. Verify `backend/.env` has correct Supabase URL and key
2. Check internet connection
3. Verify Supabase project is active

### Issue 3: File Upload Fails
**Check**:
1. File size < 50MB
2. File is valid PDF
3. File is not empty
4. `backend/data/uploads/` directory exists

### Issue 4: Chat Not Working
**Check**:
1. Policy exists in database
2. Groq API key is set
3. Backend logs for errors
4. Message length < 10K characters

---

## 📊 Database Queries (For Verification)

### Check Policies Table
```sql
SELECT id, filename, classification, compliance_score, created_at 
FROM policies 
ORDER BY created_at DESC;
```

### Check Chat Sessions
```sql
SELECT cs.id, p.filename, cs.message_count, cs.last_activity_at
FROM chat_sessions cs
JOIN policies p ON p.id = cs.policy_id
ORDER BY cs.last_activity_at DESC;
```

### Check Chat Messages
```sql
SELECT cm.role, LEFT(cm.content, 100) as message_preview, cm.created_at
FROM chat_messages cm
JOIN chat_sessions cs ON cs.id = cm.session_id
ORDER BY cm.created_at DESC
LIMIT 20;
```

### Check Statistics
```sql
SELECT 
    COUNT(*) as total_policies,
    SUM(CASE WHEN classification = 'COMPLIANT' THEN 1 ELSE 0 END) as compliant,
    SUM(CASE WHEN classification = 'NON_COMPLIANT' THEN 1 ELSE 0 END) as non_compliant,
    SUM(CASE WHEN classification = 'REQUIRES_REVIEW' THEN 1 ELSE 0 END) as review_required,
    ROUND(AVG(compliance_score)::numeric, 0) as average_score
FROM policies;
```

---

## 🔍 Backend Logs to Watch

### Successful Upload
```
✅ Uploaded policy <uuid>: <filename> (<size> bytes)
✅ Analysis complete: COMPLIANT
```

### Successful Chat
```
Chat request for policy <uuid>: <message>
✅ Chat response generated for session <uuid>
```

### Database Operations
```
Created policy in database: <uuid>
Retrieved policy from database: <uuid>
Deleted policy from database: <uuid>
```

---

## 🎯 Success Criteria

After running all tests:
- ✅ All uploads succeed
- ✅ File validation works
- ✅ Chat messages persist
- ✅ Statistics are accurate
- ✅ Data survives server restart
- ✅ Deletes cascade properly
- ✅ No console errors
- ✅ No backend errors

---

## 📞 Troubleshooting

### Backend Won't Start
1. Check Python version (3.11)
2. Check all dependencies installed
3. Check port 8000 not in use
4. Check `.env` file exists

### Frontend Won't Start
1. Check Node version
2. Run `npm install`
3. Check port 3000 not in use

### Database Not Connecting
1. Verify Supabase project is active
2. Check `.env` credentials
3. Test internet connection
4. Check Supabase dashboard

### Analysis Takes Too Long
1. Verify using Groq API (not local Ollama)
2. Check Groq API key is valid
3. Should complete in 30-60 seconds

---

## 📈 Performance Benchmarks

### Expected Timings:
- **File Upload**: < 1 second
- **Policy Analysis**: 30-60 seconds (with Groq)
- **Chat Response**: 1-2 seconds
- **Statistics Load**: < 1 second
- **Policy List**: < 1 second

### If Slower:
- Check internet connection
- Verify Groq API is being used
- Check backend logs for errors

---

## 🎉 Migration Complete Checklist

Before considering migration complete:
- [ ] Supabase package installed
- [ ] All endpoints work
- [ ] File validation works
- [ ] Chat persistence verified
- [ ] Statistics accurate
- [ ] Server restart test passed
- [ ] Cascade delete verified
- [ ] No compile errors
- [ ] No runtime errors
- [ ] Frontend displays correct limits

---

**Testing Time**: ~15 minutes
**Critical Tests**: 7
**Optional Tests**: Additional edge cases

Good luck! 🚀
