"""Question router as an injectable service."""

from __future__ import annotations

from typing import Iterable, Optional

from assessor.ports.llm import LLMPort
from assessor.ports.router import RouterPort
from assessor.router import decide
from assessor.schemas import RouteDecision


class RouterService(RouterPort):
    def __init__(self, llm: LLMPort):
        self._llm = llm

    def decide(self, question: str, known_vendors: Iterable[str]) -> RouteDecision:
        return decide(question, known_vendors, llm=self._llm)  # type: ignore[arg-type]
