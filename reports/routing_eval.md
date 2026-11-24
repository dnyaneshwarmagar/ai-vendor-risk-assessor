# Routing eval

Accuracy: **100.0%** (30/30)

| id | expected | got | ok | reason |
|---|---|---|---|---|
| r01 | assessment | assessment | ✓ | Asks whether a named tool may be used → needs policy + vendor facts. |
| r02 | assessment | assessment | ✓ | Asks whether a named tool may be used → needs policy + vendor facts. |
| r03 | assessment | assessment | ✓ | Asks whether a named tool may be used → needs policy + vendor facts. |
| r04 | assessment | assessment | ✓ | Asks whether a named tool may be used → needs policy + vendor facts. |
| r05 | assessment | assessment | ✓ | Asks whether a named tool may be used → needs policy + vendor facts. |
| r06 | assessment | assessment | ✓ | Asks whether a named tool may be used → needs policy + vendor facts. |
| r07 | assessment | assessment | ✓ | Asks whether a named tool may be used → needs policy + vendor facts. |
| r08 | assessment | assessment | ✓ | Asks whether a named tool may be used → needs policy + vendor facts. |
| r09 | vendor | vendor | ✓ | Factual question about a named vendor (semantic meaning over the word 'policy'). |
| r10 | vendor | vendor | ✓ | Factual question about a named vendor (semantic meaning over the word 'policy'). |
| r11 | vendor | vendor | ✓ | Factual question about a named vendor (semantic meaning over the word 'policy'). |
| r12 | vendor | vendor | ✓ | Factual question about a named vendor (semantic meaning over the word 'policy'). |
| r13 | vendor | vendor | ✓ | Factual question about a named vendor (semantic meaning over the word 'policy'). |
| r14 | vendor | vendor | ✓ | Factual question about a named vendor (semantic meaning over the word 'policy'). |
| r15 | policy | policy | ✓ | No vendor named → internal policy question. |
| r16 | policy | policy | ✓ | No vendor named → internal policy question. |
| r17 | policy | policy | ✓ | Asks what OUR records say about a named vendor → policy library. |
| r18 | policy | policy | ✓ | No vendor named → internal policy question. |
| r19 | policy | policy | ✓ | No vendor named → internal policy question. |
| r20 | policy | policy | ✓ | No vendor named → internal policy question. |
| r21 | policy | policy | ✓ | No vendor named → internal policy question. |
| r22 | policy | policy | ✓ | No vendor named → internal policy question. |
| r23 | refuse | refuse | ✓ | Only a human approver can approve a vendor (AI-5.1). |
| r24 | refuse | refuse | ✓ | Only a human approver can approve a vendor (AI-5.1). |
| r25 | refuse | refuse | ✓ | Only a human approver can approve a vendor (AI-5.1). |
| r26 | refuse | refuse | ✓ | Off-topic; not vendor risk or policy. |
| r27 | refuse | refuse | ✓ | Off-topic; not vendor risk or policy. |
| r28 | vendor | vendor | ✓ | Factual question about a named vendor (semantic meaning over the word 'policy'). |
| r29 | policy | policy | ✓ | No vendor named → internal policy question. |
| r30 | policy | policy | ✓ | Asks what OUR records say about a named vendor → policy library. |
