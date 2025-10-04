"""Integrated RAG + LLaMA compliance service.

This is the main service that combines:
1. Legal-BERT for document understanding and embeddings
2. RAG for retrieving relevant regulations
3. LLaMA for reasoning and classification
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from app.models.enums import ComplianceClassification
from app.core.config import settings
from .rag import RegulationVectorStore, RegulationRetriever
from .llm import LLaMAComplianceEngine, LLMConfig

logger = logging.getLogger(__name__)


class RAGLLaMAComplianceService:
    """Integrated service combining RAG + LLaMA for compliance analysis."""
    
    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        vector_store: Optional[RegulationVectorStore] = None
    ):
        """Initialize the integrated service.
        
        Args:
            llm_config: Configuration for LLaMA engine
            vector_store: Optional pre-configured vector store
        """
        # Use config from settings if not provided
        if llm_config is None and settings.LLM_PROVIDER:
            llm_config = LLMConfig(
                provider=settings.LLM_PROVIDER,
                model=settings.LLM_MODEL if settings.LLM_PROVIDER != "groq" else settings.GROQ_MODEL,
                api_key=settings.GROQ_API_KEY if settings.LLM_PROVIDER == "groq" else None,
                temperature=settings.LLM_TEMPERATURE,
                timeout=settings.LLM_TIMEOUT,
                max_tokens=settings.LLM_MAX_TOKENS
            )
            logger.info(f"🔧 Using LLM provider from config: {settings.LLM_PROVIDER}")
        
        # Initialize components
        self.vector_store = vector_store or RegulationVectorStore()
        self.retriever = RegulationRetriever(self.vector_store)
        self.llama_engine = LLaMAComplianceEngine(config=llm_config)
        
        self._initialized = False
        self._chat_sessions: Dict[str, List[Dict[str, str]]] = {}
        
    async def initialize(self) -> None:
        """Initialize all components."""
        if self._initialized:
            return
        
        try:
            logger.info("🚀 Initializing RAG + LLaMA compliance service...")
            
            # Initialize RAG components
            logger.info("📚 Setting up vector store and retriever...")
            await self.retriever.initialize()
            
            # Initialize LLaMA
            logger.info("🤖 Connecting to LLaMA engine...")
            await self.llama_engine.initialize()
            
            self._initialized = True
            logger.info("✅ RAG + LLaMA service ready!")
            
            # Log configuration
            vector_stats = self.vector_store.get_stats()
            llm_info = self.llama_engine.get_info()
            logger.info(f"📊 Vector Store: {vector_stats.get('total_documents', 0)} regulations indexed")
            logger.info(f"🤖 LLM Provider: {llm_info['provider']} ({llm_info['model']})")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize service: {e}")
            raise
    
    async def analyze_policy(
        self,
        policy_text: str,
        policy_metadata: Optional[Dict[str, Any]] = None,
        top_k_regulations: int = 10
    ) -> Dict[str, Any]:
        """Full policy compliance analysis using RAG + LLaMA.
        
        Args:
            policy_text: Full policy document text
            policy_metadata: Optional metadata (filename, type, etc.)
            top_k_regulations: Number of regulations to retrieve
            
        Returns:
            Comprehensive analysis results
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info("🔍 Starting RAG + LLaMA policy analysis...")
        
        # Step 1: Retrieve relevant regulations using Legal-BERT embeddings
        logger.info(f"📖 Retrieving top {top_k_regulations} relevant regulations...")
        regulations = await self.retriever.retrieve_for_policy(
            policy_text=policy_text,
            top_k=top_k_regulations,
            min_relevance="HIGH"
        )
        
        if not regulations:
            logger.warning("⚠️  No regulations retrieved - using fallback analysis")
            regulations = []
        
        # Step 2: Format regulations for LLaMA
        formatted_regulations = self.retriever.format_regulations_for_llm(
            regulations=regulations,
            include_metadata=True
        )
        
        logger.info(f"✅ Retrieved {len(regulations)} regulations")
        
        # Step 3: LLaMA reasoning and classification
        logger.info("🧠 Running LLaMA compliance reasoning...")
        analysis_result = await self.llama_engine.analyze_compliance(
            policy_text=policy_text,
            regulations=formatted_regulations,
            policy_metadata=policy_metadata
        )
        
        # Step 4: Enrich results with retrieval metadata
        analysis_result['rag_metadata'] = {
            'regulations_retrieved': len(regulations),
            'top_regulation_sources': [
                r['metadata'].get('source', 'UNKNOWN') 
                for r in regulations[:5]
            ],
            'retrieval_scores': [
                r.get('similarity_score', 0.0)
                for r in regulations[:5]
            ]
        }
        
        logger.info(f"✅ Analysis complete: {analysis_result.get('classification')}")
        return analysis_result
    
    async def chat_about_policy(
        self,
        session_id: str,
        user_query: str,
        analysis_results: Dict[str, Any],
        policy_text: Optional[str] = None
    ) -> str:
        """Interactive Q&A about policy analysis.
        
        Args:
            session_id: Unique session identifier for conversation
            user_query: User's question
            analysis_results: Previous analysis results
            policy_text: Optional policy text for context
            
        Returns:
            Assistant's response
        """
        if not self._initialized:
            await self.initialize()
        
        # Get or create chat history
        if session_id not in self._chat_sessions:
            self._chat_sessions[session_id] = []
        
        chat_history = self._chat_sessions[session_id]
        
        # Retrieve relevant policy excerpt if policy text provided
        policy_excerpt = ""
        if policy_text and len(policy_text) > 500:
            # Use RAG to find relevant excerpt for the query
            relevant_sections = await self.retriever.retrieve_for_policy(
                policy_text=user_query,  # Use query to find relevant policy sections
                top_k=2
            )
            if relevant_sections:
                policy_excerpt = relevant_sections[0]['text'][:500]
        
        # Generate response
        response = await self.llama_engine.chat(
            user_query=user_query,
            analysis_results=analysis_results,
            chat_history=chat_history,
            policy_excerpt=policy_excerpt
        )
        
        # Update chat history
        chat_history.append({"role": "user", "content": user_query})
        chat_history.append({"role": "assistant", "content": response})
        
        # Keep only last 10 messages
        self._chat_sessions[session_id] = chat_history[-10:]
        
        return response
    
    async def analyze_section(
        self,
        section_text: str,
        section_type: str,
        top_k_regulations: int = 5
    ) -> Dict[str, Any]:
        """Analyze a specific policy section.
        
        Args:
            section_text: Text of the section
            section_type: Type of section (coverage, exclusions, etc.)
            top_k_regulations: Number of regulations to retrieve
            
        Returns:
            Section analysis results
        """
        if not self._initialized:
            await self.initialize()
        
        # Retrieve section-specific regulations
        regulations = await self.retriever.retrieve_for_section(
            section_text=section_text,
            section_type=section_type,
            top_k=top_k_regulations
        )
        
        formatted_regulations = self.retriever.format_regulations_for_llm(
            regulations=regulations,
            include_metadata=False
        )
        
        # Analyze with LLaMA
        result = await self.llama_engine.analyze_section(
            section_text=section_text,
            section_type=section_type,
            regulations=formatted_regulations
        )
        
        return result
    
    def clear_chat_session(self, session_id: str) -> None:
        """Clear chat history for a session."""
        if session_id in self._chat_sessions:
            del self._chat_sessions[session_id]
            logger.info(f"🗑️  Cleared chat session: {session_id}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status information about the service."""
        return {
            "initialized": self._initialized,
            "vector_store": self.vector_store.get_stats(),
            "llm_engine": self.llama_engine.get_info(),
            "active_chat_sessions": len(self._chat_sessions)
        }
