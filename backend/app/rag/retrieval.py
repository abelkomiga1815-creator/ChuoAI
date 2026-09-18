# backend/app/rag/retrieval.py
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.config import settings
from .embedding import EmbeddingService
from .reranking import RerankingService
from ..ai.router import QueryRouter, QueryCategory
from ..models.source import SourceType, SourceAuthority
from ..models.academic_year import TCUStatistic, TCUStatisticType, AcademicYear


class RetrievalFilters:
    """Filters for retrieval queries."""
    def __init__(
        self,
        source_types: Optional[List[SourceType]] = None,
        academic_year: Optional[str] = None,
        academic_year_id: Optional[str] = None,
        university_id: Optional[str] = None,
        is_verified: Optional[bool] = None,
        authority_levels: Optional[List[SourceAuthority]] = None,
        min_similarity: Optional[float] = None,
    ):
        self.source_types = source_types
        self.academic_year = academic_year
        self.academic_year_id = academic_year_id
        self.university_id = university_id
        self.is_verified = is_verified
        self.authority_levels = authority_levels
        self.min_similarity = min_similarity


class RetrievalService:
    """Service for retrieving relevant documents."""
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService(db)
        self.reranking_service = RerankingService()
    
    def _build_filter_conditions(self, filters: Optional[RetrievalFilters]) -> tuple[str, dict]:
        """Build SQL WHERE conditions from filters."""
        conditions = []
        params = {}
        
        if not filters:
            return "", params
        
        if filters.source_types:
            placeholders = ", ".join([f":source_type_{i}" for i in range(len(filters.source_types))])
            conditions.append(f"dc.metadata->>'source_type' IN ({placeholders})")
            for i, st in enumerate(filters.source_types):
                params[f"source_type_{i}"] = st.value
        
        if filters.academic_year:
            conditions.append("dc.metadata->>'academic_year' = :academic_year")
            params["academic_year"] = filters.academic_year
        
        if filters.academic_year_id:
            conditions.append("dc.metadata->>'academic_year_id' = :academic_year_id")
            params["academic_year_id"] = filters.academic_year_id
        
        if filters.university_id:
            conditions.append("dc.metadata->>'university_id' = :university_id")
            params["university_id"] = filters.university_id
        
        if filters.is_verified is not None:
            conditions.append("(dc.metadata->>'is_verified')::boolean = :is_verified")
            params["is_verified"] = filters.is_verified
        
        if filters.authority_levels:
            placeholders = ", ".join([f":authority_{i}" for i in range(len(filters.authority_levels))])
            conditions.append(f"dc.metadata->>'authority_level' IN ({placeholders})")
            for i, al in enumerate(filters.authority_levels):
                params[f"authority_{i}"] = al.value
        
        if filters.min_similarity is not None:
            conditions.append("1 - (dc.embedding <=> :embedding::vector) >= :min_sim")
            params["min_sim"] = filters.min_similarity
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params

    async def retrieve(
        self,
        query: str,
        category: Optional[QueryCategory] = None,
        top_k: int = None,
        filters: Optional[RetrievalFilters] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query with optional filters."""
        top_k = top_k or settings.TOP_K_RETRIEVAL
        
        # Generate query embedding
        query_embeddings = await self.embedding_service.generate_embeddings([query])
        query_embedding = query_embeddings[0]
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        # Build filter conditions
        where_clause, filter_params = self._build_filter_conditions(filters)
        
        # Search similar chunks with filters
        query_sql = text(f"""
            SELECT 
                dc.id,
                dc.document_id,
                dc.chunk_index,
                dc.chunk_text,
                dc.metadata,
                1 - (dc.embedding <=> :embedding::vector) as similarity
            FROM document_chunks dc
            WHERE 1 - (dc.embedding <=> :embedding::vector) > :threshold
            AND {where_clause}
            ORDER BY dc.embedding <=> :embedding::vector
            LIMIT :limit
        """)
        
        params = {
            "embedding": embedding_str,
            "threshold": settings.SIMILARITY_THRESHOLD if hasattr(settings, 'SIMILARITY_THRESHOLD') else 0.7,
            "limit": top_k * 2,  # Get more for reranking
            **filter_params
        }
        
        result = self.db.execute(query_sql, params)
        
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
        
        # Rerank results
        reranked = self.reranking_service.rerank(
            query=query,
            results=chunks,
            top_k=top_k
        )
        
        return reranked
    
    async def retrieve_with_context(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        category: Optional[QueryCategory] = None,
        filters: Optional[RetrievalFilters] = None
    ) -> Dict[str, Any]:
        """Retrieve documents and build context for LLM with fallback strategies."""
        # Classify query if not provided
        if category is None:
            category = QueryRouter.classify(query)
        
        # Extract entities for auto-filtering
        entities = QueryRouter.extract_entities(query)
        
        # Auto-apply entity-based filters if not explicitly provided
        if filters is None:
            filters = RetrievalFilters()
        
        # If university entity found and no university filter set, use it
        if entities.get("university") and not filters.university_id:
            # Try to resolve university alias to ID
            from ..models.university import University, UniversityAlias
            uni = self.db.query(University).filter(
                (University.name.ilike(f"%{entities['university']}%")) |
                (University.abbreviation.ilike(f"%{entities['university']}%"))
            ).first()
            if not uni:
                alias = self.db.query(UniversityAlias).filter(
                    UniversityAlias.alias.ilike(f"%{entities['university']}%")
                ).first()
                if alias:
                    uni = self.db.query(University).filter(University.id == alias.university_id).first()
            if uni:
                filters.university_id = uni.id
        
        # If academic year mentioned, use it
        if entities.get("academic_year") and not filters.academic_year:
            filters.academic_year = entities["academic_year"]
        
        # Determine academic year for retrieval
        academic_year = entities.get("academic_year") or filters.academic_year
        
        # STRATEGY 1: For TCU_STATISTICS, try structured lookup FIRST
        structured_results = []
        if category == QueryCategory.TCU_STATISTICS:
            structured_results = await self.lookup_tcu_statistics(query, academic_year)
        
        # STRATEGY 2: Standard vector retrieval with filters
        documents = []
        # For TCU_STATISTICS with structured results, we can skip vector search if we have good structured results
        # This also handles the case where embeddings are not available (missing API key)
        skip_vector_search = (category == QueryCategory.TCU_STATISTICS and len(structured_results) > 0)
        
        if not skip_vector_search:
            try:
                documents = await self.retrieve(query, category, filters=filters)
            except Exception as e:
                # If vector search fails (e.g., missing API key), log and continue with other strategies
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Vector search failed, continuing with structured/fallback: {e}")
                documents = []
        
        # STRATEGY 3: If no documents and no structured results, try fallback retrieval
        fallback_results = []
        if not documents and not structured_results:
            fallback_results = await self._fallback_retrieval(query, category, academic_year)
        
        # Combine all results (structured first, then vector, then fallback)
        all_documents = structured_results + documents + fallback_results
        
        # Deduplicate by ID
        seen_ids = set()
        unique_documents = []
        for doc in all_documents:
            doc_id = doc.get("id")
            if doc_id and doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_documents.append(doc)
            elif not doc_id:
                unique_documents.append(doc)
        
        # Build context
        context_parts = []
        sources = []
        
        for doc in unique_documents:
            context_parts.append(doc["text"])
            
            # Extract source information
            metadata = doc.get("metadata", {})
            source_info = {
                "title": metadata.get("title", "Unknown"),
                "source_type": metadata.get("source_type", "other"),
                "authority_level": metadata.get("authority_level", "LEVEL_5"),
                "url": metadata.get("url"),
                "university": metadata.get("university"),
                "university_id": metadata.get("university_id"),
                "academic_year": metadata.get("academic_year"),
                "academic_year_id": metadata.get("academic_year_id"),
                "page": metadata.get("page"),
                "section": metadata.get("section_title"),
                "similarity": doc.get("similarity", 0),
                "is_verified": metadata.get("is_verified", False)
            }
            sources.append(source_info)
        
        context = "\n\n".join(context_parts)
        
        return {
            "query": query,
            "category": category.value,
            "context": context,
            "documents": unique_documents,
            "sources": sources,
            "entities": entities,
            "filters_applied": {
                "source_types": [st.value for st in filters.source_types] if filters.source_types else None,
                "academic_year": filters.academic_year,
                "university_id": filters.university_id,
                "is_verified": filters.is_verified,
            } if filters else None,
            "retrieval_strategies": {
                "structured_tcu_stats": len(structured_results) > 0,
                "vector_search": len(documents) > 0,
                "fallback": len(fallback_results) > 0,
            }
        }

    async def retrieve_for_verification(
        self,
        university_name: Optional[str] = None,
        programme_name: Optional[str] = None,
        academic_year: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Specialized retrieval for verification queries."""
        query_parts = []
        if university_name:
            query_parts.append(university_name)
        if programme_name:
            query_parts.append(programme_name)
        if academic_year:
            query_parts.append(academic_year)
        
        query = " ".join(query_parts) if query_parts else "university programme verification"
        
        filters = RetrievalFilters(
            source_types=[SourceType.TCU_OFFICIAL, SourceType.UNIVERSITY_OFFICIAL, SourceType.GOVERNMENT],
            academic_year=academic_year,
            authority_levels=[SourceAuthority.LEVEL_1, SourceAuthority.LEVEL_2, SourceAuthority.LEVEL_3],
            is_verified=True
        )
        
        if university_name:
            # Try to get university ID
            from ..models.university import University
            uni = self.db.query(University).filter(
                University.name.ilike(f"%{university_name}%")
            ).first()
            if uni:
                filters.university_id = uni.id
        
        return await self.retrieve(query, filters=filters, top_k=top_k)

    async def lookup_tcu_statistics(
        self,
        query: str,
        academic_year: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Direct structured lookup of TCU statistics from the database.
        Returns structured TCU statistic records matching the query.
        """
        from ..models.academic_year import TCUStatistic, TCUStatisticType, AcademicYear
        
        query_lower = query.lower()
        results = []
        
        # Determine which statistic types to search for
        statistic_types = []
        
        # University institutions count
        if any(keyword in query_lower for keyword in [
            "how many universities", "number of universities", "count of universities",
            "how many university institutions", "number of university institutions",
            "total universities", "university institutions count"
        ]):
            statistic_types.append(TCUStatisticType.UNIVERSITY_INSTITUTIONS)
            statistic_types.append(TCUStatisticType.ACCREDITED_UNIVERSITIES)
        
        # Academic programmes count
        if any(keyword in query_lower for keyword in [
            "how many academic programmes", "number of academic programmes", "count of programmes",
            "how many programmes", "total programmes", "academic programmes count"
        ]):
            statistic_types.append(TCUStatisticType.ACADEMIC_PROGRAMMES)
        
        # If no specific type matched, search all
        if not statistic_types:
            statistic_types = list(TCUStatisticType)
        
        # Build query for TCU statistics
        q = self.db.query(TCUStatistic).filter(
            TCUStatistic.is_verified == True,
            TCUStatistic.statistic_type.in_(statistic_types)
        )
        
        # Apply academic year filter if specified
        if academic_year:
            q = q.filter(TCUStatistic.academic_year_label == academic_year)
        else:
            # Default to current academic year
            current_ay = self.db.query(AcademicYear).filter(AcademicYear.is_current == True).first()
            if current_ay:
                q = q.filter(TCUStatistic.academic_year_label == current_ay.year_label)
        
        # Order by most recent
        q = q.order_by(TCUStatistic.last_crawled_at.desc().nullslast())
        
        stats = q.all()
        
        for stat in stats:
            results.append({
                "id": stat.id,
                "statistic_type": stat.statistic_type.value,
                "metric_name": stat.metric_name,
                "value": stat.value,
                "unit": stat.unit,
                "source_url": stat.source_url,
                "source_page_title": stat.source_page_title,
                "source_section": stat.source_section,
                "academic_year": stat.academic_year_label,
                "academic_year_id": stat.academic_year_id,
                "is_verified": stat.is_verified,
                "verified_at": stat.verified_at.isoformat() if stat.verified_at else None,
                "last_crawled_at": stat.last_crawled_at.isoformat() if stat.last_crawled_at else None,
                "notes": stat.notes,
                "metadata_json": stat.metadata_json,
                "similarity": 1.0,  # Exact match
                "text": f"According to TCU's official statistics ({stat.academic_year_label}), the {stat.metric_name.replace('_', ' ')} is {stat.value:,} {stat.unit}.",
                "metadata": {
                    "title": f"TCU Statistic: {stat.metric_name}",
                    "source_type": "TCU_OFFICIAL",
                    "authority_level": "LEVEL_1",
                    "url": stat.source_url,
                    "university": None,
                    "academic_year": stat.academic_year_label,
                    "is_verified": True
                }
            })
        
        return results

    async def _fallback_retrieval(
        self,
        query: str,
        category: Optional[QueryCategory] = None,
        academic_year: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fallback retrieval strategies when primary retrieval returns no results.
        Tries progressively broader searches.
        """
        from ..models.source import SourceType, SourceAuthority
        
        results = []
        
        # Fallback 1: Broaden source types (include OTHER sources)
        fallback_filters_1 = RetrievalFilters(
            source_types=[SourceType.TCU_OFFICIAL, SourceType.UNIVERSITY_OFFICIAL, 
                         SourceType.GOVERNMENT, SourceType.HESLB, SourceType.NACTVET, SourceType.OTHER],
            academic_year=academic_year,
            authority_levels=[SourceAuthority.LEVEL_1, SourceAuthority.LEVEL_2, 
                             SourceAuthority.LEVEL_3, SourceAuthority.LEVEL_4, SourceAuthority.LEVEL_5],
            is_verified=None  # Don't require verification
        )
        
        try:
            results_1 = await self.retrieve(query, category, filters=fallback_filters_1, top_k=5)
            results.extend(results_1)
        except Exception as e:
            # If vector search fails (e.g., missing API key), skip this fallback
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Fallback 1 (broadened sources) failed: {e}")
        
        # Fallback 2: No filters at all - pure vector search
        if not results:
            fallback_filters_2 = RetrievalFilters()
            try:
                results_2 = await self.retrieve(query, category, filters=fallback_filters_2, top_k=5)
                results.extend(results_2)
            except Exception as e:
                # If vector search fails, skip this fallback
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Fallback 2 (no filters) failed: {e}")
        
        # Fallback 3: Keyword-based search in document chunks (using ILIKE)
        if not results:
            try:
                results_3 = await self._keyword_search(query, academic_year)
                results.extend(results_3)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Fallback 3 (keyword search) failed: {e}")
        
        return results

    async def _keyword_search(
        self,
        query: str,
        academic_year: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Keyword-based search in document chunks as last resort.
        """
        # Extract keywords from query
        keywords = [w for w in query.lower().split() if len(w) > 3]
        if not keywords:
            return []
        
        # Build ILIKE conditions
        conditions = []
        params = {"limit": 5}
        
        for i, keyword in enumerate(keywords):
            param_name = f"keyword_{i}"
            conditions.append(f"dc.chunk_text ILIKE :{param_name}")
            params[param_name] = f"%{keyword}%"
        
        if academic_year:
            conditions.append("dc.metadata->>'academic_year' = :academic_year")
            params["academic_year"] = academic_year
        
        where_clause = " OR ".join(conditions) if conditions else "1=1"
        
        query_sql = text(f"""
            SELECT 
                dc.id,
                dc.document_id,
                dc.chunk_index,
                dc.chunk_text,
                dc.metadata,
                1 - (dc.embedding <=> :embedding::vector) as similarity
            FROM document_chunks dc
            WHERE {where_clause}
            ORDER BY dc.embedding <=> :embedding::vector
            LIMIT :limit
        """)
        
        # Use a generic embedding for keyword search
        query_embeddings = await self.embedding_service.generate_embeddings([query])
        query_embedding = query_embeddings[0]
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        params["embedding"] = embedding_str
        
        result = self.db.execute(query_sql, params)
        
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