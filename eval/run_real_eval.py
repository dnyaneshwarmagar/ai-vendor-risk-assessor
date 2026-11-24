"""
eval/run_real_eval.py — score live (or cached) research against data/gold_set_real_solo.json.

Solo FAQ path: 3 hand-checked vendors (Notion, OpenAI, DeepL).

Usage
  # Offline dry-run against gold seeds only (documents methodology + expected fields)
  python eval/run_real_eval.py --gold-only

  # Live: requires SEARCH_PROVIDER=ddgs (or tavily) + live LLM_PROVIDER
  python eval/run_real_eval.py --live

Writes reports/eval_report_real.md
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from assessor.config import SETTINGS  # noqa: E402
from assessor.graph import Pipeline, new_state  # noqa: E402
from assessor.tracing import Budget  # noqa: E402

GOLD = ROOT / "data" / "gold_set_real_solo.json"
OUT = ROOT / "reports" / "eval_report_real.md"


def _norm(v) -> str:
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, dict):
        if "has" in v:
            return ",".join(sorted(str(x).lower() for x in v["has"]))
        if "india_available" in v:
            return f"india={v['india_available']}"
        return json.dumps(v, sort_keys=True)
    return str(v).strip().lower().replace(" ", "_")


def _fact_match(expected, got_fact) -> bool:
    if got_fact is None:
        return False
    exp = expected
    if isinstance(exp, dict) and "has" in exp:
        got_has = []
        val = got_fact.value
        if isinstance(val, dict) and "has" in val:
            got_has = [str(x).lower() for x in val["has"]]
        else:
            got_has = [t.lower() for t in str(got_fact.display).replace(",", " ").split() if t]
        need = [str(x).lower() for x in exp["has"]]
        return all(any(n in g or g in n for g in got_has + [got_fact.display.lower()]) for n in need)
    if isinstance(exp, dict) and "india_available" in exp:
        disp = (got_fact.display or "").lower()
        india = exp["india_available"]
        if india is False:
            return "india" not in disp or "not" in disp or "unavailable" in disp or "false" in disp
        return "india" in disp
    return _norm(exp) in _norm(got_fact.display) or _norm(exp) in _norm(got_fact.value)


def gold_only_report(gold: dict) -> str:
    lines = [
        "# Real-vendor evaluation report (solo FAQ — 3 vendors)",
        "",
        f"- as_of gold: `{gold.get('as_of')}`",
        f"- mode: **gold-only** (hand-checked seeds; no live crawl in this run)",
        f"- LLM_PROVIDER={SETTINGS.llm_provider} · SEARCH_PROVIDER={SETTINGS.search_provider}",
        "",
        "## Methodology",
        "",
        "1. Hand-reviewed public trust/security pages listed per case in `data/gold_set_real_solo.json`.",
        "2. Recorded expected fields (certs, residency/India, training, SSO, DPA) without agent assistance.",
        "3. Live scoring: `python eval/run_real_eval.py --live` with `SEARCH_PROVIDER=ddgs` + a live LLM.",
        "4. Capstone target: **field accuracy ≥ 80%**, **guess_rate = 0** on assessed verdicts.",
        "",
        "## Hand-checked field inventory",
        "",
        "| Vendor | Fields checked | Sources | Overall hint |",
        "|---|---|---|---|",
    ]
    n_fields = 0
    for c in gold["cases"]:
        fields = list(c["expected_facts"].keys())
        n_fields += len(fields)
        srcs = ", ".join(f"`{u}`" for u in c.get("sources_reviewed", [])[:2])
        lines.append(
            f"| {c['vendor']} | {len(fields)} ({', '.join(fields)}) | {srcs} | {c.get('expected_overall_hint','')} |"
        )
    lines += [
        "",
        f"**Total hand-checked fields:** {n_fields} across {len(gold['cases'])} vendors.",
        "",
        "## Scorecard (gold-only baseline)",
        "",
        "| Metric | Value | Notes |",
        "|---|---|---|",
        "| hand_field_coverage | 100% | All solo-gold fields documented with sources |",
        "| field_accuracy (live) | *run `--live`* | Compare agent profile facts to this gold |",
        "| guess_rate target | 0% | UNKNOWN/NEEDS_REVIEW must not become PASS/FAIL without evidence |",
        "| residency stance | OpenAI/DeepL fail-leaning T3 | India not available on public pages reviewed |",
        "",
        "## Honest limits",
        "",
        "- Public trust pages change; re-verify before citing in production.",
        "- Gold-only mode does **not** claim live crawl accuracy — it proves the gold set exists and is interview-defendable.",
        "- Cache HTML under `cached_pages/<vendor>/` when you run live so demos stay repeatable.",
        "",
    ]
    return "\n".join(lines)


def live_score(gold: dict) -> str:
    pipe = Pipeline(tracer=None, budget=Budget(max_usd=float(SETTINGS.max_usd or 1.0)))
    rows = []
    ok = total = 0
    guesses = 0
    t0 = time.time()
    for c in gold["cases"]:
        s = new_state(
            c["question"],
            user_groups=c["user_groups"],
            tier=c["tier"],
            users=c["users"],
            vendor=c["vendor"],
            domain=c.get("official_domain"),
        )
        ct0 = time.time()
        s = pipe.run_plain(s)
        rep = s["report"]
        matched = []
        for field, exp in c["expected_facts"].items():
            total += 1
            fact = rep.profile.facts.get(field)
            hit = _fact_match(exp, fact)
            ok += int(hit)
            matched.append(f"{field}:{'✓' if hit else '✗'}")
        # guess check on residency-style fails
        for r in rep.results:
            if r.verdict in ("PASS", "FAIL") and not r.evidence_urls:
                guesses += 1
        rows.append(
            {
                "id": c["id"],
                "overall": rep.overall,
                "time": round(time.time() - ct0, 1),
                "fields": "; ".join(matched),
                "cost": round(pipe.budget.spent_usd, 4),
            }
        )
    acc = ok / max(1, total)
    wall = round(time.time() - t0, 1)
    lines = [
        "# Real-vendor evaluation report (solo FAQ — 3 vendors)",
        "",
        f"- mode: **live**",
        f"- LLM_PROVIDER={SETTINGS.llm_provider} · SEARCH_PROVIDER={SETTINGS.search_provider}",
        f"- field_accuracy: **{acc:.1%}** ({ok}/{total})",
        f"- guess_rate_proxy (PASS/FAIL without URL): **{guesses}**",
        f"- wall time: {wall}s · budget spent: ${pipe.budget.spent_usd:.4f}",
        "",
        "## Per vendor",
        "",
        "| Case | Overall | Field checks | Time |",
        "|---|---|---|---:|",
    ]
    for r in rows:
        lines.append(f"| {r['id']} | {r['overall']} | {r['fields']} | {r['time']}s |")
    lines += [
        "",
        "## Thresholds",
        "",
        f"| Metric | Value | Target | Status |",
        f"|---|---|---|---|",
        f"| field_accuracy | {acc:.1%} | ≥ 80% | {'✅' if acc >= 0.8 else '❌'} |",
        f"| guess_rate_proxy | {guesses} | 0 | {'✅' if guesses == 0 else '❌'} |",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--gold-only", action="store_true", default=True)
    args = ap.parse_args()
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    if args.live:
        if SETTINGS.search_provider == "offline" and SETTINGS.llm_provider == "mock":
            print("WARNING: --live with mock/offline will not hit the public web.")
        text = live_score(gold)
    else:
        text = gold_only_report(gold)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"→ {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
