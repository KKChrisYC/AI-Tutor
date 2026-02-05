"""
Text splitter for chunking documents
"""
from typing import List, Dict, Optional
import re


class TextSplitter:
    """
    Split text into chunks for vector embedding.
    
    Supports multiple splitting strategies optimized for educational content.
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize the text splitter.
        
        Args:
            chunk_size: Target size of each chunk (in characters)
            chunk_overlap: Overlap between consecutive chunks
            separators: List of separators to split on (in order of priority)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",      # Paragraph break
            "\n",        # Line break
            "。",        # Chinese period
            ".",         # English period
            "；",        # Chinese semicolon
            ";",         # English semicolon
            "，",        # Chinese comma
            ",",         # English comma
            " ",         # Space
            ""           # Character level (last resort)
        ]
    
    def split_text(self, text: str, metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: Text to split
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dicts with content and metadata
        """
        chunks = self._recursive_split(text, self.separators)
        
        # Add metadata to each chunk
        result = []
        for i, chunk in enumerate(chunks):
            chunk_data = {
                "content": chunk,
                "chunk_index": i,
                "char_count": len(chunk)
            }
            if metadata:
                chunk_data["metadata"] = metadata
            result.append(chunk_data)
        
        return result
    
    def split_document(self, document: Dict) -> List[Dict]:
        """
        Split a parsed document into chunks.
        
        Args:
            document: Document dict from PDFParser
            
        Returns:
            List of chunks with source information
        """
        chunks = []
        filename = document.get("filename", "unknown")
        
        # Process each page separately to maintain page references
        for page in document.get("pages", []):
            page_num = page["page_number"]
            content = page["content"]
            
            # Split page content
            page_chunks = self._recursive_split(content, self.separators)
            
            for i, chunk_content in enumerate(page_chunks):
                chunks.append({
                    "content": chunk_content,
                    "metadata": {
                        "source": filename,
                        "page": page_num,
                        "chunk_index": i
                    }
                })
        
        return chunks
    
    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """
        Recursively split text using separators.
        
        Args:
            text: Text to split
            separators: Remaining separators to try
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # If text is already small enough, return it
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []
        
        # Try each separator
        for i, separator in enumerate(separators):
            if separator == "":
                # Character-level split (last resort)
                return self._split_by_size(text)
            
            if separator in text:
                splits = text.split(separator)
                
                # Recursively process each split
                chunks = []
                current_chunk = ""
                
                for split in splits:
                    # Add separator back (except for the last one)
                    piece = split + separator if separator else split
                    
                    if len(current_chunk) + len(piece) <= self.chunk_size:
                        current_chunk += piece
                    else:
                        if current_chunk.strip():
                            # Current chunk is full, save it
                            chunks.append(current_chunk.strip())
                        
                        # Start new chunk (with overlap if possible)
                        if self.chunk_overlap > 0 and current_chunk:
                            overlap = current_chunk[-self.chunk_overlap:]
                            current_chunk = overlap + piece
                        else:
                            current_chunk = piece
                        
                        # If piece itself is too large, split it further
                        if len(current_chunk) > self.chunk_size:
                            sub_chunks = self._recursive_split(
                                current_chunk, 
                                separators[i+1:]
                            )
                            if sub_chunks:
                                chunks.extend(sub_chunks[:-1])
                                current_chunk = sub_chunks[-1] if sub_chunks else ""
                
                # Don't forget the last chunk
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                
                return chunks
        
        # No separator found, split by size
        return self._split_by_size(text)
    
    def _split_by_size(self, text: str) -> List[str]:
        """Split text by fixed size with overlap."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            if chunk.strip():
                chunks.append(chunk.strip())
            
            start = end - self.chunk_overlap
        
        return chunks


class CodeAwareTextSplitter(TextSplitter):
    """
    Text splitter that preserves code blocks.
    
    Useful for Data Structures course materials that contain code examples.
    """
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        super().__init__(chunk_size, chunk_overlap)
        # Pattern to match code blocks
        self.code_pattern = re.compile(
            r'```[\s\S]*?```|'  # Markdown code blocks
            r'(?:^|\n)(?:    |\t).*(?:\n(?:    |\t).*)*',  # Indented code
            re.MULTILINE
        )
    
    def split_text(self, text: str, metadata: Optional[Dict] = None) -> List[Dict]:
        """Split text while preserving code blocks."""
        # Find all code blocks
        code_blocks = list(self.code_pattern.finditer(text))
        
        if not code_blocks:
            return super().split_text(text, metadata)
        
        chunks = []
        last_end = 0
        
        for match in code_blocks:
            # Split text before code block
            before_text = text[last_end:match.start()]
            if before_text.strip():
                chunks.extend(super().split_text(before_text, metadata))
            
            # Keep code block as a single chunk (if not too large)
            code_block = match.group()
            if len(code_block) <= self.chunk_size * 2:  # Allow larger chunks for code
                chunk_data = {
                    "content": code_block,
                    "chunk_index": len(chunks),
                    "char_count": len(code_block),
                    "is_code": True
                }
                if metadata:
                    chunk_data["metadata"] = metadata
                chunks.append(chunk_data)
            else:
                # Code block too large, split it
                chunks.extend(super().split_text(code_block, metadata))
            
            last_end = match.end()
        
        # Handle remaining text after last code block
        remaining = text[last_end:]
        if remaining.strip():
            chunks.extend(super().split_text(remaining, metadata))
        
        return chunks
