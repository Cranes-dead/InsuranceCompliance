"""
Generate sample motor vehicle insurance policies for testing
Creates 3 different policy types: COMPLIANT, NON_COMPLIANT, REQUIRES_REVIEW
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import os

def create_compliant_policy():
    """Create a COMPLIANT motor vehicle insurance policy"""
    
    os.makedirs('test_samples', exist_ok=True)
    doc = SimpleDocTemplate('test_samples/sample_policy_compliant.pdf', pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Header
    story.append(Paragraph('MOTOR VEHICLE INSURANCE POLICY - COMPLIANT SAMPLE', styles['Title']))
    story.append(Spacer(1, 0.2*inch))

    # Policy details
    content = '''
<b>Policy Number:</b> COMP/2025/MV001<br/>
<b>Insured Name:</b> John Doe<br/>
<b>Vehicle Registration:</b> KA01AB1234<br/>
<b>Policy Period:</b> 01/01/2025 to 31/12/2025<br/>
<br/>
<b>COVERAGE DETAILS (IRDAI COMPLIANT):</b><br/>
<br/>
1. <b>Third Party Liability Coverage:</b><br/>
   - Bodily Injury: Rs. 15,00,000 per person (as per IRDAI Motor Tariff)<br/>
   - Property Damage: Rs. 7,50,000 per incident<br/>
   - Legal Liability to Passengers: Rs. 2,00,000 per passenger<br/>
<br/>
2. <b>Personal Accident Coverage for Owner-Driver:</b><br/>
   - Death/Permanent Total Disability: Rs. 15,00,000<br/>
   - Temporary Total Disability: Rs. 750 per week (max 100 weeks)<br/>
   - Medical Expenses: Rs. 50,000<br/>
<br/>
3. <b>Comprehensive Coverage:</b><br/>
   - Own Damage: Rs. 8,50,000 (IDV)<br/>
   - Zero Depreciation Add-on included<br/>
   - Engine Protection Cover included<br/>
<br/>
4. <b>Premium Structure (IRDAI Approved):</b><br/>
   - Base Premium: Rs. 12,500<br/>
   - Add-on Premiums: Rs. 3,200<br/>
   - Service Tax: Rs. 2,826 (18% GST)<br/>
   - Total Premium: Rs. 18,526<br/>
<br/>
<b>REGULATORY COMPLIANCE:</b><br/>
- This policy complies with IRDAI Motor Insurance Regulations 2016<br/>
- Premium rates as per approved IRDAI Motor Tariff<br/>
- All mandatory covers as per Motor Vehicle Act 1988 included<br/>
- Policy documents issued within prescribed timelines<br/>
- Grievance redressal mechanism as per IRDAI guidelines<br/>
<br/>
<b>IMPORTANT NOTES:</b><br/>
- Policy is subject to standard policy terms and conditions<br/>
- Claims must be reported within 30 days of incident<br/>
- Survey required for claims above Rs. 50,000<br/>
- No claim bonus applicable as per IRDAI norms<br/>
'''

    story.append(Paragraph(content, styles['Normal']))
    doc.build(story)
    print('✅ Created: sample_policy_compliant.pdf')

def create_non_compliant_policy():
    """Create a NON_COMPLIANT motor vehicle insurance policy"""
    
    doc = SimpleDocTemplate('test_samples/sample_policy_non_compliant.pdf', pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Header
    story.append(Paragraph('MOTOR VEHICLE INSURANCE POLICY - NON-COMPLIANT SAMPLE', styles['Title']))
    story.append(Spacer(1, 0.2*inch))

    # Policy details
    content = '''
<b>Policy Number:</b> NONC/2025/MV002<br/>
<b>Insured Name:</b> Jane Smith<br/>
<b>Vehicle Registration:</b> MH12CD5678<br/>
<b>Policy Period:</b> 15/03/2025 to 14/03/2026<br/>
<br/>
<b>COVERAGE DETAILS (REGULATORY VIOLATIONS):</b><br/>
<br/>
1. <b>Third Party Liability Coverage:</b><br/>
   - Bodily Injury: Rs. 5,00,000 per person (BELOW IRDAI MINIMUM)<br/>
   - Property Damage: Rs. 2,00,000 per incident (INSUFFICIENT)<br/>
   - Legal Liability to Passengers: NOT INCLUDED (MANDATORY MISSING)<br/>
<br/>
2. <b>Personal Accident Coverage:</b><br/>
   - PERSONAL ACCIDENT COVER FOR OWNER-DRIVER NOT INCLUDED<br/>
   - This violates Motor Vehicle Act 1988 mandatory requirements<br/>
<br/>
3. <b>Own Damage Coverage:</b><br/>
   - Own Damage: Rs. 6,00,000 (IDV)<br/>
   - Basic coverage only, no add-ons<br/>
<br/>
4. <b>Premium Structure (NON-STANDARD):</b><br/>
   - Base Premium: Rs. 8,500 (BELOW IRDAI RATES)<br/>
   - Discount Applied: 25% (EXCEEDS PERMITTED LIMITS)<br/>
   - Service Tax: Rs. 1,147 (13.5% - INCORRECT TAX RATE)<br/>
   - Total Premium: Rs. 7,647<br/>
<br/>
<b>REGULATORY VIOLATIONS:</b><br/>
- Third party liability limits below IRDAI Motor Tariff requirements<br/>
- Missing mandatory Personal Accident Coverage for owner-driver<br/>
- Premium rates below IRDAI approved minimum rates<br/>
- Excessive discount percentage violating tariff guidelines<br/>
- Incorrect service tax calculation (should be 18% GST)<br/>
- No legal liability to passenger coverage<br/>
<br/>
<b>WARNING:</b><br/>
- This policy does not meet regulatory requirements<br/>
- May not provide adequate legal compliance<br/>
- Claims may be disputed due to insufficient coverage<br/>
- Policy may be subject to regulatory action<br/>
'''

    story.append(Paragraph(content, styles['Normal']))
    doc.build(story)
    print('✅ Created: sample_policy_non_compliant.pdf')

def create_requires_review_policy():
    """Create a REQUIRES_REVIEW motor vehicle insurance policy"""
    
    doc = SimpleDocTemplate('test_samples/sample_policy_requires_review.pdf', pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Header
    story.append(Paragraph('MOTOR VEHICLE INSURANCE POLICY - REVIEW REQUIRED', styles['Title']))
    story.append(Spacer(1, 0.2*inch))

    # Policy details
    content = '''
<b>Policy Number:</b> REV/2025/MV003<br/>
<b>Insured Name:</b> Rajesh Kumar<br/>
<b>Vehicle Registration:</b> DL05EF9012<br/>
<b>Policy Period:</b> 01/07/2025 to 30/06/2026<br/>
<br/>
<b>COVERAGE DETAILS (REQUIRES CLARIFICATION):</b><br/>
<br/>
1. <b>Third Party Liability Coverage:</b><br/>
   - Bodily Injury: Rs. 15,00,000 per person<br/>
   - Property Damage: Rs. 7,50,000 per incident<br/>
   - Legal Liability: Rs. 2,00,000 per passenger (coverage details unclear)<br/>
<br/>
2. <b>Personal Accident Coverage:</b><br/>
   - Coverage Amount: Rs. 15,00,000 (meets minimum requirements)<br/>
   - Medical Expenses: Rs. 50,000<br/>
   - Scope of coverage needs verification for commercial use<br/>
<br/>
3. <b>Commercial Vehicle Usage:</b><br/>
   - Vehicle used for ride-sharing services (Ola/Uber)<br/>
   - Commercial use endorsement status unclear<br/>
   - May require additional commercial vehicle insurance<br/>
<br/>
4. <b>Premium Structure:</b><br/>
   - Base Premium: Rs. 15,000<br/>
   - Commercial Use Surcharge: Rs. 4,500 (rate verification needed)<br/>
   - Service Tax: Rs. 3,510 (18% GST)<br/>
   - Total Premium: Rs. 23,010<br/>
<br/>
5. <b>Geographic Coverage:</b><br/>
   - Coverage extends to neighboring states<br/>
   - Inter-state permit requirements need verification<br/>
   - Road tax compliance for multiple states unclear<br/>
<br/>
<b>AREAS REQUIRING REVIEW:</b><br/>
- Commercial vehicle usage classification and appropriate coverage<br/>
- Premium calculation for ride-sharing services<br/>
- Compliance with transport department regulations<br/>
- Verification of vehicle modification permissions<br/>
- Multi-state operation permit requirements<br/>
- Driver licensing requirements for commercial operation<br/>
<br/>
<b>ADDITIONAL CONSIDERATIONS:</b><br/>
- Policy may need endorsement for commercial use<br/>
- State-specific regulations may apply<br/>
- Platform-specific insurance requirements (Ola/Uber policies)<br/>
- Driver background verification requirements<br/>
- Vehicle safety inspection compliance<br/>
<br/>
<b>RECOMMENDATION:</b><br/>
This policy requires detailed review by underwriting team to ensure<br/>
proper classification and compliance with commercial vehicle regulations.<br/>
'''

    story.append(Paragraph(content, styles['Normal']))
    doc.build(story)
    print('✅ Created: sample_policy_requires_review.pdf')

if __name__ == "__main__":
    print("🚗 Generating Motor Vehicle Insurance Policy Samples")
    print("=" * 55)
    
    create_compliant_policy()
    create_non_compliant_policy()
    create_requires_review_policy()
    
    print("\n🎉 All sample policies generated successfully!")
    print("📂 Files created in: test_samples/ directory")
    print("\nFiles for testing:")
    print("1. sample_policy_compliant.pdf (Expected: COMPLIANT)")
    print("2. sample_policy_non_compliant.pdf (Expected: NON_COMPLIANT)")  
    print("3. sample_policy_requires_review.pdf (Expected: REQUIRES_REVIEW)")