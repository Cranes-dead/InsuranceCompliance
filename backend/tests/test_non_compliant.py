import asyncio
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ml.inference.simple_compliance_engine import SimpleComplianceEngine
from app.processing.parsers.document_parser import DocumentParser
SAMPLE_PATH = BACKEND_ROOT / "test_samples" / "sample_policy_non_compliant.pdf"


async def run_test() -> None:
    """Run analysis on the non-compliant sample policy."""
    print("📄 NON-COMPLIANT SAMPLE TEST")
    print("=" * 40)

    if not SAMPLE_PATH.exists():
        print("❌ Non-compliant sample PDF not found:", SAMPLE_PATH)
        return

    parser = DocumentParser()
    engine = SimpleComplianceEngine()
    await engine.initialize()

    text = await parser.parse(str(SAMPLE_PATH))
    result = await engine.analyze(text)

    print(f"🎯 Classification: {result['classification']}")
    print(f"📊 Confidence: {result['confidence']:.3f}")
    print(f"📈 Compliance Score: {result['compliance_score']:.3f}")

    print("\nMandatory Requirements:")
    for req in result.get("mandatory_compliance", []):
        status = "✅" if req.get("compliant", False) else "❌"
        print(f"  {status} {req['rule']}")
        if req.get("found_amount") and req.get("required_amount"):
            print(
                f"      Found: Rs {req['found_amount']/100000:.0f}L, "
                f"Required: Rs {req['required_amount']/100000:.0f}L"
            )

    violations = result.get("violations", [])
    if violations:
        print("\nViolations:")
        for violation in violations:
            print(f"  ⚠️ {violation['description']}")

    recommendations = result.get("recommendations", [])
    if recommendations:
        print("\nRecommendations:")
        for rec in recommendations:
            print(f"  💡 {rec}")


if __name__ == "__main__":
    asyncio.run(run_test())
