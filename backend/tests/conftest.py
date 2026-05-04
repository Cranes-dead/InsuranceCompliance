"""
Shared pytest fixtures and configuration.

Phase 8: Provides mock settings, app client, and test helpers
that allow unit tests to run without heavy ML/DB dependencies.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

# Ensure backend is importable
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture(scope="session", autouse=True)
def mock_heavy_imports():
    """Mock heavy ML/DB imports so tests run without GPU or DB.
    
    This patches torch, transformers, etc. at the module level so
    that importing app.ml.* doesn't fail in CI.
    """
    # These modules may not exist in CI — provide stubs
    modules_to_mock = [
        "torch", "torch.nn", "torch.cuda",
        "transformers",
        "sklearn", "sklearn.metrics", "sklearn.metrics.pairwise",
        "chromadb",
        "faiss",
        "supabase",
    ]
    mocks = {}
    for mod_name in modules_to_mock:
        if mod_name not in sys.modules:
            mocks[mod_name] = MagicMock()
            sys.modules[mod_name] = mocks[mod_name]
    
    yield
    
    # Cleanup (optional — session-scoped so only at exit)
    for mod_name in mocks:
        sys.modules.pop(mod_name, None)


@pytest.fixture
def sample_policy_text():
    """Sample compliant policy text for unit tests."""
    return (
        "MOTOR VEHICLE INSURANCE POLICY\n"
        "Policy Number: MV-2024-001\n"
        "Insurer: ABC Insurance Co. Ltd.\n\n"
        "SECTION A: Third Party Liability\n"
        "This policy provides coverage for third party bodily injury and "
        "property damage liability as mandated under the Motor Vehicles Act, 1988. "
        "Coverage limit: Unlimited for bodily injury per IRDAI guidelines.\n\n"
        "SECTION B: Own Damage Coverage\n"
        "Comprehensive own damage coverage including fire, theft, natural calamities, "
        "and accidental damage. Deductible: Rs. 1,000.\n\n"
        "SECTION C: Personal Accident Cover\n"
        "Compulsory personal accident cover for owner-driver: Rs. 15,00,000.\n\n"
        "TERMS AND CONDITIONS\n"
        "Premium payment due within 30 days of policy inception.\n"
        "Claims must be reported within 48 hours of incident."
    )


@pytest.fixture
def sample_non_compliant_text():
    """Sample non-compliant policy text for unit tests."""
    return (
        "VEHICLE COVERAGE DOCUMENT\n"
        "This plan covers only collision damage.\n"
        "Third party liability: EXCLUDED.\n"
        "Personal accident cover: NOT PROVIDED.\n"
        "Maximum payout: Rs. 50,000."
    )


@pytest.fixture
def sample_analysis_result():
    """Sample analysis result dict for testing downstream logic."""
    return {
        "classification": "NON_COMPLIANT",
        "confidence": 0.92,
        "compliance_score": 35.0,
        "violations": [
            {
                "severity": "CRITICAL",
                "type": "MISSING_COVERAGE",
                "description": "Third party liability not included",
                "regulation_reference": "Motor Vehicles Act 1988 S.146",
                "recommendation": "Add mandatory third party coverage",
            }
        ],
        "mandatory_compliance": [
            {
                "requirement": "Third party liability coverage",
                "status": "NOT_MET",
                "evidence": "Third party liability: EXCLUDED",
            }
        ],
        "explanation": "Policy lacks mandatory third party liability coverage.",
        "recommendations": ["Add third party liability coverage"],
    }
