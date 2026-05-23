"""Core compliance service containing the main business logic."""

import asyncio
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core import get_logger, settings
from ..core.exceptions import (
    ComplianceSystemException,
    DocumentProcessingError,
    ModelInferenceError,
)
from ..ml.inference.phase2_compliance_engine import Phase2ComplianceEngine
from ..ml.rag_llama_service import RAGLLaMAComplianceService
from ..models import (
    ComplianceAnalysisResponse,
    ComplianceClassification,
    ViolationDetail,
    ViolationSeverity,
    ViolationType,
)
from ..processing.parsers.document_parser import DocumentParser
from ..services.cache_service import CacheService

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

        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_TASKS)

        async def _bounded_analyze(doc: Dict[str, str]) -> ComplianceAnalysisResponse:
            async with semaphore:
                return await self.analyze_document(
                    document_path=doc["path"],
                    document_id=doc["id"],
                    analysis_type=analysis_type,
                    include_explanation=include_explanation,
                    custom_rules=custom_rules
                )

        tasks = [_bounded_analyze(doc) for doc in documents]

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
                "violationBreakdown": [],
                "error": str(e)
            }

    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized
