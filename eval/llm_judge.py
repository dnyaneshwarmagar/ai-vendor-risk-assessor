"""
eval/llm_judge.py — Milestone 6 LLM-as-judge for verdict *reasons* (faithfulness to evidence).

Offline mock: heuristic overlap between reason tokens and evidence/profile text.
Live: asks the configured LLM whether each reason is supported by the cited evidence.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from assessor.config import GOLD_SET, SETTINGS  # noqa: E402
from assessor.graph import Pipeline, new_state  # noqa: E402
from assessor.llm import LLM  # noqa: E402
from assessor.policy_rag import tokenize  # noqa: E402
from assessor.tracing import Budget  # noqa: E402


class JudgeVerdict(BaseModel):
    faithful: bool
    reason: str = ""


JUDGE_SYSTEM = """You are an auditor. Given a requirement verdict reason and the evidence snippets,
decide whether the reason is faithful (supported) or invents facts. Return JSON
{"faithful": true|false, "reason": "..."}."""


def judge_reason(reason: str, evidence: str, llm: Optional[LLM] = None) -> JudgeVerdict:
    def mock() -> dict:
        rtoks, etoks = set(tokenize(reason)), set(tokenize(evidence))
        if not rtoks:
            return {"faithful": True, "reason": "empty reason"}
        overlap = len(rtoks & etoks) / max(1, len(rtoks))
        return {"faithful": overlap >= 0.25, "reason": f"token overlap {overlap:.2f} (heuristic)"}

    return (llm or LLM()).structured(
        JUDGE_SYSTEM, f"Reason:\n{reason}\n\nEvidence:\n{evidence[:6000]}",
        JudgeVerdict, stage="llm_judge", mock=mock,
    )


def main() -> int:
    SETTINGS.verbose = False
    gold = json.loads(GOLD_SET.read_text(encoding="utf-8"))
    pipe = Pipeline(tracer=None, budget=Budget(max_usd=5))
    llm = LLM(budget=pipe.budget)
    total = faithful = 0
    rows = []
    for case in gold["cases"]:
        s = new_state(case["question"], user_groups=case["user_groups"], tier=case["tier"],
                      users=case["users"], vendor=case["vendor"], domain=case.get("official_domain"))
        s = pipe.run_plain(s)
        rep = s["report"]
        for r in rep.results:
            if r.verdict in ("NOT_APPLICABLE",):
                continue
            evidence = " ".join(r.evidence_urls) + " " + r.reason
            # Prefer profile fact text when available
            for fact in rep.profile.facts.values():
                if any(u in fact.sources for u in r.evidence_urls):
                    evidence += " " + fact.display
            j = judge_reason(r.reason, evidence, llm)
            total += 1
            faithful += int(j.faithful)
            rows.append((case["id"], r.requirement_id, r.verdict, j.faithful, j.reason[:60]))
    rate = faithful / max(1, total)
    lines = [f"# LLM-as-judge (reason faithfulness)", "",
             f"Faithful reasons: **{faithful}/{total} = {rate:.1%}**", "",
             "| case | requirement | verdict | faithful | note |", "|---|---|---|---|---|"]
    for row in rows:
        lines.append(f"| {row[0]} | {row[1]} | {row[2]} | {'✓' if row[3] else '✗'} | {row[4]} |")
    out = ROOT / "reports" / "llm_judge_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:8]))
    print(f"... ({len(rows)} rows) → {out}")
    return 0 if rate >= 0.8 else 1


if __name__ == "__main__":
    raise SystemExit(main())
