"""
Simple document parser for frontend compatibility.
"""

import PyPDF2
from pathlib import Path
from typing import Union

def parse_document(file_path: Union[str, Path]) -> str:
    """
    Parse document and extract text.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Extracted text content
    """
    try:
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.pdf':
            return _parse_pdf(file_path)
        elif file_path.suffix.lower() == '.txt':
            return _parse_txt(file_path)
        else:
            return f"Unsupported file format: {file_path.suffix}"
    
    except Exception as e:
        return f"Error parsing document: {str(e)}"


def _parse_pdf(file_path: Path) -> str:
    """Parse PDF file."""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text.strip()


def _parse_txt(file_path: Path) -> str:
    """Parse text file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()