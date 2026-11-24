"""
assessment_service.py — application use-case orchestrator (OOP + DI).

Depends only on ports (injected). Concrete adapters are wired in `assessor.container`.
"""

from __future__ import annotations

import time
from datetime import date
from typing import Any, Callable, Optional, TypedDict

from assessor.ports.graders import GraderPort
from assessor.ports.guardrails import GuardrailPort
from assessor.ports.llm import LLMPort
from assessor.ports.matching import MatcherPort
from assessor.ports.policy import PolicyLibraryPort
from assessor.ports.research import VendorResearchPort
from assessor.ports.router import RouterPort
from assessor.ports.store import AssessmentStorePort
from assessor.questionnaire import as_email, build_questions
from assessor.report import to_markdown
from assessor.schemas import Approval, AssessmentReport, AssessmentRequest, PolicyAnswer

APPROVERS = {
    "T1": ["Team lead"],
    "T2": ["Head of Information Security"],
    "T3": ["Head of Information Security", "DPO"],
}


class AssessmentState(TypedDict, total=False):
    question: str
    user_groups: list[str]
    tier: str
    users: int
    vendor: Optional[str]
    domain: Optional[str]
    requested_by: str
    interactive: bool
    approver: Optional[str]
    decision: Optional[str]
    route: Optional[str]
    refusal: Optional[str]
    policy_answer: Any
    profile: Any
    request: Any
    results: Any
    overall: Optional[str]
    overall_reason: Optional[str]
    open_questions: list[dict]
    approval: Any
    report: Any
    answer: Optional[str]
    guardrail_notes: list[str]
    started: float


def new_assessment_state(
    question: str,
    *,
    user_groups: list[str] | None = None,
    tier: str = "T3",
    users: int = 1,
    vendor: str | None = None,
    domain: str | None = None,
    requested_by: str = "cli",
    interactive: bool = False,
    approver: str | None = None,
    decision: str | None = None,
) -> dict:
    return {
        "question": question,
        "user_groups": user_groups or ["public", "employees"],
        "tier": tier,
        "users": users,
        "vendor": vendor,
        "domain": domain,
        "requested_by": requested_by,
        "interactive": interactive,
        "approver": approver,
        "decision": decision,
        "route": None,
        "refusal": None,
        "policy_answer": None,
        "profile": None,
        "results": None,
        "overall": None,
        "overall_reason": None,
        "open_questions": [],
        "approval": None,
        "report": None,
        "answer": None,
        "guardrail_notes": [],
        "started": time.time(),
    }


