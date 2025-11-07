"""
Text analysis module for header detection and structure analysis.

Provides heuristics-based header detection for PDF text blocks.
"""

import logging
from typing import List, Dict, Any, Optional
import statistics

logger = logging.getLogger(__name__)


class TextAnalyzer:
    """Analyze text blocks to detect headers and structure."""
    
    def __init__(self):
        """Initialize text analyzer."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def detect_headers(self, text_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect headers from text blocks using heuristics.
        
        Args:
            text_blocks: List of text block dictionaries with font properties
        
        Returns:
            List of detected headers
        """
        if not text_blocks:
            return []
        
        # Analyze font sizes
        font_sizes = [block.get("font_size", 0) for block in text_blocks if block.get("font_size", 0) > 0]
        
        if not font_sizes:
            # No font size information, use other heuristics
            return self._detect_headers_by_style(text_blocks)
        
        # Calculate statistics
        median_size = statistics.median(font_sizes)
        mean_size = statistics.mean(font_sizes)
        
        # Headers are typically 1.2x - 2.5x larger than body text
        threshold = median_size * 1.2
        
        headers = []
        for block in text_blocks:
            font_size = block.get("font_size", 0)
            
            # Check multiple criteria
            is_header = False
            confidence = 0.0
            
            # Font size check
            if font_size >= threshold:
                is_header = True
                confidence += 0.4
            
            # Style check
            if block.get("is_bold", False):
                is_header = True
                confidence += 0.3
            
            # Position check (top of page/section)
            page_num = block.get("page_number", 0)
            if page_num > 0:
                # Check if this is one of the first blocks on the page
                blocks_on_page = [b for b in text_blocks if b.get("page_number") == page_num]
                if blocks_on_page.index(block) < 3:  # First 3 blocks on page
                    confidence += 0.2
            
            # Pattern matching
            text = block.get("text", "").strip()
            if self._matches_header_pattern(text):
                is_header = True
                confidence += 0.1
            
            if is_header and confidence >= 0.4:
                block_copy = block.copy()
                block_copy["type"] = "header"
                block_copy["confidence"] = min(confidence, 1.0)
                headers.append(block_copy)
        
        return headers
    
    def assign_header_levels(self, headers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assign hierarchical levels to headers (1-6).
        
        Args:
            headers: List of header dictionaries
        
        Returns:
            Headers with assigned levels
        """
        if not headers:
            return []
        
        # Sort by font size (largest = level 1)
        sorted_headers = sorted(headers, key=lambda h: h.get("font_size", 0), reverse=True)
        
        # Group by similar font sizes
        font_sizes = [h.get("font_size", 0) for h in sorted_headers]
        if not font_sizes:
            return headers
        
        # Create size groups
        size_groups = []
        current_group = [sorted_headers[0]]
        current_size = sorted_headers[0].get("font_size", 0)
        
        for header in sorted_headers[1:]:
            size = header.get("font_size", 0)
            # If size is within 10% of current group, add to same group
            if size >= current_size * 0.9:
                current_group.append(header)
            else:
                size_groups.append(current_group)
                current_group = [header]
                current_size = size
        
        if current_group:
            size_groups.append(current_group)
        
        # Assign levels
        for level, group in enumerate(size_groups, start=1):
            for header in group:
                header["level"] = min(level, 6)  # Max level 6
        
        return sorted_headers
    
    def structure_text(self, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Organize text into hierarchical structure.
        
        Args:
            blocks: List of text blocks
        
        Returns:
            Structured dictionary with sections and content
        """
        headers = self.detect_headers(blocks)
        headers = self.assign_header_levels(headers)
        
        # Build hierarchical structure
        structure = {
            "headers": headers,
            "sections": [],
            "body_text": []
        }
        
        # Group content under headers
        current_section = None
        current_content = []
        
        for block in blocks:
            # Check if this block is a header
            is_header = any(h.get("text") == block.get("text") for h in headers)
            
            if is_header:
                # Save previous section
                if current_section:
                    current_section["content"] = current_content
                    structure["sections"].append(current_section)
                
                # Start new section
                header = next(h for h in headers if h.get("text") == block.get("text"))
                current_section = {
                    "header": header,
                    "level": header.get("level", 1),
                    "content": []
                }
                current_content = []
            else:
                # Add to current section or body text
                if current_section:
                    current_content.append(block)
                else:
                    structure["body_text"].append(block)
        
        # Save last section
        if current_section:
            current_section["content"] = current_content
            structure["sections"].append(current_section)
        
        return structure
    
    def _detect_headers_by_style(self, text_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect headers using style heuristics when font size is unavailable.
        
        Args:
            text_blocks: List of text block dictionaries
        
        Returns:
            List of detected headers
        """
        headers = []
        
        for block in text_blocks:
            confidence = 0.0
            is_header = False
            
            # Bold text
            if block.get("is_bold", False):
                confidence += 0.4
                is_header = True
            
            # Pattern matching
            text = block.get("text", "").strip()
            if self._matches_header_pattern(text):
                confidence += 0.3
                is_header = True
            
            # Short lines (likely headers)
            if len(text.split()) <= 5:
                confidence += 0.2
            
            # All caps
            if text.isupper() and len(text) > 3:
                confidence += 0.1
                is_header = True
            
            if is_header and confidence >= 0.4:
                block_copy = block.copy()
                block_copy["type"] = "header"
                block_copy["confidence"] = min(confidence, 1.0)
                headers.append(block_copy)
        
        return headers
    
    def _matches_header_pattern(self, text: str) -> bool:
        """
        Check if text matches common header patterns.
        
        Args:
            text: Text to check
        
        Returns:
            True if text matches header pattern
        """
        text_lower = text.lower().strip()
        
        # Section numbers
        patterns = [
            r"^section\s+\d+",
            r"^article\s+\d+",
            r"^chapter\s+\d+",
            r"^\d+\.\s+[A-Z]",
            r"^[A-Z]\.\s+[A-Z]",
        ]
        
        import re
        for pattern in patterns:
            if re.match(pattern, text_lower):
                return True
        
        return False

