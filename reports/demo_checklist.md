# Demo checklist (offline + live)

## Offline (no key)

1. `python scripts/check_setup.py` → mock/offline, policy chunks indexed
2. `python run_assessor.py` → LedgerLens T3 **BLOCKED** (DP-3.1); quarantine + UK reject in report
3. Parakeet T2 → **READY_FOR_APPROVAL**; Parakeet T3 → **CONDITIONAL**
4. QuillDesk T3 → **BLOCKED** (claimed SOC 2 + training)
5. Policy: “Who approves a tool that handles customer data?” → **AI-5.1** / DPO
6. `python -m pytest tests -q` → 87 passed
7. `python eval/run_eval.py --strict` → all thresholds green
8. Show `runs/.../trace.jsonl` from a FAIL verdict back to the privacy-policy URL

## Product

9. `uvicorn app.api:app --port 8000` → POST /assess, GET /history, POST /approve
10. `streamlit run app/ui.py` → progress line, trace expander, Approve (blocked if overall BLOCKED)

## Live (optional)

11. Set `LLM_PROVIDER=gemini` + `SEARCH_PROVIDER=ddgs` in `.env`
12. Assess one vendor from `data/gold_set_real.json` under `$0.30` budget
13. Compare facts to the hand-checked gold (do not auto-grade with the agent’s own output)
