# Code Critique

The project is progressing. The latest changes show the right instincts: moving from naive order submission toward actual rebalancing, improving tests, and tightening packaging. The remaining issues are no longer about broad structure. They are about making the execution model precise and dependable.

## 1. Execution correctness is still the main quality gate

The code now distinguishes target weights from order deltas more clearly, which is the right direction. But the execution layer is still not robust enough to trust. Two issues show that:

- the moomoo adapter currently has an initialization bug
- target sizing is still based on starting cash rather than actual portfolio value

That means the core product promise, "take a signal and translate it into a credible rebalance," is still not fully met. Until that is stable, more strategy work will have low leverage.

## 2. The project needs an explicit portfolio-state model

The code is currently close to having one, but not quite there. Right now it passes around:

- target weights
- latest prices
- current positions
- a capital number

That should become a real domain object or at least a clearly defined contract. For example:

- portfolio NAV
- cash balance
- current positions
- target allocations
- proposed rebalance orders

Once those concepts are explicit, the sizing logic becomes easier to validate and less likely to drift between CLI, dashboard, and broker adapters.

## 3. The testing strategy is improving, but it is still too helper-oriented

The new tests are better because they finally use enough price history and validate the rebalance helper. That is meaningful progress. But the most failure-prone code path is still not covered: constructing broker adapters, fetching positions, and running the paper-trade workflow end to end with mocks.

The next test layer should focus on:

- mocked broker integration tests
- deterministic backtest math tests
- portfolio rebalance tests with changing NAV and residual cash
- error-path tests for bad broker responses and invalid config

This project does not need a huge test suite. It needs a few tests aimed directly at the highest-risk behavior.

## 4. Shared orchestration is still too thin

The dashboard now reuses `build_rebalance_orders`, which is an improvement, but it is still sharing one helper rather than a full application workflow. The orchestration for:

- loading config
- loading prices
- building strategies
- computing signals
- preparing paper orders

still exists in multiple places. That duplication is manageable now, but it will slow the team down if more broker features, metrics, or safety checks are added. A small application/service layer would help.

## 5. Packaging and repo hygiene are on the right track

This area improved meaningfully:

- `streamlit` is now declared
- `.gitignore` is better aligned with generated outputs

That said, packaging can still be stronger. The next step is to make setup and validation reproducible:

- define a dev dependency group
- document one canonical test command
- ensure fresh-environment install and smoke-run instructions stay accurate

Those changes have an outsized effect on maintainability.

## 6. The project does not need deeper quant research yet

At this stage, more research into feature extraction or more sophisticated quantitative methods is not the bottleneck. The platform is not yet stable enough for that work to compound effectively.

Adding more signals now would likely create:

- more code paths
- more tuning surface area
- more backtest outputs
- more ambiguity about whether performance changes come from better ideas or unstable plumbing

The better sequence is:

1. make execution and portfolio-state handling correct
2. make evaluation reproducible and well tested
3. then expand features, models, and research depth

## Recommended Next Steps

1. Fix the moomoo constructor bug and add a mocked regression test for broker initialization and position loading.
2. Replace `config.cash` rebalance sizing with sizing against actual portfolio NAV and available cash.
3. Extract a small service layer for backtest, optimization, and paper-trade preparation so the CLI and dashboard stop drifting.
4. Add a few deterministic tests around backtest math, rebalance logic under changing NAV, and broker error handling.
5. Standardize local setup and testing so contributors can validate changes from a clean environment.

## Bottom Line

The project is close to the point where quantitative research could become high leverage, but it is not there yet. The team should spend the next cycle on execution correctness, shared application logic, and test reliability rather than new feature extraction or model ideas.
