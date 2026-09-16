# backend/app/rag/retrieval.py
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..core.config import settings
from .embedding import EmbeddingService
from .reranking import RerankingService
from ..ai.router import QueryRouter, QueryCategory

class RetrievalService:
    """Service for retrieving relevant documents."""
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService(db)
        self.reranking_service = RerankingService()
    
    async def retrieve(
        self,
        query: str,
        category: Optional[QueryCategory] = None,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query."""
        top_k = top_k or settings.TOP_K_RETRIEVAL
        
        # Generate query embedding
        query_embeddings = await self.embedding_service.generate_embeddings([query])
        query_embedding = query_embeddings[0]
        
        # Search similar chunks
        results = self.embedding_service.search_similar(
            query_embedding=query_embedding,
            limit=top_k * 2  # Get more for reranking
        )
        
        # Rerank results
        reranked = self.reranking_service.rerank(
            query=query,
            results=results,
            top_k=top_k
        )
        
        return reranked
    
    async def retrieve_with_context(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        category: Optional[QueryCategory] = None
    ) -> Dict[str, Any]:
        """Retrieve documents and build context for LLM."""
        # Classify query if not provided
        if category is None:
            category = QueryRouter.classify(query)
        
        # Retrieve documents
        documents = await self.retrieve(query, category)
        
        # Build context
        context_parts = []
        sources = []
        
        for doc in documents:
            context_parts.append(doc["text"])
            
            # Extract source information
            metadata = doc.get("metadata", {})
            source_info = {
                "title": metadata.get("title", "Unknown"),
                "source_type": metadata.get("source_type", "other"),
                "url": metadata.get("url"),
                "university": metadata.get("university"),
                "academic_year": metadata.get("academic_year"),
                "page": metadata.get("page"),
                "similarity": doc.get("similarity", 0)
            }
            sources.append(source_info)
        
        context = "\n\n".join(context_parts)
        
        return {
            "query": query,
            "category": category.value,
            "context": context,
            "documents": documents,
            "sources": sources
        }