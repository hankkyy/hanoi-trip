from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field

from .broker_base import BrokerBase
from .order_models import OrderModel
from .safety import BrokerSafetyState, count_today_orders, validate_broker_safety_config
from src.utils.paths import LOGS_DIR

try:
    from ibapi.client import EClient
    from ibapi.contract import Contract
    from ibapi.order import Order
    from ibapi.wrapper import EWrapper
except Exception:  # pragma: no cover
    EClient = object
    EWrapper = object
    Contract = object
    Order = object


@dataclass
class IBKRState:
    connected: bool = False
    next_order_id: int | None = None
    account_summary: dict = field(default_factory=dict)
    positions: list[dict] = field(default_factory=list)
    open_orders: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class _IBWrapper(EWrapper):
    def __init__(self, state: IBKRState):
        super().__init__()
        self.state = state
        self.done_queue = queue.Queue()

    def nextValidId(self, orderId):
        self.state.next_order_id = orderId

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        self.state.errors.append(f"{errorCode}: {errorString}")

    def managedAccounts(self, accountsList):
        self.state.account_summary["managed_accounts"] = accountsList

    def accountSummary(self, reqId, account, tag, value, currency):
        self.state.account_summary.setdefault(account, {})[tag] = value

    def accountSummaryEnd(self, reqId):
        self.done_queue.put(("account_summary", True))

    def position(self, account, contract, position, avgCost):
        self.state.positions.append(
            {
                "account": account,
                "ticker": contract.symbol,
                "position": position,
                "avg_cost": avgCost,
            }
        )

    def positionEnd(self):
        self.done_queue.put(("positions", True))

    def openOrder(self, orderId, contract, order, orderState):
        self.state.open_orders.append(
            {
                "order_id": orderId,
                "ticker": contract.symbol,
                "action": order.action,
                "quantity": order.totalQuantity,
                "order_type": order.orderType,
                "status": getattr(orderState, "status", "UNKNOWN"),
            }
        )

    def openOrderEnd(self):
        self.done_queue.put(("open_orders", True))


class _IBClient(EClient):
    def __init__(self, wrapper):
        super().__init__(wrapper)


class IBKRBroker(BrokerBase):
    def __init__(self, safety_state: BrokerSafetyState):
        self.safety_state = safety_state
        self.state = IBKRState()
        self.wrapper = _IBWrapper(self.state)
        self.client = _IBClient(self.wrapper)
        self.thread: threading.Thread | None = None
        self.log_path = LOGS_DIR / "orders_ibkr_paper.csv"

    def connect(self):
        validate_broker_safety_config(self.safety_state)
        try:
            self.client.connect(self.safety_state.host, self.safety_state.port, self.safety_state.client_id)
            self.thread = threading.Thread(target=self.client.run, daemon=True)
            self.thread.start()
            time.sleep(1.5)
            self.state.connected = self.client.isConnected()
            if not self.state.connected:
                if self.state.errors:
                    raise RuntimeError("; ".join(self.state.errors))
                raise RuntimeError("IBKR connection failed. Check TWS/Gateway, API settings, host/port, client_id.")
            return True
        except Exception as exc:
            self.state.connected = False
            raise RuntimeError(
                f"IBKR connection failed: {exc}. Check whether TWS/IB Gateway is running, API is enabled, the paper port is correct, client_id is unused, and 'Enable ActiveX and Socket Clients' is enabled."
            ) from exc

    def disconnect(self):
        if self.client.isConnected():
            self.client.disconnect()
        self.state.connected = False
        return True

    def _wait_for(self, key: str, timeout: float = 5.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                name, ok = self.wrapper.done_queue.get(timeout=0.2)
                if name == key:
                    return ok
            except queue.Empty:
                continue
        return False

    def get_account(self):
        self.state.account_summary = {}
        self.client.reqManagedAccts()
        self.client.reqAccountSummary(9001, "All", "NetLiquidation,AvailableFunds")
        self._wait_for("account_summary")
        return self.state.account_summary

    def get_positions(self):
        self.state.positions = []
        self.client.reqPositions()
        self._wait_for("positions")
        return self.state.positions

    def get_orders(self):
        self.state.open_orders = []
        self.client.reqOpenOrders()
        self._wait_for("open_orders")
        return self.state.open_orders

    def get_market_price(self, ticker: str):
        return None

    def _build_contract(self, ticker: str):
        contract = Contract()
        contract.symbol = ticker
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    def place_order(self, order: OrderModel):
        if self.safety_state.dry_run:
            raise RuntimeError("DRY_RUN=true prevents sending paper or live orders")
        order_value = (order.limit_price or 0) * order.quantity
        today_count = count_today_orders(self.log_path)
        validate_broker_safety_config(self.safety_state, order_value=order_value, order_type=order.order_type, order_count_today=today_count)
        ib_order = Order()
        ib_order.action = order.side
        ib_order.orderType = "LMT" if order.order_type == "LIMIT" else "MKT"
        ib_order.totalQuantity = float(order.quantity)
        if order.limit_price is not None:
            ib_order.lmtPrice = float(order.limit_price)
        ib_order.tif = order.time_in_force
        order_id = self.state.next_order_id or 1
        self.client.placeOrder(order_id, self._build_contract(order.ticker), ib_order)
        self.state.next_order_id = order_id + 1
        return {"order_id": order_id, "status": "submitted", **order.model_dump()}

    def cancel_order(self, order_id):
        self.client.cancelOrder(order_id, "")
        return {"order_id": order_id, "status": "cancel_requested"}

    def close_position(self, ticker: str):
        return {"ticker": ticker, "status": "not_implemented"}

    def bracket_order(self, *args, **kwargs):
        raise NotImplementedError("Bracket order reserved for future version")
