from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quant_trader.cli import build_parser, build_rebalance_orders, main
from quant_trader.config import load_config
from quant_trader.strategies import build_strategy


def make_price_frame(periods: int = 260) -> pd.DataFrame:
    index = pd.date_range("2023-01-02", periods=periods, freq="B")
    t = pd.Series(range(periods), index=index, dtype=float)
    return pd.DataFrame(
        {
            "SPY": 100 + t * 0.35,
            "QQQ": 120 + t * 0.45,
            "IWM": 80 + t * 0.10 + (t % 7) * 0.15,
            "XLF": 40 + t * 0.18,
            "XLK": 60 + t * 0.40,
        },
        index=index,
    )


class SmokeTests(unittest.TestCase):
    def test_parser_builds(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["backtest", "--config", "config.json"])
        self.assertEqual(args.command, "backtest")

    def test_load_config(self) -> None:
        config = load_config(ROOT / "config.json")
        self.assertGreater(len(config.tickers), 0)
        self.assertIn("dual_momentum", config.strategies)

    def test_cli_entry_runs_parser_path(self) -> None:
        prices = make_price_frame()
        with patch("quant_trader.cli._load_prices", return_value=prices):
            exit_code = main(["backtest", "--config", "config.json", "--strategy", "dual_momentum"])
        self.assertEqual(exit_code, 0)

    def test_optimize_parser_builds(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["optimize", "--config", "config.json", "--strategy", "dual_momentum"])
        self.assertEqual(args.command, "optimize")

    def test_dual_momentum_generates_non_zero_weights_with_sufficient_history(self) -> None:
        prices = make_price_frame()
        config = load_config(ROOT / "config.json")
        strategy = build_strategy("dual_momentum", config.strategies["dual_momentum"])
        weights = strategy.generate(prices)
        self.assertGreater(weights.abs().sum(axis=1).iloc[-1], 0.0)

    def test_rebalance_orders_use_current_positions(self) -> None:
        latest_weights = pd.Series({"SPY": 0.5, "QQQ": 0.5})
        latest_prices = pd.Series({"SPY": 100.0, "QQQ": 200.0})
        current_positions = {"SPY": 500, "QQQ": 250}
        orders = build_rebalance_orders(latest_weights, latest_prices, current_positions, capital=100000.0)
        self.assertEqual(orders, [])

        reduced_positions = {"SPY": 450, "QQQ": 260}
        orders = build_rebalance_orders(latest_weights, latest_prices, reduced_positions, capital=100000.0)
        order_map = {(order.symbol, order.side): order.quantity for order in orders}
        self.assertEqual(order_map[("SPY", "BUY")], 50)
        self.assertEqual(order_map[("QQQ", "SELL")], 10)


if __name__ == "__main__":
    unittest.main()
