# Contributing

Keep changes small, testable and tied to one technical objective. Never commit secrets or confidential competition data. Raw datasets live under `data/raw/` and are ignored by Git.

Before opening a PR:

```bash
make check
```

Any model change must update `artifacts/metrics.json` and the model card or explain why metrics are unchanged.
