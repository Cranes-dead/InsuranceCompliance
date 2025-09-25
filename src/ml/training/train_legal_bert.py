"""
Training script for Legal BERT compliance classifier
"""

import argparse
import json
import logging
from pathlib import Path
import pandas as pd
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.ml.models.legal_bert import LegalBERTTrainer
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def prepare_training_data(data_dir: str) -> tuple:
    """Prepare training data from processed documents"""
    data_path = Path(data_dir)
    
    # Load actual training data from our motor vehicle compliance documents
    training_file = data_path / "motor_vehicle_training_data.csv"
    
    if not training_file.exists():
        logger.warning(f"Training file not found: {training_file}")
        logger.info("Using sample data for demonstration...")
        # Fallback sample data
        sample_data = [
            {"text": "This policy complies with all IRDAI motor insurance guidelines...", "label": "COMPLIANT"},
            {"text": "This policy violates section 3.2 of IRDAI motor vehicle regulation...", "label": "NON_COMPLIANT"},
            {"text": "This policy requires further review for motor insurance compliance...", "label": "REQUIRES_REVIEW"},
        ]
        texts = [item["text"] for item in sample_data]
        labels = [item["label"] for item in sample_data]
        return texts, labels
    
    # Load actual training data
    df = pd.read_csv(training_file)
    logger.info(f"Loaded training data from {training_file}")
    logger.info(f"Dataset shape: {df.shape}")
    
    # Display class distribution
    label_counts = df['label'].value_counts()
    logger.info(f"Label distribution: {label_counts.to_dict()}")
    
    texts = df['text'].tolist()
    labels = df['label'].tolist()
    
    return texts, labels

def main():
    parser = argparse.ArgumentParser(description="Train Legal BERT compliance classifier")
    parser.add_argument("--data-dir", required=True, help="Directory containing training data")
    parser.add_argument("--output-dir", default="./models/legal_bert_compliance", help="Output directory for trained model")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Training batch size")
    parser.add_argument("--learning-rate", type=float, default=2e-5, help="Learning rate")
    
    args = parser.parse_args()
    
    logger.info("Preparing training data...")
    texts, labels = prepare_training_data(args.data_dir)
    
    logger.info(f"Loaded {len(texts)} training examples")
    
    # Initialize trainer
    trainer = LegalBERTTrainer()
    
    # Prepare datasets
    train_dataset, val_dataset = trainer.prepare_data(texts, labels)
    
    # Train model
    logger.info("Starting training...")
    trainer.train(
        train_dataset,
        val_dataset,
        output_dir=args.output_dir,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate
    )
    
    logger.info(f"Training completed! Model saved to {args.output_dir}")

if __name__ == "__main__":
    main()