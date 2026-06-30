from __future__ import annotations

import pandas as pd


def add_ichimoku(df: pd.DataFrame) -> pd.DataFrame:
    high = df["High"]
    low = df["Low"]
    tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
    kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
    senkou_a = (tenkan + kijun) / 2
    senkou_b = (high.rolling(52).max() + low.rolling(52).min()) / 2
    df["Ichimoku Tenkan"] = tenkan
    df["Ichimoku Kijun"] = kijun
    df["Ichimoku Senkou A"] = senkou_a
    df["Ichimoku Senkou B"] = senkou_b
    df["Ichimoku Cloud Top"] = pd.concat([senkou_a, senkou_b], axis=1).max(axis=1)
    df["Ichimoku Cloud Bottom"] = pd.concat([senkou_a, senkou_b], axis=1).min(axis=1)
    return df
