"""Core compliance service containing the main business logic."""

import asyncio
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

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
from ..ml.inference.phase2_compliance_engine import Phase2ComplianceEngine

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
        self.compliance_engine = Phase2ComplianceEngine()
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize service components asynchronously."""
        if self._initialized:
            return
            
        try:
            logger.info("Initializing compliance service...")
            await self.compliance_engine.initialize()
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
            
            # Perform compliance analysis
            analysis_result = await self._analyze_compliance(document_content)

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
    
    async def _analyze_compliance(self, content: str) -> Dict[str, Any]:
        """Perform compliance analysis using the simple engine."""
        try:
            return await self.compliance_engine.analyze(content)
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
        """Get compliance statistics for documents."""
        # This would typically query a database
        # For now, return mock statistics
        return {
            "total_documents": 100,
            "compliant_count": 70,
            "non_compliant_count": 20,
            "requires_review_count": 10,
            "compliance_rate": 70.0,
            "average_confidence": 0.85,
            "most_common_violations": [
                {"type": "REGULATION_BREACH", "count": 15},
                {"type": "POLICY_INCONSISTENCY", "count": 8},
            ]
        }
    
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized