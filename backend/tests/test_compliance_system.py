"""
Unified Compliance System Test Suite

This comprehensive test file consolidates all testing functionality into a single script.
Tests both simple and Phase 2 models across CLI, API, and document analysis scenarios.

Usage:
    # Run all tests
    python tests/test_compliance_system.py

    # Run specific test suite
    python tests/test_compliance_system.py --suite api
    python tests/test_compliance_system.py --suite models
    python tests/test_compliance_system.py --suite documents

    # Test specific model
    python tests/test_compliance_system.py --model simple
    python tests/test_compliance_system.py --model phase2

    # Verbose output
    python tests/test_compliance_system.py --verbose
"""

import asyncio
import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
import time

# Setup paths
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Import after path setup
from app.processing.parsers.document_parser import DocumentParser
from app.ml.inference.simple_compliance_engine import SimpleComplianceEngine
from app.ml.inference.phase2_compliance_engine import Phase2ComplianceEngine

# Configuration
API_BASE_URL = "http://localhost:8000"
SAMPLE_DIR = BACKEND_ROOT / "test_samples"
SAMPLES = {
    "compliant": SAMPLE_DIR / "sample_policy_compliant.pdf",
    "non_compliant": SAMPLE_DIR / "sample_policy_non_compliant.pdf",
    "requires_review": SAMPLE_DIR / "sample_policy_requires_review.pdf",
}


@dataclass
class TestResult:
    """Test result data structure."""
    test_name: str
    passed: bool
    message: str
    duration: float
    details: Optional[Dict[str, Any]] = None


