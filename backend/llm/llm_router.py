"""
Sports AI — LLM Router
Selects and routes requests to the configured LLM provider.
Supports: MiniMax (default), DeepSeek, OpenAI, Claude, Grok.
"""

import re
import httpx
from typing import Dict, List, Optional
from backend.config.settings import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Regex to strip <think>…</think> blocks (MiniMax-M2.7 reasoning traces)
_THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL)

# Provider configurations
PROVIDER_CONFIG = {
    "minimax": {
        "base_url": "https://api.minimax.io",
        "model": "MiniMax-M2.7",
        "api_key_field": "minimax_api_key",
    },
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
        logger.info(f"LLM Router initialized with provider: {self.provider}")

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> str:
        """
        Send a chat completion request to the configured LLM.

        Returns:
            LLM response text (thinking traces stripped automatically).
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        if self.provider == "claude":
            raw = await self._chat_anthropic(
                system_prompt, user_message, temperature, max_tokens
            )
        else:
            raw = await self._chat_openai_compatible(
                messages, temperature, max_tokens
            )

        return self._strip_thinking(raw)

    # ── OpenAI-compatible (MiniMax, DeepSeek, OpenAI, Grok) ──────

    async def _chat_openai_compatible(
        self, messages: List[Dict], temperature: float, max_tokens: int
    ) -> str:
        config = PROVIDER_CONFIG.get(self.provider, PROVIDER_CONFIG["minimax"])
        api_key = getattr(settings, config["api_key_field"], "")

        if not api_key:
            logger.warning(f"No API key configured for {self.provider}")
            return ""

        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=config["base_url"],
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=120.0,
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
        except httpx.HTTPStatusError as e:
            logger.error(
                f"{self.provider} API error (HTTP {e.response.status_code}): {e}"
            )
            return ""
        except Exception as e:
            logger.error(f"{self.provider} API error: {e}")
            return ""

    # ── Anthropic Claude ─────────────────────────────────────────

    async def _chat_anthropic(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        api_key = settings.anthropic_api_key

        if not api_key:
            logger.warning("No API key configured for Claude")
            return ""

        if not self._client:
            self._client = httpx.AsyncClient(
                base_url="https://api.anthropic.com",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                timeout=120.0,
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
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Claude API error (HTTP {e.response.status_code}): {e}"
            )
            return ""
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return ""

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _strip_thinking(text: str) -> str:
        """Remove <think>…</think> reasoning traces from model output."""
        if not text:
            return ""
        return _THINK_RE.sub("", text).strip()

    async def close(self):
        """Close HTTP client."""
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
