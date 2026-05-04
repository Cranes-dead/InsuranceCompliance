"""Core compliance service containing the main business logic."""

import asyncio
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..services.cache_service import CacheService

from ..core import get_logger
from ..core.exceptions import (
    ComplianceSystemException,
    DocumentProcessingError,
    ModelInferenceError,
)
from ..models import (
    ComplianceAnalysisResponse,
    ComplianceClassification,
    ViolationDetail,
    ViolationSeverity,
    ViolationType,
)
from ..processing.parsers.document_parser import DocumentParser
from ..ml.rag_llama_service import RAGLLaMAComplianceService
from ..ml.inference.phase2_compliance_engine import Phase2ComplianceEngine
from pathlib import Path

logger = get_logger(__name__)


class ComplianceService:
    """
    Core compliance service for document analysis.
    
    This service provides a clean interface for the API layer and handles
    all business logic related to compliance checking.
    """
    
    def __init__(self):
        """Initialize the compliance service."""
        self.document_parser = DocumentParser()
        # Primary: RAG+LLaMA (uses Legal-BERT for embeddings + regulation retrieval + LLaMA reasoning)
        self.rag_llama_service = RAGLLaMAComplianceService()
        # Fallback: Phase 2 classifier (if RAG+LLaMA unavailable)
        self.phase2_engine = Phase2ComplianceEngine()
        # Phase 5: Content-hash cache (Redis or in-memory)
        self.cache = CacheService()
        self._initialized = False
        self._use_rag_llama = True  # Default to RAG+LLaMA
        
    async def initialize(self) -> None:
        """Initialize service components asynchronously."""
        if self._initialized:
            return
            
        try:
            logger.info("Initializing compliance service...")
            
            # Try to initialize RAG+LLaMA (primary approach)
            try:
                logger.info("🚀 Attempting to initialize RAG+LLaMA service...")
                await self.rag_llama_service.initialize()
                self._use_rag_llama = True
                logger.info("✅ RAG+LLaMA service initialized successfully")
                logger.info("   - Legal-BERT: Embeddings only (no classification head)")
                logger.info("   - RAG: 112 IRDAI regulations indexed")
                logger.info("   - LLaMA: Reasoning engine connected")
            except Exception as rag_error:
                logger.warning(f"⚠️ RAG+LLaMA initialization failed: {rag_error}")
                logger.info("📋 Falling back to Phase 2 classifier...")
                await self.phase2_engine.initialize()
                self._use_rag_llama = False
                logger.info("✅ Phase 2 classifier initialized as fallback")
            
            self._initialized = True
            logger.info("Compliance service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize compliance service: {e}")
            raise ComplianceSystemException(
                "Service initialization failed",
                error_code="SERVICE_INIT_ERROR",
                details={"error": str(e)}
            )
    
    async def analyze_document(
        self,
        document_path: str,
        document_id: str,
        analysis_type: str = "full",
        include_explanation: bool = True,
        custom_rules: Optional[List[str]] = None
    ) -> ComplianceAnalysisResponse:
        """
        Analyze a document for compliance violations.
        
        Args:
            document_path: Path to the document file
            document_id: Unique identifier for the document
            analysis_type: Type of analysis to perform
            include_explanation: Whether to include AI explanation
            custom_rules: Optional custom rules to apply
            
        Returns:
            ComplianceAnalysisResponse with analysis results
            
        Raises:
            DocumentProcessingError: If document processing fails
            ModelInferenceError: If ML model inference fails
        """
        if not self._initialized:
            await self.initialize()
            
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting compliance analysis for document {document_id}")
            
            # Parse document
            document_content = await self._parse_document(document_path)
            
            # Phase 5: Check cache before running expensive LLM analysis
            cache_key = self.cache.make_document_key(document_content)
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"⚡ Cache HIT for document {document_id} — skipping LLM")
                analysis_result = cached_result
            else:
                # Perform compliance analysis (pass document_path for metadata)
                analysis_result = await self._analyze_compliance(document_content, document_path)
                
                # Cache the result (skip REQUIRES_REVIEW — LLM was uncertain, retry may improve)
                classification = analysis_result.get("classification", "")
                if classification != "REQUIRES_REVIEW":
                    await self.cache.set(cache_key, analysis_result)
                    logger.info(f"💾 Cached analysis result for document {document_id}")

            explanation = analysis_result.get("explanation") if include_explanation else None
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            violations = [
                self._build_violation_detail(violation, fallback_confidence=analysis_result.get("confidence", 0.0))
                for violation in analysis_result.get("violations", [])
            ]

            # Build response
            try:
                classification = ComplianceClassification(analysis_result["classification"])
            except ValueError:
                classification = ComplianceClassification.REQUIRES_REVIEW

            response = ComplianceAnalysisResponse(
                document_id=document_id,
                classification=classification,
                confidence=analysis_result["confidence"],
                violations=violations,
                recommendations=analysis_result["recommendations"],
                explanation=explanation,
                processing_time=processing_time,
                metadata={
                    "analysis_type": analysis_type,
                    "document_length": len(document_content),
                    "custom_rules_applied": len(custom_rules) if custom_rules else 0,
                    "compliance_score": analysis_result.get("compliance_score"),
                    "mandatory_requirements": analysis_result.get("mandatory_compliance", []),
                    "probabilities": analysis_result.get("probabilities", {}),
                }
            )
            
            logger.info(
                f"Completed compliance analysis for document {document_id} "
                f"in {processing_time:.2f} seconds"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Compliance analysis failed for document {document_id}: {e}")
            logger.debug(traceback.format_exc())
            
            if isinstance(e, (DocumentProcessingError, ModelInferenceError)):
                raise
                
            raise ComplianceSystemException(
                f"Analysis failed for document {document_id}",
                error_code="ANALYSIS_ERROR",
                details={"document_id": document_id, "error": str(e)}
            )
    
    async def analyze_batch(
        self,
        documents: List[Dict[str, str]],  # [{"id": str, "path": str}]
        analysis_type: str = "full",
        include_explanation: bool = True,
        custom_rules: Optional[List[str]] = None
    ) -> List[ComplianceAnalysisResponse]:
        """
        Analyze multiple documents in batch.
        
        Args:
            documents: List of document info dicts with id and path
            analysis_type: Type of analysis to perform
            include_explanation: Whether to include AI explanations
            custom_rules: Optional custom rules to apply
            
        Returns:
            List of ComplianceAnalysisResponse objects
        """
        if not self._initialized:
            await self.initialize()
            
        logger.info(f"Starting batch analysis for {len(documents)} documents")
        
        # Create analysis tasks
        tasks = []
        for doc in documents:
            task = self.analyze_document(
                document_path=doc["path"],
                document_id=doc["id"],
                analysis_type=analysis_type,
                include_explanation=include_explanation,
                custom_rules=custom_rules
            )
            tasks.append(task)
        
        # Execute tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_results = []
        failed_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Analysis failed for document {documents[i]['id']}: {result}")
                failed_count += 1
            else:
                successful_results.append(result)
        
        logger.info(
            f"Batch analysis completed: {len(successful_results)} successful, "
            f"{failed_count} failed"
        )
        
        return successful_results
    
    async def _parse_document(self, document_path: str) -> str:
        """Parse document and extract text content."""
        try:
            return await self.document_parser.parse(document_path)
        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to parse document: {document_path}",
                error_code="DOCUMENT_PARSE_ERROR",
                details={"path": document_path, "error": str(e)}
            )
    
    async def _analyze_compliance(self, content: str, document_path: str = None) -> Dict[str, Any]:
        """Perform compliance analysis using RAG+LLaMA or Phase2 fallback."""
        try:
            if self._use_rag_llama:
                # Use RAG+LLaMA (primary approach)
                logger.info("🔍 Using RAG+LLaMA for analysis...")
                try:
                    result = await self.rag_llama_service.analyze_policy(
                        policy_text=content,
                        policy_metadata={
                            "filename": Path(document_path).name if document_path else "unknown"
                        },
                        top_k_regulations=10  # Retrieve top 10 relevant regulations
                    )
                    logger.info("✅ RAG+LLaMA analysis completed")
                    return result
                except Exception as rag_error:
                    logger.warning(f"⚠️ RAG+LLaMA analysis failed: {rag_error}")
                    logger.info("📋 Falling back to Phase 2 classifier for this request...")
                    return await self.phase2_engine.analyze(content)
            else:
                # Use Phase 2 classifier (fallback)
                logger.info("📋 Using Phase 2 classifier (fallback mode)")
                return await self.phase2_engine.analyze(content)
        except Exception as e:
            raise ModelInferenceError(
                "Compliance engine inference failed",
                error_code="MODEL_INFERENCE_ERROR",
                details={"error": str(e)}
            )

    def _build_violation_detail(
        self,
        violation: Dict[str, Any],
        fallback_confidence: float
    ) -> ViolationDetail:
        violation_type = violation.get("type", ViolationType.OTHER)
        if not isinstance(violation_type, ViolationType):
            try:
                violation_type = ViolationType(str(violation_type))
            except ValueError:
                violation_type = ViolationType.OTHER

        severity = violation.get("severity", ViolationSeverity.MEDIUM)
        if not isinstance(severity, ViolationSeverity):
            try:
                severity = ViolationSeverity(str(severity))
            except ValueError:
                severity = ViolationSeverity.MEDIUM

        confidence = float(violation.get("confidence", fallback_confidence))

        return ViolationDetail(
            type=violation_type,
            severity=severity,
            description=violation.get("description", ""),
            regulation_reference=violation.get("regulation_reference"),
            suggested_action=violation.get("suggested_action"),
            confidence=confidence,
            location=violation.get("location"),
        )
    
    async def get_compliance_statistics(
        self,
        document_ids: Optional[List[str]] = None
    ) -> Dict:
        """Get compliance statistics for documents from the database."""
        try:
            from ..db import get_supabase_service
            db = get_supabase_service()
            stats = await db.get_statistics()
            return stats
        except Exception as e:
            logger.error(f"Failed to get compliance statistics from database: {e}")
            # Return empty stats structure on error rather than fake data
            return {
                "totalPolicies": 0,
                "compliantPolicies": 0,
                "nonCompliantPolicies": 0,
                "reviewRequired": 0,
                "averageScore": 0,
                "recentAnalyses": [],
                "error": str(e)
            }
    
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized
    
    async def generate_chat_response(
        self,
        query: str,
        context: str
    ) -> str:
        """
        Generate chat response using LLaMA.
        
        Args:
            query: User's question
            context: Context string with policy information
            
        Returns:
            AI-generated response
        """
        try:
            # Try to use RAG LLaMA service if available
            from ..ml.rag_llama_service import RAGLLaMAComplianceService
            
            # Check if we have a RAG LLaMA service instance
            if not hasattr(self, 'rag_llama_service'):
                self.rag_llama_service = RAGLLaMAComplianceService()
                await self.rag_llama_service.initialize()
            
            # Use simplified chat (context is pre-built)
            # Extract policy data from context if available
            analysis_results = {"explanation": context}
            
            response = await self.rag_llama_service.llama_engine.provider.generate(
                prompt=f"{context}\n\nProvide a clear, helpful response to the user.",
                temperature=0.3
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            logger.debug(f"Full error details: {e.__class__.__name__}: {str(e)}")
            
            # Generate intelligent fallback response
            if "Policy Information" in context:
                # Extract key information from context
                lines = context.split('\n')
                policy_info = {}
                for line in lines:
                    if ': ' in line:
                        key, value = line.split(': ', 1)
                        policy_info[key.strip('- ')] = value
                
                # Build user-friendly response
                filename = policy_info.get('Filename', 'the policy')
                classification = policy_info.get('Classification', 'UNKNOWN')
                score = policy_info.get('Compliance Score', 'N/A')
                
                fallback = f"Based on the analysis of {filename}:\n\n"
                
                if 'violation' in query.lower() or 'issue' in query.lower() or 'problem' in query.lower():
                    fallback += f"**Status:** {classification}\n"
                    fallback += f"**Compliance Score:** {score}\n\n"
                    
                    if 'Violations Found:' in context:
                        # Extract violation count
                        for line in lines:
                            if 'Violations Found:' in line:
                                fallback += f"I found {line.split(':')[1].strip()} violation(s) in your policy.\n\n"
                                break
                        
                        # Extract violations
                        in_violations = False
                        for line in lines:
                            if 'Key Violations:' in line:
                                in_violations = True
                                continue
                            if in_violations and line.strip().startswith(('1.', '2.', '3.')):
                                fallback += f"{line.strip()}\n"
                            elif in_violations and 'Recommendations:' in line:
                                break
                    else:
                        fallback += "No specific violations were detected in the initial analysis.\n"
                
                elif 'fix' in query.lower() or 'recommendation' in query.lower() or 'improve' in query.lower():
                    fallback += f"**Current Status:** {classification} ({score})\n\n"
                    fallback += "**Recommendations to improve compliance:**\n\n"
                    
                    if 'Recommendations:' in context:
                        in_recs = False
                        for line in lines:
                            if 'Recommendations:' in line:
                                in_recs = True
                                continue
                            if in_recs and line.strip().startswith(('1.', '2.', '3.')):
                                fallback += f"{line.strip()}\n"
                            elif in_recs and 'User Question:' in line:
                                break
                
                elif 'regulation' in query.lower() or 'irdai' in query.lower():
                    fallback += "This policy was analyzed against IRDAI insurance regulations.\n\n"
                    fallback += f"**Compliance Status:** {classification}\n"
                    fallback += f"**Confidence:** {policy_info.get('Confidence', 'N/A')}\n\n"
                    fallback += "The analysis used relevant IRDAI guidelines to assess compliance."
                
                else:
                    # General query
                    fallback += f"**Classification:** {classification}\n"
                    fallback += f"**Compliance Score:** {score}\n"
                    fallback += f"**Confidence:** {policy_info.get('Confidence', 'N/A')}\n\n"
                    fallback += "For specific information about violations or recommendations, please ask about those topics."
                
                return fallback
            else:
                return f"I'd be happy to help answer '{query}', but I need a policy to analyze first. Please upload a policy document to get started."