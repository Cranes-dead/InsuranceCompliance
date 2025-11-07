# Advanced Insurance Compliance AI Platform

The Capstone project delivers an AI-assisted compliance assistant for Indian motor vehicle insurance policies. The platform ingests PDF policies, extracts semantic meaning with a domain-adapted Legal-BERT model, retrieves supporting regulations from a ChromaDB vector store, and uses Groq-hosted LLaMA to generate explanations and remediation guidance. A FastAPI backend exposes the pipeline, while the forthcoming Next.js frontend provides an interactive workspace for underwriters and analysts.

## Key Capabilities
- **Automated policy grading** against IRDAI regulations with confidence scoring.
- **RAG-assisted explanations** that cite the closest matching regulations and propose fixes.
- **Interactive policy chat** that reuses retrieval context and prior conversation turns.
- **Hybrid AI strategy** with graceful fallback to simpler models when GPU-class resources are unavailable.
- **Supabase-backed persistence** for policies, analysis history, and chat transcripts.

## Repository Layout
```
Capstone/
├── backend/                # FastAPI services, ML pipeline, data assets
│   ├── api/                # Versioned REST endpoints and middleware
│   ├── app/                # Core application modules (config, services, ML, DB)
│   ├── data/               # Training corpora, uploaded documents, vector store
│   ├── models/             # Persisted models (Legal-BERT variants, baselines)
│   └── tests/              # PyTest suites and diagnostic scripts
├── frontend-nextjs/        # Next.js 15 client (in-progress modern UI)
├── diagrams/               # Mermaid source and rendered architecture diagrams
├── requirements.txt        # Consolidated Python dependency lock
├── README.md               # High-level orientation (this file)
├── STARTUP_GUIDE.md        # Environment setup and runbook
└── DESIGN_DOCUMENT.md      # Detailed architecture and design rationale
```

## Quick Start (TL;DR)
> Full instructions, including environment variables and troubleshooting, live in [STARTUP_GUIDE.md](STARTUP_GUIDE.md).

1. **Install prerequisites**
   - Python 3.11 (with virtual environment)
   - Node.js 20 LTS (for Next.js client)
2. **Install Python dependencies**
   ```powershell
   cd backend
   pip install -r requirements.txt
   ```
3. **Configure environment variables** (copy `.env.example` to `.env`, fill Groq, Supabase, and storage paths).
4. **Run the FastAPI backend**
   ```powershell
   python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```
5. **Launch the Next.js frontend** (optional/in-progress)
   ```powershell
   cd ..\frontend-nextjs
   npm install
   npm run dev
   ```
6. **Open the docs**: http://localhost:8000/docs and http://localhost:3000 (or the Streamlit fallback) to interact with the system.

## Documentation Map
| Document | Purpose |
| --- | --- |
| [STARTUP_GUIDE.md](STARTUP_GUIDE.md) | Step-by-step setup, environment configuration, and run commands. |
| [DESIGN_DOCUMENT.md](DESIGN_DOCUMENT.md) | Architecture decisions, component responsibilities, data flow, and future roadmap. |
| `diagrams/hybrid-architecture.png` | Visual overview of the five-layer system architecture. |

## Technology Stack
- **Backend**: FastAPI, Pydantic v2, Uvicorn, Supabase Python SDK
- **ML / AI**: PyTorch, HuggingFace Transformers (Legal-BERT), ChromaDB, Groq LLaMA 3.3 API
- **Frontend**: Next.js 15, React 19, Tailwind CSS (Streamlit legacy UI retained during migration)
- **Data & Ops**: Supabase PostgreSQL, ChromaDB SQLite vector store, PowerShell tooling for diagram generation

## Testing & Quality Gates
- Unit and integration tests under `backend/tests/` (PyTest)
- Scenario scripts in `backend/test_samples/` to validate compliant, non-compliant, and review-required policies
- Automated linting via `ruff` and `black` (configure in your IDE) and type checking with `mypy`

## Contributing
1. Open a feature branch from `main`.
2. Run the full test suite before committing:
   ```powershell
   cd backend
   pytest
   ```
3. Submit a PR with links to relevant diagrams or documents when architecture changes.

Questions or improvements? Open an issue or reach out to the team—the repository is organized so new contributors can become productive quickly.

## Roadmap

- [ ] Multi-language support (Hindi, regional languages)
- [ ] Integration with more document formats
- [ ] Advanced visualization and reporting
- [ ] Real-time compliance monitoring
- [ ] Mobile application
- [ ] Cloud deployment templates
- [ ] Advanced ML model fine-tuning tools

---

**Note**: This system is for educational and demonstration purposes. For production use in regulated environments, ensure compliance with all applicable laws and regulations.
