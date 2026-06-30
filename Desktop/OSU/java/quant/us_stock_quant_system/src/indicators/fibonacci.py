from __future__ import annotations

import pandas as pd


def add_fibonacci_levels(df: pd.DataFrame, lookback: int = 60) -> pd.DataFrame:
    rolling_high = df["High"].rolling(lookback).max()
    rolling_low = df["Low"].rolling(lookback).min()
    spread = rolling_high - rolling_low
    df["Fib 38.2"] = rolling_high - spread * 0.382
    df["Fib 50"] = rolling_high - spread * 0.5
    df["Fib 61.8"] = rolling_high - spread * 0.618
    return df
