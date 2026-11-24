"""
container.py — composition root (Dependency Injection).

Wires concrete adapters to ports. Callers (CLI, API, UI, tests) ask the container
for an AssessmentService / Pipeline instead of `new`-ing dependencies themselves.

Usage
  from assessor.container import AppContainer
  app = AppContainer.create()
  pipe = app.pipeline(tracer=tracer, budget=budget)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from assessor.config import SETTINGS, Settings
from assessor.llm import LLM
from assessor.matcher import Matcher
from assessor.policy_rag import PolicyLibrary
from assessor.services.assessment_service import AssessmentService
from assessor.services.grader_service import GraderService
from assessor.services.guard_service import GuardService
from assessor.services.router_service import RouterService
from assessor.store import AssessmentStore
from assessor.tracing import Budget, Tracer
from assessor.vendor_research import AssessmentMemory, VendorResearcher


@dataclass
class AppContainer:
    """Application composition root. Immutable after `create()`."""

    settings: Settings
    policy_library: PolicyLibrary
    store: AssessmentStore
    memory: AssessmentMemory
    _library_shared: bool = field(default=True, repr=False)

    @classmethod
    def create(
        cls,
        *,
        settings: Settings | None = None,
        policy_library: PolicyLibrary | None = None,
        store: AssessmentStore | None = None,
        memory: AssessmentMemory | None = None,
    ) -> "AppContainer":
        """Build the shared long-lived graph (policy index, store, memory)."""
        return cls(
            settings=settings or SETTINGS,
            policy_library=policy_library or PolicyLibrary(),
            store=store or AssessmentStore(),
            memory=memory if memory is not None else AssessmentMemory(),
        )

    # ------------------------------------------------------------------ factories (per-request / per-run)
    def budget(self, max_usd: float | None = None) -> Budget:
        return Budget(max_usd=max_usd) if max_usd is not None else Budget()

    def tracer(self, kind: str = "assess") -> Tracer:
        return Tracer(kind)

    def llm(self, budget: Budget, tracer: Tracer | None = None, *, small: bool = False) -> LLM:
        if small:
            return LLM.small(budget=budget, tracer=tracer)
        return LLM(budget=budget, tracer=tracer)

    def researcher(self, budget: Budget, tracer: Tracer | None = None) -> VendorResearcher:
        return VendorResearcher(budget=budget, tracer=tracer, memory=self.memory)

    def matcher(self) -> Matcher:
        return Matcher(self.policy_library)

    def guards(self) -> GuardService:
        return GuardService()

    def router(self, llm: LLM) -> RouterService:
        return RouterService(llm=llm)

    def graders(self, llm: LLM) -> GraderService:
        return GraderService(llm=llm)

    def pipeline(
        self,
        *,
        tracer: Tracer | None = None,
        budget: Budget | None = None,
        on_progress: Callable[[str, dict], None] | None = None,
    ) -> AssessmentService:
        """Compose one AssessmentService with constructor-injected dependencies."""
        budget = budget or self.budget()
        llm = self.llm(budget, tracer)
        researcher = self.researcher(budget, tracer)
        return AssessmentService(
            policy_library=self.policy_library,
            researcher=researcher,
            matcher=self.matcher(),
            llm=llm,
            router=self.router(llm),
            graders=self.graders(llm),
            guards=self.guards(),
            budget=budget,
            tracer=tracer,
            on_progress=on_progress,
            known_vendors=list(researcher.web.vendors),
            store=self.store,
        )


# Module-level lazy singleton for CLI / API convenience
_default: Optional[AppContainer] = None


def get_container() -> AppContainer:
    global _default
    if _default is None:
        _default = AppContainer.create()
    return _default


def reset_container() -> None:
    """Tests can clear the singleton between cases."""
    global _default
    _default = None
