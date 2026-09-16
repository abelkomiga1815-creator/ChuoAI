# backend/app/models/__init__.py
from .user import User
from .university import University
from .programme import Programme
from .admission import AdmissionRequirement
from .document import Document
from .conversation import Conversation
from .message import Message
from .scholarship import Scholarship
from .faq import FAQ
from .source import Source

__all__ = [
    'User',
    'University',
    'Programme',
    'AdmissionRequirement',
    'Document',
    'Conversation',
    'Message',
    'Scholarship',
    'FAQ',
    'Source',
]