from __future__ import annotations

import importlib
import os

from langchain_core.language_models.chat_models import BaseChatModel

from config import (
    LLM_PROVIDER,
    LLM_MODEL,
    LLM_TEMPERATURE,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)


def get_provider_name() -> str:
    """Resolve the effective provider from configuration."""
    provider = (LLM_PROVIDER or "auto").lower().strip()
    if provider == "auto":
        try:
            from os import getenv

            if getenv("ANTHROPIC_API_KEY"):
                return "anthropic"
        except Exception:
            pass
        return "stub"
    return provider


def get_required_env_vars(provider: str) -> list[str]:
    provider_name = provider.strip().lower()
    if provider_name == "anthropic":
        return ["ANTHROPIC_API_KEY"]
    if provider_name == "openai_compatible":
        return ["OPENAI_API_KEY"]
    if provider_name == "ollama":
        return []
    if provider_name == "stub":
        return []
    return []


def get_missing_env_vars(provider: str | None = None) -> list[str]:
    effective_provider = get_provider_name() if provider is None else provider
    required = get_required_env_vars(effective_provider)
    missing = [name for name in required if not os.getenv(name)]
    return missing


def get_provider_report() -> dict[str, object]:
    configured = (LLM_PROVIDER or "auto").lower().strip()
    effective = get_provider_name()
    missing = get_missing_env_vars(effective)

    notes: list[str] = []
    if configured == "auto":
        if effective == "anthropic":
            notes.append(
                "auto selected anthropic because ANTHROPIC_API_KEY is set")
        else:
            notes.append(
                "auto selected stub because ANTHROPIC_API_KEY is not set")
    if effective == "openai_compatible" and not OPENAI_BASE_URL:
        notes.append(
            "OPENAI_BASE_URL is empty; default provider endpoint will be used")

    return {
        "configured_provider": configured,
        "effective_provider": effective,
        "missing_env_vars": missing,
        "notes": notes,
    }


def is_stub_mode() -> bool:
    return get_provider_name() == "stub"


def _build_anthropic(temperature: float) -> BaseChatModel:
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(model=LLM_MODEL, temperature=temperature)


def _build_openai_compatible(temperature: float) -> BaseChatModel:
    try:
        chat_openai_mod = importlib.import_module("langchain_openai")
        ChatOpenAI = getattr(chat_openai_mod, "ChatOpenAI")
    except Exception as exc:
        raise RuntimeError(
            "LLM_PROVIDER=openai_compatible requires langchain-openai. "
            "Install it with: pip install langchain-openai"
        ) from exc

    kwargs = {
        "model": OPENAI_MODEL,
        "temperature": temperature,
    }
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL

    return ChatOpenAI(**kwargs)


def _build_ollama(temperature: float) -> BaseChatModel:
    try:
        chat_ollama_mod = importlib.import_module("langchain_ollama")
        ChatOllama = getattr(chat_ollama_mod, "ChatOllama")
    except Exception as exc:
        raise RuntimeError(
            "LLM_PROVIDER=ollama requires langchain-ollama. "
            "Install it with: pip install langchain-ollama"
        ) from exc

    return ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=temperature)


def get_llm(temperature: float | None = None) -> BaseChatModel:
    """Return a configured chat model for non-stub providers."""
    resolved_temp = LLM_TEMPERATURE if temperature is None else temperature
    provider = get_provider_name()

    if provider == "anthropic":
        return _build_anthropic(resolved_temp)
    if provider == "openai_compatible":
        return _build_openai_compatible(resolved_temp)
    if provider == "ollama":
        return _build_ollama(resolved_temp)

    raise RuntimeError(
        "Stub mode does not provide a chat model instance. "
        "Use is_stub_mode() checks in node execution paths."
    )
