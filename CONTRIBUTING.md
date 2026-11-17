# Contributing

Issues and pull requests are welcome, especially:

- prior work we missed (see Related work in the README)
- bugs or false positives/negatives in the cheat detector (please include the submission and test code)
- runs on other models, with logs

## Ground rules

- **The hypotheses in the README are frozen.** Changes to them, to the memory texts or to the analysis plan after data collection has started must be recorded in the README with a date and a reason, never made silently.
- Report results as they come out, null and negative ones included.
- Keep files in `results/` small (summaries and `.eval` logs, no model weights or activation dumps).

## Development

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
uv pip install --no-deps -r requirements-impossiblebench.txt
pytest -m "not network"   # fast unit tests
pytest                    # also the end-to-end smoke test (downloads the dataset)
```

CI runs both on every push and pull request.
