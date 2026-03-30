# Project Plan

## Current Assessment

The project does not need more quantitative-method research yet. The main constraint is product reliability, especially in the paper-trading workflow. The team has already started fixing the right things, but the platform layer still needs another pass before further signal research is worth the effort.

## Priority Direction

Focus on execution correctness and platform trustworthiness before expanding strategy sophistication.

## P0

1. Fix the moomoo broker initialization bug in [quant_trader/brokers.py](/Users/liyuan/Desktop/codex-image-agent/quant-trading-analyzer/quant_trader/brokers.py).
2. Define rebalance sizing against actual portfolio NAV and available cash, not just starting cash from config.
3. Add regression tests for broker construction, position retrieval, and paper-trade order generation with mocks.

## P1

1. Extract shared service functions for backtesting, optimization, and paper-trade preparation.
2. Add clearer runtime safety rails:
   dry-run mode, max order-size checks, order previews, and better failure messages.
3. Improve configuration validation and minimum-data checks.

## P2

1. Improve observability:
   structured logs for data source, strategy outputs, rebalance decisions, and order submission results.
2. Add better evaluation metrics:
   turnover, exposure, benchmark-relative performance, and short-backtest warnings.
3. Tighten developer workflow:
   reproducible setup, a canonical test command, and clearer contributor guidance.

## Research Guidance

Do not prioritize new feature extraction or more advanced quantitative methods yet.

Research becomes worthwhile after:

1. the paper-trading path is correct
2. portfolio state is modeled explicitly
3. tests cover the execution path and backtest math
4. setup is reproducible from a clean environment

Once those are true, the next research topics should be:

1. benchmark-relative evaluation
2. regime filters and validation discipline
3. richer feature engineering only if it is supported by better evaluation controls

## Exit Criteria For This Phase

- Broker adapters construct and run reliably.
- Rebalance targets reflect actual account state.
- CLI and dashboard share the same workflow layer.
- Key trading behaviors have deterministic tests.
- A fresh setup can install and run the project without guesswork.
