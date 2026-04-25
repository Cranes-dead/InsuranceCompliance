"""Retriever module that combines vector search with filtering logic."""

import logging
from typing import Dict, List, Optional, Any

from .vector_store import RegulationVectorStore

logger = logging.getLogger(__name__)


class RegulationRetriever:
    """High-level interface for retrieving relevant regulations."""
    
    def __init__(self, vector_store: Optional[RegulationVectorStore] = None):
        """Initialize retriever.
        
        Args:
            vector_store: Optional pre-configured vector store
        """
        self.vector_store = vector_store or RegulationVectorStore()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the retriever and vector store."""
        if self._initialized:
            return
        
        await self.vector_store.initialize()
        
        # Index regulations if not already indexed
        stats = await self.vector_store.index_regulations()
        logger.info(f"📊 Retriever ready: {stats}")
        
        self._initialized = True
    
    async def retrieve_for_policy(
        self,
        policy_text: str,
        top_k: int = 10,
        min_relevance: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve regulations relevant to a policy document.
        
        Uses a focused query strategy since Legal-BERT truncates at 512 tokens.
        Instead of passing the full policy text (which would silently lose most
        of the content), we extract key portions to build a representative query.
        
        Args:
            policy_text: Full or partial policy text
            top_k: Number of regulations to retrieve
            min_relevance: Minimum relevance threshold ('HIGH' = only HIGH,
                           'MEDIUM' = HIGH + MEDIUM). Default: no filter.
            
        Returns:
            List of relevant regulations with metadata
        """
        if not self._initialized:
            await self.initialize()
        
        # LOGIC-02 FIX: Build proper threshold filter instead of equality match
        # ChromaDB 'where' only supports equality, so we expand to matching values
        filter_metadata = None
        if min_relevance:
            relevance_hierarchy = ["HIGH", "MEDIUM", "LOW"]
            try:
                threshold_idx = relevance_hierarchy.index(min_relevance)
                allowed_values = relevance_hierarchy[:threshold_idx + 1]
                filter_metadata = {"relevance": {"$in": allowed_values}}
            except ValueError:
                logger.warning(f"Unknown relevance level '{min_relevance}', skipping filter")
        
        # LOGIC-01 FIX: Build a focused query instead of passing full policy text.
        # Legal-BERT truncates at 512 tokens (~400 words), so passing a 50K-char
        # document means only the first ~400 words are actually embedded.
        query_text = self._build_focused_query(policy_text)
        
        # Retrieve from vector store
        results = await self.vector_store.retrieve(
            query=query_text,
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        # Add semantic similarity score (convert distance to similarity)
        for result in results:
            # ChromaDB returns L2 distance, convert to similarity score
            distance = result['distance']
            similarity = 1 / (1 + distance)  # Normalize to 0-1 range
            result['similarity_score'] = round(similarity, 4)
        
        return results
    
    def _build_focused_query(self, policy_text: str, max_words: int = 350) -> str:
        """Build a focused query from a policy document.
        
        Instead of embedding the full text (which gets truncated silently),
        extracts a representative sample: the beginning (which usually contains
        policy type, insurer, coverage overview) and the end (which often has
        compliance-critical terms and conditions).
        
        Args:
            policy_text: Full policy document text
            max_words: Maximum words for the query (should stay under 512 tokens)
            
        Returns:
            Focused query text suitable for embedding
        """
        words = policy_text.split()
        
        if len(words) <= max_words:
            return policy_text
        
        # Take first 250 words (policy type, coverage, insurer info) and 
        # last 100 words (terms, conditions, compliance clauses)
        head_words = 250
        tail_words = 100
        
        head = " ".join(words[:head_words])
        tail = " ".join(words[-tail_words:])
        
        query = f"{head} [...] {tail}"
        logger.debug(
            f"Built focused query: {len(words)} words → {head_words + tail_words} words "
            f"(head + tail strategy)"
        )
        return query
    
    async def retrieve_for_section(
        self,
        section_text: str,
        section_type: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve regulations for a specific policy section.
        
        Args:
            section_text: Text of the policy section
            section_type: Type of section (e.g., 'coverage', 'exclusions')
            top_k: Number of regulations to retrieve
            
        Returns:
            List of relevant regulations
        """
        # Add section type as context
        enriched_query = f"Policy section ({section_type}): {section_text}"
        
        results = await self.retrieve_for_policy(
            policy_text=enriched_query,
            top_k=top_k,
            min_relevance="HIGH"
        )
        
        return results
    
    def format_regulations_for_llm(
        self,
        regulations: List[Dict[str, Any]],
        include_metadata: bool = True
    ) -> str:
        """Format retrieved regulations for LLM context.
        
        Args:
            regulations: List of regulation dictionaries
            include_metadata: Whether to include source/relevance metadata
            
        Returns:
            Formatted string for LLM prompt
        """
        if not regulations:
            return "No specific regulations retrieved."
        
        formatted = []
        for i, reg in enumerate(regulations, 1):
            text = reg['text']
            
            if include_metadata:
                metadata = reg.get('metadata', {})
                source = metadata.get('source', 'UNKNOWN')
                relevance = metadata.get('relevance', 'UNKNOWN')
                similarity = reg.get('similarity_score', 0.0)
                
                formatted.append(
                    f"[Regulation {i}] (Source: {source}, Relevance: {relevance}, Similarity: {similarity:.2f})\n"
                    f"{text}\n"
                )
            else:
                formatted.append(f"[Regulation {i}]\n{text}\n")
        
        return "\n".join(formatted)
