"""Utility functions for loading chat models with graceful fallbacks."""

from __future__ import annotations

import os
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_openai import ChatOpenAI

try:
    from langchain_anthropic import ChatAnthropic
except Exception:  # pragma: no cover - optional dependency
    ChatAnthropic = None  # type: ignore

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except Exception:  # pragma: no cover - optional dependency
    ChatGoogleGenerativeAI = None  # type: ignore


class StubChatModel(BaseChatModel):
    """Minimal chat model used when API keys are missing."""

    model_name: str = "stub-model"

    def _generate(self, messages: list[BaseMessage], **kwargs) -> ChatResult:
        content = "Stub response: please configure a real LLM provider via environment variables."
        generation = ChatGeneration(message=AIMessage(content=content))
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "stub"


def get_chat_model(provider: str | None = None, model: Optional[str] = None) -> BaseChatModel:
    """
    Load a chat model with the requested provider, falling back to a stub when keys are absent.

    Args:
        provider: Identifier for the provider ("openai", "anthropic", "gemini").
        model: Optional explicit model name.

    Returns:
        BaseChatModel instance ready for use.
    """

    resolved_provider = (provider or os.getenv("LLM_PROVIDER") or "openai").lower()
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))

    if resolved_provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return ChatOpenAI(model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=temperature)
        return StubChatModel()

    if resolved_provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key and ChatAnthropic:
            return ChatAnthropic(
                model_name=model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
                temperature=temperature,
                timeout=None,  # or a reasonable default like 60
                stop=None
            )
        return StubChatModel()

    if resolved_provider in {"gemini", "google"}:
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key and ChatGoogleGenerativeAI:
            return ChatGoogleGenerativeAI(model=model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash"), temperature=temperature)
        return StubChatModel()

    return StubChatModel()
