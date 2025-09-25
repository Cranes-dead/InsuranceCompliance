# Insurance Compliance System

## Overview

An AI-powered insurance compliance monitoring system that leverages Legal BERT and Ollama to analyze insurance documents against IRDAI guidelines. The system provides automated compliance checking, violation detection, and human-readable explanations for regulatory adherence.

## Features

- 🔍 **Automated Compliance Analysis**: AI-powered document analysis using Legal BERT
- 📊 **Batch Processing**: Analyze multiple documents simultaneously  
- 🤖 **AI Explanations**: Human-readable explanations powered by Ollama
- 📈 **Compliance Dashboard**: Visual analytics and reporting
- 🔄 **Real-time Processing**: Live document analysis and results
- 📱 **Web Interface**: User-friendly Streamlit frontend
- 🚀 **RESTful API**: FastAPI backend for integrations
- 🕷️ **Document Scraping**: Integrated IRDAI document scraper

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI   │◄──►│   API Gateway   │◄──►│  Core Services  │
│   (Streamlit)   │    │   (FastAPI)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Layer    │◄──►│ Processing Layer│◄──►│   AI/ML Layer   │
│   (SQLite/     │    │ (Document       │    │ (Legal BERT +   │
│   File System) │    │  Processors)    │    │     Ollama)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Project Structure

```
capstone/
├── src/
│   ├── api/                    # FastAPI backend
│   │   ├── routes/             # API endpoints
│   │   ├── models/             # Pydantic schemas
│   │   └── main.py             # FastAPI app
│   ├── ml/                     # Machine learning components
│   │   ├── models/             # Legal BERT implementation
│   │   ├── training/           # Training scripts
│   │   └── inference/          # Ollama integration
│   ├── processing/             # Document processing
│   │   └── parsers/            # PDF/text processors
│   ├── data/                   # Data management
│   │   └── database.py         # SQLAlchemy models
│   └── frontend/               # Streamlit UI
│       └── app.py              # Main app
├── data/                       # Data storage
├── models/                     # Trained models
├── configs/                    # Configuration
├── tests/                      # Test suites
├── scraper.py                  # IRDAI document scraper
└── scraper_streamlined.py      # Optimized scraper
```

## Installation

### Prerequisites

- Python 3.8+
- Ollama (for AI explanations)
- Chrome/Firefox (for web scraping)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Cranes-dead/Capstone.git
   cd Capstone
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Linux/Mac:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install spaCy model:**
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Install and start Ollama:**
   ```bash
   # Download from https://ollama.ai
   # Then pull the model:
   ollama pull llama3.1
   ```

6. **Set up directories:**
   ```bash
   mkdir -p data/uploads data/processed models
   ```

## Usage

### 1. Start the API Server

```bash
cd src/api
python main.py
```

The API will be available at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### 2. Launch the Frontend

```bash
cd src/frontend
streamlit run app.py
```

The web interface will open at `http://localhost:8501`

### 3. Use the Web Interface

1. **Upload Documents**: Use the "Document Upload" page to upload PDF files
2. **Single Analysis**: Analyze individual documents for compliance
3. **Batch Analysis**: Process multiple documents simultaneously
4. **Dashboard**: View compliance metrics and trends
5. **Document Library**: Manage uploaded documents

### 4. Document Scraping

Use the integrated IRDAI scraper to collect regulatory documents:
```python
from scraper import ComplianceDocumentScraper

# Use default directory (D:/compliance_scraper)
scraper = ComplianceDocumentScraper()
scraper.run()
```

### 5. API Usage Examples

**Upload Document:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@policy.pdf"
```

**Analyze Document:**
```bash
curl -X POST "http://localhost:8000/analysis/compliance" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{
       "document_id": "12345",
       "analysis_type": "full",
       "include_explanation": true
     }'
