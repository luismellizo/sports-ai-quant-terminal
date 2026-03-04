"""
Sports AI — LLM Router
Selects and routes requests to the configured LLM provider.
Supports: DeepSeek (dev), OpenAI, Claude, Grok (production).
"""

import httpx
from typing import Dict, List, Optional
from backend.config.settings import get_settings
from backend.llm.deepseek_client import DeepSeekClient
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Provider configurations
PROVIDER_CONFIG = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "api_key_field": "deepseek_api_key",
    },
    "openai": {
        "base_url": "https://api.openai.com",
        "model": "gpt-4o",
        "api_key_field": "openai_api_key",
    },
    "claude": {
        "base_url": "https://api.anthropic.com",
        "model": "claude-sonnet-4-20250514",
        "api_key_field": "anthropic_api_key",
    },
    "grok": {
        "base_url": "https://api.x.ai",
        "model": "grok-2",
        "api_key_field": "grok_api_key",
    },
}


class LLMRouter:
    """Routes LLM requests to the configured provider."""

    def __init__(self, provider: str = None):
        self.provider = provider or settings.llm_provider
        self._client: Optional[httpx.AsyncClient] = None
        self._deepseek: Optional[DeepSeekClient] = None
        logger.info(f"LLM Router initialized with provider: {self.provider}")

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """
        Send a chat completion request to the configured LLM.

        Args:
            system_prompt: System message for the LLM
            user_message: User message
            temperature: Sampling temperature
            max_tokens: Max tokens

        Returns:
            LLM response text
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        if self.provider == "deepseek":
            return await self._chat_deepseek(messages, temperature, max_tokens)
        elif self.provider == "claude":
            return await self._chat_anthropic(system_prompt, user_message, temperature, max_tokens)
        else:
            return await self._chat_openai_compatible(messages, temperature, max_tokens)

    async def _chat_deepseek(
        self, messages: List[Dict], temperature: float, max_tokens: int
    ) -> str:
        """Route to DeepSeek API."""
        if not self._deepseek:
            self._deepseek = DeepSeekClient()
        return await self._deepseek.chat(messages, temperature=temperature, max_tokens=max_tokens)

    async def _chat_openai_compatible(
        self, messages: List[Dict], temperature: float, max_tokens: int
    ) -> str:
        """Route to OpenAI-compatible API (OpenAI, Grok)."""
        config = PROVIDER_CONFIG.get(self.provider, PROVIDER_CONFIG["openai"])
        api_key = getattr(settings, config["api_key_field"], "")

        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=config["base_url"],
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )

        try:
            response = await self._client.post(
                "/v1/chat/completions",
                json={
                    "model": config["model"],
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"{self.provider} API error: {e}")
            return ""

    async def _chat_anthropic(
        self, system_prompt: str, user_message: str, temperature: float, max_tokens: int
    ) -> str:
        """Route to Anthropic Claude API (different format)."""
        api_key = settings.anthropic_api_key

        if not self._client:
            self._client = httpx.AsyncClient(
                base_url="https://api.anthropic.com",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )

        try:
            response = await self._client.post(
                "/v1/messages",
                json={
                    "model": PROVIDER_CONFIG["claude"]["model"],
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_message}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return ""

    async def close(self):
        """Close all HTTP clients."""
        if self._deepseek:
            await self._deepseek.close()
        if self._client:
            await self._client.aclose()


# Singleton
_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """Get or create LLM router singleton."""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
