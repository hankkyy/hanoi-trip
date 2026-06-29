from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Trade:
    ticker: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    shares: float
    pnl: float
    holding_days: int