```

## Development

### Training Legal BERT Model

1. **Prepare training data:**
   - Create labeled dataset of compliance documents
   - Use the scraper to collect IRDAI documents
   - Label documents as COMPLIANT, NON_COMPLIANT, or REQUIRES_REVIEW

2. **Train the model:**
   ```bash
   python src/ml/training/train_legal_bert.py --data-dir ./data/training --epochs 3
   ```

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/

# Type checking
mypy src/

# Linting
flake8 src/
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=sqlite:///./compliance_system.db

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# API
API_HOST=0.0.0.0
API_PORT=8000

# File uploads
MAX_FILE_SIZE=52428800  # 50MB
UPLOAD_DIR=./data/uploads

# Logging
LOG_LEVEL=INFO
```

### Model Configuration

Edit `configs/config.py` to customize:
- Legal BERT model parameters
- Classification thresholds
- Processing options
- API settings

## Deployment

### Docker (Recommended)

```bash
# Build image
docker build -t compliance-system .

# Run container
docker run -p 8000:8000 -p 8501:8501 compliance-system
```

### Production Deployment

1. **Use PostgreSQL** instead of SQLite for database
2. **Set up reverse proxy** (nginx/Apache) 
3. **Configure SSL/HTTPS**
4. **Set up monitoring** (logs, metrics)
5. **Scale with containers** (Docker Swarm/Kubernetes)

## Use Cases

### 1. Policy Document Compliance Check
- Upload insurance policy documents
- Get automated compliance assessment
- Receive detailed violation reports
- Download compliance certificates

### 2. Claim Rejection Analysis
- Upload claim rejection letters
- Identify compliance violations
- Get legal backing for disputes
- Receive actionable next steps

### 3. Bulk Compliance Audit
- Upload multiple policies for batch analysis
- Generate comprehensive compliance reports
- Export audit results for regulators
- Track compliance trends over time

## API Reference

### Endpoints

- `POST /documents/upload` - Upload documents
- `GET /documents/` - List documents
- `POST /analysis/compliance` - Analyze single document
- `POST /analysis/batch` - Start batch analysis
- `GET /analysis/batch/{batch_id}` - Get batch status
- `GET /health` - Health check

### Response Formats

**Compliance Analysis:**
```json
{
  "document_id": "12345",
  "classification": "NON_COMPLIANT",
  "confidence": 0.87,
  "violations": [
    {
      "type": "REGULATION_BREACH",
      "description": "Policy violates IRDAI circular XYZ-2023",
      "severity": "HIGH",
      "regulation_reference": "IRDAI/REG/2023/001"
    }
  ],
  "recommendations": ["Update policy terms", "Consult legal team"],
  "explanation": "AI-generated explanation...",
  "analysis_timestamp": "2024-01-15T10:30:00Z"
}
```

## Scraper Features

The integrated document scraper provides:
- **Multi-source scraping**: IRDAI, MoRTH, and GIC websites
- **Language detection**: Automatic detection of Hindi and English documents
- **Selenium-based**: Handles dynamic content and JavaScript-heavy sites
- **Dual browser support**: Chrome with Firefox fallback
- **Robust error handling**: Retry mechanisms and graceful degradation
- **File size management**: Configurable limits and validation
- **Duplicate prevention**: Tracks processed URLs to avoid re-downloads
- **UTF-8 support**: Proper handling of Hindi Devanagari script

## Troubleshooting

### Common Issues

**1. Ollama Connection Error:**
- Ensure Ollama is running: `ollama serve`
- Check if model is available: `ollama list`
- Verify connection: `curl http://localhost:11434/api/tags`

**2. Model Loading Issues:**
- Download spaCy model: `python -m spacy download en_core_web_sm`
- Check CUDA availability for PyTorch
- Verify model files in `./models/` directory

**3. File Upload Errors:**
- Check file size limits (50MB default)
- Verify file permissions in upload directory
- Ensure supported file formats (PDF, TXT, DOCX)

**4. Database Issues:**
- Delete SQLite file to reset: `rm compliance_system.db`
- Check database permissions
- Verify SQLAlchemy connection string

**5. Chrome Driver Issues:**
If Chrome fails to start:
- Ensure Chrome browser is installed
- Check Windows compatibility (script handles common issues)
- Firefox will automatically be used as fallback

### Performance Optimization

- Use GPU for Legal BERT inference
- Implement caching for frequent analyses
- Optimize batch processing chunk sizes
- Use connection pooling for database

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in `/docs`
- Review API documentation at `/docs` endpoint

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
