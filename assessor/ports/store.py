from __future__ import annotations

from typing import Optional, Protocol


class AssessmentStorePort(Protocol):
    def save_report(
        self,
        run_id: str,
        report: dict,
        *,
        question: str,
        vendor: str,
        tier: str,
        users: int,
        requested_by: str,
        role: str,
    ) -> None: ...

    def get(self, run_id: str) -> Optional[dict]: ...

    def list_recent(self, limit: int = 20) -> list[dict]: ...

    def update_approval(self, run_id: str, approval: dict) -> Optional[dict]: ...
