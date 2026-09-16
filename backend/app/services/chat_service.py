# backend/app/services/chat_service.py
from typing import AsyncGenerator, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from ..models.conversation import Conversation
from ..models.message import Message
from ..ai.router import QueryRouter, QueryCategory
from ..ai.provider import Message as AIMessage
from ..core.config import settings
from ..rag.retrieval import RetrievalService

SYSTEM_PROMPT = (
    "You are ChuoAI, an AI assistant specialised in Tanzanian higher education: "
    "universities, colleges, TCU (Tanzania Commission for Universities) rules and "
    "accreditation, admissions, programmes, fees, scholarships, and eligibility. "
    "Use the CONTEXT provided below (retrieved from official/verified sources) as "
    "your primary source of truth. If the context does not fully answer the "
    "question, say what you're unsure about rather than guessing, and recommend "
    "the person confirm with TCU or the relevant university. "
    "Reply in the same language as the user (English or Kiswahili)."
)


def _get_ai_provider():
    """Build the configured AI provider (openai or groq)."""
    provider_type = settings.LLM_PROVIDER.lower()
    if provider_type == "groq":
        from ..ai.groq_provider import GroqProvider
        return GroqProvider()
    from ..ai.openai_provider import OpenAIProvider
    return OpenAIProvider()


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.provider = _get_ai_provider()
        self.retrieval_service = RetrievalService(db)

    def _get_conversation_history(
        self,
        conversation_id: str,
        exclude_message_id: Optional[str] = None,
        limit: int = 12,
    ) -> List[AIMessage]:
        """Load recent messages of a conversation to give the model memory."""
        q = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
        if exclude_message_id:
            q = q.filter(Message.id != exclude_message_id)

        history: List[AIMessage] = []
        for row in q.limit(limit).all():
            role = "user" if row.role == "USER" else ("assistant" if row.role == "ASSISTANT" else "system")
            history.append(AIMessage(role=role, content=row.content))
        return history

    async def _build_messages(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        exclude_message_id: Optional[str] = None,
    ) -> tuple[List[AIMessage], list]:
        """Retrieve relevant context and build the prompt for the LLM."""
        sources: list = []
        context = ""
        try:
            retrieval_result = await self.retrieval_service.retrieve_with_context(message)
            context = retrieval_result.get("context", "")
            sources = retrieval_result.get("sources", [])
        except Exception:
            # Retrieval is best-effort: if it fails (e.g. no documents ingested
            # yet, or the vector DB is unavailable) fall back to answering
            # from general knowledge rather than crashing the chat.
            context = ""
            sources = []

        system_content = SYSTEM_PROMPT
        if context:
            system_content += f"\n\nCONTEXT:\n{context}"

        messages = [AIMessage(role="system", content=system_content)]

        # Add conversation history so ChuoAI remembers the current thread.
        if conversation_id:
            history = self._get_conversation_history(
                conversation_id, exclude_message_id=exclude_message_id
            )
            messages.extend(history)

        messages.append(AIMessage(role="user", content=message))
        return messages, sources

    async def list_conversations(
        self, user_id: str, skip: int = 0, limit: int = 50, search: Optional[str] = None
    ) -> List[Conversation]:
        q = self.db.query(Conversation).filter(
            Conversation.user_id == user_id, Conversation.is_active == True
        )
        if search:
            q = q.filter(Conversation.title.ilike(f"%{search}%"))
        return q.order_by(Conversation.updated_at.desc().nullslast()).offset(skip).limit(limit).all()

    async def create_conversation(self, user_id: str, title: str = "New Conversation") -> Conversation:
        conversation = Conversation(user_id=user_id, title=title)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    async def get_conversation(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )

    async def update_conversation(self, conversation_id: str, user_id: str, data) -> Optional[Conversation]:
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        conversation.title = data.title
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return False
        conversation.is_active = False
        self.db.commit()
        return True

    async def chat(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        language: Optional[str] = "auto",
    ) -> dict:
        # Get or create conversation
        conversation = None
        if conversation_id:
            conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            # Auto-title from first message
            title = message[:50] + ("..." if len(message) > 50 else "")
            conversation = await self.create_conversation(user_id, title)

        # Store user message
        user_msg = Message(
            conversation_id=conversation.id,
            role="USER",
            content=message,
        )
        self.db.add(user_msg)
        self.db.commit()
        self.db.refresh(user_msg)

        # Retrieve relevant TCU/university context and build the AI prompt
        messages, sources = await self._build_messages(
            message,
            conversation_id=conversation.id,
            exclude_message_id=user_msg.id,
        )

        full_response = ""
        async for chunk in self.provider.chat_completion(messages, stream=False):
            full_response += chunk.content

        # Store assistant message
        assistant_msg = Message(
            conversation_id=conversation.id,
            role="ASSISTANT",
            content=full_response,
            sources=sources,
        )
        self.db.add(assistant_msg)
        self.db.commit()

        return {
            "message": full_response,
            "conversation_id": conversation.id,
            "sources": sources,
        }

    async def stream_chat(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        language: Optional[str] = "auto",
    ) -> AsyncGenerator[dict, None]:
        # Get or create conversation
        conversation = None
        if conversation_id:
            conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            title = message[:50] + ("..." if len(message) > 50 else "")
            conversation = await self.create_conversation(user_id, title)

        # Send conversation_id to client first
        yield {"conversation_id": conversation.id}

        # Store user message
        user_msg = Message(
            conversation_id=conversation.id,
            role="USER",
            content=message,
        )
        self.db.add(user_msg)
        self.db.commit()
        self.db.refresh(user_msg)

        # Retrieve relevant TCU/university context and build the AI prompt
        messages, sources = await self._build_messages(
            message,
            conversation_id=conversation.id,
            exclude_message_id=user_msg.id,
        )

        full_response = ""
        try:
            async for chunk in self.provider.chat_completion(messages, stream=True):
                full_response += chunk.content
                yield {"content": chunk.content}
        except Exception as e:
            yield {"error": str(e)}
            return

        # Store assistant message
        assistant_msg = Message(
            conversation_id=conversation.id,
            role="ASSISTANT",
            content=full_response,
            sources=sources,
        )
        self.db.add(assistant_msg)
        self.db.commit()

        # Send final sources
        yield {"sources": sources}