from __future__ import annotations

from typing import Optional, Protocol

from assessor.schemas import AssessmentReport


class GuardrailPort(Protocol):
    def redact_input(self, text: str) -> tuple[str, list[str]]: ...

    def check_intent(self, text: str) -> Optional[str]: ...

    def enforce_output(self, report: AssessmentReport) -> AssessmentReport: ...
