# 12-minute interview demo (+ 2–3 min video cut)

Record a Loom/YouTube following this script. Link the finished video from the README (`docs/demo-video.url`).

## Full 12-minute arc

| Min | Action | Say |
|---:|---|---|
| 0–1 | `python run_assessor.py` | LedgerLens T3 is **BLOCKED** on DP-3.1 — India residency. Matcher decided, not the LLM. |
| 1–3 | Open `runs/.../report.md` + `trace.jsonl` | UK look-alike rejected; injection page quarantined; forum rumour dropped. |
| 3–4 | `--groups public,employees` | AVL hidden — ACL lives in retrieval. |
| 4–6 | Parakeet T3 then T2 | CONDITIONAL vs READY_FOR_APPROVAL; refuse Approve on BLOCKED in UI. |
| 6–9 | Streamlit + Notion/OpenAI gold | Live or cached real vendor vs `gold_set_real_solo.json`. |
| 9–10 | Point at quarantined URL | Injection never reaches the verdict. |
| 10–12 | `reports/eval_report.md` + ablations | 100% fictional verdict/safety, guess_rate 0, 15/15 red team, 15/15 real gold fields. Two honest failures (below). |

## 2–3 minute video cut (same story, tighter)

1. Hook (15s): “I automated vendor security review — and kept the LLM from deciding.”
2. BLOCKED + trace (45s)
3. ACL + Parakeet contrast (30s)
4. UI human gate (20s)
5. Scorecard numbers (30s)
6. Honest failures (20s)

## Honest failures (always say these)

1. Small local models (`qwen2.5:3b`) often fail structured `ResearchPlan` JSON — we fall back to a deterministic planner rather than inventing queries.
2. Ragas Faithfulness on short packed contexts can score low even when matcher verdicts are correct — we do **not** use Ragas as a release gate; strict fictional eval + red team do.

## Commands cheat-sheet

```bash
python run_assessor.py
python run_assessor.py "Can we use Parakeet Translate for support chats?" --tier T3 --users 60
python run_assessor.py "Can the product team use Parakeet Translate for roadmap docs?" --tier T2 --users 8
python run_assessor.py --groups public,employees
uvicorn app.api:app --port 8000
streamlit run app/ui.py
python -m pytest tests -q
python eval/run_eval.py --strict
```
