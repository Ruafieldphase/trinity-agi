# Contributing

1. Fork & branch from `main`.
2. Install hooks: `pip install pre-commit && pre-commit install`.
3. Run local checks: `ruff . && black --check .` and `python tools/adaptive_feedback/run_tests.sh`.
4. Open a PR; CI must pass.
