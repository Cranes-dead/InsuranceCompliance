"""
Legal BERT Classification Training - Phase 2
Uses the domain-adapted model from Phase 1 and fine-tunes for compliance classification
"""

import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, AutoConfig, AdamW, get_linear_schedule_with_warmup
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import numpy as np
from pathlib import Path
import json
from typing import List, Dict
import logging
from tqdm import tqdm


BACKEND_ROOT = Path(__file__).resolve().parent
DATA_DIR = BACKEND_ROOT / "data"
TRAINING_DATA_PATH = DATA_DIR / "training" / "motor_vehicle_training_data.csv"
MODELS_DIR = BACKEND_ROOT / "models"
DEFAULT_DOMAIN_MODEL_DIR = MODELS_DIR / "legal_bert_domain_adapted"
DEFAULT_OUTPUT_DIR = MODELS_DIR / "legal_bert_compliance_final"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceDataset(Dataset):
    """Dataset class for compliance classification"""
    
    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int = 512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        # Tokenize
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

class DomainAdaptedClassifier(nn.Module):
    """Classification head on top of domain-adapted Legal BERT"""
    
    def __init__(self, model_path: Path | str, num_labels: int = 3):
        super().__init__()
        self.num_labels = num_labels
        self.model_path = Path(model_path)
        
        # Load domain-adapted BERT
        self.config = AutoConfig.from_pretrained(self.model_path)
        self.bert = AutoModel.from_pretrained(self.model_path)
        
        # Classification head
        self.dropout = nn.Dropout(0.1)
        self.classifier = nn.Linear(self.config.hidden_size, num_labels)
    
    def forward(self, input_ids, attention_mask=None, labels=None):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        
        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))
        
        return {'loss': loss, 'logits': logits}

