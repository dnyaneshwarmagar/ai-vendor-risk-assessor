# Cached pages (live-demo repeatability)

Store saved trust-centre HTML (or markdown excerpts) here so live demos do not depend on flaky network pages:

```
cached_pages/
  notion/security.md
  openai/enterprise-privacy.md
  deepl/pro-security.md
```

Re-fetch before a graded live run:

```bash
# after setting SEARCH_PROVIDER=ddgs + a live LLM
python eval/run_real_eval.py --live
```

The solo gold set lives at `data/gold_set_real_solo.json` (Notion, OpenAI, DeepL).
