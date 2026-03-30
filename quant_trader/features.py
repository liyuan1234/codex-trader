from __future__ import annotations

import numpy as np
import pandas as pd


def compute_rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def build_feature_frame(prices: pd.Series) -> pd.DataFrame:
    returns = prices.pct_change()
    volatility_20 = returns.rolling(20).std() * np.sqrt(252)
    ma_10 = prices.rolling(10).mean()
    ma_20 = prices.rolling(20).mean()
    ma_50 = prices.rolling(50).mean()
    ma_200 = prices.rolling(200).mean()
    momentum_21 = prices.pct_change(21)
    momentum_63 = prices.pct_change(63)
    momentum_126 = prices.pct_change(126)
    zscore_20 = (prices - ma_20) / prices.rolling(20).std()
    breakout_20 = prices / prices.rolling(20).max() - 1
    rsi_14 = compute_rsi(prices, window=14)

    features = pd.DataFrame(
        {
            "ret_1d": returns,
            "ret_5d": prices.pct_change(5),
            "ret_21d": momentum_21,
            "ret_63d": momentum_63,
            "ret_126d": momentum_126,
            "vol_20": volatility_20,
            "ma10_ratio": prices / ma_10 - 1,
            "ma20_ratio": prices / ma_20 - 1,
            "ma50_ratio": prices / ma_50 - 1,
            "ma200_ratio": prices / ma_200 - 1,
            "zscore_20": zscore_20,
            "breakout_20": breakout_20,
            "rsi_14": rsi_14 / 100.0,
        },
        index=prices.index,
    )
    return features.replace([np.inf, -np.inf], np.nan)


def make_ml_dataset(prices: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    features = build_feature_frame(prices)
    target = (prices.pct_change().shift(-1) > 0).astype(int)
    dataset = features.join(target.rename("target")).dropna()
    return dataset.drop(columns=["target"]), dataset["target"]
