from src.brokers.dry_run_broker import DryRunBroker
from src.brokers.order_models import OrderModel
from src.brokers.safety import BrokerSafetyState


def test_dry_run_broker_logs_without_real_order():
    broker = DryRunBroker(BrokerSafetyState(
        broker_active="dry_run",
        host="127.0.0.1",
        port=7497,
        client_id=101,
        dry_run=True,
        paper_trading=True,
        live_trading=False,
        confirm_live_trading="",
        auto_submit_paper_orders=False,
        allow_market_orders=False,
        max_order_value_usd=3000.0,
        max_daily_order_count=10,
    ))
    broker.connect()
    result = broker.place_order(OrderModel(
        ticker="AAPL",
        side="BUY",
        quantity=1,
        order_type="LIMIT",
        limit_price=100,
    ))
    assert result["status"] == "DRY_RUN_ONLY"
