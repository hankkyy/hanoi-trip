import pandas as pd

from src.risk.position_sizing import calculate_position_size


def _risk_config():
    return {
        "account": {"account_equity": 20000},
        "risk": {
            "risk_per_trade_pct": 0.005,
            "max_position_pct": 0.15,
            "max_order_value_usd": 3000,
            "allow_fractional_shares": True,
            "semiconductor_max_positions": 2,
        },
    }


def test_position_size_respects_caps():
    row = pd.Series({"ticker": "AAPL", "close": 100, "suggested_stop": 94, "stop_distance_pct": 0.06})
    result = calculate_position_size(row, _risk_config(), "Technology")
    assert result.capped_position_value <= 3000
    assert result.estimated_risk_usd <= 100


def test_stop_distance_too_wide_blocks_buy():
    row = pd.Series({"ticker": "AAPL", "close": 100, "suggested_stop": 80, "stop_distance_pct": 0.2})
    result = calculate_position_size(row, _risk_config(), "Technology")
    assert result.position_allowed is False
