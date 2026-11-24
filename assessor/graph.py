"""
graph.py — backward-compatible façade over AssessmentService.

Prefer:
  from assessor.container import AppContainer
  pipe = AppContainer.create().pipeline(tracer=..., budget=...)

`Pipeline` still works for tests and older call sites: it constructs default
adapters when dependencies are omitted (convenience constructor).
"""

from __future__ import annotations

from typing import Callable, Optional

from assessor.llm import LLM
from assessor.matcher import Matcher
from assessor.policy_rag import PolicyLibrary
from assessor.services.assessment_service import (  # noqa: F401 — re-export
    APPROVERS,
    AssessmentService,
    AssessmentState,
    new_assessment_state,
)
from assessor.services.grader_service import GraderService
from assessor.services.guard_service import GuardService
from assessor.services.router_service import RouterService
from assessor.tracing import Budget, Tracer
from assessor.vendor_research import VendorResearcher

# Public aliases expected by tests / CLI / eval
State = AssessmentState
new_state = new_assessment_state


class Pipeline(AssessmentService):
    """
    Compatibility wrapper: `Pipeline(tracer=, budget=, library=)` still works.

    Internally uses constructor injection of ports/services.
    """

    def __init__(
        self,
        tracer: Tracer | None = None,
        budget: Budget | None = None,
        library: PolicyLibrary | None = None,
        on_progress: Callable[[str, dict], None] | None = None,
        *,
        researcher: VendorResearcher | None = None,
        matcher: Matcher | None = None,
        llm: LLM | None = None,
        router: RouterService | None = None,
        graders: GraderService | None = None,
        guards: GuardService | None = None,
        store=None,
        known_vendors: list[str] | None = None,
    ):
        budget = budget or Budget()
        library = library or PolicyLibrary()
        llm = llm or LLM(budget=budget, tracer=tracer)
        researcher = researcher or VendorResearcher(budget=budget, tracer=tracer)
        matcher = matcher or Matcher(library)
        router = router or RouterService(llm=llm)
        graders = graders or GraderService(llm=llm)
        guards = guards or GuardService()
        vendors = known_vendors if known_vendors is not None else list(researcher.web.vendors)

        super().__init__(
            policy_library=library,
            researcher=researcher,
            matcher=matcher,
            llm=llm,
            router=router,
            graders=graders,
            guards=guards,
            budget=budget,
            tracer=tracer,
            on_progress=on_progress,
            known_vendors=vendors,
            store=store,
        )
