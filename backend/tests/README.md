# Compliance System Test Suite

A comprehensive, unified test suite for the Insurance Compliance System that consolidates all testing functionality into a single executable script.

## Features

- **API Testing**: Health checks, document upload, full analysis workflow
- **Model Testing**: Both Simple and Phase 2 Legal-BERT models
- **Document Parsing**: PDF/TXT document processing validation
- **Flexible Execution**: Run all tests or specific suites
- **Detailed Reporting**: Pass/fail status, timing, and error messages

## Quick Start

### Run All Tests
```bash
cd backend
python tests/test_compliance_system.py
```

### Run Specific Test Suite
```bash
# API tests only (requires backend running)
python tests/test_compliance_system.py --suite api

# Model inference tests only
python tests/test_compliance_system.py --suite models

# Document parsing tests only
python tests/test_compliance_system.py --suite documents
```

### Test Specific Model
```bash
# Test Simple model only
python tests/test_compliance_system.py --suite models --model simple

# Test Phase 2 model only
python tests/test_compliance_system.py --suite models --model phase2
```

### Verbose Output
```bash
python tests/test_compliance_system.py --verbose
```

## Test Suites

### 1. API Tests
Tests the FastAPI backend endpoints:
- Health check (`/health`)
- Document upload (`/api/v1/documents/upload`)
- Compliance analysis (`/api/v1/compliance/analyze`)

**Requirements**: Backend must be running on `http://localhost:8000`

**Start Backend**:
```bash
cd backend
python -m uvicorn api.main:app --reload --port 8000
```

### 2. Model Inference Tests
Tests direct model inference (bypasses API):
- **Simple Model**: `legal_bert_simple` - lightweight classification
- **Phase 2 Model**: `legal_bert_compliance_final` - domain-adapted classifier

Tests each model against all sample documents:
- `sample_policy_compliant.pdf`
- `sample_policy_non_compliant.pdf`
- `sample_policy_requires_review.pdf`

### 3. Document Parsing Tests
Tests PDF/TXT parsing functionality:
- File reading
- Text extraction
- Character count validation

## Sample Test Output

```
============================================================
COMPLIANCE SYSTEM TEST SUITE
============================================================
Backend Root: C:\...\backend
API URL: http://localhost:8000
Test Suite: all

============================================================
API TESTS
============================================================
✅ PASS | API Health Check (0.05s)
✅ PASS | Document Upload (compliant) (0.23s)
✅ PASS | API Analysis (compliant) (5.34s)

============================================================
MODEL INFERENCE TESTS
============================================================
✅ PASS | Simple Model (compliant) (2.15s)
    └─ Classification: COMPLIANT | Confidence: 0.881
✅ PASS | Phase2 Model (compliant) (5.52s)
    └─ Classification: REQUIRES_REVIEW | Confidence: 0.954

============================================================
TEST SUMMARY
============================================================
Total Tests: 13
✅ Passed: 13
❌ Failed: 0
⏱️  Total Time: 35.42s

Success Rate: 100.0%
```

## Test Results Interpretation

### Simple Model Results
- Generally classifies most documents as `COMPLIANT`
- Faster inference (~2s per document)
- Good for quick validation

### Phase 2 Model Results
- More conservative, often classifies as `REQUIRES_REVIEW`
- Slower inference (~5s per document)
- Higher confidence scores
- Better for production use where false positives are costly

## Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed

Useful for CI/CD pipelines:
```bash
python tests/test_compliance_system.py && echo "Tests passed" || echo "Tests failed"
```

## Troubleshooting

### API Connection Failed
**Symptom**: `Cannot connect to API` error

**Solution**: Start the backend:
```bash
cd backend
python -m uvicorn api.main:app --reload --port 8000
```

### Sample Files Not Found
**Symptom**: `Sample file not found` error

**Solution**: Ensure test samples exist in `backend/test_samples/`:
- `sample_policy_compliant.pdf`
- `sample_policy_non_compliant.pdf`
- `sample_policy_requires_review.pdf`

### Model Loading Errors
**Symptom**: `Model not found` or import errors

**Solution**: 
1. Verify models exist in `backend/models/`:
   - `legal_bert_simple/`
   - `legal_bert_compliance_final/`
   - `legal_bert_domain_adapted/`

2. Run training if models are missing:
   ```bash
   # Simple model
   python backend/simple_legal_bert_training.py
   
   # Phase 2 model
   python backend/phase1_domain_adaptation_optimized.py
   python backend/phase2_classification_training.py
   ```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run Compliance Tests
  run: |
    cd backend
    python tests/test_compliance_system.py --suite models
```

### Pre-commit Hook
```bash
#!/bin/bash
cd backend
python tests/test_compliance_system.py --suite documents --suite models
```

## Development

### Adding New Tests

1. Add test method to `TestRunner` class:
```python
async def test_new_feature(self) -> TestResult:
    start = time.time()
    try:
        # Your test logic
        return TestResult(
            test_name="New Feature Test",
            passed=True,
            message="Test passed",
            duration=time.time() - start
        )
    except Exception as e:
        return TestResult(
            test_name="New Feature Test",
            passed=False,
            message=f"Error: {e}",
            duration=time.time() - start
        )
```

2. Call it from appropriate suite:
```python
async def run_api_tests(self):
    # ... existing tests
    result = await self.test_new_feature()
    self.add_result(result)
```

## Command Line Reference

```
usage: test_compliance_system.py [-h] [--suite {api,models,documents,all}]
                                 [--model {simple,phase2,all}] [--verbose]

Unified Compliance System Test Suite

optional arguments:
  -h, --help            show this help message and exit
  --suite {api,models,documents,all}
                        Test suite to run
  --model {simple,phase2,all}
                        Model type to test (for model suite)
  --verbose, -v         Verbose output
```

## Performance Benchmarks

Typical execution times (CPU):
- Document parsing: ~0.1s per document
- Simple model inference: ~2s per document
- Phase 2 model inference: ~5s per document
- API workflow: ~6s per document (includes upload + parse + inference)

Total suite runtime:
- Models only: ~30s
- API only: ~20s (with backend running)
- Full suite: ~35s

## Related Files

- Test script: `backend/tests/test_compliance_system.py`
- API tests: Requires backend at `http://localhost:8000`
- Sample data: `backend/test_samples/*.pdf`
- Models: `backend/models/legal_bert_*/`

## License

Part of the Insurance Compliance System - See main project README.
