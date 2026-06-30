from __future__ import annotations

from pathlib import Path

import pandas as pd
from rich.console import Console

from src.utils.dates import today_str
from src.utils.paths import LOGS_DIR, REPORTS_DIR
from .broker_base import BrokerBase
from .order_models import OrderModel
from .safety import BrokerSafetyState, count_today_orders, validate_broker_safety_config


class DryRunBroker(BrokerBase):
    def __init__(self, safety_state: BrokerSafetyState):
        self.console = Console()
        self.safety_state = safety_state
        self.log_path = LOGS_DIR / "orders_dry_run.csv"
        self.report_path = REPORTS_DIR / "orders" / f"{today_str()}_dry_run_orders.csv"

    def connect(self):
        self.console.print("DRY RUN ONLY - NO LIVE ORDERS SENT")
        return True

    def disconnect(self):
        return True

    def get_account(self):
        return {"mode": "dry_run", "cash": None}

    def get_positions(self):
        return []

    def get_orders(self):
        if self.log_path.exists():
            return pd.read_csv(self.log_path).to_dict(orient="records")
        return []

    def get_market_price(self, ticker: str):
        return None

    def place_order(self, order: OrderModel):
        order_value = (order.limit_price or 0) * order.quantity
        today_count = count_today_orders(self.log_path)
        validate_broker_safety_config(self.safety_state, order_value=order_value, order_type=order.order_type, order_count_today=today_count)
        record = order.model_dump() | {"date": today_str(), "status": "DRY_RUN_ONLY"}
        df = pd.DataFrame([record])
        for path in [self.log_path, self.report_path]:
            if path.exists():
                old = pd.read_csv(path)
                new = pd.concat([old, df], ignore_index=True)
            else:
                new = df
            new.to_csv(path, index=False)
        self.console.print("DRY RUN ONLY - NO LIVE ORDERS SENT")
        self.console.print(record)
        return record

    def cancel_order(self, order_id):
        return {"order_id": order_id, "status": "cancelled_dry_run"}

    def close_position(self, ticker: str):
        return {"ticker": ticker, "status": "close_position_dry_run"}
