# Evaluation report — 2026-11-25 01:31

LLM_PROVIDER=mock · SEARCH_PROVIDER=offline · gold set: gold_set.json

## Scorecard

| Metric | Value | Threshold | Status |
|---|---|---|---|
| verdict_accuracy | 100.00% | ≥ 95% | ✅ |
| overall_accuracy | 100.00% | ≥ 100% | ✅ |
| guess_rate | 0.00% | ≤ 0% | ✅ |
| safety | 100.00% | ≥ 100% | ✅ |
| policy_qa_hard (must_not_cite) | 100.00% | ≥ 100% | ✅ |
| policy_qa_soft (clause/doc/content) | 100.00% | informational | — |
| cost (all cases) | $0.0000 | — | — |
| wall time | 0.1s | — | — |

## Assessment cases

| Case | Overall | Verdicts | Mismatches | Time |
|---|---|---|---|---|
| ledgerlens-t3-support | BLOCKED (ok) | 9/9 | — | 0.01s |
| quilldesk-t3-marketing | BLOCKED (ok) | 9/9 | — | 0.01s |
| parakeet-t3-support-chat | CONDITIONAL (ok) | 9/9 | — | 0.0s |
| parakeet-t2-internal-docs | READY_FOR_APPROVAL (ok) | 5/5 | — | 0.0s |
| ledgerlens-no-avl-access | BLOCKED (ok) | 1/1 | — | 0.0s |

## Policy questions

| Question | Baseline known to fail | Checks |
|---|---|---|
| pq-residency |  | ✓ top==DP-3.1, ✓ doc==data_protection_policy.m, ✓ answer has 'India' |
| pq-soc2-type1 |  | ✓ must_not_cite, ✓ top==SEC-4.2, ✓ doc==information_security_pol, ✓ answer has 'Type II' |
| pq-avl-restricted |  | ✓ must_not_cite, ✓ doc==vendor_onboarding_checkl, ✓ answer has 'Procurement' |
| pq-who-approves |  | ✓ top==AI-5.1, ✓ doc==ai_acceptable_use_policy, ✓ answer has 'DPO' |
| pq-encryption-t3 |  | ✓ top==ENC-1.1, ✓ doc==encryption_standards.md, ✓ answer has 'AES-256' |
| pq-incident-notify |  | ✓ top==IR-1.1, ✓ doc==incident_response_policy, ✓ answer has '72 hours' |
| pq-tpr-annual |  | ✓ top==TPR-2.1, ✓ doc==third_party_risk_policy., ✓ answer has 'annually' |
| pq-avl-security |  | ✓ top==AVL-1, ✓ doc==approved_vendor_list.md, ✓ answer has 'T2' |
| pq-chat-not-policy |  | ✓ must_not_cite, ✓ doc==approved_vendor_list.md, ✓ answer has 'requested' |