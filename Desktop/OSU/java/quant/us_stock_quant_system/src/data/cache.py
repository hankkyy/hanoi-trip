from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils.paths import CACHE_DIR


def cache_path_for_ticker(ticker: str) -> Path:
    return CACHE_DIR / f"{ticker}.csv"


def save_ticker_data(ticker: str, df: pd.DataFrame) -> Path:
    path = cache_path_for_ticker(ticker)
    df.to_csv(path, index=False)
    return path


def load_ticker_data(ticker: str) -> pd.DataFrame:
    path = cache_path_for_ticker(ticker)
    if not path.exists():
        raise FileNotFoundError(f"Cached data not found for {ticker}: {path}")
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df
