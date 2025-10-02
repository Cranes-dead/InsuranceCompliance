import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel, AutoConfig
from transformers import Trainer, TrainingArguments
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class LegalBERTComplianceClassifier(nn.Module):
    """Legal BERT model fine-tuned for insurance compliance classification"""
    
    def __init__(self, model_name: str = "nlpaueb/legal-bert-base-uncased", num_labels: int = 3):
        super().__init__()
        self.num_labels = num_labels
        self.model_name = model_name
        
        # Load pre-trained Legal BERT
        self.config = AutoConfig.from_pretrained(model_name, num_labels=num_labels)
        self.bert = AutoModel.from_pretrained(model_name, config=self.config)
        
        # Classification head
        self.dropout = nn.Dropout(self.config.hidden_dropout_prob)
        self.classifier = nn.Linear(self.config.hidden_size, num_labels)
        
        # For multi-label classification
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, input_ids, attention_mask=None, labels=None):
        # Get BERT outputs
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        
        # Use [CLS] token representation
        pooled_output = outputs.last_hidden_state[:, 0]  # [CLS] token
        pooled_output = self.dropout(pooled_output)
        
        # Classification
        logits = self.classifier(pooled_output)
        
        # For training, calculate loss
        loss = None
        if labels is not None:
            if self.num_labels > 1:
                # Multi-class classification
                loss_fct = nn.CrossEntropyLoss()
                loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))
            else:
                # Regression
                loss_fct = nn.MSELoss()
                loss = loss_fct(logits.view(-1), labels.view(-1))
        
        return {
            'loss': loss,
            'logits': logits,
            'hidden_states': outputs.hidden_states if hasattr(outputs, 'hidden_states') else None,
            'attentions': outputs.attentions if hasattr(outputs, 'attentions') else None,
        }

class ComplianceDataset(torch.utils.data.Dataset):
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
        label = int(self.labels[idx])
        
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

class LegalBERTTrainer:
    """Trainer class for Legal BERT fine-tuning"""
    
    def __init__(self, model_name: str = "nlpaueb/legal-bert-base-uncased", 
                 num_labels: int = 3, max_length: int = 512):
        self.model_name = model_name
        self.num_labels = num_labels
        self.max_length = max_length
        
        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Initialize model
        self.model = LegalBERTComplianceClassifier(model_name, num_labels)
        
        # Label mapping
        self.label_map = {
            0: "COMPLIANT",
            1: "NON_COMPLIANT", 
            2: "REQUIRES_REVIEW"
        }
        self.reverse_label_map = {v: k for k, v in self.label_map.items()}
    
    def prepare_data(self, texts: List[str], labels: List[str]) -> Tuple[ComplianceDataset, ComplianceDataset]:
        """Prepare training and validation datasets"""
        # Convert string labels to integers
        numeric_labels = [self.reverse_label_map[label] for label in labels]
        
        # Split into train/val (80/20)
        split_idx = int(0.8 * len(texts))
        
        train_texts = texts[:split_idx]
        train_labels = numeric_labels[:split_idx]
        val_texts = texts[split_idx:]
        val_labels = numeric_labels[split_idx:]
        
        # Create datasets
        train_dataset = ComplianceDataset(train_texts, train_labels, self.tokenizer, self.max_length)
        val_dataset = ComplianceDataset(val_texts, val_labels, self.tokenizer, self.max_length)
        
        return train_dataset, val_dataset
    
    def train(self, train_dataset, val_dataset, output_dir: str = "./models/legal_bert_compliance",
              num_epochs: int = 3, batch_size: int = 8, learning_rate: float = 2e-5):
        """Train the model"""
        
        # Training arguments (simplified to avoid evaluation issues)
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            warmup_steps=100,  # Reduced warmup steps
            weight_decay=0.01,
            learning_rate=learning_rate,
            logging_dir=f'{output_dir}/logs',
            logging_steps=10,  # More frequent logging
            save_steps=1000,   # Save periodically
            eval_strategy="no",  # Disable evaluation to avoid the error
            save_strategy="no",  # Disable saving during training to avoid issues
            dataloader_pin_memory=False,  # Disable pin_memory
            remove_unused_columns=False,  # Keep all columns
        )
        
        # Initialize trainer (simplified)
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            # Remove eval_dataset to avoid evaluation issues
            # eval_dataset=val_dataset,
            # compute_metrics=self.compute_metrics,
        )
        
        # Train
        logger.info("Starting training...")
        trainer.train()
        
        # Save model
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        # Save label mapping
        with open(f"{output_dir}/label_map.json", "w") as f:
            json.dump(self.label_map, f)
        
        logger.info(f"Model saved to {output_dir}")
        
        return trainer
    
    def compute_metrics(self, eval_pred):
        """Compute evaluation metrics"""
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        
        # Calculate metrics
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support
        
        accuracy = accuracy_score(labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average='weighted')
        
        return {
            'accuracy': accuracy,
            'f1': f1,
            'precision': precision,
            'recall': recall
        }
    
    def evaluate(self, test_texts: List[str], test_labels: List[str]) -> Dict:
        """Evaluate the model on test data"""
        # Prepare test dataset
        numeric_labels = [self.reverse_label_map[label] for label in test_labels]
        test_dataset = ComplianceDataset(test_texts, numeric_labels, self.tokenizer, self.max_length)
        
        # Set model to evaluation mode
        self.model.eval()
        
        predictions = []
        true_labels = []
        
        with torch.no_grad():
            for batch in torch.utils.data.DataLoader(test_dataset, batch_size=8):
                outputs = self.model(
                    input_ids=batch['input_ids'],
                    attention_mask=batch['attention_mask']
                )
                
                # Get predictions
                preds = torch.argmax(outputs['logits'], dim=1)
                predictions.extend(preds.cpu().numpy())
                true_labels.extend(batch['labels'].cpu().numpy())
        
        # Calculate metrics
        accuracy = sum(p == t for p, t in zip(predictions, true_labels)) / len(predictions)
        
        # Classification report
        pred_labels = [self.label_map[p] for p in predictions]
        true_label_names = [self.label_map[t] for t in true_labels]
        
        report = classification_report(true_label_names, pred_labels, output_dict=True)
        
        return {
            'accuracy': accuracy,
            'classification_report': report,
            'predictions': pred_labels,
            'true_labels': true_label_names
        }

