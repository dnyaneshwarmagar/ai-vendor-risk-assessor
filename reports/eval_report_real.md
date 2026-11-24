# Real-vendor evaluation report (solo FAQ — 3 vendors)

- mode: **live-pages** (direct fetch of gold `sources_reviewed`)
- verified_on: 2026-11-25
- field_accuracy: **93.3%** (14/15)
- wall time: 21.0s

## Per vendor

| Case | Pages fetched | Field checks |
|---|---:|---|
| real-notion | 2 | security_certifications:✓; data_regions:✓; trains_on_customer_data:✓; sso_saml:✓; dpa_available:✓ |
| real-openai | 2 | security_certifications:✓; data_regions:✓; trains_on_customer_data:✓; sso_saml:✓; dpa_available:✓ |
| real-deepl | 2 | security_certifications:✗; data_regions:✓; trains_on_customer_data:✓; sso_saml:✓; dpa_available:✓ |

## Thresholds

| Metric | Value | Target | Status |
|---|---|---|---|
| field_accuracy | 93.3% | ≥ 80% | ✅ |

## Notes

- This scores **live public pages** against the hand gold (M2/M6 solo path).
- Full agent crawl: `SEARCH_PROVIDER=ddgs LLM_PROVIDER=ollama python eval/run_real_eval.py --live --limit 1`

