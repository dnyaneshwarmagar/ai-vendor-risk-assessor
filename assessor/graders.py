"""
graders.py — the two checks before an answer leaves the system.

COURSE MAP
  Agentic RAG guide  "agents.py → Answer Grader" and "Hallucination Grader".
  Production RAG     Module 9 "Reasoning, self-checks and guardrails"; Module 10 faithfulness.

Milestone 3: grader prompts from the Agentic RAG kit; `LLM.structured()` with GradeResult;
retry loop — relevant=no → broaden search; grounded=no → stricter regenerate, then abstain.
"""

from __future__ import annotations

import re
from typing import Callable, Optional

from pydantic import BaseModel

from .llm import LLM
from .policy_rag import tokenize
from .schemas import PolicyAnswer, PolicyHit


class GradeResult(BaseModel):
    verdict: bool
    reason: str = ""


# Agentic RAG Answer Grader backstory → system prompt
RELEVANCE_SYSTEM = """You are a strict Answer Grader for Nimbu Mart policy Q&A.
You read the question and the retrieved policy text and judge ONLY one thing: does this text
actually address the question? Related topic is not enough — the key ideas that answer the
question must be present (e.g. the right clause, tier, or role).
Return JSON {"verdict": true|false, "reason": "..."}.
verdict true = relevant; false = not relevant."""

# Agentic RAG Hallucination Grader backstory → system prompt
GROUNDED_SYSTEM = """You are a fact-checker Hallucination Grader for Nimbu Mart policy answers.
Compare the draft answer with the source policy clauses. Every important claim, number, role
name and requirement in the answer must be supported by that source. An answer that invents
facts, numbers or names is a hallucination — verdict false.
Return JSON {"verdict": true|false, "reason": "..."}.
verdict true = fully grounded; false = hallucinated or unsupported."""


def grade_relevance(question: str, context: str, llm: Optional[LLM] = None) -> GradeResult:
    def mock() -> dict:
        q, c = set(tokenize(question)), set(tokenize(context))
        overlap = len(q & c)
        return {"verdict": overlap >= max(1, len(q) // 3),
                "reason": f"{overlap}/{len(q)} question terms found in context (heuristic)"}

    return (llm or LLM()).structured(
        RELEVANCE_SYSTEM, f"Question: {question}\n\nContext:\n{context[:6000]}",
        GradeResult, stage="grade_relevance", mock=mock)


def grade_grounded(answer: str, sources: str, llm: Optional[LLM] = None) -> GradeResult:
    def mock() -> dict:
        src = set(tokenize(sources))
        body = re.sub(r"^[A-Z]{1,5}-[\d.]+:\s*", "", answer)
        body = re.sub(r"\(source:.*?\)\s*$", "", body).strip()
        sentences = [s for s in re.split(r"(?<=[.!?])\s+|\s*\|\s*", body) if len(tokenize(s)) >= 3]
        unsupported = [s for s in sentences if len(set(tokenize(s)) & src) / max(1, len(set(tokenize(s)))) < 0.6]
        return {"verdict": not unsupported,
                "reason": ("all sentences supported" if not unsupported else f"unsupported: {unsupported[0][:80]}")
                          + " (heuristic)"}

    return (llm or LLM()).structured(
        GROUNDED_SYSTEM, f"Sources:\n{sources[:8000]}\n\nAnswer:\n{answer}",
        GradeResult, stage="grade_grounded", mock=mock)


def _ctx(hits: list[PolicyHit]) -> str:
    return "\n\n".join(f"{h.clause_id or h.heading}\n{h.text}" for h in hits)


def grade_policy_answer(
    pa: PolicyAnswer,
    llm: Optional[LLM] = None,
    *,
    broaden: Callable[[], PolicyAnswer] | None = None,
    regenerate: Callable[[list[PolicyHit]], PolicyAnswer] | None = None,
) -> PolicyAnswer:
    """Grade relevance + groundedness with retry (Milestone 3).

    relevant=no → call `broaden()` once for a wider retrieval + new answer.
    grounded=no → call `regenerate()` with a stricter prompt, then abstain if still bad.
    """
    if pa.abstained or not pa.citations:
        return pa

    llm = llm or LLM()
    ctx = _ctx(pa.citations)
    rel = grade_relevance(pa.question, ctx, llm)
    pa.grader_relevant = rel.verdict

    if not rel.verdict and broaden is not None:
        pa = broaden()
        if pa.abstained or not pa.citations:
            return pa
        ctx = _ctx(pa.citations)
        rel = grade_relevance(pa.question, ctx, llm)
        pa.grader_relevant = rel.verdict

    if not pa.grader_relevant:
        pa.abstained = True
        pa.answer = ("I could not find policy text that actually answers this question. "
                     "Try naming a clause id (e.g. AI-5.1) or asking Procurement.")
        return pa

    gnd = grade_grounded(pa.answer, ctx, llm)
    pa.grader_grounded = gnd.verdict

    if not gnd.verdict and regenerate is not None:
        pa = regenerate(pa.citations)
        ctx = _ctx(pa.citations)
        gnd = grade_grounded(pa.answer, ctx, llm)
        pa.grader_grounded = gnd.verdict
        pa.grader_relevant = True

    if not pa.grader_grounded:
        pa.abstained = True
        pa.answer = ("I found related policy text but could not produce an answer that is fully "
                     "supported by it. Please read the cited clauses directly.")
    return pa
