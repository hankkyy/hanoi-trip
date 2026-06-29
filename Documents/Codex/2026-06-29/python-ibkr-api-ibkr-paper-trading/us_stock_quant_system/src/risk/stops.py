from __future__ import annotations

import pandas as pd


def calculate_suggested_stop(row: pd.Series, atr_multiplier: float = 1.8) -> tuple[float, float, str]:
    close = float(row["Close"])
    atr = float(row.get("ATR14", 0) or 0)
    atr_stop = close - atr_multiplier * atr
    swing_low = row.get("20D Low")
    source = "atr"
    if pd.notna(swing_low):
        swing_stop = float(swing_low) * 0.995
        suggested = min(atr_stop, swing_stop)
        source = "conservative_min(atr,swing_low)"
    else:
        suggested = atr_stop
    suggested = min(suggested, close * 0.97)
    stop_distance_pct = max((close - suggested) / close, 0.03)
    suggested = close * (1 - stop_distance_pct)
    return round(suggested, 4), round(stop_distance_pct, 4), source