class TestRunner:
    """Unified test runner for all compliance system tests."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[TestResult] = []

    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose."""
        if self.verbose or level == "ERROR":
            prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}.get(level, "•")
            print(f"{prefix} {message}")

    def add_result(self, result: TestResult):
        """Add test result and print summary."""
        self.results.append(result)
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"{status} | {result.test_name} ({result.duration:.2f}s)")
        if not result.passed:
            print(f"    └─ {result.message}")
        elif self.verbose and result.details:
            print(f"    └─ {result.message}")

    async def test_api_health(self) -> TestResult:
        """Test API health endpoint."""
        start = time.time()
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            passed = response.status_code == 200
            data = response.json() if passed else {}
            
            return TestResult(
                test_name="API Health Check",
                passed=passed,
                message="API is healthy" if passed else f"API returned {response.status_code}",
                duration=time.time() - start,
                details=data
            )
        except Exception as e:
            return TestResult(
                test_name="API Health Check",
                passed=False,
                message=f"Cannot connect to API: {e}",
                duration=time.time() - start
            )

    async def test_document_upload(self, sample_name: str = "compliant") -> TestResult:
        """Test document upload via API."""
        start = time.time()
        sample_path = SAMPLES.get(sample_name)
        
        if not sample_path or not sample_path.exists():
            return TestResult(
                test_name=f"Document Upload ({sample_name})",
                passed=False,
                message=f"Sample file not found: {sample_path}",
                duration=time.time() - start
            )
        
        try:
            with open(sample_path, 'rb') as f:
                files = {'file': (sample_path.name, f, 'application/pdf')}
                response = requests.post(f"{API_BASE_URL}/api/v1/documents/upload", files=files, timeout=10)
            
            passed = response.status_code == 200
            doc_data = response.json() if passed else {}
            
            return TestResult(
                test_name=f"Document Upload ({sample_name})",
                passed=passed,
                message=f"Uploaded: {doc_data.get('document_id', 'N/A')}" if passed else response.text,
                duration=time.time() - start,
                details=doc_data
            )
        except Exception as e:
            return TestResult(
                test_name=f"Document Upload ({sample_name})",
                passed=False,
                message=f"Upload failed: {e}",
                duration=time.time() - start
            )

    async def test_api_analysis(self, sample_name: str = "compliant") -> TestResult:
        """Test full API workflow: upload + analyze."""
        start = time.time()
        sample_path = SAMPLES.get(sample_name)
        
        if not sample_path or not sample_path.exists():
            return TestResult(
                test_name=f"API Analysis ({sample_name})",
                passed=False,
                message=f"Sample file not found: {sample_path}",
                duration=time.time() - start
            )
        
        try:
            # Upload
            with open(sample_path, 'rb') as f:
                files = {'file': (sample_path.name, f, 'application/pdf')}
                upload_response = requests.post(f"{API_BASE_URL}/api/v1/documents/upload", files=files, timeout=10)
            
            if upload_response.status_code != 200:
                return TestResult(
                    test_name=f"API Analysis ({sample_name})",
                    passed=False,
                    message=f"Upload failed: {upload_response.status_code}",
                    duration=time.time() - start
                )
            
            doc_id = upload_response.json()['document_id']
            
            # Analyze
            analysis_response = requests.post(
                f"{API_BASE_URL}/api/v1/compliance/analyze",
                json={"document_id": doc_id, "analysis_type": "full", "include_explanation": True},
                timeout=30
            )
            
            passed = analysis_response.status_code == 200
            result = analysis_response.json() if passed else {}
            
            message = (
                f"Classification: {result.get('classification')} | "
                f"Confidence: {result.get('confidence', 0):.3f} | "
                f"Time: {result.get('processing_time', 0):.2f}s"
            ) if passed else f"Analysis failed: {analysis_response.status_code}"
            
            return TestResult(
                test_name=f"API Analysis ({sample_name})",
                passed=passed,
                message=message,
                duration=time.time() - start,
                details=result
            )
        except Exception as e:
            return TestResult(
                test_name=f"API Analysis ({sample_name})",
                passed=False,
                message=f"Error: {e}",
                duration=time.time() - start
            )

    async def test_simple_model_inference(self, sample_name: str = "compliant") -> TestResult:
        """Test simple model direct inference."""
        start = time.time()
        sample_path = SAMPLES.get(sample_name)
        
        if not sample_path or not sample_path.exists():
            return TestResult(
                test_name=f"Simple Model ({sample_name})",
                passed=False,
                message=f"Sample file not found: {sample_path}",
                duration=time.time() - start
            )
        
        try:
            parser = DocumentParser()
            engine = SimpleComplianceEngine()
            await engine.initialize()
            
            text = await parser.parse(str(sample_path))
            result = await engine.analyze(text)
            
            message = (
                f"Classification: {result.get('classification')} | "
                f"Confidence: {result.get('confidence', 0):.3f}"
            )
            
            return TestResult(
                test_name=f"Simple Model ({sample_name})",
                passed=True,
                message=message,
                duration=time.time() - start,
                details=result
            )
        except Exception as e:
            return TestResult(
                test_name=f"Simple Model ({sample_name})",
                passed=False,
                message=f"Inference failed: {e}",
                duration=time.time() - start
            )

    async def test_phase2_model_inference(self, sample_name: str = "compliant") -> TestResult:
        """Test Phase 2 model direct inference."""
        start = time.time()
        sample_path = SAMPLES.get(sample_name)
        
        if not sample_path or not sample_path.exists():
            return TestResult(
                test_name=f"Phase2 Model ({sample_name})",
                passed=False,
                message=f"Sample file not found: {sample_path}",
                duration=time.time() - start
            )
        
        try:
            parser = DocumentParser()
            engine = Phase2ComplianceEngine()
            await engine.initialize()
            
            text = await parser.parse(str(sample_path))
            result = await engine.analyze(text)
            
            message = (
                f"Classification: {result.get('classification')} | "
                f"Confidence: {result.get('confidence', 0):.3f}"
            )
            
            return TestResult(
                test_name=f"Phase2 Model ({sample_name})",
                passed=True,
                message=message,
                duration=time.time() - start,
                details=result
            )
        except Exception as e:
            return TestResult(
                test_name=f"Phase2 Model ({sample_name})",
                passed=False,
                message=f"Inference failed: {e}",
                duration=time.time() - start
            )

    async def test_document_parser(self, sample_name: str = "compliant") -> TestResult:
        """Test document parser."""
        start = time.time()
        sample_path = SAMPLES.get(sample_name)
        
        if not sample_path or not sample_path.exists():
            return TestResult(
                test_name=f"Document Parser ({sample_name})",
                passed=False,
                message=f"Sample file not found: {sample_path}",
                duration=time.time() - start
            )
        
        try:
            parser = DocumentParser()
            text = await parser.parse(str(sample_path))
            
            passed = len(text) > 0
            message = f"Parsed {len(text)} characters" if passed else "Empty document"
            
            return TestResult(
                test_name=f"Document Parser ({sample_name})",
                passed=passed,
                message=message,
                duration=time.time() - start,
                details={"text_length": len(text), "preview": text[:100]}
            )
        except Exception as e:
            return TestResult(
                test_name=f"Document Parser ({sample_name})",
                passed=False,
                message=f"Parse failed: {e}",
                duration=time.time() - start
            )

    async def run_api_tests(self):
        """Run all API-related tests."""
        print("\n" + "=" * 60)
        print("API TESTS")
        print("=" * 60)
        
        # Health check
        result = await self.test_api_health()
        self.add_result(result)
        
        if not result.passed:
            print("\n⚠️  API is not running. Skipping remaining API tests.")
            print("   Start API with: cd backend && python -m uvicorn api.main:app --reload")
            return
        
        # Upload tests
        for sample in ["compliant", "non_compliant", "requires_review"]:
            result = await self.test_document_upload(sample)
            self.add_result(result)
        
        # Analysis tests
        for sample in ["compliant", "non_compliant", "requires_review"]:
            result = await self.test_api_analysis(sample)
            self.add_result(result)

    async def run_model_tests(self, model_type: Optional[str] = None):
        """Run model inference tests."""
        print("\n" + "=" * 60)
        print("MODEL INFERENCE TESTS")
        print("=" * 60)
        
        samples = ["compliant", "non_compliant", "requires_review"]
        
        # Test simple model
        if model_type is None or model_type == "simple":
            for sample in samples:
                result = await self.test_simple_model_inference(sample)
                self.add_result(result)
        
        # Test Phase 2 model
        if model_type is None or model_type == "phase2":
            for sample in samples:
                result = await self.test_phase2_model_inference(sample)
                self.add_result(result)

    async def run_document_tests(self):
        """Run document parsing tests."""
        print("\n" + "=" * 60)
        print("DOCUMENT PARSING TESTS")
        print("=" * 60)
        
        for sample in ["compliant", "non_compliant", "requires_review"]:
            result = await self.test_document_parser(sample)
            self.add_result(result)

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        total_time = sum(r.duration for r in self.results)
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if not result.passed:
                    print(f"  • {result.test_name}: {result.message}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        return failed == 0


async def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Unified Compliance System Test Suite")
    parser.add_argument("--suite", choices=["api", "models", "documents", "all"], default="all",
                      help="Test suite to run")
    parser.add_argument("--model", choices=["simple", "phase2", "all"], default="all",
                      help="Model type to test (for model suite)")
    parser.add_argument("--verbose", "-v", action="store_true",
                      help="Verbose output")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("COMPLIANCE SYSTEM TEST SUITE")
    print("=" * 60)
    print(f"Backend Root: {BACKEND_ROOT}")
    print(f"API URL: {API_BASE_URL}")
    print(f"Test Suite: {args.suite}")
    if args.suite == "models":
        print(f"Model Type: {args.model}")
    
    runner = TestRunner(verbose=args.verbose)
    
    # Run selected test suites
    if args.suite in ["api", "all"]:
        await runner.run_api_tests()
    
    if args.suite in ["models", "all"]:
        model_type = args.model if args.model != "all" else None
        await runner.run_model_tests(model_type)
    
    if args.suite in ["documents", "all"]:
        await runner.run_document_tests()
    
    # Print summary
    all_passed = runner.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
