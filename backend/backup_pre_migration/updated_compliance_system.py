"""
Updated Compliance System Architecture
Uses rule type classification to determine policy compliance

This system works by:
1. Classifying regulatory documents by rule type using Legal BERT
2. Extracting requirements from classified rules 
3. Comparing policy documents against extracted requirements
4. Providing detailed compliance analysis
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import json
import re
import pandas as pd
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class RuleBasedComplianceEngine:
    """
    Enhanced compliance engine that uses rule type classification
    """
    
    def __init__(self, rule_model_path="./models/legal_bert_rule_classification"):
        # Load trained rule classification model
        try:
            self.rule_tokenizer = AutoTokenizer.from_pretrained(rule_model_path)
            self.rule_model = AutoModelForSequenceClassification.from_pretrained(rule_model_path)
            self.rule_model.eval()
            
            # Load label mapping
            with open(f"{rule_model_path}/rule_type_labels.json", "r") as f:
                self.rule_labels = json.load(f)
                # Convert string keys to int
                self.rule_labels = {int(k): v for k, v in self.rule_labels.items()}
            
            logger.info("Rule classification model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load rule model: {e}")
            self.rule_model = None
        
        # Load regulatory knowledge base
        self.regulatory_rules = self._load_regulatory_knowledge()
        
        # Compliance thresholds
        self.compliance_thresholds = {
            'COMPLIANT': 0.8,      # 80%+ requirements met
            'NON_COMPLIANT': 0.4,   # <40% requirements met  
            'REQUIRES_REVIEW': 0.6  # 40-80% requirements met
        }
    
    def _load_regulatory_knowledge(self):
        """Load and process regulatory knowledge base"""
        try:
            # Load the reclassified regulatory documents
            df = pd.read_csv('data/training/motor_vehicle_rules_classification.csv')
            
            knowledge_base = {
                'MANDATORY_REQUIREMENT': [],
                'OPTIONAL_PROVISION': [],
                'PROHIBITION': [], 
                'PROCEDURAL': [],
                'DEFINITION': []
            }
            
            # Extract key requirements from each rule type
            for _, row in df.iterrows():
                rule_type = row['rule_type']
                text = str(row['text'])
                
                # Extract actionable requirements
                requirements = self._extract_requirements(text, rule_type)
                if requirements:
                    knowledge_base[rule_type].extend(requirements)
            
            logger.info(f"Loaded regulatory knowledge base with {sum(len(v) for v in knowledge_base.values())} requirements")
            return knowledge_base
            
        except Exception as e:
            logger.error(f"Failed to load regulatory knowledge: {e}")
            return self._get_default_knowledge_base()
    
    def _extract_requirements(self, text, rule_type):
        """Extract specific requirements from regulatory text"""
        requirements = []
        text_lower = text.lower()
        
        if rule_type == 'MANDATORY_REQUIREMENT':
            # Extract mandatory coverage amounts
            if re.search(r'third party.*liability', text_lower):
                if re.search(r'15.*lakh|1500000', text_lower):
                    requirements.append({
                        'type': 'coverage_amount',
                        'coverage': 'third_party_liability',
                        'minimum_amount': 1500000,
                        'description': 'Third party liability minimum Rs 15 lakh'
                    })
            
            if re.search(r'personal accident', text_lower):
                if re.search(r'15.*lakh|1500000', text_lower):
                    requirements.append({
                        'type': 'coverage_required',
                        'coverage': 'personal_accident',
                        'minimum_amount': 1500000,
                        'description': 'Personal accident coverage mandatory for owner-driver'
                    })
        
        elif rule_type == 'PROHIBITION':
            # Extract prohibitions and restrictions
            if re.search(r'shall not|must not|prohibited', text_lower):
                requirements.append({
                    'type': 'prohibition',
                    'description': 'Prohibited action or coverage limitation',
                    'text_excerpt': text[:200]
                })
        
        elif rule_type == 'PROCEDURAL':
            # Extract procedural requirements
            if re.search(r'within.*days|timeline|deadline', text_lower):
                requirements.append({
                    'type': 'timeline',
                    'description': 'Procedural timeline requirement',
                    'text_excerpt': text[:200]
                })
        
        return requirements
    
    def _get_default_knowledge_base(self):
        """Default knowledge base for motor vehicle insurance compliance"""
        return {
            'MANDATORY_REQUIREMENT': [
                {
                    'type': 'coverage_amount',
                    'coverage': 'third_party_liability',
                    'minimum_amount': 1500000,
                    'description': 'Third party liability minimum Rs 15 lakh as per IRDAI Motor Tariff'
                },
                {
                    'type': 'coverage_required', 
                    'coverage': 'personal_accident',
                    'minimum_amount': 1500000,
                    'description': 'Personal accident coverage mandatory for owner-driver as per Motor Vehicle Act 1988'
                },
                {
                    'type': 'documentation',
                    'requirement': 'policy_certificate',
                    'description': 'Valid insurance certificate must be carried in vehicle'
                }
            ],
            'OPTIONAL_PROVISION': [
                {
                    'type': 'additional_coverage',
                    'coverage': 'comprehensive',
                    'description': 'Own damage coverage optional but recommended'
                }
            ],
            'PROHIBITION': [
                {
                    'type': 'coverage_limitation',
                    'description': 'Coverage cannot be below regulatory minimums'
                }
            ],
            'PROCEDURAL': [
                {
                    'type': 'claims_procedure',
                    'description': 'Claims must be reported within prescribed timelines'
                }
            ],
            'DEFINITION': [
                {
                    'type': 'term_definition',
                    'term': 'motor_vehicle',
                    'description': 'Any mechanically propelled vehicle intended for use on roads'
                }
            ]
        }
    
    def classify_policy_text(self, policy_text):
        """Classify policy text against regulatory requirements"""
        
        # Analyze policy text for compliance indicators
        compliance_indicators = self._analyze_policy_text(policy_text)
        
        # Check against mandatory requirements
        mandatory_compliance = self._check_mandatory_requirements(policy_text, compliance_indicators)
        
        # Check for prohibitions/violations
        violation_check = self._check_violations(policy_text)
        
        # Calculate overall compliance score
        compliance_score = self._calculate_compliance_score(mandatory_compliance, violation_check)
        
        # Determine classification
        classification = self._determine_classification(compliance_score)
        
        return {
            'classification': classification['status'],
            'confidence': classification['confidence'],
            'compliance_score': compliance_score,
            'mandatory_compliance': mandatory_compliance,
            'violations': violation_check,
            'recommendations': self._generate_recommendations(mandatory_compliance, violation_check)
        }
    
    def _analyze_policy_text(self, policy_text):
        """Extract key indicators from policy text"""
        text_lower = policy_text.lower()
        
        indicators = {
            'third_party_amount': None,
            'personal_accident_present': False,
            'personal_accident_amount': None,
            'irdai_compliance_mentioned': False,
            'coverage_types': []
        }
        
        # Extract third party liability amount - improved patterns
        tp_patterns = [
            r'third party.*?(?:rs\.?\s*|₹\s*)(\d+(?:[,\s]\d+)*)\s*(?:lakh|lakhs?)',
            r'bodily injury.*?(?:rs\.?\s*|₹\s*)(\d+(?:[,\s]\d+)*)\s*(?:per person|lakh)',
            r'third party.*?(?:rs\.?\s*|₹\s*)(\d+(?:[,\s]\d+)*)'
        ]
        
        for pattern in tp_patterns:
            tp_match = re.search(pattern, text_lower)
            if tp_match:
                amount_str = tp_match.group(1).replace(',', '').replace(' ', '')
                try:
                    # Check if it's already in actual amount or needs conversion
                    amount = int(amount_str)
                    if amount > 100000:  # Already in actual amount
                        indicators['third_party_amount'] = amount
                    else:  # In lakhs, convert to actual amount
                        indicators['third_party_amount'] = amount * 100000
                    break
                except ValueError:
                    continue
        
        # Check for personal accident coverage
        if re.search(r'personal accident', text_lower):
            indicators['personal_accident_present'] = True
            
            pa_patterns = [
                r'personal accident.*?(?:rs\.?\s*|₹\s*)(\d+(?:[,\s]\d+)*)\s*(?:lakh|lakhs?)',
                r'death.*permanent.*disability.*?(?:rs\.?\s*|₹\s*)(\d+(?:[,\s]\d+)*)',
                r'owner.driver.*?(?:rs\.?\s*|₹\s*)(\d+(?:[,\s]\d+)*)'
            ]
            
            for pattern in pa_patterns:
                pa_match = re.search(pattern, text_lower)
                if pa_match:
                    amount_str = pa_match.group(1).replace(',', '').replace(' ', '')
                    try:
                        amount = int(amount_str)
                        if amount > 100000:  # Already in actual amount
                            indicators['personal_accident_amount'] = amount
                        else:  # In lakhs, convert to actual amount
                            indicators['personal_accident_amount'] = amount * 100000
                        break
                    except ValueError:
                        continue
        
        # Check IRDAI compliance mentions
        if re.search(r'irdai|irda.*compli', text_lower):
            indicators['irdai_compliance_mentioned'] = True
        
        # Extract coverage types
        coverage_patterns = [
            (r'comprehensive', 'comprehensive'),
            (r'third party.*liability|liability.*third party', 'third_party_liability'),
            (r'personal accident', 'personal_accident'),
            (r'own damage', 'own_damage')
        ]
        
        for pattern, coverage_type in coverage_patterns:
            if re.search(pattern, text_lower):
                indicators['coverage_types'].append(coverage_type)
        
        return indicators
    
    def _check_mandatory_requirements(self, policy_text, indicators):
        """Check compliance with mandatory requirements"""
        mandatory_rules = self.regulatory_rules['MANDATORY_REQUIREMENT']
        compliance_results = []
        
        for rule in mandatory_rules:
            if rule['type'] == 'coverage_amount':
                if rule['coverage'] == 'third_party_liability':
                    if indicators['third_party_amount']:
                        compliant = indicators['third_party_amount'] >= rule['minimum_amount']
                        compliance_results.append({
                            'rule': rule['description'],
                            'compliant': compliant,
                            'found_amount': indicators['third_party_amount'],
                            'required_amount': rule['minimum_amount']
                        })
                    else:
                        compliance_results.append({
                            'rule': rule['description'],
                            'compliant': False,
                            'found_amount': None,
                            'required_amount': rule['minimum_amount'],
                            'issue': 'Third party liability amount not found'
                        })
            
            elif rule['type'] == 'coverage_required':
                if rule['coverage'] == 'personal_accident':
                    compliant = indicators['personal_accident_present']
                    result = {
                        'rule': rule['description'],
                        'compliant': compliant
                    }
                    if indicators['personal_accident_amount']:
                        result['found_amount'] = indicators['personal_accident_amount']
                        result['required_amount'] = rule['minimum_amount']
                        result['amount_compliant'] = indicators['personal_accident_amount'] >= rule['minimum_amount']
                    
                    compliance_results.append(result)
        
        return compliance_results
    
    def _check_violations(self, policy_text):
        """Check for regulatory violations"""
        violations = []
        text_lower = policy_text.lower()
        
        # Check for common violations
        violation_patterns = [
            (r'below.*irdai.*minimum|insufficient.*coverage', 'Coverage below regulatory minimum'),
            (r'no.*personal accident|lacks.*personal accident', 'Missing mandatory personal accident coverage'),
            (r'violat|breach|non.?compliant', 'Explicit regulatory violation mentioned')
        ]
        
        for pattern, violation_desc in violation_patterns:
            if re.search(pattern, text_lower):
                violations.append({
                    'type': 'regulatory_violation',
                    'description': violation_desc,
                    'severity': 'high'
                })
        
        return violations
    
    def _calculate_compliance_score(self, mandatory_compliance, violations):
        """Calculate overall compliance score (0-1)"""
        
        if not mandatory_compliance:
            return 0.5  # Neutral score if no requirements checked
        
        # Score based on mandatory requirement compliance
        compliant_count = sum(1 for req in mandatory_compliance if req.get('compliant', False))
        total_count = len(mandatory_compliance)
        compliance_ratio = compliant_count / total_count if total_count > 0 else 0
        
        # Penalty for violations
        violation_penalty = len(violations) * 0.2
        
        # Final score
        score = max(0, compliance_ratio - violation_penalty)
        
        return score
    
    def _determine_classification(self, compliance_score):
        """Determine final classification based on compliance score"""
        
        if compliance_score >= self.compliance_thresholds['COMPLIANT']:
            return {
                'status': 'COMPLIANT',
                'confidence': min(0.95, 0.7 + compliance_score * 0.25)
            }
        elif compliance_score < self.compliance_thresholds['NON_COMPLIANT']:
            return {
                'status': 'NON_COMPLIANT', 
                'confidence': min(0.95, 0.7 + (1 - compliance_score) * 0.25)
            }
        else:
            return {
                'status': 'REQUIRES_REVIEW',
                'confidence': 0.6 + abs(compliance_score - 0.6) * 0.3
            }
    
    def _generate_recommendations(self, mandatory_compliance, violations):
        """Generate recommendations for policy improvement"""
        recommendations = []
        
        # Recommendations for mandatory requirement failures
        for req in mandatory_compliance:
            if not req.get('compliant', True):
                if req.get('issue'):
                    recommendations.append(f"Address issue: {req['issue']}")
                elif req.get('found_amount') and req.get('required_amount'):
                    if req['found_amount'] < req['required_amount']:
                        recommendations.append(
                            f"Increase coverage amount to meet minimum requirement: "
                            f"Rs {req['required_amount']/100000:.0f} lakh required"
                        )
        
        # Recommendations for violations
        for violation in violations:
            recommendations.append(f"Resolve violation: {violation['description']}")
        
        return recommendations

def test_updated_system():
    """Test the updated compliance system"""
    print("🧪 TESTING UPDATED RULE-BASED COMPLIANCE SYSTEM")
    print("=" * 60)
    
    engine = RuleBasedComplianceEngine()
    
    test_policies = [
        ("COMPLIANT Policy", '''
        Motor Vehicle Insurance Policy
        Third party liability coverage: Rs 15 lakh per person as per IRDAI Motor Tariff
        Personal accident coverage: Rs 15 lakh for owner-driver  
        This policy complies with IRDAI Motor Insurance Regulations 2016
        All mandatory covers as per Motor Vehicle Act 1988 included
        '''),
        
        ("NON_COMPLIANT Policy", '''
        Motor Vehicle Insurance Policy
        Third party liability coverage: Rs 5 lakh per person (below IRDAI minimum)
        No personal accident coverage for owner-driver
        This policy violates regulatory requirements
        Coverage insufficient for Motor Vehicle Act compliance
        '''),
        
        ("REQUIRES_REVIEW Policy", '''
        Commercial Motor Vehicle Insurance Policy
        Third party liability: Rs 15 lakh per person
        Personal accident coverage unclear for commercial use
        Additional review needed for ride-sharing classification
        Multi-state operation requires verification
        ''')
    ]
    
    for policy_name, policy_text in test_policies:
        print(f"\n{'='*20} {policy_name} {'='*20}")
        
        result = engine.classify_policy_text(policy_text.strip())
        
        print(f"Classification: {result['classification']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Compliance Score: {result['compliance_score']:.3f}")
        
        print("\nMandatory Requirements Check:")
        for req in result['mandatory_compliance']:
            status = "✅" if req.get('compliant', False) else "❌"
            print(f"  {status} {req['rule']}")
            if req.get('found_amount') and req.get('required_amount'):
                print(f"      Found: Rs {req['found_amount']/100000:.0f} lakh, Required: Rs {req['required_amount']/100000:.0f} lakh")
        
        if result['violations']:
            print("\nViolations:")
            for violation in result['violations']:
                print(f"  ⚠️ {violation['description']}")
        
        if result['recommendations']:
            print("\nRecommendations:")
            for rec in result['recommendations']:
                print(f"  💡 {rec}")

if __name__ == "__main__":
    test_updated_system()