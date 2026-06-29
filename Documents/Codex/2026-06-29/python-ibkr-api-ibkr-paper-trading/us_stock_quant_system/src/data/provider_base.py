from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class DataProviderBase(ABC):
    @abstractmethod
    def fetch_history(
        self,
        ticker: str,
        start_date: str,
        end_date: str | None,
        interval: str,
        auto_adjust: bool,
    ) -> pd.DataFrame:
        raise NotImplementedError
