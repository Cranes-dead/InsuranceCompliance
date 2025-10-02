"""
Legal BERT Domain Adaptation Script - Optimized Version
Phase 1: Pre-train Legal BERT on insurance domain text using Masked Language Modeling
This helps the model learn insurance terminology and legal language patterns.
"""

import pandas as pd
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForMaskedLM, 
    DataCollatorForLanguageModeling
)
from torch.utils.data import Dataset, DataLoader
import pdfplumber
from pathlib import Path
import re
import logging
from typing import List
import time


BACKEND_ROOT = Path(__file__).resolve().parent
DATA_DIR = BACKEND_ROOT / "data"
TRAINING_DATA_PATH = DATA_DIR / "training" / "motor_vehicle_training_data.csv"
TEST_SAMPLES_DIR = BACKEND_ROOT / "test_samples"
MODELS_DIR = BACKEND_ROOT / "models"
DEFAULT_DOMAIN_MODEL_DIR = MODELS_DIR / "legal_bert_domain_adapted"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedInsuranceDomainDataset(Dataset):
    """Optimized dataset for insurance domain text"""
    
    def __init__(self, texts: List[str], tokenizer, max_length: int = 256):
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        # Pre-tokenize all texts for faster training
        logger.info("Pre-tokenizing texts for faster training...")
        self.tokenized_texts = []
        
        for i, text in enumerate(texts):
            if i % 100 == 0:
                logger.info(f"Tokenizing progress: {i}/{len(texts)}")
                
            # Clean and tokenize text
            clean_text = self.clean_text(text)
            
            # Tokenize with proper settings
            tokens = self.tokenizer(
                clean_text,
                max_length=self.max_length,
                truncation=True,
                padding=False,  # Don't pad here, let collator handle it
                return_tensors=None  # Return lists, not tensors
            )
            
            self.tokenized_texts.append(tokens)
        
        logger.info(f"Pre-tokenization complete! Dataset size: {len(self.tokenized_texts)}")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?()-]', ' ', text)
        return text.strip()
    
    def __len__(self):
        return len(self.tokenized_texts)
    
    def __getitem__(self, idx):
        return {
            'input_ids': self.tokenized_texts[idx]['input_ids'],
            'attention_mask': self.tokenized_texts[idx]['attention_mask']
        }

