"""DI / OOP architecture smoke tests."""
from pathlib import Path

from assessor.container import AppContainer, reset_container
from assessor.graph import Pipeline, new_state
from assessor.llm import LLM
from assessor.policy_rag import PolicyLibrary
from assessor.services.assessment_service import AssessmentService
from assessor.services.grader_service import GraderService
from assessor.services.guard_service import GuardService
from assessor.services.router_service import RouterService
from assessor.store import AssessmentStore
from assessor.vendor_research import AssessmentMemory


def test_container_builds_assessment_service(tmp_path: Path):
    reset_container()
    app = AppContainer.create(
        store=AssessmentStore(tmp_path / "h.sqlite3"),
        memory=AssessmentMemory(tmp_path / "m.json"),
    )
    pipe = app.pipeline()
    assert isinstance(pipe, AssessmentService)
    assert isinstance(pipe.llm, LLM)
    assert isinstance(pipe.library, PolicyLibrary)
    assert isinstance(pipe.router, RouterService)
    assert isinstance(pipe.graders, GraderService)
    assert isinstance(pipe.guards, GuardService)


def test_pipeline_convenience_constructor_still_works():
    """Legacy Pipeline(...) without container remains usable for tests."""
    pipe = Pipeline()
    s = pipe.run_plain(new_state("Where must customer personal data be stored?", user_groups=["public", "employees"]))
    assert s["route"] == "policy"
    assert "India" in s["answer"]


def test_injected_pipeline_runs_assessment():
    app = AppContainer.create()
    pipe = app.pipeline()
    s = pipe.run_plain(
        new_state(
            "Can our support team use LedgerLens AI to summarise customer tickets?",
            user_groups=["public", "employees", "security"],
            tier="T3",
            users=35,
            vendor="LedgerLens AI",
        )
    )
    assert s["report"].overall == "BLOCKED"
