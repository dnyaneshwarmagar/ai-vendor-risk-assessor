# Vendor risk assessment — LedgerLens AI

**Question:** Can our support team use LedgerLens AI to summarise customer tickets?  
**Data tier:** T3 (Customer data) · **Users:** 35 · **Requested by:** cli  
**Evidence as of:** 2026-11-01 · **Run:** `20261124-200202-assess` · **LLM calls:** 13 · **Est. cost:** $0.0000 · **Time:** 1.8s

## Outcome: BLOCKED for this data tier

Blocking requirement(s) failed: DP-3.1 (Customer data stored in India).

> This is an input to the review, not an approval. Approvers for T3: Head of Information Security, DPO. Approval status: **pending**.

## 1. Vendor identity
- Vendor: **LedgerLens AI** · official domain: `ledgerlens.example`
- Legal entity: LedgerLens AI Inc (United States)
- Pages read: 12 · rejected as a different company: 1 · quarantined for prompt injection: 1

## 2. Requirements

| Requirement | Clause | Verdict | Severity | Reason | Evidence | As of |
|---|---|---|---|---|---|---|
| Independent security assurance (SOC 2 Type II or ISO 27001) | SEC-4.2 | ✅ PASS | blocker | Current, independently issued: SOC 2 Type II (2026-01-20). | [trust.ledgerlens.example/](https://trust.ledgerlens.example/) (documented) | 2026-09-01 |
| Security assurance for internal-data tools (Type I or questionnaire acceptable) | SEC-4.2 | — n/a | major | Applies to tiers T2; this request is T3, 35 users. | [trust.ledgerlens.example/](https://trust.ledgerlens.example/) (documented) | 2026-09-01 |
| Customer data stored in India | DP-3.1 | ❌ FAIL | blocker | India is only planned, which does not count. Available today: European Union, United States. | [ledgerlens.example/legal/privacy](https://ledgerlens.example/legal/privacy) (documented) | 2026-03-15 |
| Storage region recorded (internal data) | DP-3.2 | — n/a | minor | Applies to tiers T2; this request is T3, 35 users. | [ledgerlens.example/legal/privacy](https://ledgerlens.example/legal/privacy) (documented) | 2026-03-15 |
| No training on Nimbu Mart data | AI-2.1 | ⚠️ NEEDS REVIEW | blocker | No training on Business/Enterprise plans; Free/Pro content used unless opted out (on by default). Acceptable only with the conditions in AI-2.1; record how they are met. | [ledgerlens.example/legal/ai-data-use](https://ledgerlens.example/legal/ai-data-use) (documented) | 2026-05-05 |
| Sub-processors disclosed; model providers identified | AI-3.4 | ⚠️ NEEDS REVIEW | major | 4 sub-processors disclosed. Model provider(s) present: Orbital Models Inc (United States) — confirm AI-2.1 applies to them too. | [ledgerlens.example/legal/subprocessors](https://ledgerlens.example/legal/subprocessors) (documented) | 2026-08-20 |
| Deletion within 30 days of contract end or request | DP-5.4 | ✅ PASS | major | Default retention 30 days (limit 30). Deleted 30 days after subscription ends; deletion on request within 30 days. | [ledgerlens.example/legal/privacy](https://ledgerlens.example/legal/privacy) (documented) | 2026-03-15 |
| Single sign-on (SAML / OIDC) | SEC-7.1 | ✅ PASS | major | SAML 2.0 / OIDC SSO on Business and Enterprise plans; SCIM on Enterprise | [trust.ledgerlens.example/](https://trust.ledgerlens.example/) (documented) | 2026-09-01 |
| No major incident in 24 months without a published post-mortem | SEC-9.3 | ⚠️ NEEDS REVIEW | blocker | Major incident(s) with a published post-mortem: 2025-04-14: API tokens for 212 workspaces written to an over-permissioned internal log store; tokens rotated within 6 hours; no customer content accessed. Information Security must read the post-mortem before approval. | [ledgerlens.example/security/incident-2025-04](https://ledgerlens.example/security/incident-2025-04)<br>[securitydaily.example/2025/04/ledgerlens-token-e](https://securitydaily.example/2025/04/ledgerlens-token-exposure) (documented) | 2025-05-02 |
| Data Processing Agreement available | DP-2.2 | ✅ PASS | blocker | DPA published at ledgerlens.example/legal/dpa | [ledgerlens.example/legal/privacy](https://ledgerlens.example/legal/privacy) (documented) | 2026-03-15 |
| On the Approved Vendor List for this data tier | PROC-1.1 | ⚠️ NEEDS REVIEW | major | A review is already in progress (Assessment requested 2026-10-28.). Do not start a second one; attach this assessment to it. | policy library | — |

## 3. What we established about the vendor

- **legal_entity** — LedgerLens AI Inc (United States)  
  confidence 0.92 · documented · as of 2026-09-01 · sources: <https://trust.ledgerlens.example/>
- **security_certifications** — SOC 2 Type II report dated 2026-01-20 (available under NDA via trust portal); ISO 27001 in progress (audit expected 2027)  
  confidence 0.85 · documented · as of 2026-09-01 · sources: <https://trust.ledgerlens.example/>
  - conflicting value seen: SOC 2 Type I examination in progress (page from July 2024) [official, 2024-07-01, score 0.094] — https://ledgerlens.example/security-old
- **data_regions** — United States (default) and European Union (Business/Enterprise); India planned for 2027  
  confidence 0.61 · documented · as of 2026-03-15 · sources: <https://ledgerlens.example/legal/privacy>
  - conflicting value seen: US, EU and (from October 2026) Singapore for Enterprise; India still planned for 2027 [news, 2026-10-02, score 0.529] — https://technews.example/2026/10/ledgerlens-singapore-region
- **subprocessors** — 4 sub-processors disclosed: CloudStack (hosting), Orbital Models (LLM inference, US), MailRelay (email), Clearpath Analytics  
  confidence 0.72 · documented · as of 2026-08-20 · sources: <https://ledgerlens.example/legal/subprocessors>
- **trains_on_customer_data** — No training on Business/Enterprise plans; Free/Pro content used unless opted out (on by default)  
  confidence 0.47 · documented · as of 2026-05-05 · sources: <https://ledgerlens.example/legal/ai-data-use>
- **data_retention** — Deleted 30 days after subscription ends; deletion on request within 30 days  
  confidence 0.71 · documented · as of 2026-03-15 · sources: <https://ledgerlens.example/legal/privacy>
- **sso_saml** — SAML 2.0 / OIDC SSO on Business and Enterprise plans; SCIM on Enterprise  
  confidence 0.88 · documented · as of 2026-09-01 · sources: <https://trust.ledgerlens.example/>
  - conflicting value seen: Reviewers report SSO only on Enterprise (review site) [review_site, 2026-10-15, score 0.313] — https://reviewhub.example/software/ledgerlens-ai
  - conflicting value seen: SSO 'on our roadmap' (July 2024) [official, 2024-07-01, score 0.159] — https://ledgerlens.example/security-old
- **security_incidents** — 2025-04-14 major: API tokens for 212 workspaces written to an over-permissioned internal  
  confidence 0.56 · documented · as of 2025-05-02 · sources: <https://ledgerlens.example/security/incident-2025-04>, <https://securitydaily.example/2025/04/ledgerlens-token-exposure>
- **dpa_available** — DPA published at ledgerlens.example/legal/dpa  
  confidence 0.71 · documented · as of 2026-03-15 · sources: <https://ledgerlens.example/legal/privacy>

## 4. Security and validation notes
- 🛑 Quarantined (prompt injection in page): <https://aicomplianceguru.example/reviews/ledgerlens-ai-compliance-review>
- 🚫 Rejected (about a different company): <https://ledgerlens-uk.example/about-us>
- ⤵️ Dropped: https://devforum.example/t/ledgerlens-breach-again/99341 — security_incidents: rumour/forum, not evidence (SEC-9.4)
- ℹ️ 12 pages found; 1 rejected (identity); 1 quarantined (injection); 1 claims dropped; 0 duplicate pages down-weighted.

## 5. Open questions for the vendor

1. **Q-AI-2.1** (settles AI-2.1): Do you use customer content (prompts, files, outputs) to train or improve models? If this is configurable, on which
plan is it disabled by contract, and how is the setting enforced?  
   _Why:_ No training on Business/Enterprise plans; Free/Pro content used unless opted out (on by default). Acceptable only with the conditions in AI-2.1; record how they are met.
2. **Q-AI-3.4** (settles AI-3.4): Which third-party model providers receive our content? What do your agreements with them say about training and
retention?  
   _Why:_ 4 sub-processors disclosed. Model provider(s) present: Orbital Models Inc (United States) — confirm AI-2.1 applies to them too.
3. **Q-SEC-9.3** (settles SEC-9.3): Have you had a security incident affecting customer data in the last 24 months? If so, please share the post-incident
report.  
   _Why:_ Major incident(s) with a published post-mortem: 2025-04-14: API tokens for 212 workspaces written to an over-permissioned internal log store; tokens rotated within 6 hours; no customer content accessed. Information Security must read the post-mortem before approval.

---
Generated by the Nimbu Mart vendor risk assistant. Verdicts are computed by rules; a person decides.