from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class StrategyBase(ABC):
    name: str = "base"

    @abstractmethod
    def generate_signal(self, row: pd.Series, market_score: float) -> bool:
        raise NotImplementedError
