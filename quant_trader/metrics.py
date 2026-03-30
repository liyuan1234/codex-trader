from __future__ import annotations

import math

import pandas as pd


def max_drawdown(equity_curve: pd.Series) -> float:
    peak = equity_curve.cummax()
    drawdown = equity_curve / peak - 1
    return float(drawdown.min())


def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    compounded = (1 + returns).prod()
    years = max(len(returns) / periods_per_year, 1 / periods_per_year)
    return float(compounded ** (1 / years) - 1)


def annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    return float(returns.std(ddof=0) * math.sqrt(periods_per_year))


def sharpe_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
    volatility = annualized_volatility(returns, periods_per_year=periods_per_year)
    if volatility == 0:
        return 0.0
    return annualized_return(returns, periods_per_year=periods_per_year) / volatility


def summary_metrics(returns: pd.Series, equity_curve: pd.Series) -> dict[str, float]:
    return {
        "annual_return": annualized_return(returns),
        "annual_volatility": annualized_volatility(returns),
        "sharpe": sharpe_ratio(returns),
        "max_drawdown": max_drawdown(equity_curve),
        "win_rate": float((returns > 0).mean()),
    }
