"""eval/run_routing_eval.py — score the router on data/routing_eval.json (Milestone 3). Target ≥90%."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from assessor.router import decide  # noqa: E402

GOLD = ROOT / "data" / "routing_eval.json"


def main() -> int:
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    vendors = gold["known_vendors"]
    ok = 0
    rows = []
    for case in gold["cases"]:
        d = decide(case["question"], vendors)
        hit = d.route == case["expected"]
        ok += hit
        rows.append((case["id"], case["expected"], d.route, "✓" if hit else "✗", d.reason[:80]))
    n = len(gold["cases"])
    acc = ok / max(1, n)
    print(f"Routing accuracy: {ok}/{n} = {acc:.1%}  (threshold ≥90%)")
    print(f"{'id':<5} {'expected':<12} {'got':<12} {'':<2} reason")
    for r in rows:
        print(f"{r[0]:<5} {r[1]:<12} {r[2]:<12} {r[3]:<2} {r[4]}")
    out = ROOT / "reports" / "routing_eval.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Routing eval\n\nAccuracy: **{acc:.1%}** ({ok}/{n})\n",
             "| id | expected | got | ok | reason |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    return 0 if acc >= 0.9 else 1


if __name__ == "__main__":
    raise SystemExit(main())
