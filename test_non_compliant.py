from updated_compliance_system import RuleBasedComplianceEngine
from src.processing.parsers.document_parser import parse_document
import os

engine = RuleBasedComplianceEngine()
pdf_path = 'test_samples/sample_policy_non_compliant.pdf'

if os.path.exists(pdf_path):
    text = parse_document(pdf_path)
    print('📄 NON-COMPLIANT SAMPLE TEST')
    print('=' * 40)
    
    result = engine.classify_policy_text(text)
    
    print(f'🎯 Classification: {result["classification"]}')
    print(f'📊 Confidence: {result["confidence"]:.3f}')
    print(f'📈 Compliance Score: {result["compliance_score"]:.3f}')
    
    print('\nMandatory Requirements:')
    for req in result['mandatory_compliance']:
        status = '✅' if req.get('compliant', False) else '❌'
        print(f'  {status} {req["rule"]}')
        if req.get('found_amount') and req.get('required_amount'):
            print(f'      Found: Rs {req["found_amount"]/100000:.0f}L, Required: Rs {req["required_amount"]/100000:.0f}L')
    
    if result['violations']:
        print('\nViolations:')
        for violation in result['violations']:
            print(f'  ⚠️ {violation["description"]}')
    
    if result['recommendations']:
        print('\nRecommendations:')
        for rec in result['recommendations']:
            print(f'  💡 {rec}')
else:
    print('❌ Non-compliant sample PDF not found')