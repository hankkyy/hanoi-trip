from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class PositionSizingResult:
    ticker: str
    estimated_entry: float
    suggested_stop: float
    stop_distance_pct: float
    risk_amount: float
    raw_position_value: float
    capped_position_value: float
    shares: float
    estimated_risk_usd: float
    position_allowed: bool
    block_reason: str


def calculate_position_size(
    row: pd.Series,
    risk_config: dict,
    sector: str,
    existing_positions: list[dict] | None = None,
) -> PositionSizingResult:
    existing_positions = existing_positions or []
    account_equity = float(risk_config["account"]["account_equity"])
    risk_per_trade_pct = float(risk_config["risk"]["risk_per_trade_pct"])
    max_position_pct = float(risk_config["risk"]["max_position_pct"])
    max_order_value_usd = float(risk_config["risk"]["max_order_value_usd"])
    allow_fractional = bool(risk_config["risk"]["allow_fractional_shares"])
    risk_amount = account_equity * risk_per_trade_pct
    close = float(row["close"] if "close" in row else row["Close"])
    stop_distance_pct = float(row["stop_distance_pct"])
    raw_position_value = risk_amount / max(stop_distance_pct, 1e-6)
    capped_position_value = min(raw_position_value, account_equity * max_position_pct, max_order_value_usd)
    shares = capped_position_value / close if close > 0 else 0
    if not allow_fractional:
        shares = int(shares)
    estimated_risk_usd = shares * close * stop_distance_pct
    block_reason = ""
    position_allowed = True
    if stop_distance_pct > 0.12:
        position_allowed = False
        block_reason = "STOP_TOO_WIDE"
    elif shares <= 0:
        position_allowed = False
        block_reason = "SHARES_ZERO"
    elif sector == "Semiconductor":
        semiconductor_count = sum(1 for p in existing_positions if p.get("sector") == "Semiconductor")
        if semiconductor_count >= int(risk_config["risk"]["semiconductor_max_positions"]):
            position_allowed = False
            block_reason = "SEMICONDUCTOR_LIMIT"
    return PositionSizingResult(
        ticker=row["ticker"] if "ticker" in row else row["Ticker"],
        estimated_entry=round(close, 4),
        suggested_stop=round(float(row["suggested_stop"]), 4),
        stop_distance_pct=round(stop_distance_pct, 4),
        risk_amount=round(risk_amount, 4),
        raw_position_value=round(raw_position_value, 4),
        capped_position_value=round(capped_position_value, 4),
        shares=round(float(shares), 4),
        estimated_risk_usd=round(float(estimated_risk_usd), 4),
        position_allowed=position_allowed,
        block_reason=block_reason,
    )
