"""
Shared pytest fixtures and configuration.

Phase 8: Provides mock settings, app client, and test helpers
that allow unit tests to run without heavy ML/DB dependencies.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Ensure backend is importable
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# ---------------------------------------------------------------------------
# Mock heavy ML/DB imports at module level (BEFORE test collection).
#
# Why not a fixture?  Pytest session fixtures run *after* test collection,
# but Python resolves the full import chain when collecting test modules:
#   test_cache_service → app.services → compliance_service → phase2_engine → torch
# If torch isn't installed (CI), collection fails before any fixture runs.
# Patching sys.modules here guarantees stubs exist before any test file
# is imported.
# ---------------------------------------------------------------------------
_MODULES_TO_MOCK = [
    "torch", "torch.nn", "torch.cuda",
    "transformers",
    "sklearn", "sklearn.metrics", "sklearn.metrics.pairwise",
    "chromadb",
    "faiss",
    "supabase",
]

_injected_mocks: dict[str, MagicMock] = {}
for _mod_name in _MODULES_TO_MOCK:
    if _mod_name not in sys.modules:
        _injected_mocks[_mod_name] = MagicMock()
        sys.modules[_mod_name] = _injected_mocks[_mod_name]


@pytest.fixture(scope="session", autouse=True)
def mock_heavy_imports():
    """Kept for backward compatibility — actual mocking happens above at import time."""
    yield

    # Cleanup at session end
    for mod_name in _injected_mocks:
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
