# Insurance Compliance System - Design Document

## 1. System Overview

### Project Name: AI-Powered Insurance Compliance Monitoring System

### Purpose
An intelligent system that leverages Legal BERT and Ollama to analyze insurance documents against IRDAI guidelines, providing automated compliance checking, violation detection, and human-readable explanations for regulatory adherence.

### Key Features
- Automated IRDAI guideline compliance checking
- Claim rejection letter analysis
- Bulk policy compliance auditing
- Legal backing for disputes
- Human-readable explanation generation
- Export capabilities for audit reports

## 2. System Architecture

### High-Level Architecture
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

### Component Details

#### 2.1 Data Layer
- **IRDAI Document Storage**: Scraped PDFs and processed text
- **Policy Database**: User-uploaded policies and documents
- **Compliance Rules**: Structured IRDAI guidelines
- **Results Storage**: Analysis results and audit reports

#### 2.2 Processing Layer
- **Document Parser**: PDF text extraction and preprocessing
- **Text Processor**: Cleaning, tokenization, and formatting
- **Feature Extractor**: Regulatory pattern extraction
- **Batch Processor**: Bulk document handling

#### 2.3 AI/ML Layer
- **Legal BERT Model**: Fine-tuned for insurance compliance
- **Ollama Integration**: Explanation generation and reasoning
- **Classification Engine**: Multi-label compliance classification
- **Context Matcher**: Regulation-to-document mapping

#### 2.4 API Layer
- **Document Upload API**: File handling and validation
- **Analysis API**: Single and batch compliance checking
- **Report Generation API**: Audit report creation
- **Export API**: Results download functionality

#### 2.5 Frontend Layer
- **Document Upload Interface**: Drag-and-drop file upload
- **Analysis Dashboard**: Real-time compliance results
- **Report Viewer**: Interactive compliance reports
- **Export Interface**: Download functionality

## 3. Data Flow

### 3.1 Document Analysis Pipeline
```
Document Upload → PDF Parser → Text Extraction → 
Preprocessing → Legal BERT Classification → 
Ollama Explanation → Result Formatting → UI Display
```

### 3.2 Training Data Pipeline
```
IRDAI Scraper → PDF Processing → Text Labeling → 
Feature Engineering → Legal BERT Fine-tuning → 
Model Validation → Deployment
```

## 4. Technical Stack

### Backend
- **Framework**: FastAPI (Python)
- **ML/AI**: 
  - Transformers (Hugging Face) for Legal BERT
  - Ollama for LLM integration
  - scikit-learn for additional ML tasks
- **Database**: SQLite (development), PostgreSQL (production)
- **Document Processing**: PyPDF2, pdfplumber, spaCy
- **Web Scraping**: Existing scraper (selenium, requests)

### Frontend
- **Framework**: Streamlit (rapid prototyping)
- **Visualization**: Plotly, Altair
- **File Handling**: Native Streamlit components

### Infrastructure
- **Containerization**: Docker
- **API Documentation**: FastAPI automatic docs
- **Testing**: pytest, pytest-asyncio
- **Logging**: structlog

## 5. Implementation Plan

### Phase 1: Foundation (Week 1-2)
1. Project structure setup
2. Basic API framework
3. Document processing pipeline
4. Database schema design

### Phase 2: AI/ML Core (Week 3-4)
1. Legal BERT model preparation
2. Training data preparation
3. Model fine-tuning
4. Ollama integration

### Phase 3: API Development (Week 5-6)
1. RESTful API endpoints
2. Document upload handling
3. Analysis orchestration
4. Result management

### Phase 4: Frontend Development (Week 7-8)
1. Streamlit interface
2. Dashboard components
3. Report generation
4. Export functionality

### Phase 5: Integration & Testing (Week 9-10)
1. End-to-end testing
2. Performance optimization
3. Error handling
4. Documentation

## 6. Directory Structure

