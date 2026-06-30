from __future__ import annotations

import pandas as pd

from src.data.cache import load_ticker_data
from .score import compute_market_score, score_ticker


OUTPUT_COLUMNS = [
    "ticker", "date", "close", "score", "market_score", "trend_score", "momentum_score",
    "pullback_score", "risk_score", "RSI14", "MACD", "MACD Signal", "MACD Histogram",
    "ATR14", "SMA20", "SMA50", "SMA200", "Ichimoku Cloud Top", "Ichimoku Kijun",
    "Fib 38.2", "Fib 50", "Fib 61.8", "suggested_stop", "stop_distance_pct",
    "suggested_position_size", "action", "notes",
]


def run_scan(universe_cfg: dict) -> tuple[pd.DataFrame, dict]:
    tickers = universe_cfg["universe"]["benchmark"] + universe_cfg["universe"]["stocks"]
    frames = {ticker: load_ticker_data(ticker) for ticker in tickers}
    spy_row = frames["SPY"].iloc[-1]
    qqq_row = frames["QQQ"].iloc[-1]
    market_score, market_notes = compute_market_score(spy_row, qqq_row)

    results = []
    for ticker in tickers:
        df = frames[ticker].copy()
        df["Ticker"] = ticker
        latest = df.iloc[-1].copy()
        latest["_hist_prev1"] = df["MACD Histogram"].iloc[-2] if len(df) > 1 else pd.NA
        latest["_hist_prev2"] = df["MACD Histogram"].iloc[-3] if len(df) > 2 else pd.NA
        scored = score_ticker(latest, qqq_row, market_score)
        row = {
            "ticker": ticker,
            "date": pd.to_datetime(latest["Date"]).strftime("%Y-%m-%d"),
            "close": latest["Close"],
            "market_score": market_score,
            "RSI14": latest.get("RSI14"),
            "MACD": latest.get("MACD"),
            "MACD Signal": latest.get("MACD Signal"),
            "MACD Histogram": latest.get("MACD Histogram"),
            "ATR14": latest.get("ATR14"),
            "SMA20": latest.get("SMA20"),
            "SMA50": latest.get("SMA50"),
            "SMA200": latest.get("SMA200"),
            "Ichimoku Cloud Top": latest.get("Ichimoku Cloud Top"),
            "Ichimoku Kijun": latest.get("Ichimoku Kijun"),
            "Fib 38.2": latest.get("Fib 38.2"),
            "Fib 50": latest.get("Fib 50"),
            "Fib 61.8": latest.get("Fib 61.8"),
        }
        row.update(scored)
        results.append(row)
    scan_df = pd.DataFrame(results)[OUTPUT_COLUMNS].sort_values("score", ascending=False).reset_index(drop=True)
    market_context = {"market_score": market_score, "notes": market_notes}
    return scan_df, market_context
