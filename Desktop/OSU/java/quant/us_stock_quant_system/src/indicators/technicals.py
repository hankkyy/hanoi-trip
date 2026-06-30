from __future__ import annotations

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD, SMAIndicator
from ta.volatility import AverageTrueRange, BollingerBands

from .fibonacci import add_fibonacci_levels
from .ichimoku import add_ichimoku


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    close = result["Close"]
    high = result["High"]
    low = result["Low"]

    result["SMA20"] = SMAIndicator(close, window=20).sma_indicator()
    result["SMA50"] = SMAIndicator(close, window=50).sma_indicator()
    result["SMA200"] = SMAIndicator(close, window=200).sma_indicator()
    result["EMA12"] = EMAIndicator(close, window=12).ema_indicator()
    result["EMA26"] = EMAIndicator(close, window=26).ema_indicator()

    macd = MACD(close, window_fast=12, window_slow=26, window_sign=9)
    result["MACD"] = macd.macd()
    result["MACD Signal"] = macd.macd_signal()
    result["MACD Histogram"] = macd.macd_diff()

    result["RSI14"] = RSIIndicator(close, window=14).rsi()

    bb = BollingerBands(close, window=20, window_dev=2)
    result["Bollinger Middle"] = bb.bollinger_mavg()
    result["Bollinger Upper"] = bb.bollinger_hband()
    result["Bollinger Lower"] = bb.bollinger_lband()

    atr = AverageTrueRange(high, low, close, window=14)
    result["ATR14"] = atr.average_true_range()

    result = add_ichimoku(result)
    result["20D High"] = high.rolling(20).max()
    result["20D Low"] = low.rolling(20).min()
    result["60D High"] = high.rolling(60).max()
    result["60D Low"] = low.rolling(60).min()
    result = add_fibonacci_levels(result, lookback=60)
    result["20D Return"] = close.pct_change(20)
    result["60D Return"] = close.pct_change(60)
    return result
