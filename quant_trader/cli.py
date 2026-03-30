from __future__ import annotations

import argparse
import json

from .backtest import run_backtest
from .brokers import OrderRequest, build_paper_broker
from .config import load_config
from .data import download_prices, load_prices_from_csv
from .optimizer import optimize_strategy
from .strategies import build_strategy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Quant trading analyzer with backtesting and paper trading.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backtest = subparsers.add_parser("backtest", help="Run historical backtests.")
    backtest.add_argument("--config", required=True)
    backtest.add_argument("--strategy", help="Optional single strategy name.")

    train_ml = subparsers.add_parser("train-ml", help="Run the ML strategy pipeline and print metrics.")
    train_ml.add_argument("--config", required=True)

    optimize = subparsers.add_parser("optimize", help="Grid-search parameters for supported strategies.")
    optimize.add_argument("--config", required=True)
    optimize.add_argument("--strategy", required=True, choices=["dual_momentum", "mean_reversion"])

    paper = subparsers.add_parser("paper-trade", help="Generate current signal and submit simulated paper orders.")
    paper.add_argument("--config", required=True)
    paper.add_argument("--strategy", default="dual_momentum")
    return parser


def _load_prices(config):
    if config.data_cache_path:
        return load_prices_from_csv(config.data_cache_path)
    return download_prices(config.tickers, start=config.start_date, end=config.end_date)


def run_backtests(config_path: str, strategy_name: str | None = None) -> int:
    config = load_config(config_path)
    prices = _load_prices(config)
    strategy_names = [strategy_name] if strategy_name else list(config.strategies.keys())

    for name in strategy_names:
        strategy = build_strategy(name, config.strategies[name])
        weights = strategy.generate(prices)
        result = run_backtest(
            prices=prices,
            weights=weights,
            strategy_name=name,
            starting_cash=config.cash,
            transaction_cost_bps=config.transaction_cost_bps,
            slippage_bps=config.slippage_bps,
        )
        print(name)
        print(json.dumps(result.metrics, indent=2))
        print("")
    return 0


def run_ml(config_path: str) -> int:
    return run_backtests(config_path, strategy_name="ml_classifier")


def run_optimization(config_path: str, strategy_name: str) -> int:
    config = load_config(config_path)
    prices = _load_prices(config)
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
        raise ValueError(f"Optimization not configured for strategy: {strategy_name}")

    frame = optimize_strategy(
        strategy_name=strategy_name,
        prices=prices,
        parameter_grid=grid,
        starting_cash=config.cash,
        transaction_cost_bps=config.transaction_cost_bps,
        slippage_bps=config.slippage_bps,
    )
    print(frame.head(10).to_string(index=False))
    return 0


def run_paper_trade(config_path: str, strategy_name: str) -> int:
    config = load_config(config_path)
    prices = _load_prices(config)
    strategy = build_strategy(strategy_name, config.strategies[strategy_name])
    weights = strategy.generate(prices)
    latest = weights.iloc[-1].sort_values(ascending=False)
    broker = build_paper_broker(config.paper_trading)

    print(f"broker={config.paper_trading['broker']}")
    for symbol, weight in latest.items():
        if abs(weight) < 1e-6:
            continue
        side = "BUY" if weight > 0 else "SELL"
        quantity = max(1, int(abs(weight) * 100))
        receipt = broker.place_market_order(OrderRequest(symbol=symbol, side=side, quantity=quantity))
        print(json.dumps(receipt.__dict__, indent=2, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "backtest":
        return run_backtests(args.config, strategy_name=args.strategy)
    if args.command == "train-ml":
        return run_ml(args.config)
    if args.command == "optimize":
        return run_optimization(args.config, strategy_name=args.strategy)
    if args.command == "paper-trade":
        return run_paper_trade(args.config, strategy_name=args.strategy)
    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
