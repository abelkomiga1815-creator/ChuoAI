# backend/app/ai/router.py
from enum import Enum
from typing import List, Dict, Any, Optional
import re

class QueryCategory(str, Enum):
    GENERAL = "GENERAL"
    UNIVERSITY_SEARCH = "UNIVERSITY_SEARCH"
    PROGRAMME_SEARCH = "PROGRAMME_SEARCH"
    ADMISSION = "ADMISSION"
    TCU = "TCU"
    FEES = "FEES"
    SCHOLARSHIP = "SCHOLARSHIP"
    ELIGIBILITY = "ELIGIBILITY"
    TRANSFER = "TRANSFER"
    UNIVERSITY_COMPARISON = "UNIVERSITY_COMPARISON"
    DOCUMENT_SEARCH = "DOCUMENT_SEARCH"
    COMPLEX_REASONING = "COMPLEX_REASONING"

class QueryRouter:
    """Route queries to appropriate handlers."""
    
    # Keywords for each category
    CATEGORY_KEYWORDS = {
        QueryCategory.TCU: ["tcu", "tanzania commission for universities", "accreditation", "accredited"],
        QueryCategory.UNIVERSITY_SEARCH: ["university", "college", "vyuo", "chuo", "institution", "school"],
        QueryCategory.PROGRAMME_SEARCH: ["programme", "course", "degree", "diploma", "certificate", "program", "study"],
        QueryCategory.ADMISSION: ["admission", "entry", "join", "application", "apply", "requirements", "qualification"],
        QueryCategory.FEES: ["fee", "cost", "tuition", "payment", "charge", "price"],
        QueryCategory.SCHOLARSHIP: ["scholarship", "bursary", "loan", "funding", "financial aid", "sponsorship"],
        QueryCategory.ELIGIBILITY: ["eligible", "qualify", "can i", "am i", "do i qualify", "requirements", "grades"],
        QueryCategory.TRANSFER: ["transfer", "move", "change university", "credit transfer"],
        QueryCategory.UNIVERSITY_COMPARISON: ["compare", "difference", "versus", "vs", "which is better"],
    }
    
    @classmethod
    def classify(cls, query: str) -> QueryCategory:
        """Classify the query into a category."""
        query_lower = query.lower()
        
        # Check for comparison first
        if any(word in query_lower for word in ["compare", "difference", "versus", "vs"]):
            # Check if multiple universities are mentioned
            if any(univ in query_lower for univ in ["udsm", "udom", "must", "suza", "ardhi", "muhas"]):
                return QueryCategory.UNIVERSITY_COMPARISON
            return QueryCategory.UNIVERSITY_COMPARISON
        
        # Check eligibility
        if any(word in query_lower for word in ["eligible", "qualify", "can i", "am i eligible", "do i qualify"]):
            return QueryCategory.ELIGIBILITY
        
        # Check for programme search
        if any(word in query_lower for word in ["programme", "course", "degree", "diploma", "study"]):
            if "offer" in query_lower or "has" in query_lower or "have" in query_lower:
                return QueryCategory.PROGRAMME_SEARCH
        
        # Check for TCU
        if "tcu" in query_lower:
            return QueryCategory.TCU
        
        # Check for admission
        if any(word in query_lower for word in ["admission", "entry", "application", "apply"]):
            return QueryCategory.ADMISSION
        
        # Check for fees
        if any(word in query_lower for word in ["fee", "cost", "tuition", "payment"]):
            return QueryCategory.FEES
        
        # Check for scholarship
        if any(word in query_lower for word in ["scholarship", "bursary", "loan", "sponsorship"]):
            return QueryCategory.SCHOLARSHIP
        
        # Check for university
        if any(word in query_lower for word in ["university", "college", "institution"]):
            return QueryCategory.UNIVERSITY_SEARCH
        
        # Default to general
        return QueryCategory.GENERAL
    
    @classmethod
    def extract_entities(cls, query: str) -> Dict[str, Any]:
        """Extract entities from the query."""
        entities = {}
        query_lower = query.lower()
        
        # Extract university names
        university_patterns = [
            r'(udsm|udom|must|suza|ardhi|muhas|tumaini|st\. augustine|st. john|jakaya kikwete|out|open university)',
            r'(university of dar es salaam|dar es salaam university)',
            r'(university of dodoma|dodoma university)',
            r'(mbeya university of science and technology)',
            r'(sokoine university of agriculture)',
            r'(ardhi university)',
            r'(muhimbili university of health and allied sciences)'
        ]
        
        for pattern in university_patterns:
            match = re.search(pattern, query_lower)
            if match:
                entities["university"] = match.group(1)
                break
        
        # Extract programme names
        programme_patterns = [
            r'(computer science|information technology|business administration|accounting|finance|economics|law|medicine|nursing|engineering|civil engineering|mechanical engineering|electrical engineering|software engineering|data science|artificial intelligence|education|psychology|sociology|political science|international relations)',
            r'(bachelor of|master of|diploma in|certificate in)'
        ]
        
        for pattern in programme_patterns:
            match = re.search(pattern, query_lower)
            if match:
                entities["programme"] = match.group(1)
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