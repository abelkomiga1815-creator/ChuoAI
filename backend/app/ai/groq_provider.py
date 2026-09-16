# backend/app/ai/groq_provider.py
import httpx
from typing import List, Dict, Any, Optional, AsyncGenerator
import json

from .provider import AIProvider, Message, AIResponse
from ..core.config import settings

class GroqProvider(AIProvider):
    """Groq provider implementation."""
    
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.LLM_MODEL
        self.base_url = "https://api.groq.com/openai/v1"
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
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
        
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **kwargs
        }
        
        if stream:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            data = json.loads(line[6:])
                            if data.get("choices") and data["choices"][0].get("delta"):
                                content = data["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield AIResponse(
                                        content=content,
                                        sources=None,
                                        metadata={"chunk": True}
                                    )
                        except:
                            continue
        else:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            yield AIResponse(
                content=data["choices"][0]["message"]["content"],
                tokens_used=data.get("usage", {}).get("total_tokens", 0)
            )
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings (using a different provider since Groq doesn't support embeddings)."""
        # Fallback to OpenAI for embeddings if available
        from .openai_provider import OpenAIProvider
        provider = OpenAIProvider()
        return await provider.generate_embeddings(texts)
    
    async def is_available(self) -> bool:
        """Check if the provider is available."""
        try:
            response = await self.client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except:
            return False