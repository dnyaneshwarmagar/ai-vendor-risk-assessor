# GitHub packaging notes

Public repo: https://github.com/dnyaneshwarmagar/ai-vendor-risk-assessor

## Enable / re-push Actions (if the badge stays red or missing)

Pushing `.github/workflows/*` needs the `workflow` OAuth scope:

```bash
gh auth refresh -h github.com -s workflow,repo
git push
```

Then open the Actions tab and confirm `CI` is green.

## Record the demo video

1. Follow [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) (2–3 min cut).
2. Paste the Loom/YouTube URL into [`demo-video.url`](demo-video.url).
3. Optionally add the same link under the Demo section of the README.
