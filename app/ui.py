"""
app/ui.py — Streamlit front end for reviewers (Milestone 5).

Run:   streamlit run app/ui.py

Shows node-by-node progress, trace viewer, history, and Approve/Reject that persists via SQLite.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from assessor.config import SETTINGS  # noqa: E402
from assessor.container import get_container  # noqa: E402
from assessor.graph import new_state  # noqa: E402
from assessor.store import groups_for_role  # noqa: E402

st.set_page_config(page_title="Vendor Risk Assessor — Nimbu Mart", layout="wide")
st.title("AI Vendor Risk Assessor")
st.caption(
    f"Nimbu Mart · LLM: {SETTINGS.llm_provider} · search: {SETTINGS.search_provider} · "
    "an input to the review, not an approval · DI: AppContainer"
)

_APP = get_container()
STORE = _APP.store

with st.sidebar:
    st.header("Who is asking")
    role = st.selectbox("Role (server-derived ACL)", ["employee", "security", "procurement", "admin"], index=1)
    groups = groups_for_role(role)
    st.caption(f"Groups: {', '.join(groups)}")
    tier = st.selectbox("Highest data tier", ["T1", "T2", "T3"], index=2)
    users = st.number_input("Number of users", 1, 10000, 35)
    vendor = st.text_input("Vendor (optional, otherwise detected)", "")
    domain = st.text_input("Official domain (optional)", "")
    st.divider()
    st.subheader("Recent assessments")
    for row in STORE.list_recent(8):
        st.caption(f"{row['run_id'][:22]}… · {row['vendor']} · {row['overall']} · {row['status']}")

q = st.text_input("Question", "Can our support team use LedgerLens AI to summarise customer tickets?")
col_run, col_hist = st.columns([1, 1])
run_clicked = col_run.button("Run assessment", type="primary")

if run_clicked:
    SETTINGS.verbose = False
    tracer = _APP.tracer("ui")
    progress_box = st.empty()
    events: list[dict] = []

    def on_progress(stage: str, data: dict):
        events.append({"stage": stage, **data})
        progress_box.info(" → ".join(e["stage"] for e in events[-8:]))

    pipe = _APP.pipeline(tracer=tracer, budget=_APP.budget(), on_progress=on_progress)
    with st.spinner("Routing → researching → matching…"):
        s = pipe.run(new_state(
            q, user_groups=groups, tier=tier, users=int(users),
            vendor=vendor or None, domain=domain or None, requested_by=f"ui:{role}",
        ), thread_id=tracer.run_id)
    tracer.close()
    st.session_state["last_state"] = s
    st.session_state["last_events"] = list(tracer.events) or events
    st.session_state["last_run_id"] = tracer.run_id
    rep = s.get("report")
    if rep is not None:
        STORE.save_report(
            tracer.run_id, rep.model_dump(mode="json"), question=q, vendor=rep.request.vendor,
            tier=tier, users=int(users), requested_by=f"ui:{role}", role=role,
        )

s = st.session_state.get("last_state")
if s:
    rep = s.get("report")
    if rep is None:
        st.subheader(f"Route: {s['route']}")
        st.markdown(s["answer"])
    else:
        colour = {"BLOCKED": "red", "CONDITIONAL": "orange", "READY_FOR_APPROVAL": "green"}[rep.overall]
        st.markdown(f"### :{colour}[{rep.overall}] — {rep.overall_reason}")
        rows = [{
            "Requirement": r.title, "Clause": r.clause, "Verdict": r.verdict, "Severity": r.severity,
            "Reason": r.reason, "Evidence": ", ".join(r.evidence_urls[:2]), "As of": str(r.evidence_as_of or ""),
        } for r in rep.results]
        st.dataframe(rows, use_container_width=True, hide_index=True)

        if rep.open_questions:
            st.subheader("Questions for the vendor")
            for i, oq in enumerate(rep.open_questions, 1):
                st.markdown(f"**{i}. {oq['id']}** — {oq['question']}")

        left, right = st.columns(2)
        with left:
            with st.expander("Full review file (Markdown)", expanded=False):
                st.markdown(s["answer"])
        with right:
            with st.expander("Trace (click a stage)", expanded=True):
                for e in st.session_state.get("last_events", []):
                    st.write(f"**{e.get('stage')}**", {k: v for k, v in e.items() if k != "stage"})

        st.divider()
        st.subheader("Human decision")
        st.caption(f"Approvers for {tier}: {', '.join(rep.approval.approver_roles)}")
        if rep.overall == "BLOCKED":
            st.warning("BLOCKED assessments cannot be approved. Resolve blockers or change the data tier.")
        approver = st.text_input("Your name", "A. Sharma")
        comment = st.text_input("Comment", "")
        c1, c2, c3 = st.columns(3)
        run_id = st.session_state.get("last_run_id", rep.run_id)
        if c1.button("Approve", disabled=rep.overall == "BLOCKED"):
            from datetime import date
            approval = {
                "status": "approved", "decided_by": approver, "decided_on": date.today().isoformat(),
                "comment": comment, "approver_roles": rep.approval.approver_roles,
            }
            STORE.update_approval(run_id, approval)
            st.success(f"Approved by {approver}. Decision saved to SQLite (survives restart).")
        if c2.button("Reject"):
            from datetime import date
            approval = {
                "status": "rejected", "decided_by": approver, "decided_on": date.today().isoformat(),
                "comment": comment, "approver_roles": rep.approval.approver_roles,
            }
            STORE.update_approval(run_id, approval)
            st.error(f"Rejected by {approver}. Decision saved.")
        if c3.button("Leave pending"):
            st.info("Left pending for another approver.")

        st.caption(
            f"Run `{run_id}` · {rep.llm_calls} LLM calls · est. ${rep.cost_usd:.4f} · "
            f"{rep.duration_s}s · approval: {STORE.get(run_id)['status'] if STORE.get(run_id) else rep.approval.status}"
        )
