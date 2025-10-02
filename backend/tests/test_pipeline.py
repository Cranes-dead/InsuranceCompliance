import asyncio
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ml.inference.simple_compliance_engine import SimpleComplianceEngine
from app.processing.parsers.document_parser import DocumentParser
SAMPLE_PATH = BACKEND_ROOT / "test_samples" / "sample_policy_compliant.pdf"


async def run_pipeline() -> None:
    """Run end-to-end compliance analysis on the sample compliant policy."""
    print("🧪 TESTING COMPLETE COMPLIANCE ANALYSIS PIPELINE")
    print("=" * 60)

    if not SAMPLE_PATH.exists():
        print("❌ Sample PDF not found:", SAMPLE_PATH)
        return

    parser = DocumentParser()
    engine = SimpleComplianceEngine()
    await engine.initialize()

    text = await parser.parse(str(SAMPLE_PATH))
    print(f"📄 Parsed document: {len(text)} characters")

    result = await engine.analyze(text)

    print(f"🎯 Classification: {result['classification']}")
    print(f"📊 Confidence: {result['confidence']:.3f}")
    print(f"📈 Compliance Score: {result['compliance_score']:.3f}")

    print("\n✅ Mandatory Requirements:")
    for req in result.get("mandatory_compliance", []):
        status = "✅" if req.get("compliant", False) else "❌"
        print(f"  {status} {req['rule']}")
        if req.get("found_amount") and req.get("required_amount"):
            print(
                f"      Found: Rs {req['found_amount']/100000:.0f}L, "
                f"Required: Rs {req['required_amount']/100000:.0f}L"
            )

    recommendations = result.get("recommendations", [])
    if recommendations:
        print("\n💡 Recommendations:")
        for rec in recommendations:
            print(f"  • {rec}")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
