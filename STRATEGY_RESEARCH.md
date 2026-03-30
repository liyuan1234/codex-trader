# Strategy Research Memo

Date: 2026-03-30

## Executive View

For this codebase, the best next strategies are not the most sophisticated ones in the literature. They are the ones that are:

- empirically well supported
- implementable with daily price data from `yfinance`
- compatible with ETF and liquid large-cap universes
- robust enough to survive realistic transaction costs and basic paper-trading constraints

The highest-quality roadmap is:

1. strengthen trend-following into a proper time-series momentum and breakout family
2. add a volatility-managed overlay and crash control around momentum
3. add sector or industry momentum rotation
4. add a more disciplined residual mean-reversion or pairs framework
5. defer more ambitious ML feature research until the execution and evaluation stack is stable

## Research Conclusion

The project does **not** need deeper research into novel quantitative features yet. The literature already gives enough strong ideas to keep this repo busy for multiple iterations. The bottleneck is implementation quality, portfolio construction, and evaluation discipline.

That said, there are several high-quality strategies worth implementing now.

## Recommended Strategy Stack

### 1. Time-Series Momentum With Breakout Variants

**Recommendation:** implement now

This should be the core strategy family. The evidence base is strong, the data requirements are light, and the strategy fits the repo's daily-bar architecture. The current dual moving-average model is a simplified version of this idea, but it should be expanded into a more research-grounded family.

Why it belongs:

- time-series momentum has strong academic support across asset classes
- it is relatively robust under simple daily implementation
- it works naturally with ETFs
- it pairs well with volatility scaling and crisis diversification

Practical variants to implement:

- 12-1 time-series momentum signal: long if trailing 12-month return is positive, flat or short if negative
- breakout rules: long if price is above the trailing 6-, 9-, or 12-month high; flat or short otherwise
- moving-average slope or normalized trend-strength variants
- ensemble trend signal: combine multiple lookbacks instead of relying on one fast/slow window pair

Implementation notes:

- keep signals simple and diversify across lookbacks
- add vol targeting and max gross exposure constraints
- use weekly or monthly rebalance options in addition to daily to reduce turnover
- start with long-only ETF trend if the broker path is not ready for systematic shorting

Why this is stronger than adding more ML now:

- stronger evidence base
- lower estimation risk
- easier attribution of results
- fewer hidden failure modes

### 2. Volatility-Managed Momentum

**Recommendation:** implement immediately after the trend family

This is the highest-value overlay after basic trend-following. The literature shows that scaling risk down when realized volatility is high materially improves risk-adjusted performance in many factor portfolios, including momentum.

Why it belongs:

- easy to implement on top of existing signals
- directly addresses one of momentum's main weaknesses: crash risk
- consistent with current code structure, which already contains simple volatility targeting

Practical variants to implement:

- inverse-realized-vol scaling using 20-, 40-, or 60-day realized volatility
- capped leverage with floor and ceiling bands
- panic-state de-risking when both volatility is elevated and market drawdown is large

Implementation notes:

- compare static momentum vs vol-managed momentum in identical backtests
- evaluate turnover and crash-period behavior, not just full-sample Sharpe
- do not overfit the volatility window

### 3. Sector / Industry Momentum Rotation

**Recommendation:** implement soon

For this repo, sector rotation is a better next momentum expansion than broad single-name cross-sectional momentum. It fits the current data pipeline, avoids much of the microstructure noise that exists in smaller stocks, and is easier to trade operationally.

Why it belongs:

- academically supported by evidence that industry momentum explains a meaningful part of stock momentum
- straightforward with liquid sector ETFs such as `XLF`, `XLK`, `XLE`, `XLI`, `XLV`
- lower implementation complexity than stock-level long-short cross-sectional momentum

Practical variants to implement:

- rank sector ETFs by trailing 6- or 12-month return and hold the top `N`
- risk-normalized sector momentum using trailing vol or ATR-style scaling
- combine absolute momentum and relative momentum:
  sectors must have positive absolute trend and top-ranked relative performance

Implementation notes:

- start with monthly rebalance
- enforce diversification caps so one ETF does not dominate because of lower volatility
- compare against simple equal-weight sector rotation and SPY benchmark

### 4. Residual Mean Reversion / ETF Pairs

**Recommendation:** implement, but only after the execution stack is stable

Mean reversion is worth keeping, but the next version should be more disciplined than simple z-score reversion on raw prices. The more robust research direction is residual mean reversion:

- pair related ETFs
- regress an ETF on a benchmark or sector basket
- trade deviations in the residual rather than raw price distance

Why it belongs:

- daily data is sufficient
- this is closer to the statistical-arbitrage literature than naive price-level reversion
- can be implemented on liquid ETF pairs with lower microstructure risk than stock-level stat-arb

Practical variants to implement:

