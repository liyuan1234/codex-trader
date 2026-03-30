from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quant_trader.cli import build_parser, main
from quant_trader.config import load_config


class SmokeTests(unittest.TestCase):
    def test_parser_builds(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["backtest", "--config", "config.json"])
        self.assertEqual(args.command, "backtest")

    def test_load_config(self) -> None:
        config = load_config(Path(__file__).resolve().parents[1] / "config.json")
        self.assertGreater(len(config.tickers), 0)
        self.assertIn("dual_momentum", config.strategies)

    def test_cli_entry_runs_parser_path(self) -> None:
        prices = pd.DataFrame(
            {
                "SPY": [100, 101, 102, 103, 104, 105, 106, 107],
                "QQQ": [200, 202, 204, 203, 205, 207, 208, 210],
                "IWM": [90, 89, 91, 92, 94, 95, 96, 98],
                "XLF": [30, 30.5, 31, 31.2, 31.5, 31.7, 32, 32.1],
                "XLK": [50, 51, 52, 53, 54, 55, 56, 57],
            },
            index=pd.date_range("2024-01-01", periods=8, freq="D"),
        )
        with patch("quant_trader.cli._load_prices", return_value=prices):
            exit_code = main(["backtest", "--config", "config.json", "--strategy", "dual_momentum"])
        self.assertEqual(exit_code, 0)

    def test_optimize_parser_builds(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["optimize", "--config", "config.json", "--strategy", "dual_momentum"])
        self.assertEqual(args.command, "optimize")


if __name__ == "__main__":
    unittest.main()
