# backend/app/rag/embedding.py
from typing import List, Optional
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.config import settings
from ..ai.provider import AIProvider
from ..ai.openai_provider import OpenAIProvider

class EmbeddingService:
    """Service for generating and managing embeddings."""
    
    def __init__(self, db: Session):
        self.db = db
        self.provider = self._get_provider()
        self.dimension = 1536  # OpenAI embedding dimension
    
    def _get_provider(self) -> AIProvider:
        """Get the appropriate AI provider."""
        provider_type = settings.LLM_PROVIDER.lower()
        
        if provider_type == "openai":
            return OpenAIProvider()
        elif provider_type == "groq":
            from ..ai.groq_provider import GroqProvider
            return GroqProvider()
        else:
            # Default to OpenAI
            return OpenAIProvider()
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []
        
        # Process in batches to avoid API limits
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = await self.provider.generate_embeddings(batch)
            all_embeddings.extend(embeddings)
        
        return all_embeddings
    
    def store_embedding(
        self,
        document_id: str,
        chunk_index: int,
        chunk_text: str,
        embedding: List[float],
        metadata: Optional[dict] = None
    ) -> str:
        """Store an embedding in the database."""
        import uuid
        
        chunk_id = str(uuid.uuid4())
        
        # Convert embedding to PostgreSQL vector format
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        # Insert into pgvector table
        query = text("""
            INSERT INTO document_chunks 
            (id, document_id, chunk_index, chunk_text, embedding, metadata, created_at)
            VALUES 
            (:id, :document_id, :chunk_index, :chunk_text, :embedding::vector, :metadata, NOW())
        """)
        
        self.db.execute(
            query,
            {
                "id": chunk_id,
                "document_id": document_id,
                "chunk_index": chunk_index,
                "chunk_text": chunk_text,
                "embedding": embedding_str,
                "metadata": metadata or {}
            }
        )
        self.db.commit()
        
        return chunk_id
    
    def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
        document_ids: Optional[List[str]] = None
    ) -> List[dict]:
        """Search for similar chunks using cosine similarity."""
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        query = text("""
            SELECT 
                dc.id,
                dc.document_id,
                dc.chunk_index,
                dc.chunk_text,
                dc.metadata,
                1 - (dc.embedding <=> :embedding::vector) as similarity
            FROM document_chunks dc
            WHERE 1 - (dc.embedding <=> :embedding::vector) > :threshold
            ORDER BY dc.embedding <=> :embedding::vector
            LIMIT :limit
        """)
        
        result = self.db.execute(
            query,
            {
                "embedding": embedding_str,
                "threshold": threshold,
                "limit": limit
            }
        )
        
        chunks = []
        for row in result:
            chunks.append({
                "id": row.id,
                "document_id": row.document_id,
                "chunk_index": row.chunk_index,
                "text": row.chunk_text,
                "metadata": row.metadata,
                "similarity": float(row.similarity)
            })
        
        return chunks