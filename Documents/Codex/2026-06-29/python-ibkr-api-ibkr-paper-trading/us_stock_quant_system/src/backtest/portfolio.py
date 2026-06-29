from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Position:
    ticker: str
    entry_date: str
    entry_price: float
    shares: float
    stop: float
    sector: str
    entry_risk: float


@dataclass
class Portfolio:
    cash: float
    positions: dict[str, Position] = field(default_factory=dict)
