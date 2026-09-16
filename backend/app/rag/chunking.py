# backend/app/rag/chunking.py
from typing import List, Dict, Any, Optional
import re
from dataclasses import dataclass

@dataclass
class Chunk:
    """Represents a document chunk."""
    text: str
    index: int
    metadata: Dict[str, Any]

class ChunkingService:
    """Service for chunking documents."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """Split text into chunks with overlap."""
        if not text:
            return []
        
        # Clean text
        text = self._clean_text(text)
        
        # Split by sentences first
        sentences = self._split_sentences(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(Chunk(
                    text=chunk_text,
                    index=chunk_index,
                    metadata=metadata or {}
                ))
                chunk_index += 1
                
                # Keep overlap
                overlap_text = self._get_overlap(current_chunk)
                current_chunk = [overlap_text]
                current_length = len(overlap_text)
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add remaining
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(Chunk(
                text=chunk_text,
                index=chunk_index,
                metadata=metadata or {}
            ))
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace and special characters."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s.,;:!?()\-\[\]{}"\'/]', '', text)
        return text.strip()
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap(self, sentences: List[str]) -> str:
        """Get overlap text from the end of sentences."""
        overlap = []
        current_length = 0
        
        for sentence in reversed(sentences):
            if current_length + len(sentence) > self.chunk_overlap:
                break
            overlap.insert(0, sentence)
            current_length += len(sentence)
        
        return ' '.join(overlap)