from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class OrderModel(BaseModel):
    ticker: str
    side: Literal["BUY", "SELL"]
    quantity: float = Field(gt=0)
    order_type: Literal["LIMIT", "MARKET"] = "LIMIT"
    limit_price: float | None = None
    stop_price: float | None = None
    time_in_force: str = "DAY"
    reason: str = ""
    strategy_name: str = "trend_pullback_v1"
    broker_mode: str = "dry_run"
    live_trading: bool = False
    paper_trading: bool = True
    dry_run: bool = True
