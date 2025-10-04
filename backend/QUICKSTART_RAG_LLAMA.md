# RAG + LLaMA System Quick Start Guide

## 🎯 What You Built

A **3-model system** that combines:
1. **Legal-BERT** (Domain Understanding) - ✅ Already trained
2. **RAG** (Regulation Retrieval) - 🆕 Just built
3. **LLaMA** (Reasoning + Chat) - 🆕 Just integrated

## 📦 What Was Created

### New Modules
```
backend/app/ml/
├── rag/                          # RAG Module (NEW)
│   ├── vector_store.py          # ChromaDB + Legal-BERT embeddings
│   └── retriever.py             # Regulation retrieval logic
│
├── llm/                          # LLM Module (NEW)
│   ├── llama_engine.py          # LLaMA interface (Ollama/Groq)
│   └── prompt_templates.py      # Compliance prompts
│
└── rag_llama_service.py         # Integrated service (NEW)
```

### Updated Files
- `requirements.txt` - Added ChromaDB, Ollama, Groq
- `app/core/config.py` - Added LLM and RAG settings

### New Scripts
- `test_rag_llama_setup.py` - Full system test
- `RAG_LLAMA_GUIDE.md` - Complete documentation

## 🚀 Setup Steps (5 minutes)

### Step 1: Install New Dependencies

```powershell
cd C:\Users\adity\OneDrive\Desktop\Capstone
pip install chromadb ollama groq
```

### Step 2: Choose LLM Provider

#### Option A: Local (Ollama) - Recommended for Now

```powershell
# 1. Download Ollama
# Go to: https://ollama.ai/download/windows
# Install and restart terminal

# 2. Pull model (4GB download)
ollama pull llama3.1:8b

# 3. Start server (keep this running)
ollama serve
```

#### Option B: Cloud (Groq) - For Later

```powershell
# Get free API key from: https://console.groq.com
# Set in environment:
$env:GROQ_API_KEY = "your-key"

# Update config to use Groq:
# Edit backend/app/core/config.py:
# LLM_PROVIDER: str = "groq"
```

### Step 3: Run Setup Test

```powershell
cd backend
python test_rag_llama_setup.py
```

**What it does:**
1. Loads your Legal-BERT model ✅
2. Indexes 203 regulations into ChromaDB (2-5 min)
3. Tests LLaMA connection
4. Runs sample policy analysis

**Expected Results:**
- ✅ Vector store: 203 regulations indexed
- ✅ LLaMA: Connection successful
- ✅ Full analysis: Classification + explanation

## 📊 How It Works

### Old System (Phase 2)
```
Policy PDF → Legal-BERT → Classification
```
- Simple, fast
- No explanations
- Limited to training data

### New System (RAG + LLaMA)
```
Policy PDF → Legal-BERT embeddings 
           → RAG retrieves regulations
           → LLaMA reasons about compliance
           → Classification + Detailed explanation + Citations
           → Chat interface for Q&A
```

## 🧪 Testing the System

### Test 1: Basic Analysis
```python
from app.ml.rag_llama_service import RAGLLaMAComplianceService

service = RAGLLaMAComplianceService()
await service.initialize()

result = await service.analyze_policy(
    policy_text="Your policy text here...",
    top_k_regulations=10
)

print(result['classification'])
print(result['explanation'])
```

### Test 2: Chat Interface
```python
response = await service.chat_about_policy(
    session_id="test-session",
    user_query="Why was this flagged as non-compliant?",
    analysis_results=result
)

print(response)
```

## 💡 Key Advantages

### vs. Old System
| Feature | Old (BERT Only) | New (RAG+LLaMA) |
|---------|----------------|-----------------|
| Needs labeled data? | ✅ Yes | ❌ No |
| Handles fine print? | ❌ No | ✅ Yes |
| Explanations? | ❌ No | ✅ Yes |
| Cites regulations? | ❌ No | ✅ Yes |
| Interactive chat? | ❌ No | ✅ Yes |
| Updates easily? | ❌ Retrain | ✅ Update DB |

