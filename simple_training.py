"""
Simple training script for Motor Vehicle Insurance Compliance
Uses a lighter approach that's more reliable than full BERT training
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
import pickle
import os
from pathlib import Path

def train_simple_compliance_model():
    """Train a simple but effective compliance classifier"""
    
    print("🚗 Starting Motor Vehicle Insurance Compliance Model Training")
    print("=" * 60)
    
    # Load training data
    training_file = "data/training/motor_vehicle_training_data.csv"
    if not os.path.exists(training_file):
        print(f"❌ Training file not found: {training_file}")
        return
    
    df = pd.read_csv(training_file)
    print(f"📊 Loaded {len(df)} training examples")
    print(f"📈 Label distribution:")
    print(df['label'].value_counts())
    print()
    
    # Prepare data
    texts = df['text'].fillna('').astype(str)
    labels = df['label']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    print(f"🔄 Training set: {len(X_train)} examples")
    print(f"🔍 Test set: {len(X_test)} examples")
    print()
    
    # Feature extraction
    print("📝 Extracting features using TF-IDF...")
    vectorizer = TfidfVectorizer(
        max_features=10000,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95
    )
    
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)
    
    print(f"✅ Feature matrix shape: {X_train_tfidf.shape}")
    print()
    
    # Train model
    print("🎯 Training Logistic Regression model...")
    model = LogisticRegression(
        max_iter=1000,
        random_state=42,
        class_weight='balanced'  # Handle imbalanced classes
    )
    
    model.fit(X_train_tfidf, y_train)
    print("✅ Training completed!")
    print()
    
    # Evaluate
    print("📊 Evaluating model performance...")
    y_pred = model.predict(X_test_tfidf)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"🎯 Accuracy: {accuracy:.4f}")
    print()
    print("📈 Detailed Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save model
    model_dir = Path("models/simple_compliance")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the model and vectorizer
    with open(model_dir / "model.pkl", "wb") as f:
        pickle.dump(model, f)
    
    with open(model_dir / "vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
    
    # Save label mapping
    label_map = {label: idx for idx, label in enumerate(model.classes_)}
    with open(model_dir / "label_map.pkl", "wb") as f:
        pickle.dump(label_map, f)
    
    print(f"💾 Model saved to: {model_dir}")
    print()
    
    # Test with sample predictions
    print("🧪 Testing with sample predictions:")
    test_samples = [
        "This motor insurance policy complies with IRDAI third party liability requirements of Rs 15 lakhs",
        "This policy does not have the mandatory personal accident cover",
        "The premium calculation needs review for IRDAI motor tariff compliance"
    ]
    
    for i, sample in enumerate(test_samples, 1):
        sample_tfidf = vectorizer.transform([sample])
        prediction = model.predict(sample_tfidf)[0]
        confidence = model.predict_proba(sample_tfidf)[0]
        max_confidence = max(confidence)
        
        print(f"   {i}. Text: {sample[:60]}...")
        print(f"      Prediction: {prediction} (confidence: {max_confidence:.3f})")
        print()
    
    print("🎉 Motor Vehicle Insurance Compliance Model Training Complete!")
    print("=" * 60)
    
    return model, vectorizer, label_map

if __name__ == "__main__":
    train_simple_compliance_model()