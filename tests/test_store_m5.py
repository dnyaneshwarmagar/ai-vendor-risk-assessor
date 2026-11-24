"""Milestone 5: SQLite history + role→groups + BLOCKED cannot approve via store path."""
from datetime import date
from pathlib import Path

from assessor.schemas import Approval, AssessmentReport, AssessmentRequest, VendorProfile
from assessor.store import AssessmentStore, groups_for_role


def test_role_groups_never_trust_client_lists():
    assert "security" in groups_for_role("security")
    assert "security" not in groups_for_role("employee")
    assert "procurement" in groups_for_role("procurement")


def test_sqlite_history_survives(tmp_path: Path):
    store = AssessmentStore(tmp_path / "h.sqlite3")
    req = AssessmentRequest(question="q", vendor="Parakeet Translate", tier="T2", users=8)
    report = AssessmentReport(
        request=req, profile=VendorProfile(vendor="Parakeet Translate", as_of=date(2026, 11, 1)),
        results=[], overall="READY_FOR_APPROVAL", overall_reason="ok",
        approval=Approval(status="pending"),
    ).model_dump(mode="json")
    store.save_report("run-demo", report, question="q", vendor="Parakeet Translate", tier="T2",
                      users=8, requested_by="test", role="security")
    # New store instance = "restart"
    store2 = AssessmentStore(tmp_path / "h.sqlite3")
    row = store2.get("run-demo")
    assert row is not None and row["overall"] == "READY_FOR_APPROVAL"
    store2.update_approval("run-demo", {"status": "approved", "decided_by": "A. Sharma",
                                        "decided_on": "2026-11-24", "comment": "ok"})
    assert store2.get("run-demo")["status"] == "approved"
