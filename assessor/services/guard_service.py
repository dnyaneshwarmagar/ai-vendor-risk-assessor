"""Input / output guardrails as an injectable service."""

from __future__ import annotations

from typing import Optional

from assessor.guardrails import check_intent, enforce_output_policy, redact_input
from assessor.ports.guardrails import GuardrailPort
from assessor.schemas import AssessmentReport


class GuardService(GuardrailPort):
    """Implements GuardrailPort; thin OOP façade over guardrails module functions."""

    def redact_input(self, text: str) -> tuple[str, list[str]]:
        return redact_input(text)

    def check_intent(self, text: str) -> Optional[str]:
        return check_intent(text)

    def enforce_output(self, report: AssessmentReport) -> AssessmentReport:
        return enforce_output_policy(report)
