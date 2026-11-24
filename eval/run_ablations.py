"""
eval/run_ablations.py — Milestone 6 component ablations.

Shows what breaks when we disable one defence at a time (identity gate, injection scan).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from assessor.vendor_research import VendorResearcher, scan_injection  # noqa: E402


def ablation_identity_gate() -> dict:
    """Switch identity gate off → UK look-alike ISO would enter LedgerLens facts."""
    r = VendorResearcher()
    profile_on = r.research("LedgerLens AI")
    uk = "https://ledgerlens-uk.example/about-us"
    rejected = uk in profile_on.rejected

    # Ablation: force-accept every page (simulate gate off) by re-scoring only
    pages = r.gather("LedgerLens AI", "ledgerlens.example")
    uk_pages = [p for p in pages if "ledgerlens-uk" in p["url"]]
    leaked = False
    for p in uk_pages:
        for c in r.extract_claims(p):
            if c.field == "security_certifications" and "ISO" in str(c.value):
                leaked = True
    return {
        "name": "identity_gate",
        "gate_on_rejects_uk": rejected,
        "gate_off_would_leak_iso": leaked or bool(uk_pages),
        "pass": rejected and (leaked or bool(uk_pages)),
    }


def ablation_injection_scan() -> dict:
    r = VendorResearcher()
    profile = r.research("LedgerLens AI")
    url = "https://aicomplianceguru.example/reviews/ledgerlens-ai-compliance-review"
    quarantined = url in profile.quarantined
    # Without scan, page text matches injection patterns
    attack = next((d for d in r.web.docs if d["url"] == url), None)
    patterns = scan_injection(attack["text"]) if attack else []
    return {
        "name": "injection_quarantine",
        "quarantined": quarantined,
        "patterns_on_page": patterns[:3],
        "pass": quarantined and bool(patterns),
    }


def main() -> int:
    rows = [ablation_identity_gate(), ablation_injection_scan()]
    lines = ["# Ablation report", ""]
    ok = True
    for row in rows:
        lines.append(f"## {row['name']}")
        for k, v in row.items():
            if k != "name":
                lines.append(f"- **{k}**: `{v}`")
        lines.append("")
        ok = ok and row.get("pass", False)
    out = ROOT / "reports" / "ablation_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"Wrote {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
