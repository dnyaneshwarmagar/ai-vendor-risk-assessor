from __future__ import annotations

from typing import Protocol

from assessor.schemas import AssessmentRequest, Overall, RequirementResult, VendorProfile


class MatcherPort(Protocol):
    def evaluate(self, profile: VendorProfile, request: AssessmentRequest) -> list[RequirementResult]: ...

    def overall(self, results: list[RequirementResult]) -> tuple[Overall, str]: ...
