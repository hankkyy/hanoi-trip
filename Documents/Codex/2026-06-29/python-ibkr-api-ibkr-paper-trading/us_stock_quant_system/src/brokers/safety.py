from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


class BrokerSafetyError(RuntimeError):
    pass


@dataclass
class BrokerSafetyState:
    broker_active: str
    host: str
    port: int
    client_id: int
    dry_run: bool
    paper_trading: bool
    live_trading: bool
    confirm_live_trading: str
    auto_submit_paper_orders: bool
    allow_market_orders: bool
    max_order_value_usd: float
    max_daily_order_count: int


def build_broker_safety_state(configs: dict) -> BrokerSafetyState:
    broker_cfg = configs["broker"]
    env = configs["env"]
    ibkr_cfg = broker_cfg["ibkr"]
    safety_cfg = broker_cfg["safety"]
    return BrokerSafetyState(
        broker_active=broker_cfg["broker"]["active"],
        host=env["IBKR_HOST"],
        port=env["IBKR_PORT"],
        client_id=env["IBKR_CLIENT_ID"],
        dry_run=env["DRY_RUN"],
        paper_trading=env["PAPER_TRADING"],
        live_trading=env["LIVE_TRADING"],
        confirm_live_trading=env["CONFIRM_LIVE_TRADING"],
        auto_submit_paper_orders=env["AUTO_SUBMIT_PAPER_ORDERS"],
        allow_market_orders=env["ALLOW_MARKET_ORDERS"],
        max_order_value_usd=float(safety_cfg["max_order_value_usd"]),
        max_daily_order_count=int(safety_cfg["max_daily_order_count"]),
    )


def validate_broker_safety_config(state: BrokerSafetyState, order_value: float | None = None, order_type: str | None = None, order_count_today: int = 0) -> None:
    paper_ports = {7497, 4002}
    live_ports = {7496, 4001}
    if state.dry_run and state.live_trading:
        raise BrokerSafetyError("DRY_RUN=true conflicts with LIVE_TRADING=true")
    if state.paper_trading and state.broker_active == "ibkr_live":
        raise BrokerSafetyError("PAPER_TRADING=true cannot be used with broker.active=ibkr_live")
    if state.broker_active == "ibkr_live" and not state.live_trading:
        raise BrokerSafetyError("broker.active=ibkr_live requires LIVE_TRADING=true")
    if state.live_trading:
        if state.confirm_live_trading != "I_UNDERSTAND_THE_RISK":
            raise BrokerSafetyError("LIVE_TRADING=true requires explicit CONFIRM_LIVE_TRADING")
        if state.paper_trading or state.dry_run or state.broker_active != "ibkr_live":
            raise BrokerSafetyError("LIVE_TRADING=true requires PAPER_TRADING=false, DRY_RUN=false, broker.active=ibkr_live")
    if state.paper_trading and state.port not in paper_ports:
        raise BrokerSafetyError("PAPER_TRADING=true requires paper port 7497 or 4002")
    if not state.live_trading and state.port in live_ports:
        raise BrokerSafetyError("LIVE_TRADING=false cannot connect to live port 7496 or 4001")
    if order_type == "MARKET" and not state.allow_market_orders:
        raise BrokerSafetyError("Market orders are disabled")
    if order_value is not None and order_value > state.max_order_value_usd:
        raise BrokerSafetyError("Order value exceeds max_order_value_usd")
    if order_count_today >= state.max_daily_order_count:
        raise BrokerSafetyError("Daily order count limit exceeded")


def count_today_orders(log_path: Path) -> int:
    if not log_path.exists():
        return 0
    df = pd.read_csv(log_path)
    if "date" not in df.columns:
        return 0
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    return int((df["date"] == today).sum())
