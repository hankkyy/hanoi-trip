from src.data.mock_provider import MockProvider
from src.indicators.technicals import add_indicators


def test_indicator_columns_exist():
    df = MockProvider().fetch_history("AAPL", "2020-01-01", "2022-12-31", "1d", True)
    out = add_indicators(df)
    required = ["SMA20", "SMA50", "SMA200", "MACD", "MACD Signal", "RSI14", "ATR14", "Ichimoku Cloud Top", "Fib 50"]
    for column in required:
        assert column in out.columns
    assert out["RSI14"].notna().sum() > 0
    assert out["MACD"].notna().sum() > 0
    assert out["ATR14"].notna().sum() > 0
