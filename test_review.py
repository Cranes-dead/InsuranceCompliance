from updated_compliance_system import RuleBasedComplianceEngine
from src.processing.parsers.document_parser import parse_document

engine = RuleBasedComplianceEngine()
text = parse_document('test_samples/sample_policy_requires_review.pdf')
print('📄 REQUIRES REVIEW SAMPLE TEST')
print('=' * 40)

result = engine.classify_policy_text(text)

print(f'Classification: {result["classification"]}')
print(f'Confidence: {result["confidence"]:.3f}')
print(f'Score: {result["compliance_score"]:.3f}')