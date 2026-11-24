"""
eval/run_ragas_eval.py — live pipeline answers + Ragas LLM-as-judge.

Models (via .env / assessor.providers):
  LLM_MODEL          — generates answers (e.g. ollama qwen2.5:3b)
  LLM_JUDGE_MODEL    — Ragas Faithfulness judge (e.g. ollama qwen2.5:7b)
  LLM_PROVIDER       — ollama | groq | openai | …

Usage
  python eval/run_ragas_eval.py --case pq-residency          # one gold case
  python eval/run_ragas_eval.py --one-by-one --limit 3        # cases sequentially
  python eval/run_ragas_eval.py --limit 2                    # batch of N

Requires: openai, ragas, langchain-openai, datasets + a live LLM_PROVIDER.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from assessor.config import GOLD_SET, SETTINGS  # noqa: E402
from assessor.graph import Pipeline, new_state  # noqa: E402
from assessor.providers import (  # noqa: E402
    build_langchain_chat,
    provider_summary,
    resolve_judge,
    resolve_provider,
)
from assessor.tracing import Budget  # noqa: E402


def _normalize_case(raw: dict, *, kind: str) -> dict:
    """Assessment cases and policy_questions share one shape for the pipeline."""
    return {
        "id": raw["id"],
        "kind": kind,
        "question": raw["question"],
        "user_groups": raw.get("user_groups") or ["public", "employees"],
        "tier": raw.get("tier", "T3"),
        "users": raw.get("users", 1),
        "vendor": raw.get("vendor"),
        "official_domain": raw.get("official_domain"),
        "expected_overall": raw.get("expected_overall", ""),
        "expected_verdicts": raw.get("expected_verdicts", {}),
    }


def _load_cases(*, case_id: str | None, limit: int | None, prefer_policy: bool = True) -> list[dict]:
    gold = json.loads(GOLD_SET.read_text(encoding="utf-8"))
    assessments = [_normalize_case(c, kind="assessment") for c in gold.get("cases", [])]
    policies = [_normalize_case(c, kind="policy") for c in gold.get("policy_questions", [])]
    # Policy Q&A is lighter for live Ollama; assessments first only when asked by id/limit over all
    cases = (policies + assessments) if prefer_policy else (assessments + policies)
    if case_id:
        matched = [c for c in cases if c["id"] == case_id]
        if not matched:
            ids = ", ".join(c["id"] for c in cases)
            raise SystemExit(f"Unknown case {case_id!r}. Available: {ids}")
        return matched
    if limit is not None:
        return cases[:limit]
    return cases


def _sample_from_case(case: dict, pipe: Pipeline) -> dict:
    s = new_state(
        case["question"],
        user_groups=case["user_groups"],
        tier=case["tier"],
        users=case["users"],
        vendor=case.get("vendor"),
        domain=case.get("official_domain"),
    )
    t0 = time.time()
    # Policy gold rows: force the policy path so a small local router cannot
    # mis-route into vendor_research (seen with qwen2.5:3b on SOC2 questions).
    if case.get("kind") == "policy":
        s.update(pipe.guard_input(s))
        if s.get("route") == "refuse":
            s.update(pipe.refuse(s))
        else:
            s["route"] = "policy"
            s.update(pipe.policy_qa(s))
    else:
        s = pipe.run_plain(s)
    gen_s = round(time.time() - t0, 1)
    rep = s.get("report")
    pa = s.get("policy_answer")
    if pa is not None and getattr(pa, "answer", None):
        answer = pa.answer
        cites = getattr(pa, "citations", None) or []
        contexts = [getattr(c, "text", None) or str(c) for c in cites] or []
    elif rep is not None:
        answer = f"Overall: {rep.overall}. " + "; ".join(
            f"{r.requirement_id}={r.verdict}: {r.reason}" for r in (rep.results or [])[:5]
        )
        contexts = [r.reason for r in (rep.results or []) if r.reason][:5]
        for fact in list(rep.profile.facts.values())[:5]:
            contexts.append(f"{fact.field}: {fact.display}")
    else:
        answer = s.get("answer") or "(no answer)"
        contexts = [answer]
    if not contexts:
        contexts = [answer]
    return {
        "user_input": case["question"],
        "response": (answer or "")[:1200],
        "retrieved_contexts": [c[:800] for c in contexts[:4]],
        "reference": case.get("expected_overall", "") + " " + json.dumps(case.get("expected_verdicts", {})),
        "case_id": case["id"],
        "gen_seconds": gen_s,
        "route": s.get("route"),
    }


def _score_sample(sample: dict, judge, Faithfulness, run_cfg) -> dict:
    from datasets import Dataset
    from ragas import evaluate

    ds = Dataset.from_list(
        [
            {
                "user_input": sample["user_input"],
                "response": sample["response"],
                "retrieved_contexts": sample["retrieved_contexts"],
                "reference": sample["reference"],
            }
        ]
    )
    kwargs: dict = {"metrics": [Faithfulness()], "llm": judge}
    if run_cfg is not None:
        kwargs["run_config"] = run_cfg
    t0 = time.time()
    result = evaluate(ds, **kwargs)
    judge_s = round(time.time() - t0, 1)
    scores: dict = {}
    try:
        if hasattr(result, "to_pandas"):
            df = result.to_pandas()
            if "faithfulness" in df.columns:
                scores["faithfulness"] = float(df["faithfulness"].mean())
        if not scores and hasattr(result, "scores") and result.scores is not None:
            raw = result.scores
            scores = dict(raw[0]) if isinstance(raw, list) and raw else dict(raw)
        if not scores:
            as_map = dict(result)
            # ragas sometimes stringifies nested maps
            if "faithfulness" in as_map:
                scores["faithfulness"] = float(as_map["faithfulness"])
            else:
                scores = as_map
    except Exception as exc:  # noqa: BLE001
        scores = {"raw": str(result), "parse_error": str(exc)[:120]}
    return {"scores": scores, "judge_seconds": judge_s}


def main() -> int:
    ap = argparse.ArgumentParser(description="Live Ollama answers + Ragas judge")
    ap.add_argument("--case", type=str, default="", help="Single gold case id")
    ap.add_argument("--limit", type=int, default=None, help="Max cases (ignored if --case)")
    ap.add_argument("--one-by-one", action="store_true", help="Generate + judge each case separately")
    args = ap.parse_args()

    summary = provider_summary()
    gen_cfg = resolve_provider()
    judge_cfg = resolve_judge()
    print(
        f"Provider: {summary['provider']}\n"
        f"  generate (LLM_MODEL):      {gen_cfg.model}\n"
        f"  judge    (LLM_JUDGE_MODEL): {judge_cfg.model}\n"
        f"  base: {summary['base_url']}"
    )
    if summary["provider"] == "mock":
        print("ERROR: Set LLM_PROVIDER=ollama (or groq/openai) in .env — mock cannot generate or judge.")
        return 2

    try:
        from ragas.metrics import Faithfulness  # noqa: F401
        from ragas.run_config import RunConfig
    except ImportError as exc:
        print(f"ERROR: pip install openai ragas langchain-openai datasets\n{exc}")
        return 2

    # Default: first 3 policy questions (lighter live LLM). Use --case for a specific id.
    default_limit = None if args.case else 3
    cases = _load_cases(
        case_id=args.case or None,
        limit=args.limit if args.limit is not None else default_limit,
        prefer_policy=True,
    )
    one_by_one = args.one_by_one or bool(args.case) or True  # always one-by-one for live Ollama

    judge = build_langchain_chat(judge_cfg, temperature=0.0)
    try:
        run_cfg = RunConfig(timeout=600, max_workers=1)
    except Exception:  # noqa: BLE001
        run_cfg = None

    rows: list[dict] = []
    print(f"\nEvaluating {len(cases)} case(s) {'one-by-one' if one_by_one else 'as a batch'}…\n")

    if one_by_one:
        for i, case in enumerate(cases, 1):
            print(f"── [{i}/{len(cases)}] {case['id']} ──")
            print(f"Q: {case['question'][:100]}")
            pipe = Pipeline(tracer=None, budget=Budget(max_usd=5.0))
            sample = _sample_from_case(case, pipe)
            print(f"  route={sample['route']}  gen={sample['gen_seconds']}s  answer_len={len(sample['response'])}")
            scored = _score_sample(sample, judge, Faithfulness, run_cfg)
            faith = scored["scores"].get("faithfulness", scored["scores"])
            print(f"  faithfulness={faith}  judge={scored['judge_seconds']}s\n")
            rows.append({**sample, **scored})
    else:
        pipe = Pipeline(tracer=None, budget=Budget(max_usd=10.0))
        samples = [_sample_from_case(c, pipe) for c in cases]
        from datasets import Dataset
        from ragas import evaluate

        ds = Dataset.from_list(
            [
                {
                    "user_input": s["user_input"],
                    "response": s["response"],
                    "retrieved_contexts": s["retrieved_contexts"],
                    "reference": s["reference"],
                }
                for s in samples
            ]
        )
        kwargs: dict = {"metrics": [Faithfulness()], "llm": judge}
        if run_cfg is not None:
            kwargs["run_config"] = run_cfg
        result = evaluate(ds, **kwargs)
        try:
            batch_scores = dict(result)
        except Exception:  # noqa: BLE001
            batch_scores = {"raw": str(result)}
        for s in samples:
            rows.append({**s, "scores": batch_scores, "judge_seconds": None})

    lines = [
        "# Ragas LLM-as-judge report (live generation)",
        "",
        f"- provider: `{summary['provider']}`",
        f"- generate model: `{gen_cfg.model}`",
        f"- judge model: `{judge_cfg.model}`",
        f"- cases: {len(rows)} ({', '.join(r['case_id'] for r in rows)})",
        "",
        "## Per-case",
        "",
        "| case | route | gen_s | faithfulness | judge_s |",
        "|---|---|---:|---|---:|",
    ]
    for r in rows:
        faith = r.get("scores", {}).get("faithfulness", r.get("scores"))
        if isinstance(faith, float):
            faith_s = f"{faith:.3f}"
        else:
            faith_s = str(faith)
        lines.append(
            f"| {r['case_id']} | {r.get('route')} | {r.get('gen_seconds')} | {faith_s} | {r.get('judge_seconds')} |"
        )
    lines += [
        "",
        "## Models",
        "",
        "```env",
        "LLM_PROVIDER=ollama",
        "LLM_MODEL=qwen2.5:3b          # answer generation",
        "LLM_JUDGE_MODEL=qwen2.5:7b    # Ragas judge",
        "```",
        "",
    ]
    out = ROOT / "reports" / "ragas_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    # Reload dotenv into process if Settings was imported before .env edit in same shell
    raise SystemExit(main())
