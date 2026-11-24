from __future__ import annotations

from typing import Any, Callable, Protocol


class BudgetPort(Protocol):
    spent_usd: float
    llm_calls: int

    def charge(self, input_tokens: int, output_tokens: int) -> None: ...


class TracerPort(Protocol):
    run_id: str

    def event(self, stage: str, **data: Any) -> None: ...

    def close(self) -> None: ...


ProgressPort = Callable[[str, dict], None]
