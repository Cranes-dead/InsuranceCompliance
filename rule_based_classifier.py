"""
Simple rule-based compliance classifier for immediate use
This provides reliable predictions while you collect more training data
"""

import re
import os

class RuleBasedComplianceClassifier:
    def __init__(self):
        # Define keyword patterns for each class
        self.compliant_patterns = [
            (r'third party.*15.*lakh|15.*lakh.*third party', 2),
            (r'personal accident.*15.*lakh|15.*lakh.*personal accident', 2),
            (r'irdai.*compliant|compliant.*irdai', 2),
            (r'mandatory.*coverage.*included|includes.*mandatory.*coverage', 1),
            (r'approved.*premium|premium.*approved', 1),
            (r'regulatory.*compliance|compliance.*regulatory', 1),
            (r'motor vehicle act.*1988', 1),
            (r'proper.*documentation', 1)
        ]
        
        self.non_compliant_patterns = [
            (r'insufficient.*coverage|inadequate.*coverage', 3),
            (r'below.*minimum|less than.*required', 2),
            (r'lacks.*mandatory|missing.*mandatory|no.*personal accident', 3),
            (r'violates|violation|non-compliant', 3),
            (r'third party.*[2-9].*lakh|[2-9].*lakh.*third party', 2),  # Below 10 lakh
            (r'below.*irdai|insufficient.*irdai', 2),
            (r'incorrect.*tax|wrong.*gst', 1),
            (r'excessive.*discount', 1)
        ]
        
        self.review_patterns = [
            (r'requires.*review|needs.*review|review.*required', 3),
            (r'commercial.*vehicle|ride.*sharing|uber|ola', 2),
            (r'multi.*state|transport.*permit', 2),
            (r'needs.*verification|requires.*clarification', 2),
            (r'unclear|ambiguous|complex', 1),
            (r'classification.*unclear', 2)
        ]
    
    def preprocess_text(self, text):
        """Clean and normalize text"""
        text = text.lower()
        # Normalize currency amounts
        text = re.sub(r'rs\.?\s*(\d+),(\d+),(\d+)', r'rs \1\2\3', text)
        text = re.sub(r'rs\.?\s*(\d+)\s*lakh', r'rs \1 lakh', text)
        return text
    
    def calculate_scores(self, text):
        """Calculate scores for each class based on pattern matching"""
        text = self.preprocess_text(text)
        
        compliant_score = 0
        non_compliant_score = 0  
        review_score = 0
        
        # Check compliant patterns
        for pattern, weight in self.compliant_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                compliant_score += weight
        
        # Check non-compliant patterns  
        for pattern, weight in self.non_compliant_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                non_compliant_score += weight
                
        # Check review patterns
        for pattern, weight in self.review_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                review_score += weight
        
        return compliant_score, non_compliant_score, review_score
    
    def predict(self, text):
        """Predict compliance classification"""
        compliant_score, non_compliant_score, review_score = self.calculate_scores(text)
        
        # Decision logic
        total_score = compliant_score + non_compliant_score + review_score
        
        if total_score == 0:
            # Default for unclear cases
            return 'REQUIRES_REVIEW', 0.5
        
        # Find the winning class
        scores = {
            'COMPLIANT': compliant_score,
            'NON_COMPLIANT': non_compliant_score,
            'REQUIRES_REVIEW': review_score
        }
        
        predicted_class = max(scores, key=scores.get)
        max_score = scores[predicted_class]
        
        # Calculate confidence based on score margin
        confidence = min(0.95, 0.6 + (max_score / (total_score + 1)) * 0.35)
        
        return predicted_class, confidence
    
    def predict_batch(self, texts):
        """Predict for multiple texts"""
        results = []
        for text in texts:
            classification, confidence = self.predict(text)
            results.append({
                'classification': classification,
                'confidence': confidence
            })
        return results

def test_rule_based_classifier():
    """Test the rule-based classifier"""
    print("🧪 TESTING RULE-BASED COMPLIANCE CLASSIFIER")
    print("=" * 50)
    
    classifier = RuleBasedComplianceClassifier()
    
    test_cases = [
        ("COMPLIANT Policy", '''
        Motor vehicle insurance policy with comprehensive third party liability coverage 
        of Rs 15 lakh per person as mandated by IRDAI Motor Tariff guidelines. 
        Personal accident coverage of Rs 15 lakh for owner-driver is included. 
        Premium rates follow IRDAI approved structure with proper GST calculation.
        This policy complies with Motor Vehicle Act 1988 requirements.
        '''),
        
        ("NON_COMPLIANT Policy", '''
        Motor insurance policy with third party liability coverage of Rs 5 lakh per person 
        which is below IRDAI minimum requirement of Rs 15 lakh. 
        No personal accident coverage for owner-driver is included. 
        This policy violates regulatory requirements and has insufficient coverage.
        Premium rates are below approved minimums.
        '''),
        
        ("REQUIRES_REVIEW Policy", '''
        Commercial vehicle insurance policy for ride-sharing services like Uber. 
        Multi-state operation requires verification of transport permits. 
        Premium calculation for commercial use needs review and clarification.
        Vehicle classification requires review for proper regulatory compliance.
        ''')
    ]
    
    for test_name, text in test_cases:
        prediction, confidence = classifier.predict(text.strip())
        scores = classifier.calculate_scores(text.strip())
        
        print(f"\n{test_name}:")
        print(f"  Prediction: {prediction}")
        print(f"  Confidence: {confidence:.3f}")
        print(f"  Scores (C/NC/R): {scores}")
    
    return classifier

if __name__ == "__main__":
    classifier = test_rule_based_classifier()
    
    # Save for use in API
    import joblib
    os.makedirs('models/rule_based_compliance', exist_ok=True)
    joblib.dump(classifier, 'models/rule_based_compliance/classifier.pkl')
    
    print(f"\n💾 Rule-based classifier saved to: models/rule_based_compliance/")
    print("\n🎉 Rule-Based Compliance Classifier Ready!")
    print("This provides reliable predictions while you collect more training data.")