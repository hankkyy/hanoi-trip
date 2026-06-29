from src.data.mock_provider import MockProvider
from src.indicators.technicals import add_indicators


def test_indicator_pipeline_for_backtest_like_data():
    df = MockProvider().fetch_history("NVDA", "2018-01-01", "2024-12-31", "1d", True)
    out = add_indicators(df)
    assert out["SMA200"].notna().sum() > 0
    assert out["Ichimoku Cloud Top"].notna().sum() > 0
