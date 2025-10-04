"""Vector store for regulation documents using ChromaDB.

This module handles:
1. Creating embeddings for regulations using domain-adapted Legal-BERT
2. Storing embeddings in ChromaDB
3. Retrieving relevant regulations via similarity search
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
import torch
from transformers import AutoModel, AutoTokenizer
import chromadb
from chromadb.config import Settings

from app.core.config import settings

logger = logging.getLogger(__name__)


class RegulationVectorStore:
    """Manages vector embeddings and retrieval for regulations."""
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        persist_directory: Optional[Path] = None,
        collection_name: str = "motor_vehicle_regulations"
    ):
        """Initialize vector store with Legal-BERT embeddings.
        
        Args:
            model_path: Path to domain-adapted Legal-BERT model
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name for the ChromaDB collection
        """
        self.model_path = model_path or settings.MODEL_DIR / "legal_bert_domain_adapted"
        self.persist_directory = persist_directory or settings.DATA_DIR / "vector_store"
        self.collection_name = collection_name
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModel] = None
        self.client: Optional[chromadb.ClientAPI] = None
        self.collection: Optional[chromadb.Collection] = None
        self._initialized = False
        
        logger.info(f"🗄️  Vector store initialized with device: {self.device}")
        
    async def initialize(self) -> None:
        """Load models and setup ChromaDB."""
        if self._initialized:
            return
            
        try:
            logger.info("📚 Loading Legal-BERT model for embeddings...")
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
            self.model = AutoModel.from_pretrained(str(self.model_path))
            self.model.to(self.device)
            self.model.eval()
            
            # Initialize ChromaDB
            logger.info(f"🔧 Setting up ChromaDB at {self.persist_directory}...")
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                count = self.collection.count()
                logger.info(f"✅ Loaded existing collection with {count} regulations")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Motor vehicle insurance regulations"}
                )
                logger.info("📝 Created new empty collection")
            
            self._initialized = True
            logger.info("✅ Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector store: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a text using Legal-BERT.
        
        Args:
            text: Input text to embed
            
        Returns:
            Dense vector embedding (768 dimensions)
        """
        if not self._initialized:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")
        
        # Tokenize and truncate
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate embedding
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use mean pooling over token embeddings
            embedding = outputs.last_hidden_state.mean(dim=1).squeeze()
            
        return embedding.cpu().numpy().tolist()
    
    async def index_regulations(
        self,
        csv_path: Optional[Path] = None,
        force_reindex: bool = False
    ) -> Dict[str, Any]:
        """Index regulations from CSV into vector store.
        
        Args:
            csv_path: Path to training data CSV
            force_reindex: If True, clear existing data and reindex
            
        Returns:
            Dictionary with indexing statistics
        """
        if not self._initialized:
            await self.initialize()
        
        csv_path = csv_path or settings.DATA_DIR / "training" / "motor_vehicle_training_data.csv"
        
        # Check if already indexed
        if self.collection.count() > 0 and not force_reindex:
            logger.info(f"⏭️  Collection already has {self.collection.count()} items. Use force_reindex=True to rebuild.")
            return {
                "status": "skipped",
                "existing_count": self.collection.count(),
                "message": "Collection already indexed"
            }
        
        # Clear if force reindex
        if force_reindex and self.collection.count() > 0:
            logger.info("🗑️  Clearing existing collection...")
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Motor vehicle insurance regulations"}
            )
        
        # Load regulations
        logger.info(f"📖 Loading regulations from {csv_path}...")
        df = pd.read_csv(csv_path)
        
        # Filter for high relevance regulations
        high_relevance = df[df['relevance'].isin(['HIGH', 'MEDIUM'])].copy()
        logger.info(f"Found {len(high_relevance)} high/medium relevance regulations")
        
        # Generate embeddings and index
        logger.info("🔄 Generating embeddings (this may take a few minutes)...")
        embeddings = []
        documents = []
        metadatas = []
        ids = []
        
        batch_size = 16
        for idx in range(0, len(high_relevance), batch_size):
            batch = high_relevance.iloc[idx:idx + batch_size]
            
            for i, row in batch.iterrows():
                text = str(row['text'])
                embedding = self._generate_embedding(text)
                
                embeddings.append(embedding)
                documents.append(text)
                metadatas.append({
                    "source": str(row.get('source', 'UNKNOWN')),
                    "relevance": str(row.get('relevance', 'UNKNOWN')),
                    "label": str(row.get('label', 'UNKNOWN'))
                })
                ids.append(f"reg_{i}")
            
            if (idx + batch_size) % 100 == 0:
                logger.info(f"Processed {min(idx + batch_size, len(high_relevance))}/{len(high_relevance)}")
        
        # Add to collection
        logger.info(f"💾 Adding {len(embeddings)} embeddings to ChromaDB...")
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        stats = {
            "status": "success",
            "total_regulations": len(df),
            "indexed_count": len(embeddings),
            "collection_name": self.collection_name,
            "model": str(self.model_path)
        }
        
        logger.info(f"✅ Indexing complete: {stats}")
        return stats
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve most relevant regulations for a query.
        
        Args:
            query: Query text (e.g., policy content)
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of relevant regulations with scores
        """
        if not self._initialized:
            await self.initialize()
        
        if self.collection.count() == 0:
            logger.warning("⚠️  Collection is empty. Run index_regulations() first.")
            return []
        
        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata
        )
        
        # Format results
        regulations = []
        for i in range(len(results['ids'][0])):
            regulations.append({
                "id": results['ids'][0][i],
                "text": results['documents'][0][i],
                "distance": results['distances'][0][i],
                "metadata": results['metadatas'][0][i]
            })
        
        logger.info(f"🔍 Retrieved {len(regulations)} relevant regulations")
        return regulations
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        if not self._initialized or not self.collection:
            return {"status": "not_initialized"}
        
        return {
            "collection_name": self.collection_name,
            "total_documents": self.collection.count(),
            "model_path": str(self.model_path),
            "device": str(self.device),
            "persist_directory": str(self.persist_directory)
        }