class ClassificationTrainer:
    """Trainer for compliance classification using domain-adapted model"""
    
    def __init__(self, domain_adapted_model_path: Path | str = DEFAULT_DOMAIN_MODEL_DIR):
        self.domain_adapted_model_path = Path(domain_adapted_model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(self.domain_adapted_model_path)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Label mappings
        self.label_map = {
            "COMPLIANT": 0,
            "NON_COMPLIANT": 1, 
            "REQUIRES_REVIEW": 2
        }
        self.id2label = {v: k for k, v in self.label_map.items()}
        
        logger.info(f"Using device: {self.device}")
        logger.info(f"Domain-adapted model: {self.domain_adapted_model_path}")
    
    def load_labeled_data_only(self, data_path: Path | str) -> tuple:
        """Load only the originally labeled data (not the auto-added PDF chunks)"""
        data_path = Path(data_path)
        logger.info(f"Loading labeled data from {data_path}")
        
        df = pd.read_csv(data_path)
        
        # Filter to get only original labeled data (not the PDF chunks we added)
        # Original data doesn't have "_chunk_" in the source field
        original_data = df[~df['source'].str.contains('_chunk_', na=False)]
        
        logger.info(f"Filtered to {len(original_data)} originally labeled samples")
        logger.info(f"Skipped {len(df) - len(original_data)} auto-added PDF chunks")
        
        # Prepare texts and labels
        texts = original_data['text'].tolist()
        labels = [self.label_map[label] for label in original_data['label'].tolist()]
        
        logger.info(f"Label distribution: {original_data['label'].value_counts().to_dict()}")
        
        return texts, labels
    
    def create_data_loaders(self, texts, labels, test_size=0.2, batch_size=8):
        """Create train/validation data loaders"""
        
        # Split data
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=test_size, random_state=42, stratify=labels
        )
        
        # Create datasets
        train_dataset = ComplianceDataset(train_texts, train_labels, self.tokenizer)
        val_dataset = ComplianceDataset(val_texts, val_labels, self.tokenizer)
        
        # Create data loaders
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        logger.info(f"Train samples: {len(train_dataset)}")
        logger.info(f"Validation samples: {len(val_dataset)}")
        
        return train_loader, val_loader
    
    def train_classifier(
        self,
        data_path: Path | str,
        output_dir: Path | str,
        epochs: int = 3,
        batch_size: int = 8,
        learning_rate: float = 2e-5
    ):
        """Train the classification model on labeled data"""
        
        data_path = Path(data_path)
        output_dir = Path(output_dir)
        
        # Check if domain-adapted model exists
        if not self.domain_adapted_model_path.exists():
            logger.error(f"Domain-adapted model not found at {self.domain_adapted_model_path}")
            logger.info("Please run Phase 1 (domain adaptation) first!")
            return None
        
        # Load labeled data only
        texts, labels = self.load_labeled_data_only(data_path)
        train_loader, val_loader = self.create_data_loaders(texts, labels, batch_size=batch_size)
        
        # Initialize model with domain-adapted weights
        model = DomainAdaptedClassifier(self.domain_adapted_model_path, len(self.label_map))
        model.to(self.device)
        
        # Optimizer and scheduler
        optimizer = AdamW(model.parameters(), lr=learning_rate)
        total_steps = len(train_loader) * epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer, num_warmup_steps=0, num_training_steps=total_steps
        )
        
        # Training loop
        logger.info("Starting classification training...")
        model.train()
        
        for epoch in range(epochs):
            total_loss = 0
            progress_bar = tqdm(train_loader, desc=f'Epoch {epoch+1}/{epochs}')
            
            for batch in progress_bar:
                # Move to device
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                # Forward pass
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                loss = outputs['loss']
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                
                total_loss += loss.item()
                progress_bar.set_postfix({'loss': f'{loss.item():.4f}'})
            
            avg_loss = total_loss / len(train_loader)
            logger.info(f"Epoch {epoch+1} - Average Loss: {avg_loss:.4f}")
            
            # Validation
            val_accuracy = self.evaluate(model, val_loader)
            logger.info(f"Epoch {epoch+1} - Validation Accuracy: {val_accuracy:.4f}")
        
        # Save model
        self.save_model(model, output_dir)
        logger.info(f"Classification training completed! Model saved to {output_dir}")
        
        return model
    
    def evaluate(self, model, data_loader):
        """Evaluate the model"""
        model.eval()
        predictions = []
        true_labels = []
        
        with torch.no_grad():
            for batch in data_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs['logits']
                
                predictions.extend(torch.argmax(logits, dim=1).cpu().numpy())
                true_labels.extend(labels.cpu().numpy())
        
        model.train()
        return accuracy_score(true_labels, predictions)
    
    def save_model(self, model, output_dir: Path | str):
        """Save the trained model"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save model weights
        torch.save(model.state_dict(), output_path / "pytorch_model.bin")
        
        # Save tokenizer
        self.tokenizer.save_pretrained(output_path)
        
        # Save config
        with open(output_path / "config.json", "w") as f:
            json.dump({
                "model_type": "domain_adapted_classifier",
                "domain_adapted_model_path": str(self.domain_adapted_model_path),
                "num_labels": len(self.label_map),
                "hidden_size": 768  # Legal BERT hidden size
            }, f, indent=2)
        
        # Save label mappings
        with open(output_path / "label_map.json", "w") as f:
            json.dump(self.id2label, f, indent=2)
        
        logger.info(f"Model artifacts saved to {output_path}")

def main():
    """Main classification training function"""
    print("🎯 Legal BERT Classification Training - Phase 2")
    print("=" * 60)
    print("Training classifier on labeled data using domain-adapted model...")
    print("=" * 60)
    
    # Configuration
    data_path = TRAINING_DATA_PATH
    domain_adapted_model_path = DEFAULT_DOMAIN_MODEL_DIR
    output_dir = DEFAULT_OUTPUT_DIR
    epochs = 3
    batch_size = 4
    learning_rate = 2e-5
    
    # Check if data exists
    if not data_path.exists():
        logger.error(f"Training data not found at {data_path}")
        return
    
    # Check if domain-adapted model exists
    if not domain_adapted_model_path.exists():
        logger.error(f"Domain-adapted model not found at {domain_adapted_model_path}")
        logger.info("Please run Phase 1 (domain adaptation) first!")
        return
    
    # Initialize trainer
    trainer = ClassificationTrainer(domain_adapted_model_path)
    
    # Train classifier
    try:
        model = trainer.train_classifier(
            data_path=data_path,
            output_dir=output_dir,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate
        )
        
        print("🎉 Phase 2 (Classification Training) completed successfully!")
        print(f"📁 Final model saved to: {output_dir}")
        print("🚀 Your Legal BERT model is ready for compliance classification!")
        
    except Exception as e:
        logger.error(f"Classification training failed: {e}")
        raise

if __name__ == "__main__":
    main()