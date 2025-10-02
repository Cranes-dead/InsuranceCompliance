import asyncio
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ml.inference.simple_compliance_engine import SimpleComplianceEngine
from app.processing.parsers.document_parser import DocumentParser
SAMPLE_PATH = BACKEND_ROOT / "test_samples" / "sample_policy_requires_review.pdf"


async def run_test() -> None:
    """Run analysis on the sample policy that requires manual review."""
    print("📄 REQUIRES REVIEW SAMPLE TEST")
    print("=" * 44)

    if not SAMPLE_PATH.exists():
        print("❌ Review sample PDF not found:", SAMPLE_PATH)
        return

    parser = DocumentParser()
    engine = SimpleComplianceEngine()
    await engine.initialize()

    text = await parser.parse(str(SAMPLE_PATH))
    result = await engine.analyze(text)

    print(f"🎯 Classification: {result['classification']}")
    print(f"📊 Confidence: {result['confidence']:.3f}")
    print(f"📈 Compliance Score: {result['compliance_score']:.3f}")

    recommendations = result.get("recommendations", [])
    if recommendations:
        print("\nRecommendations:")
        for rec in recommendations:
            print(f"  💡 {rec}")

    explanation = result.get("explanation")
    if explanation:
        print("\n🤖 AI Explanation:")
        print(explanation)


if __name__ == "__main__":
    asyncio.run(run_test())
