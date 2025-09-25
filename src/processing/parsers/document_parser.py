import os
import re
import pdfplumber
import spacy
from typing import List, Dict, Optional
from pathlib import Path
import logging
from langdetect import detect

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles document parsing and text extraction"""
    
    def __init__(self):
        # Try to load spaCy model, install if not available
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy English model not found. Please install: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, any]:
        """Extract text from PDF file with metadata"""
        try:
            text_content = ""
            metadata = {
                "total_pages": 0,
                "language": "unknown",
                "file_size": os.path.getsize(pdf_path)
            }
            
            with pdfplumber.open(pdf_path) as pdf:
                metadata["total_pages"] = len(pdf.pages)
                
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
            
            # Detect language
            if text_content.strip():
                try:
                    metadata["language"] = detect(text_content[:1000])
                except:
                    metadata["language"] = "en"  # Default to English
            
            return {
                "text": self.clean_text(text_content),
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return {"text": "", "metadata": {"error": str(e)}}
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]]', ' ', text)
        
        # Remove repeated punctuation
        text = re.sub(r'\.{2,}', '.', text)
        
        # Strip and return
        return text.strip()
    
    def extract_regulatory_patterns(self, text: str) -> List[Dict[str, str]]:
        """Extract regulatory patterns and references"""
        patterns = []
        
        # IRDAI regulation patterns
        irdai_pattern = r'IRDAI[\/\s\-]*\(?([^)]*)\)?'
        irdai_matches = re.finditer(irdai_pattern, text, re.IGNORECASE)
        
        for match in irdai_matches:
            patterns.append({
                "type": "IRDAI_REFERENCE",
                "text": match.group(0),
                "position": match.start()
            })
        
        # Date patterns for regulations
        date_pattern = r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})\b'
        date_matches = re.finditer(date_pattern, text)
        
        for match in date_matches:
            patterns.append({
                "type": "DATE",
                "text": match.group(0),
                "position": match.start()
            })
        
        # Policy number patterns
        policy_pattern = r'\b[A-Z]{2,4}[\d\/\-]{8,}\b'
        policy_matches = re.finditer(policy_pattern, text)
        
        for match in policy_matches:
            patterns.append({
                "type": "POLICY_NUMBER",
                "text": match.group(0),
                "position": match.start()
            })
        
        return patterns
    
    def segment_document(self, text: str, max_length: int = 512) -> List[str]:
        """Segment document into chunks for processing"""
        if not self.nlp:
            # Simple sentence splitting if spaCy not available
            sentences = text.split('.')
        else:
            doc = self.nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents]
        
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            if len(current_segment) + len(sentence) < max_length:
                current_segment += sentence + " "
            else:
                if current_segment:
                    segments.append(current_segment.strip())
                current_segment = sentence + " "
        
        if current_segment:
            segments.append(current_segment.strip())
        
        return segments

class ComplianceDocumentProcessor:
    """Specialized processor for compliance documents"""
    
    def __init__(self, document_processor: DocumentProcessor):
        self.doc_processor = document_processor
        self.compliance_keywords = [
            "compliance", "violation", "regulation", "guideline", 
            "mandatory", "requirement", "prohibited", "restricted",
            "penalty", "fine", "sanction", "breach"
        ]
    
    def process_document(self, file_path: str) -> Dict[str, any]:
        """Process a compliance document and extract relevant information"""
        # Extract text
        extraction_result = self.doc_processor.extract_text_from_pdf(file_path)
        text = extraction_result["text"]
        metadata = extraction_result["metadata"]
        
        if not text:
            return {"error": "No text extracted from document"}
        
        # Extract regulatory patterns
        patterns = self.doc_processor.extract_regulatory_patterns(text)
        
        # Segment document
        segments = self.doc_processor.segment_document(text)
        
        # Find compliance-relevant segments
        compliance_segments = self.find_compliance_segments(segments)
        
        # Extract key compliance indicators
        compliance_indicators = self.extract_compliance_indicators(text)
        
        return {
            "text": text,
            "segments": segments,
            "compliance_segments": compliance_segments,
            "patterns": patterns,
            "compliance_indicators": compliance_indicators,
            "metadata": metadata
        }
    
    def find_compliance_segments(self, segments: List[str]) -> List[Dict[str, any]]:
        """Find segments that likely contain compliance-related content"""
        compliance_segments = []
        
        for i, segment in enumerate(segments):
            segment_lower = segment.lower()
            keyword_count = sum(1 for keyword in self.compliance_keywords 
                              if keyword in segment_lower)
            
            if keyword_count > 0:
                compliance_segments.append({
                    "segment_id": i,
                    "text": segment,
                    "keyword_count": keyword_count,
                    "relevance_score": keyword_count / len(segment.split()) * 100
                })
        
        # Sort by relevance
        compliance_segments.sort(key=lambda x: x["relevance_score"], reverse=True)
        return compliance_segments
    
    def extract_compliance_indicators(self, text: str) -> Dict[str, any]:
        """Extract indicators that suggest compliance status"""
        indicators = {
            "positive_indicators": [],
            "negative_indicators": [],
            "neutral_indicators": []
        }
        
        positive_patterns = [
            r"complies?\s+with", r"adheres?\s+to", r"in\s+accordance\s+with",
            r"meets?\s+the\s+requirements", r"satisfies?\s+the\s+conditions"
        ]
        
        negative_patterns = [
            r"violates?", r"breaches?", r"non[- ]compliant?", r"fails?\s+to\s+meet",
            r"does\s+not\s+comply", r"in\s+violation\s+of"
        ]
        
        neutral_patterns = [
            r"requires?\s+review", r"subject\s+to\s+approval", r"pending\s+verification",
            r"needs?\s+clarification"
        ]
        
        for pattern_list, indicator_type in [
            (positive_patterns, "positive_indicators"),
            (negative_patterns, "negative_indicators"), 
            (neutral_patterns, "neutral_indicators")
        ]:
            for pattern in pattern_list:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    indicators[indicator_type].append({
                        "text": match.group(0),
                        "position": match.start(),
                        "context": text[max(0, match.start()-50):match.end()+50]
                    })
        
        return indicators