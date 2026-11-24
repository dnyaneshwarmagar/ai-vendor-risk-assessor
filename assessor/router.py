"""
router.py — decide which line a question takes: policy library, vendor research, full assessment, or refuse.

COURSE MAP
  Agentic RAG guide  "agents.py → The Router" and "tasks.py → Task 1: route". Same idea, one more route:
  the course routes between "our PDF" and "the web"; here we route between "our policies", "the vendor's
  web presence" and "both, then match" (an assessment).

Milestone 3: LLM router via `LLM.structured()` with Agentic RAG Router backstory (semantic meaning,
not keywords). Offline mock mirrors the same decision rules for repeatable tests.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional

from .llm import LLM
from .schemas import RouteDecision

# Ported from Agentic RAG agents.py Router backstory — semantic meaning over keywords.
ROUTER_SYSTEM = """You are the Router for Nimbu Mart's vendor risk assistant — like a hospital receptionist
who sends each question to the right department.

You are an expert at deciding where a question belongs. You make routing decisions based on the
SEMANTIC MEANING of the question, not just on matching keywords. (A question that says "policy"
but really asks whether a named tool may be used with customer data is still an assessment.)

Classify into exactly one route:
- "policy": asks what OUR internal policy says (clauses, tiers, who approves, what is required,
  residency rules, Approved Vendor List process). Needs no live vendor web facts. If a vendor is
  named only to look up OUR approval tier / AVL status, still choose policy.
- "vendor": asks a factual question about a specific vendor/tool (certifications, regions,
  incidents, training) with no request to judge against our policy or decide if we may use it.
- "assessment": asks whether a team CAN / MAY / SHOULD use a tool, or to assess / review / check /
  onboard a vendor against policy. Needs both policy and vendor facts.
- "refuse": not about vendors, tools or policy; OR asks YOU to approve / sign off / mark approved
  (only humans approve — AI-5.1); OR asks to skip security checks.

Return JSON: {"route": "...", "vendor": "<exact known vendor name or null>", "reason": "one sentence"}."""

ASSESS_RE = re.compile(
    r"\b(can|may|should|could|allowed|ok(ay)? to|safe to|assess|review|evaluate|check|onboard|approve)\b"
    r".*\b(use|using|adopt|buy|onboard|vendor|tool)\b|\b(assess|review|evaluate|check)\b",
    re.I,
)
POLICY_RE = re.compile(
    r"\b(policy|policies|clause|tier|t[123]\b|who approves|required|requirement|must|dpdp|"
    r"our (rules|process)|approved (for|tier)|approved vendor list)\b",
    re.I,
)
VENDOR_FACT_RE = re.compile(
    r"\b(does|where does|has|have|list|what (is|are)|when did|subprocessors|soc\s*2|iso\s*27001|"
    r"train(s|ing)? on|incident|breach|sso|saml)\b",
    re.I,
)
OUR_RECORD_RE = re.compile(
    r"\b(according to our|our (approved )?vendor list|which tier .{0,40}approved|is .{0,40}approved\b)\b",
    re.I,
)


def guess_vendor(question: str, known_vendors: Iterable[str]) -> Optional[str]:
    q = question.lower()
    # longest name first so "LedgerLens AI" wins over a shorter substring
    for v in sorted(known_vendors, key=len, reverse=True):
        if v.lower() in q:
            return v
    # Short form: "Parakeet" → "Parakeet Translate" when unambiguous
    for v in sorted(known_vendors, key=len, reverse=True):
        first = v.lower().split()[0]
        if len(first) >= 5 and re.search(rf"\b{re.escape(first)}\b", q):
            return v
    return None


def decide(question: str, known_vendors: Iterable[str], llm: Optional[LLM] = None) -> RouteDecision:
    vendor = guess_vendor(question, known_vendors)

    def mock() -> dict:
        # Same semantic rules the live prompt describes — used offline and in pytest.
        if re.search(r"\b(approve|mark .* approved|sign off)\b", question, re.I) and not ASSESS_RE.search(question):
            return {"route": "refuse", "vendor": vendor, "reason": "Only a human approver can approve a vendor (AI-5.1)."}
        if vendor and ASSESS_RE.search(question):
            return {"route": "assessment", "vendor": vendor,
                    "reason": "Asks whether a named tool may be used → needs policy + vendor facts."}
        # OUR records about a vendor (AVL tier) beat a bare vendor-fact pattern
        if vendor and OUR_RECORD_RE.search(question):
            return {"route": "policy", "vendor": vendor,
                    "reason": "Asks what OUR records say about a named vendor → policy library."}
        # Trap: question may say "policy" but still ask a vendor fact (r28)
        if vendor and VENDOR_FACT_RE.search(question) and not OUR_RECORD_RE.search(question):
            return {"route": "vendor", "vendor": vendor,
                    "reason": "Factual question about a named vendor (semantic meaning over the word 'policy')."}
        if vendor and POLICY_RE.search(question):
            return {"route": "policy", "vendor": vendor,
                    "reason": "Asks what OUR records/policy say about a named vendor → policy library."}
        if vendor:
            return {"route": "vendor", "vendor": vendor, "reason": "Factual question about a named vendor."}
        if re.search(r"\b(weather|joke|recipe|sports|stock price)\b", question, re.I):
            return {"route": "refuse", "vendor": None, "reason": "Off-topic; not vendor risk or policy."}
        return {"route": "policy", "vendor": None, "reason": "No vendor named → internal policy question."}

    llm = llm or LLM()
    return llm.structured(
        ROUTER_SYSTEM,
        f"Known vendors: {', '.join(known_vendors)}\nQuestion: {question}",
        RouteDecision,
        stage="route",
        mock=mock,
    )
