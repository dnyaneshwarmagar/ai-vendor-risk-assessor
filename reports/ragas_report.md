# Ragas LLM-as-judge report (live generation)

- provider: `ollama`
- generate model: `qwen2.5:3b`
- judge model: `qwen2.5:7b`
- cases: 1 (parakeet-t2-internal-docs)

## Per-case

| case | route | gen_s | faithfulness | judge_s |
|---|---|---:|---|---:|
| parakeet-t2-internal-docs | assessment | 505.4 | 0.143 | 190.1 |

## Models

```env
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:3b          # answer generation
LLM_JUDGE_MODEL=qwen2.5:7b    # Ragas judge
```

