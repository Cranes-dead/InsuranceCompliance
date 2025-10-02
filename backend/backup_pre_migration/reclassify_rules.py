"""
Rule Type Classification Framework for Motor Vehicle Insurance Regulations
Based on analysis of scraped regulatory documents from IRDAI, MoRTH, and related sources
"""

import pandas as pd
import re
import numpy as np

class RuleTypeClassifier:
    """
    Classifies regulatory text into rule types based on linguistic patterns
    """
    
    def __init__(self):
        # Define rule type classification framework
        self.rule_types = {
            'MANDATORY_REQUIREMENT': {
                'description': 'Rules that specify mandatory requirements, obligations, or must-have provisions',
                'patterns': [
                    r'\b(must|shall|required|mandatory|obligatory|compulsory)\b',
                    r'\b(minimum|maximum|not less than|not more than|at least)\b',
                    r'\b(coverage.*required|required.*coverage)\b',
                    r'\b(liability.*minimum|minimum.*liability)\b',
                    r'\b(shall be|must be|required to be)\b'
                ],
                'keywords': ['mandatory', 'required', 'must', 'shall', 'minimum', 'maximum', 'obligatory', 'compulsory']
            },
            
            'OPTIONAL_PROVISION': {
                'description': 'Rules that specify optional provisions, recommendations, or may-have features',
                'patterns': [
                    r'\b(may|can|optional|recommended|suggested)\b',
                    r'\b(additional.*coverage|coverage.*additional)\b',
                    r'\b(add-on|rider|extension)\b',
                    r'\b(discretionary|at the option of)\b',
                    r'\b(subject to|provided that)\b'
                ],
                'keywords': ['may', 'optional', 'recommended', 'additional', 'add-on', 'discretionary']
            },
            
            'PROHIBITION': {
                'description': 'Rules that specify prohibitions, restrictions, or forbidden actions',
                'patterns': [
                    r'\b(shall not|must not|cannot|prohibited|forbidden|restricted)\b',
                    r'\b(no.*shall|not.*permitted|not.*allowed)\b',
                    r'\b(violation|breach|contravention)\b',
                    r'\b(penalty|fine|punishment)\b',
                    r'\b(exclude|exclusion|except|exemption)\b'
                ],
                'keywords': ['prohibited', 'forbidden', 'shall not', 'cannot', 'violation', 'penalty', 'restricted']
            },
            
            'PROCEDURAL': {
                'description': 'Rules about procedures, processes, documentation, and administrative requirements',
                'patterns': [
                    r'\b(procedure|process|method|steps|documentation)\b',
                    r'\b(application|filing|submission|approval)\b',
                    r'\b(form|format|template|certificate)\b',
                    r'\b(within.*days|timeline|deadline|period)\b',
                    r'\b(authority|department|office|agency)\b'
                ],
                'keywords': ['procedure', 'process', 'documentation', 'filing', 'approval', 'certificate', 'timeline']
            },
            
            'DEFINITION': {
                'description': 'Rules that provide definitions, interpretations, or explanations of terms',
                'patterns': [
                    r'\b(means|defined as|definition|interpretation)\b',
                    r'\b(for the purpose of|in this context|shall include)\b',
                    r'\b(explanation|clarification|specification)\b',
                    r'\".*\".*means',
                    r'\b(term|expression|word|phrase)\b'
                ],
                'keywords': ['definition', 'means', 'interpretation', 'explanation', 'clarification', 'term']
            }
        }
    
    def preprocess_text(self, text):
        """Clean and normalize text for classification"""
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
        # Convert to lowercase for pattern matching
        text_lower = text.lower()
        
        # Remove excessive whitespace and special characters
        text_clean = re.sub(r'\s+', ' ', text_lower)
        text_clean = re.sub(r'[^\w\s\-\(\)\[\]\"\'.,;:]', ' ', text_clean)
        
        return text_clean.strip()
    
    def calculate_rule_type_scores(self, text):
        """Calculate scores for each rule type based on patterns and keywords"""
        text_clean = self.preprocess_text(text)
        scores = {}
        
        for rule_type, config in self.rule_types.items():
            score = 0
            
            # Pattern matching (higher weight)
            for pattern in config['patterns']:
                matches = len(re.findall(pattern, text_clean, re.IGNORECASE))
                score += matches * 2
            
            # Keyword matching (lower weight)
            for keyword in config['keywords']:
                if keyword.lower() in text_clean:
                    score += 1
            
            scores[rule_type] = score
        
        return scores
    
    def classify_rule_type(self, text):
        """Classify a single regulatory text by rule type"""
        scores = self.calculate_rule_type_scores(text)
        
        # If no patterns match, default based on text characteristics
        if max(scores.values()) == 0:
            return self.default_classification(text)
        
        # Return the rule type with highest score
        predicted_type = max(scores, key=scores.get)
        confidence = scores[predicted_type] / (sum(scores.values()) + 1)
        
        return {
            'rule_type': predicted_type,
            'confidence': min(0.95, 0.5 + confidence * 0.45),
            'scores': scores
        }
    
    def default_classification(self, text):
        """Default classification for texts with no clear patterns"""
        text_clean = self.preprocess_text(text)
        
        # Heuristics for unclear cases
        if len(text_clean) < 50:
            return {
                'rule_type': 'DEFINITION',
                'confidence': 0.4,
                'scores': {'DEFINITION': 1, 'MANDATORY_REQUIREMENT': 0, 'OPTIONAL_PROVISION': 0, 'PROHIBITION': 0, 'PROCEDURAL': 0}
            }
        elif any(word in text_clean for word in ['coverage', 'policy', 'insurance']):
            return {
                'rule_type': 'MANDATORY_REQUIREMENT',
                'confidence': 0.4,
                'scores': {'MANDATORY_REQUIREMENT': 1, 'DEFINITION': 0, 'OPTIONAL_PROVISION': 0, 'PROHIBITION': 0, 'PROCEDURAL': 0}
            }
        else:
            return {
                'rule_type': 'PROCEDURAL',
                'confidence': 0.4,
                'scores': {'PROCEDURAL': 1, 'MANDATORY_REQUIREMENT': 0, 'DEFINITION': 0, 'OPTIONAL_PROVISION': 0, 'PROHIBITION': 0}
            }
    
    def reclassify_dataset(self, df):
        """Reclassify entire dataset with rule types"""
        print("🔄 Reclassifying regulatory documents by rule type...")
        print("=" * 60)
        
        results = []
        rule_type_counts = {rule_type: 0 for rule_type in self.rule_types.keys()}
        
        for idx, row in df.iterrows():
            text = row['text']
            classification = self.classify_rule_type(text)
            
            # Store results
            result = {
                'text': text,
                'rule_type': classification['rule_type'],
                'confidence': classification['confidence'],
                'source': row.get('source', ''),
                'relevance': row.get('relevance', ''),
                'original_label': row.get('label', '')
            }
            results.append(result)
            rule_type_counts[classification['rule_type']] += 1
            
            # Progress indicator
            if (idx + 1) % 20 == 0:
                print(f"Processed {idx + 1}/{len(df)} documents...")
        
        # Create new DataFrame
        reclassified_df = pd.DataFrame(results)
        
        # Display results
        print("\n📊 Rule Type Distribution:")
        for rule_type, count in rule_type_counts.items():
            percentage = (count / len(df)) * 100
            print(f"  {rule_type}: {count} documents ({percentage:.1f}%)")
        
        # Show examples
        print("\n📝 Sample Classifications:")
        for rule_type in self.rule_types.keys():
            examples = reclassified_df[reclassified_df['rule_type'] == rule_type].head(1)
            if not examples.empty:
                example = examples.iloc[0]
                text_preview = str(example['text'])[:100].replace('\n', ' ')
                print(f"\n{rule_type}:")
                print(f"  Text: {text_preview}...")
                print(f"  Confidence: {example['confidence']:.3f}")
        
        return reclassified_df

def main():
    """Main function to reclassify the regulatory training data"""
    print("🏛️ REGULATORY RULE TYPE CLASSIFICATION")
    print("=" * 60)
    
    # Load current training data
    print("📂 Loading training data...")
    df = pd.read_csv('data/training/motor_vehicle_training_data.csv')
    print(f"Loaded {len(df)} regulatory documents")
    
    # Initialize classifier
    classifier = RuleTypeClassifier()
    
    # Print rule type framework
    print("\n📋 Rule Type Framework:")
    for rule_type, config in classifier.rule_types.items():
        print(f"  {rule_type}: {config['description']}")
    
    # Reclassify the dataset
    reclassified_df = classifier.reclassify_dataset(df)
    
    # Save reclassified data
    output_file = 'data/training/motor_vehicle_rules_classification.csv'
    reclassified_df.to_csv(output_file, index=False)
    
    print(f"\n💾 Reclassified data saved to: {output_file}")
    print("\n✅ Rule type classification complete!")
    
    return reclassified_df, classifier

if __name__ == "__main__":
    reclassified_data, classifier = main()