from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from .features import make_ml_dataset


def _cross_sectional_normalize(signal: pd.DataFrame, max_weight: float = 1.0) -> pd.DataFrame:
    gross = signal.abs().sum(axis=1).replace(0, np.nan)
    scaled = signal.div(gross, axis=0) * max_weight
    return scaled.fillna(0.0)


@dataclass
class DualMomentumStrategy:
    fast_window: int = 50
    slow_window: int = 200
    volatility_target: float = 0.18
    max_leverage: float = 1.0

    def generate(self, prices: pd.DataFrame) -> pd.DataFrame:
        fast = prices.rolling(self.fast_window).mean()
        slow = prices.rolling(self.slow_window).mean()
        raw_signal = (fast > slow).astype(float)
        vol = prices.pct_change().rolling(20).std() * np.sqrt(252)
        vol_scaled = self.volatility_target / vol.replace(0, np.nan)
        weights = (raw_signal * vol_scaled).clip(upper=self.max_leverage).fillna(0.0)
        return _cross_sectional_normalize(weights, max_weight=self.max_leverage)


@dataclass
class MeanReversionStrategy:
    lookback: int = 20
    entry_z: float = 1.5
    exit_z: float = 0.5
    max_leverage: float = 1.0

    def generate(self, prices: pd.DataFrame) -> pd.DataFrame:
        mean = prices.rolling(self.lookback).mean()
        std = prices.rolling(self.lookback).std()
        zscore = (prices - mean) / std.replace(0, np.nan)

        raw = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
        raw = raw.mask(zscore > self.entry_z, -1.0)
        raw = raw.mask(zscore < -self.entry_z, 1.0)
        raw = raw.mask(zscore.abs() < self.exit_z, 0.0)
        return _cross_sectional_normalize(raw.fillna(0.0), max_weight=self.max_leverage)


@dataclass
class MLClassifierStrategy:
    train_window: int = 252
    retrain_frequency: int = 21
    probability_threshold: float = 0.54
    max_weight: float = 1.0

    def _predict_series(self, prices: pd.Series) -> pd.Series:
        features, target = make_ml_dataset(prices)
        probabilities = pd.Series(index=features.index, dtype=float)

        for current_idx in range(self.train_window, len(features), self.retrain_frequency):
            train_slice = slice(current_idx - self.train_window, current_idx)
            model = HistGradientBoostingClassifier(max_depth=4, learning_rate=0.05, random_state=7)
            model.fit(features.iloc[train_slice], target.iloc[train_slice])

            next_end = min(current_idx + self.retrain_frequency, len(features))
            batch = features.iloc[current_idx:next_end]
            probabilities.iloc[current_idx:next_end] = model.predict_proba(batch)[:, 1]

        signal = (probabilities > self.probability_threshold).astype(float)
        signal = signal.replace(0.0, -1.0).where(probabilities.notna(), 0.0)
        return signal.reindex(prices.index).fillna(0.0)

    def generate(self, prices: pd.DataFrame) -> pd.DataFrame:
        raw = pd.DataFrame({ticker: self._predict_series(prices[ticker].dropna()) for ticker in prices.columns})
        return _cross_sectional_normalize(raw.fillna(0.0), max_weight=self.max_weight)


def build_strategy(name: str, params: dict) -> object:
    if name == "dual_momentum":
        return DualMomentumStrategy(**params)
    if name == "mean_reversion":
        return MeanReversionStrategy(**params)
    if name == "ml_classifier":
        return MLClassifierStrategy(**params)
    raise ValueError(f"Unknown strategy: {name}")
