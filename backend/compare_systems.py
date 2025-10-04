"""Compare Old (Phase 2 BERT) vs New (RAG + LLaMA) systems.

This script runs both systems on the same test policies and compares:
- Classification results
- Confidence scores
- Explanation quality
- Processing time
"""

import asyncio
import time
import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

from app.ml.inference.phase2_compliance_engine import Phase2ComplianceEngine
from app.ml.rag_llama_service import RAGLLaMAComplianceService

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Test policies
TEST_POLICIES = {
    "compliant": """
    MOTOR VEHICLE THIRD-PARTY INSURANCE POLICY
    
    Coverage: This policy provides comprehensive third-party liability coverage for motor vehicles
    as mandated by the Motor Vehicles Act.
    
    Coverage Includes:
    - Third-party bodily injury: As per Motor Vehicles Act (unlimited)
    - Third-party property damage: Up to Rs. 7.5 lakhs
    - Personal accident cover for owner-driver: Rs. 15 lakhs
    - Legal liability for passengers: Included
    
    Premium: Rs. 3,500 annually for private cars
    
    Terms: Policy valid for 12 months. No exclusions that violate mandatory requirements.
    """,
    
    "non_compliant": """
    MOTOR VEHICLE INSURANCE POLICY
    
    Coverage: Basic third-party liability coverage
    
    Coverage Limits:
    - Property damage: Up to Rs. 50,000  [NON-COMPLIANT: Too low]
    - Bodily injury: Rs. 10 lakhs per accident [NON-COMPLIANT: Should be unlimited]
    
    Exclusions:
    - No coverage for owner-driver personal accident [NON-COMPLIANT: Mandatory]
    - Damage caused by intoxicated driving
    - Use for commercial purposes
    
    Premium: Rs. 2,000 annually
    
    Fine print: Claims may be denied if vehicle registration is expired.
    """,
    
    "requires_review": """
    MOTOR VEHICLE INSURANCE POLICY
    
    Coverage: Third-party liability as per regulations
    
    Coverage Details:
    - Third-party liability: "As mandated by law" [UNCLEAR: Not specific]
    - Owner-driver personal accident: "Subject to terms" [AMBIGUOUS]
    
    Exclusions:
    - "Any loss not covered under mandatory provisions" [UNCLEAR]
    - Damage while under influence of substances
    
    Premium: Market rate based on vehicle type
    
    Special Conditions:
    - Policy subject to inspection of vehicle
    - Claims processed based on investigation
    - Company reserves right to deny claims for non-disclosure
    """
}


async def run_old_system(policy_text: str) -> Dict[str, Any]:
    """Run Phase 2 BERT classifier."""
    logger.info("🔄 Running OLD system (Phase 2 BERT)...")
    
    engine = Phase2ComplianceEngine()
    await engine.initialize()
    
    start = time.time()
    result = await engine.analyze(policy_text)
    elapsed = time.time() - start
    
    return {
        "classification": result.get("classification"),
        "confidence": result.get("confidence", 0.0),
        "compliance_score": result.get("compliance_score", 0.0),
        "explanation": result.get("explanation", ""),
        "time": elapsed,
        "system": "OLD (Phase 2 BERT)"
    }


async def run_new_system(policy_text: str) -> Dict[str, Any]:
    """Run RAG + LLaMA system."""
    logger.info("🆕 Running NEW system (RAG + LLaMA)...")
    
    service = RAGLLaMAComplianceService()
    await service.initialize()
    
    start = time.time()
    result = await service.analyze_policy(
        policy_text=policy_text,
        top_k_regulations=10
    )
    elapsed = time.time() - start
    
    return {
        "classification": result.get("classification"),
        "confidence": result.get("confidence", 0.0),
        "compliance_score": result.get("compliance_score", 0.0),
        "explanation": result.get("explanation", "")[:500],  # Truncate for display
        "violations": len(result.get("violations", [])),
        "recommendations": len(result.get("recommendations", [])),
        "regulations_used": result.get("rag_metadata", {}).get("regulations_retrieved", 0),
        "time": elapsed,
        "system": "NEW (RAG + LLaMA)"
    }