- spread z-score on fixed ETF pairs such as `SPY` vs `IVV` is too trivial, but `XLF` vs `KBE`, `XLK` vs `QQQ`, `XLE` vs `USO`-style relationships may be useful
- benchmark-neutral residual reversion: regress each ETF on SPY and trade residual extremes
- rolling hedge-ratio model with entry and exit bands

Implementation notes:

- require stationarity or at least stable spread behavior before trading
- include explicit stop logic and time stops
- model transaction costs carefully because mean reversion is turnover-heavy

### 5. Dynamic Momentum Crash Control

**Recommendation:** implement after base momentum and vol management

Momentum is empirically strong but prone to crash episodes, especially during violent rebounds after market stress. A dynamic crash-control overlay is more useful than adding exotic alpha features.

Practical versions for this repo:

- reduce momentum exposure when market volatility is elevated and recent benchmark drawdown is large
- downweight or neutralize momentum when the market begins a sharp rebound from a stressed state
- switch from aggressive momentum to defensive or lower-beta trend exposures under panic conditions

This should be treated as risk management for the momentum sleeve, not a standalone alpha engine.

## Strategy Ranking For This Repo

### Tier 1: Build Now

1. Time-series momentum with multiple lookbacks
2. Breakout trend model
3. Volatility-managed overlay
4. Sector momentum rotation

### Tier 2: Build After Platform Stabilization

1. Residual mean reversion on ETFs
2. Rolling-hedge-ratio pairs trading
3. Momentum crash filter / panic-state de-risking

### Tier 3: Defer

1. Deep ML models on price features alone
2. Large stock-level stat-arb without better execution and portfolio accounting
3. Feature-heavy classifiers without stronger cross-validation and regime testing
4. Fundamental value strategies, because the current data stack does not support them well

## What To Research Later, Not Now

The codebase may eventually benefit from better feature extraction, but that is a **phase-two** problem.

Once the platform is stable, the highest-value additional features would be:

- realized volatility term structure
- downside semivariance
- trend strength normalized by volatility
- rolling beta and residual momentum
- breadth measures across the ETF universe
- drawdown-state features and rebound-state flags

I would **not** prioritize:

- generic technical-indicator sprawl
- many correlated moving-average features
- price-only ML classifiers with dozens of weakly distinct features

Those usually add complexity faster than they add durable edge.

## Recommended Implementation Sequence

### Milestone 1

- refactor the existing dual momentum into a general time-series momentum engine
- support multiple lookbacks and optional breakout logic
- add rebalance frequency controls
- add vol-target overlay with sane caps

### Milestone 2

- add sector momentum rotation
- compare absolute momentum, relative momentum, and combined filters
- report turnover, drawdown, and benchmark-relative metrics

### Milestone 3

- add ETF residual mean-reversion and pairs module
- support rolling hedge-ratio estimation
- add exposure, spread, and half-life diagnostics

### Milestone 4

- add momentum crash controls
- evaluate stressed-regime performance separately from full-sample results

## Evaluation Standards

Any new strategy should be judged on more than return and Sharpe. At minimum, compare:

- annualized return
- annualized volatility
- Sharpe ratio
- max drawdown
- turnover
- hit rate
- exposure stability
- performance during crisis regimes
- sensitivity to rebalance frequency and transaction-cost assumptions

For momentum strategies specifically, evaluate crash behavior after major market drawdowns and rebounds.

## Bottom Line

The best research direction for this project is **not** deeper feature engineering yet. It is to implement a robust family of trend and momentum strategies, add volatility-aware risk management, then extend into sector rotation and residual mean reversion.

If the team executes that sequence well, it will have a much stronger research platform than it would get from jumping early into more complex ML or feature-extraction work.

## Sources

- Moskowitz, Ooi, and Pedersen, “Time Series Momentum,” *Journal of Financial Economics* (2012): https://pages.stern.nyu.edu/~lpederse/papers/TimeSeriesMomentum.pdf
- Hurst, Ooi, and Pedersen, “A Century of Evidence on Trend-Following Investing” (2017): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2993026
- Moreira and Muir, “Volatility Managed Portfolios” (2017; NBER working paper page): https://www.nber.org/papers/w22208
- Jegadeesh and Titman, “Returns to Buying Winners and Selling Losers” (1993 abstract page): https://EconPapers.repec.org/RePEc:bla:jfinan:v:48:y:1993:i:1:p:65-91
- Moskowitz and Grinblatt, “Do Industries Explain Momentum?” (1999 abstract page): https://EconPapers.repec.org/RePEc:bla:jfinan:v:54:y:1999:i:4:p:1249-1290
- Gatev, Goetzmann, and Rouwenhorst, “Pairs Trading: Performance of a Relative-Value Arbitrage Rule” (NBER / RFS pages): https://www.nber.org/papers/w7032
- Avellaneda and Lee, “Statistical Arbitrage in the U.S. Equities Market” (SSRN abstract page): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1153505
- Daniel and Moskowitz, “Momentum Crashes” (NBER working paper page): https://www.nber.org/papers/w20439