class OptimizedDomainAdaptationTrainer:
    """Optimized trainer for domain adaptation"""
    
    def __init__(self, model_name: str = "nlpaueb/legal-bert-base-uncased"):
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        logger.info(f"Base model: {self.model_name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
    
    def prepare_domain_data(self) -> List[str]:
        """Prepare domain-specific text data for training"""
        logger.info("Loading existing training data text...")
        
        domain_texts = []
        
        # Load existing training data
        try:
            df = pd.read_csv(TRAINING_DATA_PATH)
            existing_texts = df['text'].tolist()
            # Split long texts into chunks
            for text in existing_texts:
                if len(text) > 1000:
                    # Split into smaller chunks
                    chunks = [text[i:i+1000] for i in range(0, len(text), 800)]  # 200 char overlap
                    domain_texts.extend(chunks)
                else:
                    domain_texts.append(text)
            
            logger.info(f"Added {len(domain_texts)} chunks from existing training data")
        except Exception as e:
            logger.warning(f"Could not load training data: {e}")
        
        # Process PDF documents
        logger.info("Processing PDF documents...")
        
        pdf_files = [
            "5. Motor - Add On - Approved Wordings_GEN809",
            "36..Motor Act Only_GEN743", 
            "99. Motor Vehicle- Extended Warranty_GEN651",
            "Handbook on e-Vahan Bima (e-Motor Insurance Policies)",
            "IRDAI (Obligation of Insurer in respect of Motor Third Party Insurance",
            "Motor Insurance Handbook (English)",
            "Motor Insurance"
        ]
        
        for pdf_name in pdf_files:
            pdf_path = TEST_SAMPLES_DIR / f"{pdf_name}.pdf"
            if pdf_path.exists():
                logger.info(f"Processing: {pdf_name}")
                try:
                    text = self.extract_text_from_pdf(str(pdf_path))
                    if text:
                        # Split into smaller chunks for better training
                        chunks = self.chunk_text(text, chunk_size=800)  # Smaller chunks
                        domain_texts.extend(chunks)
                        logger.info(f"Added {len(chunks)} chunks from {pdf_name}")
                except Exception as e:
                    logger.warning(f"Error processing {pdf_name}: {e}")
            else:
                logger.warning(f"PDF not found: {pdf_path}")
        
        logger.info(f"Total domain texts prepared: {len(domain_texts)}")
        return domain_texts
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
        return text
    
    def chunk_text(self, text: str, chunk_size: int = 800) -> List[str]:
        """Split text into smaller chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk = " ".join(chunk_words)
            if len(chunk.strip()) > 50:  # Only keep substantial chunks
                chunks.append(chunk.strip())
        
        return chunks
    
    def domain_adapt(self, output_dir: Path | None = None, epochs: int = 2):
        """Perform domain adaptation using Masked Language Modeling - Optimized"""
        
        output_dir = Path(output_dir) if output_dir else DEFAULT_DOMAIN_MODEL_DIR
        
        # Prepare domain data
        domain_texts = self.prepare_domain_data()
        
        if not domain_texts:
            logger.error("No domain texts found!")
            return
        
        # Limit dataset size for faster training
        if len(domain_texts) > 800:
            logger.info(f"Limiting dataset from {len(domain_texts)} to 800 samples for faster training")
            domain_texts = domain_texts[:800]
        
        # Load model for MLM
        model = AutoModelForMaskedLM.from_pretrained(self.model_name)
        model.to(self.device)
        
        # Create optimized dataset
        dataset = OptimizedInsuranceDomainDataset(domain_texts, self.tokenizer, max_length=256)
        
        # Data collator for MLM
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=True,
            mlm_probability=0.15
        )
        
        # Create dataloader with optimized settings
        dataloader = DataLoader(
            dataset, 
            batch_size=8,  # Increased batch size
            shuffle=True, 
            collate_fn=data_collator,
            num_workers=0,  # Use 0 for Windows compatibility
            pin_memory=False
        )
        
        # Use PyTorch optimizer to avoid deprecation warning
        optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)
        
        # Training loop
        logger.info("Starting optimized domain adaptation training...")
        logger.info(f"Training on {len(domain_texts)} text chunks")
        logger.info(f"Number of batches per epoch: {len(dataloader)}")
        
        model.train()
        start_time = time.time()
        
        for epoch in range(epochs):
            total_loss = 0
            batch_count = 0
            epoch_start_time = time.time()
            
            logger.info(f"Starting epoch {epoch + 1}/{epochs}")
            
            for batch_idx, batch in enumerate(dataloader):
                # Move batch to device
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                # Forward pass
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                loss = outputs.loss
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                batch_count += 1
                
                # Log every 25 batches (more frequent)
                if (batch_idx + 1) % 25 == 0:
                    avg_loss = total_loss / batch_count
                    elapsed = time.time() - epoch_start_time
                    logger.info(f"Epoch {epoch+1}, Batch {batch_idx+1}/{len(dataloader)}, "
                              f"Loss: {loss.item():.4f}, Avg Loss: {avg_loss:.4f}, "
                              f"Time: {elapsed:.1f}s")
            
            avg_epoch_loss = total_loss / len(dataloader)
            epoch_time = time.time() - epoch_start_time
            logger.info(f"Epoch {epoch+1} completed - Average Loss: {avg_epoch_loss:.4f}, "
                       f"Time: {epoch_time:.1f}s")
        
        # Save adapted model
        output_dir.mkdir(parents=True, exist_ok=True)
        
        model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        
        total_time = time.time() - start_time
        logger.info(f"Domain adaptation completed in {total_time:.1f}s!")
        logger.info(f"Adapted model saved to {output_dir}")
        
        return str(output_dir)

def main():
    """Main function to run domain adaptation"""
    print("🎯 Legal BERT Domain Adaptation - Phase 1 (Optimized)")
    print("=" * 60)
    print("Learning insurance domain language patterns...")
    print("This will help the model understand legal/insurance terminology")
    print("=" * 60)
    
    try:
        trainer = OptimizedDomainAdaptationTrainer()
        adapted_model_path = trainer.domain_adapt(
            output_dir=DEFAULT_DOMAIN_MODEL_DIR,
            epochs=2
        )
        
        if adapted_model_path:
            print("\n🎉 Phase 1 Domain Adaptation Complete!")
            print(f"📁 Model saved to: {adapted_model_path}")
            print("\n🔄 Ready for Phase 2: Classification Training")
            print("Run: python backend/phase2_classification_training.py")
        else:
            print("\n❌ Domain adaptation failed!")
            
    except Exception as e:
        logger.error(f"Domain adaptation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()