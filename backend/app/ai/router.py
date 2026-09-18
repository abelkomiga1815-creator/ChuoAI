# backend/app/ai/router.py
from enum import Enum
from typing import List, Dict, Any, Optional
import re
from datetime import datetime

class QueryCategory(str, Enum):
    GENERAL = "GENERAL"
    UNIVERSITY_SEARCH = "UNIVERSITY_SEARCH"
    PROGRAMME_SEARCH = "PROGRAMME_SEARCH"
    ADMISSION = "ADMISSION"
    TCU = "TCU"
    TCU_STATISTICS = "TCU_STATISTICS"
    FEES = "FEES"
    SCHOLARSHIP = "SCHOLARSHIP"
    ELIGIBILITY = "ELIGIBILITY"
    TRANSFER = "TRANSFER"
    UNIVERSITY_COMPARISON = "UNIVERSITY_COMPARISON"
    DOCUMENT_SEARCH = "DOCUMENT_SEARCH"
    COMPLEX_REASONING = "COMPLEX_REASONING"
    VERIFICATION = "VERIFICATION"

class QueryRouter:
    """Route queries to appropriate handlers."""
    
    # Keywords for each category
    CATEGORY_KEYWORDS = {
        QueryCategory.TCU: ["tcu", "tanzania commission for universities", "accreditation", "accredited"],
        QueryCategory.TCU_STATISTICS: [
            "how many universities", "number of universities", "count of universities",
            "how many university institutions", "number of university institutions",
            "how many academic programmes", "number of academic programmes", "count of programmes",
            "how many programmes", "total universities", "total programmes",
            "university institutions count", "academic programmes count"
        ],
        QueryCategory.UNIVERSITY_SEARCH: ["university", "college", "vyuo", "chuo", "institution", "school"],
        QueryCategory.PROGRAMME_SEARCH: ["programme", "course", "degree", "diploma", "certificate", "program", "study"],
        QueryCategory.ADMISSION: ["admission", "entry", "join", "application", "apply", "requirements", "qualification"],
        QueryCategory.FEES: ["fee", "cost", "tuition", "payment", "charge", "price"],
        QueryCategory.SCHOLARSHIP: ["scholarship", "bursary", "loan", "funding", "financial aid", "sponsorship"],
        QueryCategory.ELIGIBILITY: ["eligible", "qualify", "can i", "am i", "do i qualify", "requirements", "grades"],
        QueryCategory.TRANSFER: ["transfer", "move", "change university", "credit transfer"],
        QueryCategory.UNIVERSITY_COMPARISON: ["compare", "difference", "versus", "vs", "which is better"],
        QueryCategory.VERIFICATION: ["verify", "confirm", "is it true", "official", "real", "fake", "exists", "exist"],
    }
    
    # Academic year patterns
    ACADEMIC_YEAR_PATTERNS = [
        r'(20\d{2}/20\d{2})',  # 2026/2027
        r'(20\d{2}-20\d{2})',  # 2026-2027
        r'(academic year\s+20\d{2})',  # academic year 2026
        r'(current\s+year|this\s+year|next\s+year)',
    ]
    
    @classmethod
    def classify(cls, query: str) -> QueryCategory:
        """Classify the query into a category."""
        query_lower = query.lower()
        
        # Check for TCU statistics FIRST (most specific - before university search)
        if any(keyword in query_lower for keyword in cls.CATEGORY_KEYWORDS[QueryCategory.TCU_STATISTICS]):
            return QueryCategory.TCU_STATISTICS
        
        # Check for verification first
        if any(keyword in query_lower for keyword in cls.CATEGORY_KEYWORDS[QueryCategory.VERIFICATION]):
            return QueryCategory.VERIFICATION
        
        # Check for comparison first
        if any(keyword in query_lower for keyword in cls.CATEGORY_KEYWORDS[QueryCategory.UNIVERSITY_COMPARISON]):
            return QueryCategory.UNIVERSITY_COMPARISON
        
        # Check eligibility
        if any(keyword in query_lower for keyword in cls.CATEGORY_KEYWORDS[QueryCategory.ELIGIBILITY]):
            return QueryCategory.ELIGIBILITY
        
        # Check for TCU
        if any(keyword in query_lower for keyword in cls.CATEGORY_KEYWORDS[QueryCategory.TCU]):
            return QueryCategory.TCU
        
        # Check for programme search
        if any(keyword in query_lower for keyword in cls.CATEGORY_KEYWORDS[QueryCategory.PROGRAMME_SEARCH]):
            if any(word in query_lower for word in ["offer", "has", "have", "offer"]):
                return QueryCategory.PROGRAMME_SEARCH
        
        # Check for admission
        if any(keyword in query_lower for keyword in cls.CATEGORY_KEYWORDS[QueryCategory.ADMISSION]):
            return QueryCategory.ADMISSION
        
        # Check for fees
        if any(keyword in query_lower for keyword in cls.CATEGORY_KEYWORDS[QueryCategory.FEES]):
            return QueryCategory.FEES
        
        # Check for scholarship
        if any(keyword in query_lower for keyword in cls.CATEGORY_KEYWORDS[QueryCategory.SCHOLARSHIP]):
            return QueryCategory.SCHOLARSHIP
        
        # Check for university
        if any(keyword in query_lower for keyword in cls.CATEGORY_KEYWORDS[QueryCategory.UNIVERSITY_SEARCH]):
            return QueryCategory.UNIVERSITY_SEARCH
        
        # Default to general
        return QueryCategory.GENERAL
    
    @classmethod
    def extract_entities(cls, query: str) -> Dict[str, Any]:
        """Extract entities from the query."""
        entities = {}
        query_lower = query.lower()
        
        # Extract academic year
        for pattern in cls.ACADEMIC_YEAR_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                year = match.group(1)
                # Normalize to YYYY/YYYY format
                if "/" in year:
                    entities["academic_year"] = year
                elif "-" in year:
                    entities["academic_year"] = year.replace("-", "/")
                elif "current" in year or "this" in year:
                    # Determine current academic year
                    current_year = datetime.now().year
                    if datetime.now().month >= 9:  # Academic year starts around September
                        entities["academic_year"] = f"{current_year}/{current_year + 1}"
                    else:
                        entities["academic_year"] = f"{current_year - 1}/{current_year}"
                elif "next" in year:
                    current_year = datetime.now().year
                    entities["academic_year"] = f"{current_year + 1}/{current_year + 2}"
                break
        
        # Extract university names
        university_patterns = [
            r'(udsm|udom|must|suza|ardhi|muhas|tumaini|st\. augustine|st\. john|jakaya kikwete|out|open university)',
            r'(university of dar es salaam|dar es salaam university)',
            r'(university of dodoma|dodoma university)',
            r'(mbeya university of science and technology)',
            r'(sokoine university of agriculture)',
            r'(ardhi university)',
            r'(muhimbili university of health and allied sciences)',
            r'(mzumbe university)',
            r'(st\. augustine university of tanzania)',
            r'(st\. john\'s university of tanzania)',
        ]
        
        for pattern in university_patterns:
            match = re.search(pattern, query_lower)
            if match:
                entities["university"] = match.group(1)
                break
        
        # Extract programme names
        programme_patterns = [
            r'(computer science|information technology|business administration|accounting|finance|economics|law|medicine|nursing|engineering|civil engineering|mechanical engineering|electrical engineering|software engineering|data science|artificial intelligence|education|psychology|sociology|political science|international relations)',
            r'(bachelor of|master of|diploma in|certificate in|phd in|doctor of)\s+([a-z\s]+)',
        ]
        
        for pattern in programme_patterns:
            match = re.search(pattern, query_lower)
            if match:
                entities["programme"] = match.group(1) if len(match.groups()) == 1 else match.group(2)
                break
        
        # Extract subjects for eligibility
        subject_patterns = [
            r'(pcm|pcb|pnm|cbm|hgl|egm|physics|chemistry|mathematics|biology|history|geography|economics|commerce|accounting|computer|agriculture|bookkeeping)'
        ]
        
        match = re.search(subject_patterns[0], query_lower)
        if match:
            entities["subjects"] = match.group(1)
        
        # Extract division/grades
        grade_patterns = [
            r'(division [iv]+|division [iv]+)',
            r'(grade [a-f]|grade [a-f])',
            r'([iv]+) points'
        ]
        
        for pattern in grade_patterns:
            match = re.search(pattern, query_lower)
            if match:
                entities["grades"] = match.group(1)
                break
        
        return entities