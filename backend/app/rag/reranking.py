# backend/app/rag/reranking.py
from typing import List, Dict, Any
import numpy as np

class RerankingService:
    """Service for reranking retrieved documents."""
    
    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Rerank results based on multiple factors."""
        if not results:
            return []
        
        # Calculate scores
        scored_results = []
        for result in results:
            score = self._calculate_score(query, result)
            result["rerank_score"] = score
            scored_results.append(result)
        
        # Sort by score
        scored_results.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        return scored_results[:top_k]
    
    def _calculate_score(self, query: str, result: Dict[str, Any]) -> float:
        """Calculate a combined score for a result."""
        score = 0.0
        
        # Base similarity score (0-1)
        similarity = result.get("similarity", 0.0)
        score += similarity * 0.6
        
        # Source priority
        source_type = result.get("metadata", {}).get("source_type", "")
        source_priority = {
            "TCU_OFFICIAL": 1.0,
            "UNIVERSITY_OFFICIAL": 0.9,
            "HESLB": 0.85,
            "NACTVET": 0.85,
            "GOVERNMENT": 0.8,
            "OTHER": 0.5
        }
        score += source_priority.get(source_type, 0.5) * 0.3
        
        # Recency score
        academic_year = result.get("metadata", {}).get("academic_year", "")
        if academic_year:
            # Assume current year is 2024
            try:
                year = int(academic_year.split("/")[0])
                recency = min(1.0, max(0.0, (year - 2020) / 4))
                score += recency * 0.1
            except:
                pass
        
        return score