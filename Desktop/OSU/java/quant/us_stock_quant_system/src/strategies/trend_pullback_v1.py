from __future__ import annotations

import pandas as pd

from .base import StrategyBase


class TrendPullbackV1(StrategyBase):
    name = "trend_pullback_v1"

    def generate_signal(self, row: pd.Series, market_score: float) -> bool:
        return bool(
            market_score >= 15
            and row.get("score", 0) >= 80
            and row.get("Close", 0) > row.get("SMA200", float("inf"))
            and row.get("Close", 0) > row.get("Ichimoku Cloud Top", float("inf"))
            and 45 <= row.get("RSI14", 0) <= 70
            and row.get("MACD", 0) > row.get("MACD Signal", 0)
            and row.get("stop_distance_pct", 1) <= 0.12
            and row.get("ATR14", 0) / max(row.get("Close", 1), 1e-9) <= 0.08
        )