def print_comparison(policy_name: str, old_result: Dict, new_result: Dict):
    """Print comparison table."""
    print("\n" + "="*80)
    print(f"POLICY: {policy_name.upper()}")
    print("="*80)
    
    print(f"\n{'Metric':<30} {'OLD System':<25} {'NEW System':<25}")
    print("-"*80)
    
    # Classification
    old_class = old_result.get('classification', 'N/A')
    new_class = new_result.get('classification', 'N/A')
    match = "✅" if old_class == new_class else "⚠️"
    print(f"{'Classification':<30} {str(old_class):<25} {str(new_class):<25} {match}")
    
    # Confidence
    old_conf = old_result.get('confidence', 0.0)
    new_conf = new_result.get('confidence', 0.0)
    print(f"{'Confidence':<30} {f'{old_conf:.1%}':<25} {f'{new_conf:.1%}':<25}")
    
    # Compliance Score
    old_score = old_result.get('compliance_score', 0.0)
    new_score = new_result.get('compliance_score', 0.0)
    print(f"{'Compliance Score':<30} {f'{old_score:.1f}/100':<25} {f'{new_score:.1f}/100':<25}")
    
    # Processing Time
    old_time = old_result.get('time', 0.0)
    new_time = new_result.get('time', 0.0)
    print(f"{'Processing Time':<30} {f'{old_time:.2f}s':<25} {f'{new_time:.2f}s':<25}")
    
    # New system features
    if 'violations' in new_result:
        print(f"{'Violations Found':<30} {'N/A':<25} {str(new_result['violations']):<25}")
    if 'recommendations' in new_result:
        print(f"{'Recommendations':<30} {'N/A':<25} {str(new_result['recommendations']):<25}")
    if 'regulations_used' in new_result:
        print(f"{'Regulations Retrieved':<30} {'N/A':<25} {str(new_result['regulations_used']):<25}")
    
    # Explanations
    print("\n" + "-"*80)
    print("OLD SYSTEM EXPLANATION:")
    print("-"*80)
    old_exp = old_result.get('explanation', 'No explanation provided')
    print(f"{old_exp[:300]}...")
    
    print("\n" + "-"*80)
    print("NEW SYSTEM EXPLANATION (with regulation citations):")
    print("-"*80)
    new_exp = new_result.get('explanation', 'No explanation provided')
    print(f"{new_exp[:500]}...")


async def main():
    """Run comparison on all test policies."""
    print("\n" + "="*80)
    print("SYSTEM COMPARISON: Phase 2 BERT vs RAG + LLaMA")
    print("="*80)
    
    print("\n📋 Test Policies:")
    for name in TEST_POLICIES:
        print(f"   - {name}")
    
    results = {}
    
    for policy_name, policy_text in TEST_POLICIES.items():
        print(f"\n\n{'='*80}")
        print(f"Testing: {policy_name.upper()}")
        print(f"{'='*80}")
        
        try:
            # Run both systems
            old_result = await run_old_system(policy_text)
            new_result = await run_new_system(policy_text)
            
            # Store results
            results[policy_name] = {
                "old": old_result,
                "new": new_result
            }
            
            # Print comparison
            print_comparison(policy_name, old_result, new_result)
            
        except Exception as e:
            logger.error(f"❌ Error testing {policy_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    print("\n📊 Overall Statistics:")
    
    # Agreement rate
    agreements = sum(
        1 for r in results.values() 
        if r['old']['classification'] == r['new']['classification']
    )
    total = len(results)
    print(f"   Classification Agreement: {agreements}/{total} ({agreements/total:.1%})")
    
    # Average times
    avg_old_time = sum(r['old']['time'] for r in results.values()) / total
    avg_new_time = sum(r['new']['time'] for r in results.values()) / total
    print(f"   Average Time (OLD): {avg_old_time:.2f}s")
    print(f"   Average Time (NEW): {avg_new_time:.2f}s")
    print(f"   Speed Difference: {(avg_new_time/avg_old_time):.1f}x")
    
    # Feature comparison
    print("\n✨ NEW System Advantages:")
    print("   ✅ Detailed explanations with regulation citations")
    print("   ✅ Specific violations identified")
    print("   ✅ Actionable recommendations")
    print("   ✅ Interactive chat capability")
    print("   ✅ No labeled training data needed")
    
    print("\n⚡ OLD System Advantages:")
    print("   ✅ Faster inference (simpler model)")
    print("   ✅ Lower resource requirements")
    print("   ✅ Deterministic results")
    
    print("\n💡 Recommendation:")
    print("   Use NEW (RAG + LLaMA) for:")
    print("   - Complex policies requiring deep analysis")
    print("   - Cases needing explanations and citations")
    print("   - Interactive user applications")
    print("   - When regulation updates are frequent")
    
    print("\n   Use OLD (Phase 2 BERT) for:")
    print("   - High-volume batch processing")
    print("   - Simple accept/reject decisions")
    print("   - Resource-constrained environments")
    print("   - When speed is critical")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())
