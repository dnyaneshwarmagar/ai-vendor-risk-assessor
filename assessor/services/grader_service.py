"""Policy answer graders as an injectable service."""

from __future__ import annotations

from typing import Callable, Optional

from assessor.graders import grade_policy_answer
from assessor.ports.graders import GraderPort
from assessor.ports.llm import LLMPort
from assessor.schemas import PolicyAnswer, PolicyHit


class GraderService(GraderPort):
    def __init__(self, llm: LLMPort):
        self._llm = llm

    def grade(
        self,
        answer: PolicyAnswer,
        *,
        broaden: Callable[[], PolicyAnswer] | None = None,
        regenerate: Callable[[list[PolicyHit]], PolicyAnswer] | None = None,
    ) -> PolicyAnswer:
        return grade_policy_answer(
            answer,
            llm=self._llm,  # type: ignore[arg-type]
            broaden=broaden,
            regenerate=regenerate,
        )
