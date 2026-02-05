"""
PDF document parser using PyMuPDF
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Optional
import re


class PDFParser:
    """Parse PDF documents and extract text content"""
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> Dict:
        """
        Extract text content from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict containing:
                - filename: Name of the file
                - total_pages: Total number of pages
                - pages: List of page contents with metadata
                - full_text: Complete text content
        """
        doc = fitz.open(file_path)
        filename = Path(file_path).name
        
        pages = []
        full_text_parts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            
            # Clean up the text
            text = PDFParser._clean_text(text)
            
            if text.strip():  # Only add non-empty pages
                pages.append({
                    "page_number": page_num + 1,
                    "content": text,
                    "char_count": len(text)
                })
                full_text_parts.append(f"[第{page_num + 1}页]\n{text}")
        
        doc.close()
        
        return {
            "filename": filename,
            "total_pages": len(doc),
            "pages": pages,
            "full_text": "\n\n".join(full_text_parts)
        }
    
    @staticmethod
    def extract_text_from_bytes(file_bytes: bytes, filename: str) -> Dict:
        """
        Extract text from PDF bytes (for uploaded files).
        
        Args:
            file_bytes: PDF file content as bytes
            filename: Original filename
            
        Returns:
            Dict with extracted content
        """
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        pages = []
        full_text_parts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            text = PDFParser._clean_text(text)
            
            if text.strip():
                pages.append({
                    "page_number": page_num + 1,
                    "content": text,
                    "char_count": len(text)
                })
                full_text_parts.append(f"[第{page_num + 1}页]\n{text}")
        
        total_pages = len(doc)
        doc.close()
        
        return {
            "filename": filename,
            "total_pages": total_pages,
            "pages": pages,
            "full_text": "\n\n".join(full_text_parts)
        }
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean extracted text.
        
        - Remove excessive whitespace
        - Normalize line breaks
        - Remove page headers/footers patterns
        """
        # Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Normalize line breaks (keep paragraph structure)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove common header/footer patterns (page numbers, etc.)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    @staticmethod
    def get_pdf_metadata(file_path: str) -> Dict:
        """Get PDF metadata (title, author, etc.)"""
        doc = fitz.open(file_path)
        metadata = doc.metadata
        page_count = len(doc)
        doc.close()
        
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "page_count": page_count
        }
