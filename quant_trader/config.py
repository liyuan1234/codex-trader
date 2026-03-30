from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AppConfig:
    raw: dict[str, Any]

    @property
    def tickers(self) -> list[str]:
        return list(self.raw["tickers"])

    @property
    def benchmark(self) -> str:
        return str(self.raw["benchmark"])

    @property
    def start_date(self) -> str:
        return str(self.raw["start_date"])

    @property
    def end_date(self) -> str | None:
        value = self.raw.get("end_date")
        return None if value in (None, "") else str(value)

    @property
    def cash(self) -> float:
        return float(self.raw["cash"])

    @property
    def data_cache_path(self) -> str | None:
        value = self.raw.get("data_cache_path")
        return None if value in (None, "") else str(value)

    @property
    def transaction_cost_bps(self) -> float:
        return float(self.raw["transaction_cost_bps"])

    @property
    def slippage_bps(self) -> float:
        return float(self.raw["slippage_bps"])

    @property
    def strategies(self) -> dict[str, dict[str, Any]]:
        return dict(self.raw["strategies"])

    @property
    def paper_trading(self) -> dict[str, Any]:
        return dict(self.raw["paper_trading"])


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path).expanduser().resolve()
    with config_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return AppConfig(raw=raw)
