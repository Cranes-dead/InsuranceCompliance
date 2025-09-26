from updated_compliance_system import RuleBasedComplianceEngine
from src.processing.parsers.document_parser import parse_document
import os

print('🧪 TESTING COMPLETE COMPLIANCE ANALYSIS PIPELINE')
print('=' * 60)

engine = RuleBasedComplianceEngine()
pdf_path = 'test_samples/sample_policy_compliant.pdf'

if os.path.exists(pdf_path):
    # Parse document
    text = parse_document(pdf_path)
    print(f'📄 Parsed document: {len(text)} characters')
    
    # Analyze compliance
    result = engine.classify_policy_text(text)
    
    print(f'🎯 Classification: {result["classification"]}')
    print(f'📊 Confidence: {result["confidence"]:.3f}')
    print(f'📈 Compliance Score: {result["compliance_score"]:.3f}')
    
    print('\n✅ Mandatory Requirements:')
    for req in result['mandatory_compliance']:
        status = '✅' if req.get('compliant', False) else '❌'
        print(f'  {status} {req["rule"]}')
        if req.get('found_amount') and req.get('required_amount'):
            print(f'      Found: Rs {req["found_amount"]/100000:.0f}L, Required: Rs {req["required_amount"]/100000:.0f}L')
    
    if result['recommendations']:
        print('\n💡 Recommendations:')
        for rec in result['recommendations']:
            print(f'  • {rec}')
else:
    print('❌ Sample PDF not found')