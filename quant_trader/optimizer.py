from __future__ import annotations

from itertools import product

import pandas as pd

from .backtest import run_backtest
from .strategies import build_strategy


def optimize_strategy(
    strategy_name: str,
    prices: pd.DataFrame,
    parameter_grid: dict[str, list],
    starting_cash: float,
    transaction_cost_bps: float,
    slippage_bps: float,
) -> pd.DataFrame:
    keys = list(parameter_grid.keys())
    rows: list[dict] = []

    for values in product(*(parameter_grid[key] for key in keys)):
        params = dict(zip(keys, values))
        strategy = build_strategy(strategy_name, params)
        weights = strategy.generate(prices)
        result = run_backtest(
            prices=prices,
            weights=weights,
            strategy_name=strategy_name,
            starting_cash=starting_cash,
            transaction_cost_bps=transaction_cost_bps,
            slippage_bps=slippage_bps,
        )
        rows.append({**params, **result.metrics})

    if not rows:
        raise ValueError("Parameter grid produced no combinations.")

    frame = pd.DataFrame(rows)
    return frame.sort_values(by="sharpe", ascending=False).reset_index(drop=True)
