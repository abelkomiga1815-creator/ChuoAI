# backend/app/rag/reranking.py
from typing import List, Dict, Any
import numpy as np
from datetime import datetime

from ..models.source import SourceType, SourceAuthority


class RerankingService:
    """Service for reranking retrieved documents."""
    
    def __init__(self):
        # Current academic year for freshness calculation
        current_year = datetime.now().year
        if datetime.now().month >= 9:
            self.current_academic_year = f"{current_year}/{current_year + 1}"
        else:
            self.current_academic_year = f"{current_year - 1}/{current_year}"
    
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
        score += similarity * 0.4  # Reduced from 0.6 to make room for other factors
        
        # Source authority (0-1)
        authority = result.get("metadata", {}).get("authority_level", "LEVEL_5")
        authority_weights = {
            "LEVEL_1": 1.0,   # TCU official
            "LEVEL_2": 0.95,  # University official
            "LEVEL_3": 0.85,  # Admission portals
            "LEVEL_4": 0.8,   # Official PDFs/prospectuses
            "LEVEL_5": 0.5,   # Other
        }
        score += authority_weights.get(authority, 0.5) * 0.25
        
        # Source type priority (0-1)
        source_type = result.get("metadata", {}).get("source_type", "")
        source_priority = {
            "TCU_OFFICIAL": 1.0,
            "UNIVERSITY_OFFICIAL": 0.9,
            "HESLB": 0.85,
            "NACTVET": 0.85,
            "GOVERNMENT": 0.8,
            "OTHER": 0.4,
        }
        score += source_priority.get(source_type, 0.4) * 0.15
        
        # Verification status bonus
        if result.get("metadata", {}).get("is_verified", False):
            score += 0.1
        
        # Freshness score (0-1)
        academic_year = result.get("metadata", {}).get("academic_year", "")
        if academic_year:
            freshness = self._calculate_freshness(academic_year)
            score += freshness * 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_freshness(self, academic_year: str) -> float:
        """Calculate freshness score based on academic year."""
        try:
            # Parse academic year (format: YYYY/YYYY or YYYY-YYYY)
            year_part = academic_year.split("/")[0] if "/" in academic_year else academic_year.split("-")[0]
            year = int(year_part)
            
            current_year = int(self.current_academic_year.split("/")[0])
            
            # Score: 1.0 for current year, decreasing by 0.15 per year
            diff = current_year - year
            if diff <= 0:
                return 1.0
            elif diff == 1:
                return 0.85
            elif diff == 2:
                return 0.7
            elif diff == 3:
                return 0.5
            else:
                return 0.3
        except (ValueError, IndexError):
            return 0.5  # Unknown freshness