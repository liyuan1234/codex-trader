# ML Classifier Strategy Walkthrough

## What the code does

Sources:

- [`quant_trader/strategies.py`](/Users/liyuan/Desktop/codex-image-agent/quant-trading-analyzer/quant_trader/strategies.py)
- [`quant_trader/features.py`](/Users/liyuan/Desktop/codex-image-agent/quant-trading-analyzer/quant_trader/features.py)

For each ticker independently:

1. Build price-derived features:
   - `ret_1d`, `ret_5d`, `ret_21d`, `ret_63d`, `ret_126d`
   - `vol_20`
   - moving-average ratios against 10, 20, 50, and 200 days
   - `zscore_20`
   - `breakout_20`
   - `rsi_14`
2. Define the training target as:
   - `1` if the next day return is positive
   - `0` otherwise
3. Train a `HistGradientBoostingClassifier` on a rolling `252`-row window.
4. Retrain every `21` rows.
5. Convert predicted probabilities into trading signals:
   - long if `probability > 0.54`
   - short if `probability <= 0.54`
   - flat only before predictions become available
6. Cross-sectionally normalize the resulting long/short signals.

This is a directional classifier, not a stop-based execution system.

## Buy condition

- Buy when the predicted probability of a positive next-day return is greater than `0.54`.

## Sell condition

- Sell a long when the probability falls back to `0.54` or below.
- Short when the probability remains below the threshold.

## Stop loss

- There is no explicit stop-loss order in the current implementation.
- The exit is signal-driven, not loss-driven.
- The model can stay short or long through adverse price moves until the classifier output changes.

## What the feature set is trying to detect

The classifier combines:

- short and medium-term momentum
- recent volatility
- overbought/oversold state through RSI and z-score
- breakout state relative to the 20-day high
- position of price relative to multiple moving averages

In institutional terms, this is a compact price-only feature stack for short-horizon directional classification.

## Example decision path

Data file: [`results/prices_2018_to_2026-03-30.csv`](/Users/liyuan/Desktop/codex-image-agent/quant-trading-analyzer/results/prices_2018_to_2026-03-30.csv)

The committed backtest result for this strategy is in:

- [`results/ml_classifier_metrics.txt`](/Users/liyuan/Desktop/codex-image-agent/quant-trading-analyzer/results/ml_classifier_metrics.txt)
- [`results/ml_classifier_equity_curve.csv`](/Users/liyuan/Desktop/codex-image-agent/quant-trading-analyzer/results/ml_classifier_equity_curve.csv)

Backtest result:

- annual return: `-2.74%`
- annual volatility: `14.47%`
- Sharpe: `-0.19`
- max drawdown: `-28.86%`
- ending equity: about `$79,586`

Decision interpretation:

- the model predicts one-day direction separately for each ETF
- those predictions are converted into long or short signals
- the portfolio is then normalized across all active names

## Why there is no options example here

- The current codebase does not trade options.
- The current ML model produces a directional underlying signal only.
- It has no option-chain data, implied volatility features, Greek constraints, or expiry selection logic.

## Limitations

- No explicit stop-loss
- No probability calibration analysis
- No option-chain integration
- No transaction-cost model specific to shorting or options
