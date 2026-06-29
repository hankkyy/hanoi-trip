from __future__ import annotations

import pandas as pd

from .provider_base import DataProviderBase


class YFinanceProvider(DataProviderBase):
    def fetch_history(
        self,
        ticker: str,
        start_date: str,
        end_date: str | None,
        interval: str,
        auto_adjust: bool,
    ) -> pd.DataFrame:
        import yfinance as yf

        data = yf.download(
            tickers=ticker,
            start=start_date,
            end=end_date,
            interval=interval,
            auto_adjust=auto_adjust,
            progress=False,
            threads=False,
        )
        if data.empty:
            raise ValueError(f"No data returned by yfinance for {ticker}")
        data = data.reset_index()
        if "Date" not in data.columns:
            raise ValueError(f"Missing Date column for {ticker}")
        data["Date"] = pd.to_datetime(data["Date"]).dt.tz_localize(None)
        return data
