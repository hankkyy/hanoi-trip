import pandas as pd

from src.data.mock_provider import MockProvider
from src.data.validators import validate_ohlcv


def test_mock_provider_generates_required_columns():
    df = MockProvider().fetch_history("AAPL", "2020-01-01", "2020-12-31", "1d", True)
    assert not df.empty
    for column in ["Open", "High", "Low", "Close", "Volume"]:
        assert column in df.columns


def test_validation_passes_for_mock_data():
    df = MockProvider().fetch_history("MSFT", "2020-01-01", "2020-12-31", "1d", True)
    result = validate_ohlcv(df)
    assert result.passed is True
