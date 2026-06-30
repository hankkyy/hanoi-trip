from __future__ import annotations

from abc import ABC, abstractmethod

from .order_models import OrderModel


class BrokerBase(ABC):
    @abstractmethod
    def connect(self): ...

    @abstractmethod
    def disconnect(self): ...

    @abstractmethod
    def get_account(self): ...

    @abstractmethod
    def get_positions(self): ...

    @abstractmethod
    def get_orders(self): ...

    @abstractmethod
    def get_market_price(self, ticker: str): ...

    @abstractmethod
    def place_order(self, order: OrderModel): ...

    @abstractmethod
    def cancel_order(self, order_id): ...

    @abstractmethod
    def close_position(self, ticker: str): ...
