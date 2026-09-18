# backend/app/models/__init__.py
from .user import User
from .university import University, UniversityType, UniversityStatus, UniversityAlias
from .programme import Programme, ProgrammeLevel, ProgrammeStatus, StudyMode, ProgrammeAlias
from .admission import AdmissionRequirement, QualificationType
from .document import Document
from .conversation import Conversation
from .message import Message
from .scholarship import Scholarship
from .faq import FAQ
from .source import Source, SourceType, SourceAuthority
from .academic_year import AcademicYear, FeeStructure, SubjectRequirement, IngestionJob, TCUStatistic, TCUStatisticType

__all__ = [
    'User',
    'University',
    'UniversityType',
    'UniversityStatus',
    'UniversityAlias',
    'Programme',
    'ProgrammeLevel',
    'ProgrammeStatus',
    'StudyMode',
    'ProgrammeAlias',
    'AdmissionRequirement',
    'QualificationType',
    'Document',
    'Conversation',
    'Message',
    'Scholarship',
    'FAQ',
    'Source',
    'SourceType',
    'SourceAuthority',
    'AcademicYear',
    'FeeStructure',
    'SubjectRequirement',
    'IngestionJob',
    'TCUStatistic',
    'TCUStatisticType',
]