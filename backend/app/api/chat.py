# backend/app/api/chat.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import asyncio

from ..core.database import get_db
from ..auth.dependencies import get_current_user
from ..services.chat_service import ChatService
from ..schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    MessageResponse,
    ConversationCreate,
    ConversationUpdate
)

router = APIRouter()

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Stream chat response using Server-Sent Events."""
    chat_service = ChatService(db)
    
    async def event_stream():
        try:
            async for chunk in chat_service.stream_chat(
                user_id=current_user.id,
                message=request.message,
                conversation_id=request.conversation_id,
                language=request.language
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Send a chat message and get a complete response."""
    chat_service = ChatService(db)
    response = await chat_service.chat(
        user_id=current_user.id,
        message=request.message,
        conversation_id=request.conversation_id,
        language=request.language
    )
    return response

@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List user's conversations."""
    chat_service = ChatService(db)
    conversations = await chat_service.list_conversations(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        search=search
    )
    return conversations

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new conversation."""
    chat_service = ChatService(db)
    conversation = await chat_service.create_conversation(
        user_id=current_user.id,
        title=data.title
    )
    return conversation

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a conversation with messages."""
    chat_service = ChatService(db)
    conversation = await chat_service.get_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return conversation

@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    data: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update conversation (rename)."""
    chat_service = ChatService(db)
    conversation = await chat_service.update_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
        data=data
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return conversation

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a conversation."""
    chat_service = ChatService(db)
    success = await chat_service.delete_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )