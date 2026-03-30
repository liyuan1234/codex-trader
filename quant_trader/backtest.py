from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .metrics import summary_metrics


@dataclass
class BacktestResult:
    strategy_name: str
    weights: pd.DataFrame
    returns: pd.Series
    equity_curve: pd.Series
    metrics: dict[str, float]


def run_backtest(
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    strategy_name: str,
    starting_cash: float,
    transaction_cost_bps: float,
    slippage_bps: float,
) -> BacktestResult:
    asset_returns = prices.pct_change().fillna(0.0)
    shifted_weights = weights.shift(1).reindex(asset_returns.index).fillna(0.0)
    turnover = shifted_weights.diff().abs().sum(axis=1).fillna(0.0)
    gross_returns = (shifted_weights * asset_returns).sum(axis=1)
    total_cost = turnover * ((transaction_cost_bps + slippage_bps) / 10000.0)
    net_returns = gross_returns - total_cost
    equity_curve = starting_cash * (1 + net_returns).cumprod()

    return BacktestResult(
        strategy_name=strategy_name,
        weights=shifted_weights,
        returns=net_returns,
        equity_curve=equity_curve,
        metrics=summary_metrics(net_returns, equity_curve),
    )
