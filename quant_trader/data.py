from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf


def load_prices_from_csv(path: str | Path) -> pd.DataFrame:
    csv_path = Path(path).expanduser().resolve()
    frame = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    if frame.empty:
        raise RuntimeError(f"No data found in CSV cache: {csv_path}")
    return frame.sort_index().ffill().dropna(how="all")


def download_prices(
    tickers: list[str],
    start: str,
    end: str | None = None,
    interval: str = "1d",
) -> pd.DataFrame:
    """Download adjusted close data from Yahoo Finance."""

    data = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=True,
        progress=False,
        group_by="ticker",
        threads=True,
    )
    if data.empty:
        raise RuntimeError("No historical data returned from yfinance. Check network access or set data_cache_path in config.json.")

    if isinstance(data.columns, pd.MultiIndex):
        closes = data.xs("Close", axis=1, level=1)
    else:
        closes = data.rename(columns={"Close": tickers[0] if len(tickers) == 1 else "Close"})

    closes = closes.sort_index().dropna(how="all")
    return closes.ffill().dropna(how="all")
