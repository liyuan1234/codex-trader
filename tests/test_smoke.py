from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quant_trader.brokers import AccountSnapshot, MoomooPaperBroker, SimulatedPaperBroker
from quant_trader.cli import build_parser, build_rebalance_orders, estimate_portfolio_value, main, prepare_paper_trade
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
        orders = build_rebalance_orders(latest_weights, latest_prices, current_positions, portfolio_value=100000.0)
        self.assertEqual(orders, [])

        reduced_positions = {"SPY": 450, "QQQ": 260}
        orders = build_rebalance_orders(latest_weights, latest_prices, reduced_positions, portfolio_value=100000.0)
        order_map = {(order.symbol, order.side): order.quantity for order in orders}
        self.assertEqual(order_map[("SPY", "BUY")], 50)
        self.assertEqual(order_map[("QQQ", "SELL")], 10)

    def test_rebalance_orders_liquidate_untargeted_positions(self) -> None:
        latest_weights = pd.Series({"SPY": 1.0})
        latest_prices = pd.Series({"SPY": 100.0, "QQQ": 200.0})
        current_positions = {"SPY": 900, "QQQ": 10}
        orders = build_rebalance_orders(latest_weights, latest_prices, current_positions, portfolio_value=100000.0)
        order_map = {(order.symbol, order.side): order.quantity for order in orders}
        self.assertEqual(order_map[("SPY", "BUY")], 100)
        self.assertEqual(order_map[("QQQ", "SELL")], 10)

    def test_estimate_portfolio_value_uses_cash_and_holdings(self) -> None:
        snapshot = AccountSnapshot(cash_balance=25000.0, positions={"SPY": 300, "QQQ": 100})
        latest_prices = pd.Series({"SPY": 100.0, "QQQ": 200.0})
        self.assertEqual(estimate_portfolio_value(snapshot, latest_prices, fallback_cash=100000.0), 75000.0)

    def test_simulated_broker_updates_cash_and_positions(self) -> None:
        broker = SimulatedPaperBroker(starting_cash=1000.0)
        order = build_rebalance_orders(pd.Series({"SPY": 0.5}), pd.Series({"SPY": 100.0}), {}, portfolio_value=1000.0)[0]
        broker.place_market_order(order=order)
        snapshot = broker.get_account_snapshot()
        self.assertEqual(snapshot.positions["SPY"], 5)
        self.assertEqual(snapshot.cash_balance, 500.0)

    def test_prepare_paper_trade_sizes_from_account_snapshot(self) -> None:
        prices = make_price_frame()
        fake_snapshot = AccountSnapshot(cash_balance=20000.0, positions={"SPY": 300})

        class FakeBroker:
            def get_account_snapshot(self) -> AccountSnapshot:
                return fake_snapshot

            def place_market_order(self, order):
                raise AssertionError("Should not submit orders in preparation path")

        with patch("quant_trader.cli._load_prices", return_value=prices), patch("quant_trader.cli.build_paper_broker", return_value=FakeBroker()):
            prepared = prepare_paper_trade("config.json", "dual_momentum")
        self.assertGreater(float(prepared["portfolio_value"]), 20000.0)
        self.assertIs(prepared["account_snapshot"], fake_snapshot)

    def test_moomoo_broker_initializes_and_loads_snapshot(self) -> None:
        class FakeFrame:
            def __init__(self, rows):
                self._rows = rows

            def iterrows(self):
                for index, row in enumerate(self._rows):
                    yield index, row

        class FakeContext:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def unlock_trade(self, pwd):
                return 0, pwd

            def accinfo_query(self, trd_env=None):
                return 0, FakeFrame([{"cash": 12345.0}])

            def position_list_query(self, position_market=None, trd_env=None):
                return 0, FakeFrame([{"code": "SPY", "qty": 12}])

            def close(self):
                return None

        fake_moomoo = types.SimpleNamespace(
            OpenSecTradeContext=FakeContext,
            SecurityFirm=types.SimpleNamespace(FUTUSG="FUTUSG"),
            TrdMarket=types.SimpleNamespace(US="US"),
            TrdSide=types.SimpleNamespace(BUY="BUY", SELL="SELL"),
            TrdEnv=types.SimpleNamespace(SIMULATE="SIMULATE"),
            OrderType=types.SimpleNamespace(MARKET="MARKET"),
            RET_OK=0,
        )

        with patch.dict(sys.modules, {"moomoo": fake_moomoo}):
            broker = MoomooPaperBroker(host="127.0.0.1", port=11111, market="US")
            snapshot = broker.get_account_snapshot()
        self.assertEqual(broker._context_kwargs["filter_trdmarket"], "US")
        self.assertEqual(snapshot.cash_balance, 12345.0)
        self.assertEqual(snapshot.positions, {"SPY": 12})


if __name__ == "__main__":
    unittest.main()
