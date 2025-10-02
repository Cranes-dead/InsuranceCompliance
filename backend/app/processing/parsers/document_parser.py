"""
Document parser for extracting text from various document formats.
Refactored from the original document_parser.py to follow best practices.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import aiofiles

from ...core import get_logger
from ...core.exceptions import DocumentProcessingError
from ...models import DocumentType, FileExtension

logger = get_logger(__name__)


class DocumentParser:
    """
    Unified document parser supporting multiple file formats.
    
    This parser handles PDF, TXT, and DOCX files and provides
    asynchronous processing for better performance.
    """
    
    def __init__(self):
        """Initialize the document parser."""
        self._parsers = {}
        self._initialize_parsers()
    
    def _initialize_parsers(self):
        """Initialize format-specific parsers."""
        try:
            # Import parsers dynamically to handle missing dependencies gracefully
            import pdfplumber
            self._parsers[FileExtension.PDF] = self._parse_pdf
        except ImportError:
            logger.warning("pdfplumber not available - PDF parsing disabled")
        
        try:
            from docx import Document
            self._parsers[FileExtension.DOCX] = self._parse_docx
        except ImportError:
            logger.warning("python-docx not available - DOCX parsing disabled")
        
        # Text files are always supported
        self._parsers[FileExtension.TXT] = self._parse_txt
    
    async def parse(
        self,
        file_path: str,
        document_type: Optional[DocumentType] = None
    ) -> str:
        """
        Parse document and extract text content.
        
        Args:
            file_path: Path to the document file
            document_type: Optional document type hint
            
        Returns:
            Extracted text content
            
        Raises:
            DocumentProcessingError: If parsing fails
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise DocumentProcessingError(
                f"Document file not found: {file_path}",
                error_code="FILE_NOT_FOUND"
            )
        
        # Determine file extension
        extension = file_path_obj.suffix.lower()
        
        if extension not in self._parsers:
            raise DocumentProcessingError(
                f"Unsupported file format: {extension}",
                error_code="UNSUPPORTED_FORMAT",
                details={"supported_formats": list(self._parsers.keys())}
            )
        
        try:
            logger.info(f"Parsing document: {file_path}")
            
            # Parse document using appropriate parser
            parser_func = self._parsers[extension]
            content = await parser_func(file_path_obj)
            
            if not content or not content.strip():
                raise DocumentProcessingError(
                    "Document appears to be empty or unreadable",
                    error_code="EMPTY_DOCUMENT"
                )
            
            logger.info(f"Successfully parsed document: {file_path} ({len(content)} characters)")
            return content.strip()
            
        except DocumentProcessingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing document {file_path}: {e}")
            raise DocumentProcessingError(
                f"Failed to parse document: {file_path}",
                error_code="PARSE_ERROR",
                details={"error": str(e), "file_path": str(file_path)}
            )
    
    async def _parse_pdf(self, file_path: Path) -> str:
        """Parse PDF document using pdfplumber."""
        import pdfplumber
        
        def _extract_text():
            text_content = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
            return "\n".join(text_content)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _extract_text)
    
    async def _parse_docx(self, file_path: Path) -> str:
        """Parse DOCX document using python-docx."""
        from docx import Document
        
        def _extract_text():
            doc = Document(str(file_path))  # Convert Path to string
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            return "\n".join(text_content)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _extract_text)
    
    async def _parse_txt(self, file_path: Path) -> str:
        """Parse plain text document."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                return await file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            async with aiofiles.open(file_path, 'r', encoding='latin-1') as file:
                return await file.read()
    
    def get_supported_formats(self) -> list:
        """Get list of supported file formats."""
        return list(self._parsers.keys())
    
    async def validate_document(
        self,
        file_path: str,
        max_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate document before parsing.
        
        Args:
            file_path: Path to the document file
            max_size: Maximum allowed file size in bytes
            
        Returns:
            Dictionary with validation results
        """
        file_path_obj = Path(file_path)
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_info": {}
        }
        
        # Check if file exists
        if not file_path_obj.exists():
            validation_result["valid"] = False
            validation_result["errors"].append("File does not exist")
            return validation_result
        
        # Get file info
        stat = file_path_obj.stat()
        validation_result["file_info"] = {
            "size": stat.st_size,
            "extension": file_path_obj.suffix.lower(),
            "name": file_path_obj.name
        }
        
        # Check file size
        if max_size and stat.st_size > max_size:
            validation_result["valid"] = False
            validation_result["errors"].append(f"File too large: {stat.st_size} bytes")
        
        # Check format support
        extension = file_path_obj.suffix.lower()
        if extension not in self._parsers:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Unsupported format: {extension}")
        
        return validation_result