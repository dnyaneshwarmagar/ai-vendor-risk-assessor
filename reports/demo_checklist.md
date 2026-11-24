# Demo checklist (offline + live)

## Offline (no key) — M0 / M6

1. `python scripts/check_setup.py` → mock/offline, policy chunks indexed
2. `python run_assessor.py` → LedgerLens T3 **BLOCKED** (DP-3.1); quarantine + UK reject in report
3. Parakeet T2 → **READY_FOR_APPROVAL**; Parakeet T3 → **CONDITIONAL**
4. QuillDesk T3 → **BLOCKED** (claimed SOC 2 + training)
5. Policy: “Who approves a tool that handles customer data?” → **AI-5.1** / DPO
6. `python -m pytest tests -q` → **90 passed**
7. `python eval/run_eval.py --strict` → all thresholds green
8. Show `runs/.../trace.jsonl` from a FAIL verdict back to the privacy-policy URL

## Product — M5

9. `uvicorn app.api:app --port 8000` → POST /assess, GET /history, POST /approve
10. `streamlit run app/ui.py` → progress line, trace expander, Approve (blocked if overall BLOCKED)

## Live — M2 / M6

11. `pip install ddgs trafilatura httpx` (also in `requirements.txt`)
12. `python eval/run_real_eval.py --live-pages` → field accuracy **≥ 80%** on Notion / OpenAI / DeepL  
    (latest: see `reports/eval_report_real.md`)
13. Optional full agent crawl: set `SEARCH_PROVIDER=ddgs` + live `LLM_PROVIDER`, then  
    `python eval/run_real_eval.py --live --limit 1`

## Milestone map

See [`docs/MILESTONES.md`](../docs/MILESTONES.md).
