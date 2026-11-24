from __future__ import annotations

from typing import Callable, Protocol, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMPort(Protocol):
    """Outbound port for chat / structured LLM calls."""

    mock_mode: bool

    def chat(
        self,
        system: str,
        user: str,
        *,
        stage: str = "llm",
        json_mode: bool = False,
        mock: Callable[[], str] | None = None,
    ) -> str: ...

    def structured(
        self,
        system: str,
        user: str,
        schema: Type[T],
        *,
        stage: str = "llm",
        mock: Callable[[], dict] | None = None,
        max_repairs: int = 2,
    ) -> T: ...
