"""
DOCX text extraction module.

Extracts text from Microsoft Word documents with style-based header detection.
"""

from pathlib import Path
from typing import List, Dict, Any
import logging

from docx import Document
from docx.shared import Pt
from docx.enum.style import WD_STYLE_TYPE

from .base_extractor import BaseExtractor, ExtractedTextResult

logger = logging.getLogger(__name__)


class DOCXExtractor(BaseExtractor):
    """Extract text from DOCX files with style-based header detection."""
    
    def __init__(self, gemini_client=None):
        """
        Initialize DOCX extractor.
        
        Args:
            gemini_client: Optional Gemini client for text processing
        """
        super().__init__()
        self.gemini_client = gemini_client
    
    def extract(self, file_path: str) -> ExtractedTextResult:
        """
        Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
        
        Returns:
            ExtractedTextResult with extracted text and metadata
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid or not a DOCX
        """
        self._log_extraction_start(file_path)
        
        # Validate file
        self.validate_file(file_path)
        
        try:
            doc = Document(file_path)
            
            # Extract paragraphs with style information
            text_blocks = []
            full_text = []
            
            for para in doc.paragraphs:
                if not para.text.strip():
                    continue
                
                # Classify paragraph based on style
                block = self._classify_paragraph(para)
                text_blocks.append(block)
                
                # Add to full text
                full_text.append(para.text)
            
            # Combine full text
            raw_text = "\n".join(full_text)
            
            # Extract headers
            headers = [block for block in text_blocks if block.get("type") in ["header", "title"]]
            
            # Extract metadata
            metadata = {
                "file_type": "docx",
                "is_scanned": False,
                "paragraph_count": len(text_blocks),
                "extraction_method": "text",
                "extraction_strategy": "python-docx",
                "headers_detected": len(headers)
            }
            
            result = ExtractedTextResult(
                raw_text=raw_text,
                structured_text=text_blocks,
                headers=headers,
                metadata=metadata
            )
            
            self._log_extraction_complete(file_path, result)
            return result
            
        except Exception as e:
            self._log_error(file_path, e)
            raise
    
    def _classify_paragraph(self, paragraph) -> Dict[str, Any]:
        """
        Classify paragraph based on style.
        
        Args:
            paragraph: python-docx Paragraph object
        
        Returns:
            Dictionary with text block information
        """
        style_name = paragraph.style.name.lower()
        text = paragraph.text.strip()
        
        # Determine type and level
        block_type = "body"
        level = 0
        
        # Check for heading styles
        if "heading" in style_name:
            block_type = "header"
            # Extract level from style name (e.g., "Heading 1" -> level 1)
            try:
                level = int(style_name.split()[-1])
            except (ValueError, IndexError):
                level = 1  # Default to level 1 if can't parse
        
        # Check for title style
        elif "title" in style_name:
            block_type = "title"
            level = 0
        
        # Check font properties for additional clues
        is_bold = False
        is_italic = False
        font_size = None
        
        if paragraph.runs:
            first_run = paragraph.runs[0]
            if first_run.font:
                is_bold = first_run.font.bold or False
                is_italic = first_run.font.italic or False
                if first_run.font.size:
                    font_size = first_run.font.size.pt
        
        return {
            "text": text,
            "type": block_type,
            "level": level,
            "style_name": paragraph.style.name,
            "font_size": font_size,
            "is_bold": is_bold,
            "is_italic": is_italic,
            "page_number": None  # DOCX doesn't have explicit page numbers
        }

