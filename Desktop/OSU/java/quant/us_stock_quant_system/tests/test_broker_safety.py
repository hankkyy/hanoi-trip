import pytest

from src.brokers.safety import BrokerSafetyError, BrokerSafetyState, validate_broker_safety_config


def _state(**overrides):
    base = {
        "broker_active": "dry_run",
        "host": "127.0.0.1",
        "port": 7497,
        "client_id": 101,
        "dry_run": True,
        "paper_trading": True,
        "live_trading": False,
        "confirm_live_trading": "",
        "auto_submit_paper_orders": False,
        "allow_market_orders": False,
        "max_order_value_usd": 3000.0,
        "max_daily_order_count": 10,
    }
    base.update(overrides)
    return BrokerSafetyState(**base)


def test_live_trading_false_blocks_live_port():
    with pytest.raises(BrokerSafetyError):
        validate_broker_safety_config(_state(port=7496))


def test_paper_trading_true_blocks_live_broker():
    with pytest.raises(BrokerSafetyError):
        validate_broker_safety_config(_state(broker_active="ibkr_live"))


def test_market_order_blocked():
    with pytest.raises(BrokerSafetyError):
        validate_broker_safety_config(_state(), order_value=100, order_type="MARKET", order_count_today=0)


def test_order_value_limit():
    with pytest.raises(BrokerSafetyError):
        validate_broker_safety_config(_state(), order_value=4000, order_type="LIMIT", order_count_today=0)
