from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from quant_trader.backtest import run_backtest
from quant_trader.brokers import OrderRequest, build_paper_broker
from quant_trader.cli import build_rebalance_orders
from quant_trader.config import load_config
from quant_trader.data import download_prices, load_prices_from_csv
from quant_trader.optimizer import optimize_strategy
from quant_trader.strategies import build_strategy


st.set_page_config(page_title="Quant Trader", layout="wide")


@st.cache_data(show_spinner=False)
def load_prices_cached(config_path: str) -> pd.DataFrame:
    config = load_config(config_path)
    if config.data_cache_path:
        return load_prices_from_csv(config.data_cache_path)
    return download_prices(config.tickers, start=config.start_date, end=config.end_date)


def backtest_strategy(config_path: str, strategy_name: str):
    config = load_config(config_path)
    prices = load_prices_cached(config_path)
    strategy = build_strategy(strategy_name, config.strategies[strategy_name])
    weights = strategy.generate(prices)
    return prices, run_backtest(
        prices=prices,
        weights=weights,
        strategy_name=strategy_name,
        starting_cash=config.cash,
        transaction_cost_bps=config.transaction_cost_bps,
        slippage_bps=config.slippage_bps,
    )


st.title("Quant Trader")
st.caption("Backtesting, parameter search, ML signals, and paper-trading controls.")

default_config = Path(__file__).with_name("config.json")
config_path = st.sidebar.text_input("Config path", value=str(default_config))
strategy_name = st.sidebar.selectbox("Strategy", ["dual_momentum", "mean_reversion", "ml_classifier"])
tab_backtest, tab_optimize, tab_paper = st.tabs(["Backtest", "Optimize", "Paper Trade"])

with tab_backtest:
    try:
        prices, result = backtest_strategy(config_path, strategy_name)
        metric_cols = st.columns(5)
        metric_cols[0].metric("Annual Return", f"{result.metrics['annual_return']:.2%}")
        metric_cols[1].metric("Annual Vol", f"{result.metrics['annual_volatility']:.2%}")
        metric_cols[2].metric("Sharpe", f"{result.metrics['sharpe']:.2f}")
        metric_cols[3].metric("Max Drawdown", f"{result.metrics['max_drawdown']:.2%}")
        metric_cols[4].metric("Win Rate", f"{result.metrics['win_rate']:.2%}")
        st.line_chart(result.equity_curve.rename("equity"))
        st.dataframe(result.weights.tail(10))
        st.dataframe(prices.tail(20))
    except Exception as exc:
        st.error(f"Backtest failed: {exc}")

with tab_optimize:
    st.write("Run a small grid search over baseline strategy parameters.")
    if st.button("Run Optimization", type="primary"):
        try:
            config = load_config(config_path)
            prices = load_prices_cached(config_path)
            if strategy_name == "dual_momentum":
                grid = {
                    "fast_window": [20, 50, 100],
                    "slow_window": [100, 150, 200],
                    "volatility_target": [0.10, 0.15, 0.18],
                    "max_leverage": [1.0],
                }
            elif strategy_name == "mean_reversion":
                grid = {
                    "lookback": [10, 20, 40],
                    "entry_z": [1.0, 1.5, 2.0],
                    "exit_z": [0.25, 0.5, 0.75],
                    "max_leverage": [1.0],
                }
            else:
                st.warning("Optimization is currently enabled for dual_momentum and mean_reversion.")
                grid = None

            if grid is not None:
                frame = optimize_strategy(
                    strategy_name=strategy_name,
                    prices=prices,
                    parameter_grid=grid,
                    starting_cash=config.cash,
                    transaction_cost_bps=config.transaction_cost_bps,
                    slippage_bps=config.slippage_bps,
                )
                st.dataframe(frame)
        except Exception as exc:
            st.error(f"Optimization failed: {exc}")

with tab_paper:
    try:
        config = load_config(config_path)
        prices = load_prices_cached(config_path)
        strategy = build_strategy(strategy_name, config.strategies[strategy_name])
        weights = strategy.generate(prices)
        latest = weights.iloc[-1].sort_values(ascending=False)
        latest_prices = prices.iloc[-1]
        broker = build_paper_broker(config.paper_trading)
        current_positions = broker.get_positions()
        orders = build_rebalance_orders(
            target_weights=latest,
            latest_prices=latest_prices,
            current_positions=current_positions,
            capital=config.cash,
        )
        st.dataframe(latest.rename("weight"))
        st.json({"current_positions": current_positions})
        st.dataframe(pd.DataFrame([order.__dict__ for order in orders]) if orders else pd.DataFrame(columns=["symbol", "side", "quantity"]))

        if st.button("Submit Paper Orders"):
            receipts = []
            for order in orders:
                receipt = broker.place_market_order(OrderRequest(symbol=order.symbol, side=order.side, quantity=order.quantity))
                receipts.append(receipt.__dict__)
            st.code(json.dumps(receipts, indent=2, default=str))
    except Exception as exc:
        st.error(f"Paper-trade setup failed: {exc}")
