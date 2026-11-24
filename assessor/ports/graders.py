from __future__ import annotations

from typing import Callable, Protocol

from assessor.schemas import PolicyAnswer, PolicyHit


class GraderPort(Protocol):
    def grade(
        self,
        answer: PolicyAnswer,
        *,
        broaden: Callable[[], PolicyAnswer] | None = None,
        regenerate: Callable[[list[PolicyHit]], PolicyAnswer] | None = None,
    ) -> PolicyAnswer: ...
