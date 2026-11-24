"""
providers.py — single place to resolve LLM / judge clients for any backend.

Swap production providers by changing `.env` only:

  LLM_PROVIDER=ollama          # local (default for now)
  LLM_PROVIDER=groq            # cloud free tier
  LLM_PROVIDER=openai          # paid
  LLM_PROVIDER=gemini / openrouter / anthropic / custom

All live providers speak the OpenAI-compatible HTTP API, so one client code path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import SETTINGS, Settings


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    base_url: str
    api_key: str
    model: str
    supports_json_mode: bool = True
    is_local: bool = False


# Providers that often reject OpenAI `response_format=json_object`
_NO_JSON_MODE = frozenset({"ollama"})


def resolve_provider(settings: Settings | None = None, *, model_override: str | None = None) -> ProviderConfig:
    s = settings or SETTINGS
    name = s.llm_provider.lower()
    if name == "mock":
        return ProviderConfig(
            name="mock",
            base_url="",
            api_key="",
            model="mock-llm",
            supports_json_mode=False,
            is_local=True,
        )
    raw = s.resolved_llm()
    return ProviderConfig(
        name=name,
        base_url=raw["base_url"],
        api_key=raw["api_key"],
        model=model_override or raw["model"],
        supports_json_mode=name not in _NO_JSON_MODE,
        is_local=name in {"ollama", "custom"},
    )


def build_openai_client(cfg: ProviderConfig | None = None):
    """OpenAI SDK client pointed at Ollama / Groq / OpenAI / …"""
    cfg = cfg or resolve_provider()
    if cfg.name == "mock":
        raise RuntimeError("No HTTP client in mock mode")
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pip install openai") from exc
    return OpenAI(api_key=cfg.api_key or "unused", base_url=cfg.base_url, timeout=180, max_retries=2)


def resolve_judge(settings: Settings | None = None) -> ProviderConfig:
    """Judge model for Ragas — LLM_JUDGE_MODEL if set, else same as LLM_MODEL."""
    s = settings or SETTINGS
    override = (s.llm_judge_model or "").strip() or None
    return resolve_provider(s, model_override=override)


def build_langchain_chat(cfg: ProviderConfig | None = None, *, temperature: float = 0.0):
    """LangChain ChatOpenAI bound to the active provider (used by Ragas)."""
    cfg = cfg or resolve_provider()
    if cfg.name == "mock":
        raise RuntimeError("Ragas judge needs a live LLM_PROVIDER (ollama/groq/…)")
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pip install langchain-openai") from exc
    return ChatOpenAI(
        model=cfg.model,
        api_key=cfg.api_key or "unused",
        base_url=cfg.base_url,
        temperature=temperature,
        timeout=600,  # local 7B / slow CPU; cloud providers return much sooner
        max_retries=2,
    )


def provider_summary(settings: Settings | None = None) -> dict[str, Any]:
    s = settings or SETTINGS
    cfg = resolve_provider(s)
    judge = resolve_judge(s) if cfg.name != "mock" else cfg
    return {
        "provider": cfg.name,
        "model": cfg.model,
        "judge_model": judge.model,
        "base_url": cfg.base_url or "(mock)",
        "local": cfg.is_local,
        "json_mode": cfg.supports_json_mode,
        "how_to_switch": "Set LLM_PROVIDER + LLM_MODEL (+ optional LLM_JUDGE_MODEL) in .env",
    }
