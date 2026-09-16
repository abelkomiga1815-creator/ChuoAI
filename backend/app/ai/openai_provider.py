# backend/app/ai/openai_provider.py
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional, AsyncGenerator
import json

from .provider import AIProvider, Message, AIResponse
from ..core.config import settings

class OpenAIProvider(AIProvider):
    """OpenAI provider implementation (openai>=1.0 client API)."""

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set. Add it to your backend/.env file, "
                "or set LLM_PROVIDER=groq and provide GROQ_API_KEY instead."
            )
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL

    async def chat_completion(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = True,
        **kwargs
    ) -> AsyncGenerator[AIResponse, None]:
        """Generate chat completion with streaming."""
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        if stream:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta:
                    content = chunk.choices[0].delta.content or ""
                    if content:
                        yield AIResponse(
                            content=content,
                            sources=None,
                            metadata={"chunk": True}
                        )
        else:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            yield AIResponse(
                content=response.choices[0].message.content or "",
                tokens_used=(response.usage.total_tokens if response.usage else 0)
            )

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )

        return [item.embedding for item in response.data]

    async def is_available(self) -> bool:
        """Check if the provider is available."""
        if not settings.OPENAI_API_KEY:
            return False
        try:
            await self.client.embeddings.create(
                model=self.embedding_model,
                input=["test"]
            )
            return True
        except Exception:
            return False