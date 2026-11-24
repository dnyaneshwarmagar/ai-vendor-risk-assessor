"""
app/api.py — the assessor as a web service (FastAPI).

COURSE MAP  Production RAG Module 4 / 13. Milestone 5: in-process job queue, SQLite history,
server-derived user_groups, LangGraph-ready run ids.

Run:   uvicorn app.api:app --reload --port 8000
"""

from __future__ import annotations

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from assessor.config import RUNS_DIR, SETTINGS
from assessor.container import get_container
from assessor.graph import new_state
from assessor.store import groups_for_role

app = FastAPI(
    title="Nimbu Mart Vendor Risk Assessor",
    version="0.6.0",
    description="AI Vendor Risk Assessor. Assessments are inputs to a human decision. DI via AppContainer.",
)

_APP = get_container()
STORE = _APP.store
_EXEC = ThreadPoolExecutor(max_workers=2)


class AskBody(BaseModel):
    question: str
    role: str = "employee"  # server maps role → groups; client groups ignored


class AssessBody(BaseModel):
    question: str
    vendor: str
    official_domain: Optional[str] = None
    tier: str = "T3"
    users: int = 1
    role: str = "security"
    requested_by: str = "api"
    async_queue: bool = False


class ApproveBody(BaseModel):
    decision: str  # approve | reject
    approver: str
    comment: str = ""


def _role(x_role: Optional[str], body_role: str) -> str:
    # Prefer gateway header; never trust client-supplied group lists
    return (x_role or body_role or "employee").strip().lower()


@app.get("/health")
def health():
    return {"ok": True, "llm_provider": SETTINGS.llm_provider, "search_provider": SETTINGS.search_provider,
            "history_db": str(STORE.path), "architecture": "ports-adapters-di"}


@app.post("/ask")
def ask(body: AskBody, x_role: Optional[str] = Header(default=None)):
    role = _role(x_role, body.role)
    groups = groups_for_role(role)
    pipe = _APP.pipeline()
    s = pipe.run_plain(new_state(body.question, user_groups=groups, requested_by="api"))
    if s["route"] == "assessment":
        raise HTTPException(400, "This question needs a full assessment: call POST /assess.")
    return {"route": s["route"], "answer": s["answer"], "role": role, "user_groups": groups,
            "citations": [c.model_dump() for c in (s["policy_answer"].citations if s.get("policy_answer") else [])]}


def _run_assess(body: AssessBody, role: str, job_id: str | None = None) -> dict:
    groups = groups_for_role(role)
    tracer = _APP.tracer("api")
    progress: list[dict] = []

    def on_progress(stage: str, data: dict):
        progress.append({"stage": stage, **{k: v for k, v in data.items() if k != "text"}})

    pipe = _APP.pipeline(tracer=tracer, budget=_APP.budget(), on_progress=on_progress)
    s = new_state(body.question, user_groups=groups, tier=body.tier, users=body.users, vendor=body.vendor,
                  domain=body.official_domain, requested_by=body.requested_by)
    try:
        s = pipe.run(s, thread_id=tracer.run_id)
    finally:
        tracer.close()

    if job_id:
        STORE.save_job(job_id, "done", run_id=tracer.run_id)

    if s.get("report") is None:
        return {"route": s["route"], "answer": s["answer"], "run_id": tracer.run_id, "progress": progress,
                "role": role, "user_groups": groups}

    report = s["report"].model_dump(mode="json")
    STORE.save_report(tracer.run_id, report, question=body.question, vendor=body.vendor, tier=body.tier,
                      users=body.users, requested_by=body.requested_by, role=role)
    return {"run_id": tracer.run_id, "report": report, "progress": progress, "role": role, "user_groups": groups}


@app.post("/assess")
def assess(body: AssessBody, x_role: Optional[str] = Header(default=None)):
    role = _role(x_role, body.role)
    if body.async_queue:
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        STORE.save_job(job_id, "queued")

        def work():
            try:
                STORE.save_job(job_id, "running")
                _run_assess(body, role, job_id=job_id)
            except Exception as exc:  # noqa: BLE001
                STORE.save_job(job_id, "error", error=str(exc)[:500])

        _EXEC.submit(work)
        return {"job_id": job_id, "status": "queued", "poll": f"/jobs/{job_id}"}
    return _run_assess(body, role)


@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    row = STORE.get_job(job_id)
    if not row:
        raise HTTPException(404, "job not found")
    out = dict(row)
    if row["run_id"] and row["status"] == "done":
        hist = STORE.get(row["run_id"])
        if hist:
            out["report"] = json.loads(hist["report_json"])
    return out


@app.get("/history")
def history(limit: int = 20):
    return STORE.list_recent(limit)


def _run_dir(run_id: str) -> Path:
    p = RUNS_DIR / run_id
    if not p.exists() or ".." in run_id:
        raise HTTPException(404, "run not found")
    return p


@app.post("/approve/{run_id}")
def approve(run_id: str, body: ApproveBody):
    # Prefer SQLite history; fall back to runs/ folder
    hist = STORE.get(run_id)
    if hist:
        rep = json.loads(hist["report_json"])
    else:
        d = _run_dir(run_id)
        rep = json.loads((d / "report.json").read_text(encoding="utf-8"))

    if body.decision == "approve" and rep["overall"] == "BLOCKED":
        raise HTTPException(409, "A BLOCKED assessment cannot be approved. Resolve the blocking requirement or change the data tier.")

    approval = {"status": "approved" if body.decision == "approve" else "rejected",
                "decided_by": body.approver, "decided_on": date.today().isoformat(), "comment": body.comment,
                "approver_roles": (rep.get("approval") or {}).get("approver_roles", [])}
    rep["approval"] = approval
    STORE.update_approval(run_id, approval)

    # Mirror onto filesystem report if present
    try:
        d = _run_dir(run_id)
        (d / "report.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
        with open(d / "trace.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"stage": "approval", **approval}) + "\n")
    except HTTPException:
        pass
    return approval


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    hist = STORE.get(run_id)
    if hist:
        return {"run_id": run_id, "report": json.loads(hist["report_json"]), "from": "sqlite"}
    d = _run_dir(run_id)
    return {"run_id": run_id, "report": json.loads((d / "report.json").read_text(encoding="utf-8")), "from": "runs"}


@app.get("/runs/{run_id}/report.md", response_class=PlainTextResponse)
def report_md(run_id: str):
    return (_run_dir(run_id) / "report.md").read_text(encoding="utf-8")
