"""Ports — interfaces the application depends on (Dependency Inversion).

Adapters in the existing modules (LLM, PolicyLibrary, VendorResearcher, AssessmentStore)
implement these contracts. The composition root (`assessor.container`) wires them.
"""

from .llm import LLMPort
from .policy import PolicyLibraryPort
from .research import VendorResearchPort
from .router import RouterPort
from .graders import GraderPort
from .guardrails import GuardrailPort
from .matching import MatcherPort
from .store import AssessmentStorePort
from .observability import BudgetPort, TracerPort, ProgressPort

__all__ = [
    "LLMPort",
    "PolicyLibraryPort",
    "VendorResearchPort",
    "RouterPort",
    "GraderPort",
    "GuardrailPort",
    "MatcherPort",
    "AssessmentStorePort",
    "BudgetPort",
    "TracerPort",
    "ProgressPort",
]
