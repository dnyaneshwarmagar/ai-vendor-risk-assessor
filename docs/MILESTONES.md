# Capstone milestones (M0–M6)

Status against the brief’s **Done when** criteria.

| ID | Milestone | Status | Evidence |
|---|---|---|---|
| **M0** | Run starter kit | **Done** | `pytest` 90; `eval/run_eval.py --strict` 100% verdicts; LedgerLens BLOCKED / Parakeet CONDITIONAL explainable |
| **M1** | Policy library | **Done** | Hybrid BM25 + TF-IDF (RRF) + intent/cross-encoder rerank; grounded answers; ACL/archived/untrusted tests; `pq-who-approves` fixed |
| **M2** | Vendor research (live web) | **Done** | Planner/parallel/identity/quarantine/memory offline-green; live-pages field accuracy **93.3% (14/15)** ≥80% on Notion/OpenAI/DeepL (`reports/eval_report_real.md`); `ddgs` + `trafilatura` installed |
| **M3** | Router + graders | **Done** | Routing **30/30**; hallucination grader abstain path |
| **M4** | Security / red team | **Done** | **15/15** attacks + catch points; safety 100%; guess_rate 0; ablations |
| **M5** | Product (graph/API/UI/gate) | **Done** | LangGraph + interrupt; FastAPI queue/history; Streamlit; BLOCKED not approvable; SQLite survives restart |
| **M6** | Eval, write-up, demo | **Done** (demo video optional) | Fictional + real reports; CI green; offline demo script; live checklist documented |

## Stretch (optional, not required for solo FAQ)

- MCP tool for the assessor
- Continuous monitoring / re-review cron
- Redis/Postgres instead of SQLite
- Full 10×8 real-vendor matrix (solo path uses **3** vendors)

## Commands

```bash
python -m pytest tests -q
python eval/run_eval.py --strict
python eval/run_routing_eval.py
python eval/run_ablations.py
python eval/run_real_eval.py --gold-only
python eval/run_real_eval.py --live-pages   # fetch gold URLs live, score field keywords
# optional full agent on the public web:
# SEARCH_PROVIDER=ddgs LLM_PROVIDER=ollama python eval/run_real_eval.py --live --limit 1
```
