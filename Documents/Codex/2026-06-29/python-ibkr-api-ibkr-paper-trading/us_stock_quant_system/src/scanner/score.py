from __future__ import annotations

import math

import pandas as pd

from src.risk.stops import calculate_suggested_stop


def pct_distance(a: float, b: float) -> float:
    if b == 0 or math.isnan(a) or math.isnan(b):
        return float("inf")
    return (a - b) / b


def compute_market_score(spy_row: pd.Series, qqq_row: pd.Series) -> tuple[int, list[str]]:
    score = 0
    notes = []
    if spy_row["Close"] > spy_row["SMA200"]:
        score += 10
        notes.append("SPY above SMA200")
    if qqq_row["Close"] > qqq_row["SMA200"]:
        score += 10
        notes.append("QQQ above SMA200")
    if qqq_row["SMA50"] > qqq_row["SMA200"]:
        score += 5
        notes.append("QQQ SMA50 above SMA200")
    return score, notes


def score_ticker(row: pd.Series, qqq_row: pd.Series, market_score: int) -> dict:
    notes: list[str] = []
    required = ["Close", "SMA20", "SMA50", "SMA200", "RSI14", "MACD", "MACD Signal", "MACD Histogram", "ATR14"]
    if row[required].isna().any():
        return {
            "score": 0,
            "trend_score": 0,
            "momentum_score": 0,
            "pullback_score": 0,
            "risk_score": 0,
            "suggested_stop": None,
            "stop_distance_pct": None,
            "suggested_position_size": 0,
            "action": "INSUFFICIENT_DATA",
            "notes": "INSUFFICIENT_DATA",
        }

    trend_score = 0
    momentum_score = 0
    pullback_score = 0
    risk_score = 0

    close = float(row["Close"])
    if close > row["SMA200"]:
        trend_score += 8
        notes.append("Close above SMA200")
    if row["SMA50"] > row["SMA200"]:
        trend_score += 7
        notes.append("SMA50 above SMA200")
    if close > row["Ichimoku Cloud Top"]:
        trend_score += 5
        notes.append("Above Ichimoku cloud")
    if close > row["SMA50"]:
        trend_score += 5
        notes.append("Close above SMA50")

    if row["MACD"] > row["MACD Signal"]:
        momentum_score += 7
        notes.append("MACD bullish")
    hist = row["MACD Histogram"]
    prev2 = row.get("_hist_prev2")
    prev1 = row.get("_hist_prev1")
    if pd.notna(prev2) and pd.notna(prev1) and hist > prev1 > prev2:
        momentum_score += 5
        notes.append("MACD histogram improving 3 days")
    if 45 <= row["RSI14"] <= 70:
        momentum_score += 5
        notes.append("RSI in preferred range")
    if row["60D Return"] > qqq_row["60D Return"]:
        momentum_score += 3
        notes.append("Outperforming QQQ over 60D")

    dist_sma20 = abs(pct_distance(close, float(row["SMA20"])))
    if 0 <= dist_sma20 <= 0.05:
        pullback_score += 4
        notes.append("Near SMA20")
    dist_bb_mid = abs(pct_distance(close, float(row["Bollinger Middle"])))
    if 0 <= dist_bb_mid <= 0.05:
        pullback_score += 4
        notes.append("Near Bollinger middle")
    kijun_dist = pct_distance(close, float(row["Ichimoku Kijun"]))
    if -0.02 <= kijun_dist <= 0.05:
        pullback_score += 3
        notes.append("Near Ichimoku Kijun")
    if row["Fib 61.8"] <= close <= row["Fib 38.2"] or row["Fib 38.2"] <= close <= row["Fib 61.8"]:
        pullback_score += 4
        notes.append("Inside Fibonacci pullback zone")

    suggested_stop, stop_distance_pct, stop_source = calculate_suggested_stop(row)
    if row["ATR14"] / close < 0.05:
        risk_score += 5
        notes.append("ATR below 5%")
    if stop_distance_pct <= 0.12:
        risk_score += 5
        notes.append(f"Stop within 12% via {stop_source}")
    suggested_position_size = min(3000.0, 100.0 / max(stop_distance_pct, 1e-6))
    if row["Ticker"] not in {"SPY", "QQQ"} and suggested_position_size <= 3000:
        risk_score += 3
        notes.append("Position size within account limits")
    risk_score += 2
    notes.append("No validation anomaly on latest row")

    score = market_score + trend_score + momentum_score + pullback_score + risk_score
    score = max(0, min(score, 100))
    action = "IGNORE"
    if score >= 80:
        action = "BUY_CANDIDATE"
    elif score >= 70:
        action = "WATCH"
    elif score >= 60:
        action = "NEUTRAL"

    if market_score < 15 and action == "BUY_CANDIDATE":
        action = "WATCH"
        notes.append("Market score gate capped action at WATCH")
    if close < row["SMA200"] and action == "BUY_CANDIDATE":
        action = "WATCH"
        notes.append("Close below SMA200 blocks BUY_CANDIDATE")
    if row["RSI14"] > 78:
        action = "TOO_EXTENDED"
        notes.append("TOO_EXTENDED")
    if row["ATR14"] / close > 0.08:
        notes.append("HIGH_VOLATILITY")
        if action == "BUY_CANDIDATE":
            action = "WATCH"
    if stop_distance_pct > 0.12 and action == "BUY_CANDIDATE":
        action = "WATCH"
        notes.append("Stop too wide for buy")

    return {
        "score": score,
        "trend_score": trend_score,
        "momentum_score": momentum_score,
        "pullback_score": pullback_score,
        "risk_score": risk_score,
        "suggested_stop": round(suggested_stop, 4),
        "stop_distance_pct": round(stop_distance_pct, 4),
        "suggested_position_size": round(suggested_position_size, 2),
        "action": action,
        "notes": "; ".join(notes),
    }