class AssessmentService:
    """
    Vendor-risk assessment use case.

    All collaborators are constructor-injected (Dependency Inversion).
    """

    def __init__(
        self,
        *,
        policy_library: PolicyLibraryPort,
        researcher: VendorResearchPort,
        matcher: MatcherPort,
        llm: LLMPort,
        router: RouterPort,
        graders: GraderPort,
        guards: GuardrailPort,
        budget: Any,
        tracer: Any = None,
        on_progress: Callable[[str, dict], None] | None = None,
        known_vendors: list[str] | None = None,
        store: AssessmentStorePort | None = None,
    ):
        self.library = policy_library
        self.researcher = researcher
        self.matcher = matcher
        self.llm = llm
        self.router = router
        self.graders = graders
        self.guards = guards
        self.budget = budget
        self.tracer = tracer
        self.on_progress = on_progress
        self.known_vendors = known_vendors or []
        self.store = store

    # ------------------------------------------------------------------ observability
    def _t(self, stage: str, **data: Any) -> None:
        if self.tracer:
            self.tracer.event(stage, **data)
        if self.on_progress:
            try:
                self.on_progress(stage, data)
            except Exception:
                pass

    # ------------------------------------------------------------------ nodes
    def guard_input(self, s: dict) -> dict:
        q, notes = self.guards.redact_input(s["question"])
        refusal = self.guards.check_intent(q)
        self._t("guard_input", redactions=notes, refused=bool(refusal))
        return {
            "question": q,
            "guardrail_notes": s["guardrail_notes"] + notes,
            "refusal": refusal,
            "route": "refuse" if refusal else None,
        }

    def route(self, s: dict) -> dict:
        if s.get("route") == "refuse":
            return {}
        vendors = self.known_vendors + ([s["vendor"]] if s.get("vendor") else [])
        d = self.router.decide(s["question"], vendors)
        if s.get("vendor"):
            d.vendor = s["vendor"]
        self._t("route", route=d.route, vendor=d.vendor, reason=d.reason)
        return {"route": d.route, "vendor": d.vendor or s.get("vendor")}

    def policy_qa(self, s: dict) -> dict:
        pa = self.library.answer(s["question"], s["user_groups"], llm=self.llm, k=4)

        def broaden() -> PolicyAnswer:
            return self.library.answer(s["question"], s["user_groups"], llm=self.llm, k=8)

        def regenerate(citations) -> PolicyAnswer:
            top = citations[0]
            stricter = (
                f"{top.clause_id or top.heading}: "
                f"{top.text.strip().splitlines()[0][:400]}  "
                f"(source: {top.title}, v{top.version})"
            )
            return PolicyAnswer(
                question=s["question"], answer=stricter, citations=citations, mode="extractive"
            )

        pa = self.graders.grade(pa, broaden=broaden, regenerate=regenerate)
        self._t(
            "policy_qa",
            abstained=pa.abstained,
            citations=[c.clause_id or c.heading for c in pa.citations[:3]],
            relevant=pa.grader_relevant,
            grounded=pa.grader_grounded,
        )
        cites = "\n".join(
            f"  - {c.clause_id or c.heading} — {c.title} (v{c.version})" for c in pa.citations[:3]
        )
        return {
            "policy_answer": pa,
            "answer": pa.answer + ("\n\nSources:\n" + cites if cites else ""),
        }

    def vendor_research(self, s: dict) -> dict:
        profile = self.researcher.research(s["vendor"], s.get("domain"))
        return {"profile": profile}

    def facts_only(self, s: dict) -> dict:
        pf = s["profile"]
        lines = [f"What public sources say about {pf.vendor} (as of {pf.as_of}):"]
        for f, fact in pf.facts.items():
            src = fact.sources[0] if fact.sources else "n/a"
            lines.append(
                f"- {f}: {fact.display}  [{fact.evidence_level}, confidence {fact.confidence:.2f}, {src}]"
            )
        if pf.quarantined:
            lines.append(f"- {len(pf.quarantined)} page(s) quarantined for prompt injection and ignored.")
        lines.append(
            "Note: these are facts, not a policy verdict. Ask 'Can <team> use <tool>...' for an assessment."
        )
        return {"answer": "\n".join(lines)}

    def match(self, s: dict) -> dict:
        req = AssessmentRequest(
            question=s["question"],
            vendor=s["vendor"],
            official_domain=s["profile"].official_domain,
            tier=s["tier"],
            users=s["users"],
            user_groups=s["user_groups"],
            requested_by=s["requested_by"],
        )
        results = self.matcher.evaluate(s["profile"], req)
        overall, reason = self.matcher.overall(results)
        self._t("match", overall=overall, verdicts={r.requirement_id: r.verdict for r in results})
        return {"request": req, "results": results, "overall": overall, "overall_reason": reason}

    def questionnaire(self, s: dict) -> dict:
        qs = build_questions(s["results"], self.library)
        self._t("questionnaire", questions=[q["id"] for q in qs])
        return {"open_questions": qs}

    def human_gate(self, s: dict) -> dict:
        roles = APPROVERS.get(s["tier"], [])
        approval = Approval(status="pending", approver_roles=roles)
        decision = s.get("decision")
        if s.get("interactive") and decision is None:
            print(f"\nOutcome so far: {s['overall']} — {s['overall_reason']}")
            print(f"Approvers for {s['tier']}: {', '.join(roles)}")
            decision = input("Record a decision now? [approve / reject / leave pending]: ").strip().lower() or "pending"
        if decision in ("approve", "approved") and s["overall"] != "BLOCKED":
            approval = Approval(
                status="approved",
                approver_roles=roles,
                decided_by=s.get("approver") or "cli-user",
                decided_on=date.today(),
                comment="Recorded via CLI",
            )
        elif decision in ("approve", "approved") and s["overall"] == "BLOCKED":
            approval.comment = (
                "Approval refused by the gate: a blocking requirement failed. "
                "Resolve it or change the data tier."
            )
        elif decision in ("reject", "rejected"):
            approval = Approval(
                status="rejected",
                approver_roles=roles,
                decided_by=s.get("approver") or "cli-user",
                decided_on=date.today(),
            )
        self._t("human_gate", status=approval.status, decided_by=approval.decided_by)
        return {"approval": approval}

    def report(self, s: dict) -> dict:
        rep = AssessmentReport(
            request=s["request"],
            profile=s["profile"],
            results=s["results"],
            overall=s["overall"],
            overall_reason=s["overall_reason"],
            open_questions=s["open_questions"],
            approval=s["approval"],
            guardrail_notes=list(s["guardrail_notes"]),
            run_id=self.tracer.run_id if self.tracer else "",
            cost_usd=round(self.budget.spent_usd, 4),
            llm_calls=self.budget.llm_calls,
            duration_s=round(time.time() - s["started"], 2),
        )
        before = [r.verdict for r in rep.results]
        rep = self.guards.enforce_output(rep)
        if [r.verdict for r in rep.results] != before:
            rep.overall, rep.overall_reason = self.matcher.overall(rep.results)
        md = to_markdown(rep)
        if self.tracer:
            self.tracer.write_text("report.md", md)
            self.tracer.write_json("report.json", rep.model_dump(mode="json"))
            self.tracer.write_json("profile.json", rep.profile.model_dump(mode="json"))
            email = as_email(rep.request.vendor, rep.open_questions)
            if email:
                self.tracer.write_text("vendor_questions.txt", email)
        if self.store is not None and rep.run_id:
            try:
                self.store.save_report(
                    rep.run_id,
                    rep.model_dump(mode="json"),
                    question=rep.request.question,
                    vendor=rep.request.vendor,
                    tier=rep.request.tier,
                    users=rep.request.users,
                    requested_by=rep.request.requested_by,
                    role="system",
                )
            except Exception as exc:  # noqa: BLE001
                self._t("store_save_failed", error=str(exc)[:120])
        self._t("report", overall=rep.overall, run_dir=str(self.tracer.dir) if self.tracer else None)
        return {"report": rep, "answer": md}

    def refuse(self, s: dict) -> dict:
        return {"answer": s.get("refusal") or "I can only help with vendor assessments and policy questions."}

    # ------------------------------------------------------------------ engines
    def run_plain(self, s: dict) -> dict:
        s.update(self.guard_input(s))
        s.update(self.route(s))
        if s["route"] == "refuse":
            s.update(self.refuse(s))
        elif s["route"] == "policy":
            s.update(self.policy_qa(s))
        elif s["route"] == "vendor":
            s.update(self.vendor_research(s))
            s.update(self.facts_only(s))
        else:
            s.update(self.vendor_research(s))
            s.update(self.match(s))
            s.update(self.questionnaire(s))
            s.update(self.human_gate(s))
            s.update(self.report(s))
        return s

    def build_langgraph(self, *, checkpoint: bool = False, pause_for_human: bool = False):
        from langgraph.graph import END, START, StateGraph

        g = StateGraph(AssessmentState)
        for name in (
            "guard_input", "route", "policy_qa", "vendor_research", "facts_only",
            "match", "questionnaire", "human_gate", "report", "refuse",
        ):
            g.add_node(name, getattr(self, name))
        g.add_edge(START, "guard_input")
        g.add_edge("guard_input", "route")
        g.add_conditional_edges(
            "route",
            lambda st: st["route"],
            {
                "refuse": "refuse",
                "policy": "policy_qa",
                "vendor": "vendor_research",
                "assessment": "vendor_research",
            },
        )
        g.add_conditional_edges(
            "vendor_research",
            lambda st: "facts_only" if st["route"] == "vendor" else "match",
            {"facts_only": "facts_only", "match": "match"},
        )
        g.add_edge("match", "questionnaire")
        g.add_edge("questionnaire", "human_gate")
        g.add_edge("human_gate", "report")
        for leaf in ("policy_qa", "facts_only", "report", "refuse"):
            g.add_edge(leaf, END)

        kwargs: dict[str, Any] = {}
        if checkpoint or pause_for_human:
            try:
                from langgraph.checkpoint.memory import MemorySaver

                kwargs["checkpointer"] = MemorySaver()
            except Exception:
                pass
            if pause_for_human:
                kwargs["interrupt_before"] = ["human_gate"]
        return g.compile(**kwargs)

    def run(
        self,
        s: dict,
        engine: str = "auto",
        *,
        thread_id: str | None = None,
        pause_for_human: bool = False,
    ) -> dict:
        if engine in ("auto", "langgraph"):
            try:
                graph = self.build_langgraph(
                    checkpoint=bool(thread_id) or pause_for_human,
                    pause_for_human=pause_for_human,
                )
                self._t("engine", name="langgraph", pause_for_human=pause_for_human)
                cfg = {"configurable": {"thread_id": thread_id or "default"}}
                out = graph.invoke(s, cfg)
                s.update(out)
                return s
            except ImportError:
                if engine == "langgraph":
                    raise
        self._t("engine", name="plain")
        return self.run_plain(s)

    def resume_human_gate(self, thread_id: str, decision: str, approver: str) -> dict:
        graph = self.build_langgraph(checkpoint=True, pause_for_human=True)
        cfg = {"configurable": {"thread_id": thread_id}}
        return graph.invoke(
            {"decision": decision, "approver": approver, "interactive": False}, cfg
        )