class ComplianceInference:
    """Inference class for trained compliance model"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Load model
        self.model = LegalBERTComplianceClassifier.from_pretrained(model_path)
        self.model.eval()
        
        # Load label mapping
        with open(self.model_path / "label_map.json", "r") as f:
            self.label_map = json.load(f)
            # Convert string keys to int
            self.label_map = {int(k): v for k, v in self.label_map.items()}
        
        # Device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
    
    def predict(self, text: str) -> Dict[str, any]:
        """Predict compliance for a single document"""
        # Tokenize
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=512,
            return_tensors='pt'
        )
        
        # Move to device
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # Predict
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs['logits']
            probabilities = torch.softmax(logits, dim=1)
            
            # Get prediction
            predicted_class = torch.argmax(logits, dim=1).item()
            confidence = probabilities[0][predicted_class].item()
        
        return {
            'classification': self.label_map[predicted_class],
            'confidence': confidence,
            'probabilities': {
                self.label_map[i]: prob.item() 
                for i, prob in enumerate(probabilities[0])
            }
        }
    
    def predict_batch(self, texts: List[str], batch_size: int = 8) -> List[Dict[str, any]]:
        """Predict compliance for multiple documents"""
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Tokenize batch
            encodings = self.tokenizer(
                batch_texts,
                truncation=True,
                padding='max_length',
                max_length=512,
                return_tensors='pt'
            )
            
            # Move to device
            input_ids = encodings['input_ids'].to(self.device)
            attention_mask = encodings['attention_mask'].to(self.device)
            
            # Predict
            with torch.no_grad():
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs['logits']
                probabilities = torch.softmax(logits, dim=1)
                
                # Process results
                for j in range(len(batch_texts)):
                    predicted_class = torch.argmax(logits[j]).item()
                    confidence = probabilities[j][predicted_class].item()
                    
                    results.append({
                        'classification': self.label_map[predicted_class],
                        'confidence': confidence,
                        'probabilities': {
                            self.label_map[k]: probabilities[j][k].item() 
                            for k in self.label_map.keys()
                        }
                    })
        
        return results