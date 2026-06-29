from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from .provider_base import DataProviderBase


class MockProvider(DataProviderBase):
    def fetch_history(
        self,
        ticker: str,
        start_date: str,
        end_date: str | None,
        interval: str,
        auto_adjust: bool,
    ) -> pd.DataFrame:
        if interval != "1d":
            raise ValueError("MockProvider currently supports only 1d interval")
        end = pd.Timestamp(end_date) if end_date else pd.Timestamp.today().normalize()
        dates = pd.bdate_range(start=start_date, end=end)
        if len(dates) == 0:
            raise ValueError(f"No mock dates generated for {ticker}")
        seed = int(hashlib.sha256(ticker.encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        base = 80 + (seed % 200)
        drift = rng.normal(0.0005, 0.002, len(dates))
        vol = rng.normal(0, 0.015, len(dates))
        returns = drift + vol
        close = base * np.exp(np.cumsum(returns))
        open_ = close * (1 + rng.normal(0, 0.004, len(dates)))
        high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.02, len(dates)))
        low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.02, len(dates)))
        volume = rng.integers(2_000_000, 25_000_000, len(dates))
        return pd.DataFrame(
            {
                "Date": dates,
                "Open": open_.round(2),
                "High": high.round(2),
                "Low": low.round(2),
                "Close": close.round(2),
                "Volume": volume,
            }
        )
