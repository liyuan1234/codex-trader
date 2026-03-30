# Review Findings

## Findings

1. High: Paper-trade order sizing is implemented as blind resubmission of the full target weights, not a rebalance to target holdings. In [quant_trader/cli.py#L104](/Users/liyuan/Desktop/codex-image-agent/quant-trading-analyzer/quant_trader/cli.py#L104) and [dashboard.py#L109](/Users/liyuan/Desktop/codex-image-agent/quant-trading-analyzer/dashboard.py#L109), each non-zero weight becomes a fresh `BUY` or `SELL` order of `abs(weight) * 100` shares on every run. Re-running the command will keep adding or subtracting shares instead of converging to the intended portfolio. That is a real trading-behavior bug, especially against external brokers like moomoo.

2. Medium: The documented dashboard install path is incomplete because `streamlit` is imported but not declared as a dependency. [dashboard.py#L6](/Users/liyuan/Desktop/codex-image-agent/quant-trading-analyzer/dashboard.py#L6) imports `streamlit`, and the README tells users to run `streamlit run dashboard.py`, but [pyproject.toml#L11](/Users/liyuan/Desktop/codex-image-agent/quant-trading-analyzer/pyproject.toml#L11) only installs `numpy`, `pandas`, `scikit-learn`, and `yfinance`. A fresh `pip install -e .` from the README will not produce a runnable dashboard.

3. Medium: The only behavioral smoke test does not exercise the actual strategy path it claims to cover. [tests/test_smoke.py#L27](/Users/liyuan/Desktop/codex-image-agent/quant-trading-analyzer/tests/test_smoke.py#L27) feeds just 8 daily rows into `dual_momentum`, but the default config uses `fast_window=50` and `slow_window=200`. That means the generated weights stay zero throughout, so the test only proves the CLI exits successfully, not that signal generation, turnover, costs, or paper-trade logic work. This gap is large enough that the order-sizing bug above would slip through unchanged.

4. Low: The worktree includes generated artifacts that are not covered by the current ignore rules. [.gitignore#L1](/Users/liyuan/Desktop/codex-image-agent/quant-trading-analyzer/.gitignore#L1) ignores `__pycache__`, `*.pyc`, and `.DS_Store`, but the current changes also include `quant_trading_analyzer.egg-info/` and `codex_2026-03-30.log`. Those should not be reviewed or committed as source changes.

## Open Questions / Assumptions

- I assumed the intended semantics of `weights` are target portfolio exposures, because that is how they are used in backtesting. If you instead meant them to be per-run order tickets, the naming and backtest integration are misleading.
- I could not run the test suite end to end here because the environment does not have package dependencies installed. `python3 -m unittest discover -s tests -q` currently fails with `ModuleNotFoundError: No module named 'pandas'`.

## Summary

This is a new untracked project drop rather than an incremental patch, and the main risk is in paper-trade execution semantics rather than the backtest math.
