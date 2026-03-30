# Codex Trader

Quant research toolkit with:

- historical data download from `yfinance`
- backtesting for established strategies used in systematic equity trading
- ML-based directional signal generation on engineered price features
- paper-trading adapters with a local simulator and moomoo OpenAPI support

## Included strategy families

### 1. Dual Momentum / Trend Following

A long-only time-series momentum model using fast/slow moving averages, with
volatility targeting and capped leverage. This is a standard institutional
baseline because it is transparent, robust, and easy to risk-manage.

### 2. Mean Reversion

A short-horizon z-score strategy around a rolling moving average. This is a
common quant baseline for liquid index ETFs and other mean-reverting assets.

### 3. ML Classifier

A rolling `HistGradientBoostingClassifier` trained on engineered price and
volatility features. It predicts the next-day return direction and converts
probabilities into capped position signals.

## Project layout

```text
quant-trading-analyzer/
├── config.json
├── quant_trader/
│   ├── backtest.py
│   ├── brokers.py
│   ├── cli.py
│   ├── config.py
│   ├── data.py
│   ├── features.py
│   ├── metrics.py
│   └── strategies.py
└── tests/
```

## Install

```bash
cd quant-trading-analyzer
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

### Backtest all bundled strategies

```bash
codex-trader backtest --config config.json
```

### Backtest a single strategy

```bash
codex-trader backtest --config config.json --strategy dual_momentum
```

### Train the ML strategy and print summary stats

```bash
codex-trader train-ml --config config.json
```

### Optimize strategy parameters

```bash
codex-trader optimize --config config.json --strategy dual_momentum
```

### Paper trade using the local simulator

```bash
codex-trader paper-trade --config config.json --strategy dual_momentum
```

### Run the dashboard

```bash
streamlit run dashboard.py
```

### Paper trade with moomoo OpenD

Set `"broker": "moomoo"` in `config.json`, run moomoo OpenD locally, then:

```bash
codex-trader paper-trade --config config.json --strategy dual_momentum
```

## Paper trading adapters

### Simulated broker

Always available. Logs orders and maintains synthetic positions in memory.

### moomoo

Uses the `moomoo` Python SDK if installed and sends paper orders through OpenD.
The adapter targets simulated trading, not live trading.

### IBKR

An IBKR config shape is included, but the default implementation in this
project does not place IBKR orders yet. The cleaner near-term path is to prove
the stack with the simulator or moomoo first.

Paper trading rebalances to target holdings based on current positions and
latest prices. It sizes against current portfolio value when the broker can
report cash and positions, and it does not blindly resubmit the full target
weights on every run.

The same paper-trade preparation flow is shared by the CLI and the Streamlit
dashboard so sizing and rebalance behavior stay aligned.

## Important limitations

- This project is for research and simulated execution only.
- No strategy here is guaranteed profitable out of sample.
- The ML model uses only historical price-derived features, which is a weak
  signal class by itself and should be treated as an experimental overlay.
- Backtest results can be overstated by regime dependence, data quality issues,
  and slippage assumptions.

## Offline data fallback

If live `yfinance` download is blocked in your environment, set
`data_cache_path` in `config.json` to a CSV file with:

- dates in the first column
- ticker symbols as the remaining columns
- adjusted close prices as values

## Source notes

- `yfinance` is used for historical data download.
- Interactive Brokers paper trading is documented in the TWS API docs.
- moomoo OpenAPI documents simulated trade environments and order placement.
- Streamlit is used for the dashboard.
