from __future__ import annotations

from typing import Iterable, Optional, Protocol

from assessor.schemas import PolicyAnswer, PolicyHit


class PolicyLibraryPort(Protocol):
    def search(
        self,
        question: str,
        user_groups: Iterable[str] = ("public",),
        *,
        k: int = 5,
        include_archived: bool = False,
        trusted_only: bool = True,
    ) -> list[PolicyHit]: ...

    def answer(
        self,
        question: str,
        user_groups: Iterable[str] = ("public",),
        *,
        llm=None,
        k: int = 4,
        include_archived: bool = False,
    ) -> PolicyAnswer: ...

    def approved_vendor_entry(self, vendor: str, user_groups: Iterable[str]) -> dict | str | None: ...
