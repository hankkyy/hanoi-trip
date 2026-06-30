import pandas as pd

from src.scanner.score import score_ticker


def _base_row():
    return pd.Series({
        "Ticker": "AAPL",
        "Close": 100,
        "SMA20": 98,
        "SMA50": 95,
        "SMA200": 90,
        "Ichimoku Cloud Top": 94,
        "Ichimoku Kijun": 97,
        "MACD": 2,
        "MACD Signal": 1,
        "MACD Histogram": 0.5,
        "_hist_prev1": 0.4,
        "_hist_prev2": 0.3,
        "RSI14": 60,
        "ATR14": 3,
        "60D Return": 0.12,
        "Bollinger Middle": 99,
        "Fib 38.2": 103,
        "Fib 50": 100,
        "Fib 61.8": 97,
        "20D Low": 92,
    })


def test_score_is_bounded():
    row = _base_row()
    qqq = row.copy()
    qqq["60D Return"] = 0.1
    scored = score_ticker(row, qqq, 25)
    assert 0 <= scored["score"] <= 100


def test_market_score_below_15_blocks_buy():
    row = _base_row()
    qqq = row.copy()
    scored = score_ticker(row, qqq, 10)
    assert scored["action"] != "BUY_CANDIDATE"


def test_rsi_above_78_blocks_buy():
    row = _base_row()
    row["RSI14"] = 79
    qqq = row.copy()
    scored = score_ticker(row, qqq, 25)
    assert scored["action"] != "BUY_CANDIDATE"
