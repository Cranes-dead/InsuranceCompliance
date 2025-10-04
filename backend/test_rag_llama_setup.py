"""Test script for RAG + LLaMA system setup and initialization.

This script:
1. Tests Legal-BERT embedding generation
2. Indexes regulations into ChromaDB
3. Tests regulation retrieval
4. Tests LLaMA connectivity (Ollama)
5. Runs a sample compliance analysis
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.ml.rag import RegulationVectorStore, RegulationRetriever
from app.ml.llm import LLaMAComplianceEngine, LLMConfig
from app.ml.rag_llama_service import RAGLLaMAComplianceService
from app.core.config import settings

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_vector_store():
    """Test 1: Vector Store Setup"""
    print("\n" + "="*70)
    print("TEST 1: Legal-BERT Vector Store")
    print("="*70)
    
    try:
        store = RegulationVectorStore()
        await store.initialize()
        
        # Index regulations
        print("\n📊 Indexing regulations...")
        stats = await store.index_regulations(force_reindex=False)
        print(f"✅ Indexed: {stats}")
        
        # Test retrieval
        print("\n🔍 Testing retrieval...")
        test_query = "third party liability motor vehicle insurance coverage"
        results = await store.retrieve(query=test_query, top_k=3)
        
        print(f"\n📋 Top 3 regulations for: '{test_query}'")
        for i, reg in enumerate(results, 1):
            print(f"\n{i}. Similarity: {reg['distance']:.4f}")
            print(f"   Source: {reg['metadata']['source']}")
            print(f"   Text: {reg['text'][:150]}...")
        
        print("\n✅ Vector store test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Vector store test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_llama_connection():
    """Test 2: LLaMA Connectivity"""
    print("\n" + "="*70)
    print("TEST 2: LLaMA Engine Connection")
    print("="*70)
    
    print("\nℹ️  Make sure Ollama is running: ollama serve")
    print("ℹ️  And model is pulled: ollama pull llama3.1:8b")
    
    try:
        # Test Ollama (local)
        print("\n🤖 Testing Ollama connection...")
        config = LLMConfig(provider="ollama", model="llama3.1:8b")
        engine = LLaMAComplianceEngine(config=config)
        await engine.initialize()
        
        # Simple test query
        test_prompt = "What is insurance compliance? Answer in one sentence."
        print(f"\n💬 Test query: {test_prompt}")
        
        from app.ml.llm.llama_engine import OllamaProvider
        provider = OllamaProvider(config)
        response = await provider.generate(test_prompt, temperature=0.1)
        
        print(f"✅ Response: {response[:200]}...")
        print("\n✅ LLaMA connection test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ LLaMA connection test FAILED: {e}")
        print("\n⚠️  Solutions:")
        print("   1. Install Ollama: https://ollama.ai")
        print("   2. Run: ollama serve")
        print("   3. Pull model: ollama pull llama3.1:8b")
        print("\n   Or use API provider (Groq) instead - see docs")
        return False


async def test_integrated_analysis():
    """Test 3: Full RAG + LLaMA Analysis"""
    print("\n" + "="*70)
    print("TEST 3: Integrated RAG + LLaMA Analysis")
    print("="*70)
    
    try:
        # Initialize service
        print("\n🚀 Initializing RAG + LLaMA service...")
        service = RAGLLaMAComplianceService()
        await service.initialize()
        
        # Sample policy text
        sample_policy = """
        MOTOR VEHICLE INSURANCE POLICY
        
        Coverage: This policy provides third-party liability coverage for motor vehicles.
        
        Coverage Limits:
        - Property damage: Up to Rs. 50,000
        - Bodily injury: As per Motor Vehicles Act
        
        Exclusions:
        - Damage caused while driving under influence of alcohol
        - Use for racing or speed testing
        - Damage to driver's own vehicle (not covered under third-party)
        
        Premium: Rs. 2,500 annually
        
        Terms: Policy valid for 12 months from issue date.
        """
        
        print("\n📄 Sample policy:")
        print(sample_policy[:300] + "...")
        
        # Analyze
        print("\n🔍 Running compliance analysis...")
        result = await service.analyze_policy(
            policy_text=sample_policy,
            policy_metadata={"filename": "test_policy.pdf"},
            top_k_regulations=2  # Reduced to 2 for faster test
        )
        
        print("\n" + "="*70)
        print("ANALYSIS RESULTS")
        print("="*70)
        print(f"Classification: {result.get('classification')}")
        print(f"Confidence: {result.get('confidence', 0):.2%}")
        print(f"Compliance Score: {result.get('compliance_score', 0):.1f}/100")
        
        print(f"\n📊 RAG Metadata:")
        rag_meta = result.get('rag_metadata', {})
        print(f"   Regulations Retrieved: {rag_meta.get('regulations_retrieved')}")
        print(f"   Top Sources: {', '.join(rag_meta.get('top_regulation_sources', [])[:3])}")
        
        violations = result.get('violations', [])
        if violations:
            print(f"\n⚠️  Violations Found: {len(violations)}")
            for i, v in enumerate(violations[:3], 1):
                print(f"   {i}. [{v.get('severity')}] {v.get('description')[:100]}...")
        
        print(f"\n💡 Explanation:")
        explanation = result.get('explanation', 'No explanation')
        print(f"   {explanation[:300]}...")
        
        recommendations = result.get('recommendations', [])
        if recommendations:
            print(f"\n✅ Recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"   {i}. {rec[:100]}...")
        
        print("\n✅ Integrated analysis test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Integrated analysis test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("RAG + LLaMA SYSTEM TEST SUITE")
    print("="*70)
    
    results = []
    
    # Test 1: Vector Store
    results.append(("Vector Store", await test_vector_store()))
    
    # Test 2: LLaMA Connection
    results.append(("LLaMA Engine", await test_llama_connection()))
    
    # Test 3: Integrated Analysis (only if previous tests passed)
    if all(r[1] for r in results):
        results.append(("Full Analysis", await test_integrated_analysis()))
    else:
        print("\n⏭️  Skipping integrated test due to previous failures")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 All tests PASSED! System is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check errors above and:")
        print("   1. Ensure Ollama is running (ollama serve)")
        print("   2. Ensure model is pulled (ollama pull llama3.1:8b)")
        print("   3. Check that Legal-BERT model exists")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
