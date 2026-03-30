# How These Signals Could Be Mapped To Options

## Current repo status

The current `codex-trader` repo does not trade options. It only works with underlying ETF prices and converts signals into synthetic spot weights.

That means there is currently:

- no option-chain ingestion
- no expiry selection
- no strike selection
- no implied-volatility model
- no Greek risk control
- no options backtester

## How each strategy would translate conceptually

### Dual momentum

Most natural options expression:

- long calls
- call spreads
- occasionally put spreads for defensive overlays

Institutional-style mapping:

- buy 30 to 90 DTE calls when `fast_ma > slow_ma`
- roll or close when the trend filter turns off
- prefer call spreads if implied volatility is rich and directional conviction is moderate

Risk controls that would be required:

- max premium at risk per trade
- delta limits
- vega and theta limits
- exit if trend filter flips or if option premium decays below a threshold

### Mean reversion

Most natural options expression:

- short-dated call spreads after overbought signals
- short-dated put spreads after oversold signals
- sometimes premium-selling structures if IV is elevated

But this is much more dangerous than the spot version because:

- mean reversion timing is uncertain
- gamma risk is higher
- losses can accelerate quickly when price keeps trending

Minimum extra rules needed:

- hard stop based on premium loss
- IV rank filter
- time stop before expiry
- avoid earnings and other event windows on single names

### ML classifier

Most natural options expression:

- directional call or put spreads
- possibly delta-targeted options based on probability confidence

But the current model is not ready for that because it predicts only next-day direction from price data. For real options usage you would want:

- probability calibration
- confidence thresholds higher than the current `0.54`
- option liquidity filters
- IV skew and term-structure inputs
- explicit premium/risk budgeting

## Recommended next step if you want options

Do not bolt options directly onto the current backtester.

Build these first:

1. option-chain data ingestion
2. contract selection rules
3. premium, delta, vega, theta, and spread cost modeling
4. hard stop-loss and time-stop logic
5. separate options backtest and paper-trade execution layer

## Bottom line

The current strategies can be used as directional signals for options, but they are not options strategies yet. Turning them into credible options systems requires a second layer of instrument-specific modeling and risk controls.