```
capstone/
├── docs/                          # Documentation
├── src/                           # Source code
│   ├── api/                       # FastAPI application
│   │   ├── routes/                # API endpoints
│   │   ├── models/                # Pydantic models
│   │   └── middleware/            # Custom middleware
│   ├── ml/                        # Machine learning components
│   │   ├── models/                # Model definitions
│   │   ├── training/              # Training scripts
│   │   └── inference/             # Inference pipeline
│   ├── processing/                # Document processing
│   │   ├── parsers/               # PDF/text parsers
│   │   ├── extractors/            # Feature extractors
│   │   └── preprocessors/         # Text preprocessing
│   ├── data/                      # Data management
│   │   ├── scrapers/              # Web scrapers
│   │   ├── storage/               # Data storage
│   │   └── schemas/               # Database schemas
│   ├── frontend/                  # Streamlit application
│   │   ├── pages/                 # Multi-page app
│   │   ├── components/            # Reusable components
│   │   └── utils/                 # Frontend utilities
│   └── utils/                     # Shared utilities
├── tests/                         # Test suites
├── configs/                       # Configuration files
├── models/                        # Trained models
├── data/                         # Data storage
│   ├── raw/                      # Raw scraped data
│   ├── processed/                # Processed documents
│   └── training/                 # Training datasets
├── scripts/                      # Utility scripts
├── requirements.txt              # Python dependencies
├── docker-compose.yml           # Docker configuration
└── README.md                    # Project documentation
```

## 7. Database Schema

### 7.1 Documents Table
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    filename VARCHAR(255),
    file_path VARCHAR(500),
    document_type VARCHAR(50),
    upload_timestamp DATETIME,
    file_size INTEGER,
    status VARCHAR(20)
);
```

### 7.2 Compliance Results Table
```sql
CREATE TABLE compliance_results (
    id INTEGER PRIMARY KEY,
    document_id INTEGER,
    classification VARCHAR(50),
    confidence FLOAT,
    violations TEXT,
    recommendations TEXT,
    analysis_timestamp DATETIME,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
```

### 7.3 IRDAI Guidelines Table
```sql
CREATE TABLE irdai_guidelines (
    id INTEGER PRIMARY KEY,
    guideline_id VARCHAR(100),
    title VARCHAR(500),
    content TEXT,
    category VARCHAR(100),
    effective_date DATE,
    last_updated DATETIME
);
```

## 8. API Specifications

### 8.1 Document Upload
```
POST /api/documents/upload
Content-Type: multipart/form-data

Response:
{
    "document_id": "12345",
    "status": "uploaded",
    "message": "Document uploaded successfully"
}
```

### 8.2 Compliance Analysis
```
POST /api/analysis/compliance
{
    "document_id": "12345",
    "analysis_type": "full"
}

Response:
{
    "document_id": "12345",
    "classification": "NON_COMPLIANT",
    "confidence": 0.85,
    "violations": [...],
    "explanation": "...",
    "recommendations": [...]
}
```

### 8.3 Batch Analysis
```
POST /api/analysis/batch
{
    "document_ids": ["12345", "12346", "12347"]
}

Response:
{
    "batch_id": "batch_001",
    "status": "processing",
    "results": [...]
}
```

## 9. ML Model Specifications

### 9.1 Legal BERT Configuration
- **Base Model**: bert-base-uncased
- **Fine-tuning**: Insurance domain-specific
- **Output Classes**: [COMPLIANT, NON_COMPLIANT, REQUIRES_REVIEW]
- **Training Strategy**: Multi-label classification with class weights

### 9.2 Ollama Integration
- **Model**: llama3.1 or similar
- **Purpose**: Explanation generation and reasoning
- **Input**: Legal BERT predictions + document context
- **Output**: Human-readable explanations

## 10. Performance Requirements

### 10.1 Response Times
- Single document analysis: < 30 seconds
- Batch processing: < 5 minutes for 10 documents
- Report generation: < 10 seconds

### 10.2 Accuracy Targets
- Classification accuracy: > 85%
- Precision for NON_COMPLIANT: > 90%
- Recall for violations: > 80%

## 11. Security Considerations

- File upload validation and sanitization
- API rate limiting
- Secure file storage
- Data privacy compliance
- Input validation for all endpoints

## 12. Testing Strategy

### 12.1 Unit Tests
- Document processing functions
- ML model components
- API endpoint logic

### 12.2 Integration Tests
- End-to-end document processing
- API workflow testing
- Database operations

### 12.3 Performance Tests
- Load testing for batch processing
- Memory usage optimization
- Response time benchmarking

This design document provides a comprehensive roadmap for implementing the Insurance Compliance System. The next phase will involve setting up the project structure and beginning implementation of the core components.