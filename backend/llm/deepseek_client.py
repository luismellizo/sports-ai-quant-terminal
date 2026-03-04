"""
Sports AI — DeepSeek LLM Client
Async client for DeepSeek API (OpenAI-compatible endpoint).
"""

import httpx
from typing import Dict, Optional, List
from backend.config.settings import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class DeepSeekClient:
    """Client for DeepSeek LLM API."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.deepseek_api_key
        self.client = httpx.AsyncClient(
            base_url=DEEPSEEK_BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-chat",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """
        Send a chat completion request to DeepSeek.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Response text content
        """
        try:
            response = await self.client.post(
                "/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return ""

    async def close(self):
        await self.client.aclose()
