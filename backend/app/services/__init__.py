# backend/app/services/__init__.py
from .auth_service import AuthService
from .university_service import UniversityService
from .programme_service import ProgrammeService
from .chat_service import ChatService
from .eligibility_service import EligibilityService
from .comparison_service import ComparisonService
from .document_service import DocumentService

__all__ = [
    'AuthService',
    'UniversityService',
    'ProgrammeService',
    'ChatService',
    'EligibilityService',
    'ComparisonService',
    'DocumentService',
]