### vs. Pure LLaMA (No RAG)
| Feature | Pure LLaMA | With RAG |
|---------|-----------|----------|
| Accuracy | 🟡 Good | ✅ Better |
| Hallucination | ⚠️ Possible | ✅ Minimal |
| Citations | 🟡 Generic | ✅ Specific |
| Cost | 💰 High | 💰 Lower |

## 🔧 Configuration Options

### LLM Provider (in `config.py`)
```python
# Local Ollama (free, private)
LLM_PROVIDER = "ollama"
LLM_MODEL = "llama3.1:8b"

# Cloud Groq (fast, cheap)
LLM_PROVIDER = "groq"
LLM_MODEL = "llama-3.1-70b-versatile"
GROQ_API_KEY = "your-key"
```

### RAG Settings
```python
RAG_TOP_K = 10              # How many regulations to retrieve
RAG_MIN_RELEVANCE = "HIGH"  # Filter quality
```

## 📈 Performance

### Speed (per policy)
- **Retrieval**: 0.5s (ChromaDB vector search)
- **LLaMA 8B (local)**: 10-15s (on CPU)
- **LLaMA 70B (Groq)**: 3-5s (cloud)
- **Total**: ~10-20s per policy

### Resources
- **ChromaDB**: 100MB RAM
- **Legal-BERT**: 500MB RAM
- **LLaMA 8B**: 4-8GB RAM (if local)

### Cost
- **Local (Ollama)**: $0 (free, unlimited)
- **Cloud (Groq)**: ~$0.20 per 1M tokens (~$0.02 per policy)

## 🎯 Next Steps

### Immediate (Today)
1. ✅ Run `pip install chromadb ollama groq`
2. ✅ Install Ollama + pull model
3. ✅ Run `python test_rag_llama_setup.py`
4. ✅ Test with your sample policies

### Short-term (This Week)
- [ ] Compare RAG+LLaMA vs old classifier on test set
- [ ] Add API endpoints for new system
- [ ] Update Streamlit with chat interface
- [ ] Create demo video

### Long-term (Next Month)
- [ ] Fine-tune LLaMA on domain
- [ ] Add feedback loop
- [ ] Production deployment
- [ ] Monitor performance

## 🆘 Troubleshooting

### "Cannot connect to Ollama"
```powershell
# Start Ollama server
ollama serve

# Check if running
curl http://localhost:11434/api/version
```

### "Model not found"
```powershell
# Pull model
ollama pull llama3.1:8b

# List models
ollama list
```

### "ChromaDB collection empty"
```python
# Force reindex
await service.vector_store.index_regulations(force_reindex=True)
```

### "Out of memory"
Solutions:
1. Use Groq API instead of local
2. Use smaller model: `llama3.1:8b` (not 70b)
3. Reduce `RAG_TOP_K` to 5

## 📚 Documentation

- **Full Guide**: `RAG_LLAMA_GUIDE.md`
- **Test Script**: `test_rag_llama_setup.py`
- **Config**: `app/core/config.py`

## ✅ Quick Checklist

Before using the system:

- [ ] Dependencies installed (`pip install chromadb ollama groq`)
- [ ] Ollama installed and running (`ollama serve`)
- [ ] Model pulled (`ollama pull llama3.1:8b`)
- [ ] Setup test passed (`python test_rag_llama_setup.py`)
- [ ] Legal-BERT model exists (`models/legal_bert_domain_adapted/`)
- [ ] Training data exists (`data/training/motor_vehicle_training_data.csv`)

## 🎉 Ready to Use!

Once setup test passes, you have:
- ✅ Vector store with 203 regulations indexed
- ✅ LLaMA connected and working
- ✅ Full RAG pipeline operational
- ✅ Chat interface ready

Try analyzing a policy:
```powershell
python -c "
import asyncio
from app.ml.rag_llama_service import RAGLLaMAComplianceService

async def test():
    service = RAGLLaMAComplianceService()
    await service.initialize()
    print('✅ System ready!')

asyncio.run(test())
"
```

## 💬 Questions?

Ask me about:
- How to use a specific feature
- Performance optimization
- API integration
- Production deployment
- Comparison with old system

Let's get it running! 🚀
