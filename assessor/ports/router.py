from __future__ import annotations

from typing import Iterable, Protocol

from assessor.schemas import RouteDecision


class RouterPort(Protocol):
    def decide(self, question: str, known_vendors: Iterable[str]) -> RouteDecision: ...
