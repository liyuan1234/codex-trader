# Code Critique

This project has a useful shape for a compact quant-research tool: the core responsibilities are separated into data loading, strategy generation, backtesting, optimization, broker adapters, and CLI/dashboard entry points. That is a good foundation. The main improvements now are less about adding more functionality and more about tightening semantics, reducing duplication, and raising the floor on operational correctness.

## 1. Clarify the model of the system

The code mixes two different concepts without making the boundary explicit:

- target portfolio weights
- order instructions

Backtesting treats strategy output as target exposures, which is a clean design. Paper trading then reuses those same weights as if they were direct order sizes. That mismatch is the most important conceptual problem in the codebase. A stronger design would make the flow explicit:

1. strategy produces target weights
2. portfolio state converts target weights into desired positions
3. execution logic computes deltas from current holdings
4. broker adapter submits only the delta orders

Once those layers are separated, the code becomes easier to reason about and much safer to extend.

## 2. Reduce duplicated business logic

The CLI and Streamlit dashboard both repeat the same workflows:

- loading config
- loading prices
- building a strategy
- generating weights
- running optimization
- translating weights into paper orders

That duplication will drift. The CLI and dashboard should call shared service functions instead of re-implementing orchestration separately. A simple `services.py` or `app.py` layer with functions like `run_strategy_backtest`, `run_strategy_optimization`, and `build_paper_orders` would improve consistency and make it much easier to test behavior once.

## 3. Strengthen testing around behavior, not just execution

The current tests mostly prove that parsing and import paths work. They do not meaningfully validate the trading logic. For this kind of code, the most valuable tests are deterministic behavioral tests.

Examples of tests worth adding:

- a backtest with fixed prices and known weights where expected returns and costs are asserted directly
- a strategy test verifying that a rising series triggers long exposure for dual momentum
- a rebalance test proving that repeated paper-trade runs do not keep accumulating unwanted positions
- a data-loader test for single-ticker and multi-ticker `yfinance` outputs
- an optimizer test that verifies result ranking and parameter coverage

If you add only a few tests, they should target the financial semantics, not just command success.

## 4. Improve dependency and packaging discipline

The project is installable, but the packaging story is incomplete. The dashboard is documented as a first-class entry point, yet `streamlit` is not declared as a dependency. Generated artifacts like `.egg-info`, caches, and log files are also sitting in the worktree. That suggests the repo boundary between source and build/runtime output is still loose.

A cleaner setup would include:

- a fuller `.gitignore` for build, cache, and log artifacts
- optional dependency groups such as `dev` and `dashboard`
- a documented test command that works from a fresh environment

This matters because packaging problems make a project feel less reliable than the code may actually be.

## 5. Be more explicit about data assumptions

The strategy and feature code make several implicit assumptions:

- daily bars
- adjusted close behavior
- sufficient lookback history
- synchronized symbol calendars
- forward-filling missing prices is acceptable

Those may be reasonable defaults, but they should be called out in code or validation. Right now, many failures will appear only as odd results instead of explicit errors. Adding basic validation at load time would help:

- reject empty or too-short datasets for a chosen strategy
- verify required columns and monotonic timestamps
- surface when forward-filled data crosses large gaps

Quant code benefits from being opinionated about data quality rather than silently accepting everything.

## 6. Separate research code from execution code more carefully

Research tooling and broker integrations are in the same package, which is fine for a small project, but the execution path deserves stricter interfaces. Broker code should operate on well-defined domain objects such as:

- portfolio snapshot
- target allocation
- order proposal
- execution receipt

That makes it easier to simulate, test, and later support brokers beyond the current simulator and moomoo adapter. It also prevents research-stage shortcuts from leaking into the execution path.

## 7. Add stronger guardrails around runtime behavior

This code can place paper orders, so even though it is not live trading software, it should still behave like an operational system.

Useful guardrails would include:

- dry-run previews before order submission
- explicit max order size limits
- visibility into current positions before rebalance
- logging that distinguishes signal generation from order placement
- clear failure handling around broker connectivity and partial submission

The more the system touches a broker API, the less acceptable implicit behavior becomes.

## 8. Make the metrics layer a bit more honest

The metrics module is concise, which is good, but it currently presents a polished set of summary numbers without much context. In quant tooling, that can encourage overconfidence. You could improve this by adding:

- benchmark-relative metrics
- exposure statistics
- turnover statistics
- number of trades or rebalance events
- explicit warnings for too-short backtests

The point is not more metrics for their own sake. It is to make the results harder to misread.

## 9. Tighten the public interface of configuration

`AppConfig` is a thin wrapper over raw JSON, which keeps things simple, but it does not validate much. Missing keys or malformed values will fail late and somewhat indirectly. A stronger config model would validate fields when loading:

- required keys and types
- valid strategy names
- parameter ranges
- broker-specific required fields

That would turn configuration errors into immediate, readable feedback instead of runtime surprises deep in execution.

## 10. Keep the project small, but make the boundaries sharper

The codebase does not need a heavy framework. It just needs cleaner boundaries:

- domain logic for signals and portfolio targets
- application services for workflows
- infrastructure for data and brokers
- interfaces that are easy to test without network access

That would preserve the current simplicity while making future additions less fragile.

## Recommended Next Steps

1. Fix the paper-trading semantics so execution is based on position deltas, not repeated submission of target weights.
2. Extract shared workflow logic from the CLI and dashboard into common service functions.
3. Add a small set of deterministic tests for backtest math, strategy outputs, and rebalancing behavior.
4. Clean up packaging by declaring missing dependencies and ignoring generated artifacts.
5. Add validation for config input and minimum data sufficiency.

## Bottom Line

The project is already structured well enough to become a solid small research platform. The next stage of improvement is not feature breadth. It is precision: clearer semantics, less duplicated orchestration, stronger tests, and safer execution behavior.
