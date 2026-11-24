# Resume bullets (evidence-backed)

Use these only as written — each claim maps to a file in this repo.

1. Built a **human-in-the-loop vendor risk assessor** (hybrid policy RAG + deep web research + deterministic matcher) so the LLM extracts evidence but **never issues the verdict** (`assessor/matcher.py`, `assessor/services/assessment_service.py`).

2. Enforced **defense-in-depth** (identity gate, prompt-injection quarantine, ACL in retrieval) with **15/15 red-team** catches and asserted catch points (`tests/test_red_team.py`, `reports/ablation_report.md`).

3. Drove **eval-first delivery**: offline CI with **100%** fictional verdict/safety accuracy, **0% guess rate**, **30/30 routing**, **90** unit tests, plus **15/15 (100%)** hand-verified fields on **3** real vendors (`reports/eval_report.md`, `reports/eval_report_real.md`).

4. Shipped **FastAPI + Streamlit** with an approval gate that **blocks approval when overall is BLOCKED**, and auditable `trace.jsonl` from FAIL → source URL (`app/api.py`, `app/ui.py`, `docs/samples/`).

## One-line project blurb

AI Vendor Risk Assessor — policy RAG + vendor deep-search agent that drafts security reviews for humans; matcher-enforced verdicts, zero-guess eval, red-teamed injection/ACL controls.
