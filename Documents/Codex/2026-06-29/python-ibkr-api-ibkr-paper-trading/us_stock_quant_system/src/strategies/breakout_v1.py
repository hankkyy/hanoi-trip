from __future__ import annotations

import pandas as pd

from .base import StrategyBase


class BreakoutV1(StrategyBase):
    name = "breakout_v1"

    def generate_signal(self, row: pd.Series, market_score: float) -> bool:
        return bool(
            market_score >= 15
            and row.get("Close", 0) >= row.get("20D High", float("inf")) * 0.99
            and row.get("MACD", 0) > row.get("MACD Signal", 0)
        )
