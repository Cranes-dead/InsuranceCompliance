# 🏗️ Project Restructuring Plan

## New Directory Structure

```
insurance_compliance_system/
├── app/                              # Main application package
│   ├── __init__.py                   
│   ├── core/                         # Core business logic
│   │   ├── __init__.py
│   │   ├── config.py                 # Centralized configuration
│   │   ├── logging.py                # Logging configuration
│   │   ├── exceptions.py             # Custom exceptions
│   │   └── security.py               # Security utilities
│   ├── models/                       # Data models (Pydantic + SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── database.py               # Database models (SQLAlchemy)
│   │   ├── schemas.py                # API schemas (Pydantic)
│   │   └── enums.py                  # Enums and constants
│   ├── services/                     # Business logic layer
│   │   ├── __init__.py
│   │   ├── compliance_service.py     # Main compliance logic
│   │   ├── document_service.py       # Document processing
│   │   ├── analysis_service.py       # Analysis orchestration
│   │   └── storage_service.py        # File storage management
│   ├── ml/                           # Machine learning components
│   │   ├── __init__.py
│   │   ├── models/                   # ML model definitions
│   │   │   ├── __init__.py
│   │   │   ├── legal_bert.py
│   │   │   ├── rule_classifier.py
│   │   │   └── base_model.py
│   │   ├── inference/                # Inference engines
│   │   │   ├── __init__.py
│   │   │   ├── compliance_engine.py
│   │   │   └── ollama_client.py
│   │   └── training/                 # Training utilities
│   │       ├── __init__.py
│   │       ├── trainer.py
│   │       └── data_loader.py
│   ├── processing/                   # Document processing
│   │   ├── __init__.py
│   │   ├── parsers/                  # Document parsers
│   │   │   ├── __init__.py
│   │   │   ├── pdf_parser.py
│   │   │   ├── text_parser.py
│   │   │   └── base_parser.py
│   │   ├── extractors/               # Feature extractors
│   │   │   ├── __init__.py
│   │   │   ├── text_extractor.py
│   │   │   └── metadata_extractor.py
│   │   └── validators/               # Input validators
│   │       ├── __init__.py
│   │       ├── document_validator.py
│   │       └── content_validator.py
│   ├── utils/                        # Shared utilities
│   │   ├── __init__.py
│   │   ├── file_utils.py
│   │   ├── text_utils.py
│   │   ├── date_utils.py
│   │   └── async_utils.py
│   └── database/                     # Database management
│       ├── __init__.py
│       ├── connection.py             # DB connection management
│       ├── migrations/               # Database migrations
│       └── repositories/             # Data access layer
│           ├── __init__.py
│           ├── base_repository.py
│           ├── document_repository.py
│           └── analysis_repository.py
├── api/                              # FastAPI application
│   ├── __init__.py
│   ├── main.py                       # FastAPI app creation
│   ├── deps.py                       # Dependency injection
│   ├── middleware/                   # Custom middleware
│   │   ├── __init__.py
│   │   ├── cors_middleware.py
│   │   ├── auth_middleware.py
│   │   └── error_middleware.py
│   └── v1/                           # API version 1
│       ├── __init__.py
│       ├── router.py                 # Main API router
│       └── endpoints/                # API endpoints
│           ├── __init__.py
│           ├── documents.py
│           ├── compliance.py
│           ├── analysis.py
│           └── health.py
├── frontend/                         # Frontend applications
│   ├── streamlit/                    # Current Streamlit app
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── pages/
│   │   └── components/
│   └── nextjs/                       # Future Next.js app (placeholder)
├── scripts/                          # Utility scripts
│   ├── setup.py                      # Environment setup
│   ├── migration.py                  # Database migration
│   ├── train_model.py                # Model training
│   └── scraper.py                    # Document scraper
├── tests/                            # Test suites
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration
│   ├── unit/                         # Unit tests
│   ├── integration/                  # Integration tests
│   └── e2e/                          # End-to-end tests
├── data/                             # Data storage
│   ├── raw/                          # Raw data
│   ├── processed/                    # Processed data
│   ├── uploads/                      # File uploads
│   └── training/                     # Training datasets
├── models/                           # Trained models
├── configs/                          # Configuration files
│   ├── development.env
│   ├── production.env
│   └── testing.env
├── docs/                             # Documentation
├── docker/                           # Docker configuration
│   ├── Dockerfile.api
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── .env                              # Environment variables
├── .gitignore
├── pyproject.toml                    # Project configuration
├── requirements.txt                  # Dependencies
└── README.md
```

## Key Improvements

### 1. **Proper Package Structure**
- All code organized in `app/` package with proper `__init__.py` files
- Clear separation of concerns
- Import paths become: `from app.services.compliance_service import ComplianceService`

### 2. **Service Layer Pattern**
- Business logic separated from API routes
- Services handle core functionality
- Easy to test and maintain

### 3. **Configuration Management**
- Centralized configuration in `app/core/config.py`
- Environment-specific configs
- Type-safe configuration using Pydantic Settings

### 4. **Next.js Ready Backend**
- RESTful API design
- JSON responses only
- CORS properly configured
- JWT authentication ready
- OpenAPI/Swagger documentation

### 5. **Database Layer**
- Repository pattern for data access
- Migration management
- Connection pooling

### 6. **Testing Structure**
- Unit, integration, and E2E tests
- Test fixtures and factories
- CI/CD ready

### 7. **Docker Support**
- Containerized services
- Development and production configs
- Database services

## Migration Steps

1. **Phase 1**: Create new structure and core modules
2. **Phase 2**: Move and refactor existing code
3. **Phase 3**: Update imports and dependencies
4. **Phase 4**: Test and validate
5. **Phase 5**: Update documentation

## Benefits for Next.js Migration

- **API-First Design**: Backend serves only JSON APIs
- **CORS Ready**: Proper cross-origin support
- **Authentication Ready**: JWT/OAuth integration points
- **File Upload Handling**: Proper multipart handling
- **WebSocket Support**: For real-time updates
- **Caching Layer**: Redis integration ready
- **Rate Limiting**: Built-in API protection