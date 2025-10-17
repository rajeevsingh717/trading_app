"""
Unit tests for technical indicators module.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.indicators import TechnicalIndicators, calculate_indicators


@pytest.fixture
def sample_data():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='5min')
    np.random.seed(42)

    # Generate realistic price data
    price = 100.0
    prices = []
    for _ in range(100):
        price += np.random.randn() * 0.5
        prices.append(max(price, 1))  # Ensure positive prices

    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p + abs(np.random.randn() * 0.3) for p in prices],
        'low': [p - abs(np.random.randn() * 0.3) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 100)
    })

    return df


class TestTechnicalIndicators:
    """Test technical indicator calculations."""

    def test_add_sma(self, sample_data):
        """Test SMA calculation."""
        indicators = TechnicalIndicators()
        df = indicators.add_sma(sample_data.copy(), period=20)

        assert 'sma_20' in df.columns
        assert df['sma_20'].notna().sum() >= 80  # Should have values after warmup
        assert df.iloc[19]['sma_20'] > 0  # Should be positive

    def test_add_rsi(self, sample_data):
        """Test RSI calculation."""
        indicators = TechnicalIndicators()
        df = indicators.add_rsi(sample_data.copy(), period=14)

        assert 'rsi' in df.columns
        # RSI should be between 0 and 100
        assert (df['rsi'] >= 0).all()
        assert (df['rsi'] <= 100).all()

    def test_add_atr(self, sample_data):
        """Test ATR calculation."""
        indicators = TechnicalIndicators()
        df = indicators.add_atr(sample_data.copy(), period=14)

        assert 'atr' in df.columns
        # ATR should be positive
        assert (df['atr'].dropna() > 0).all()

    def test_add_volume_ma(self, sample_data):
        """Test volume MA calculation."""
        indicators = TechnicalIndicators()
        df = indicators.add_volume_ma(sample_data.copy(), period=20)

        assert 'volume_ma' in df.columns
        assert (df['volume_ma'].dropna() > 0).all()

    def test_add_all_indicators(self, sample_data):
        """Test adding all indicators at once."""
        df = calculate_indicators(sample_data.copy())

        # Check all expected columns exist
        assert 'sma_50' in df.columns
        assert 'rsi' in df.columns
        assert 'atr' in df.columns
        assert 'volume_ma' in df.columns
        assert 'volume_ratio' in df.columns

    def test_validate_indicators(self, sample_data):
        """Test indicator validation."""
        df = calculate_indicators(sample_data.copy())
        validation = TechnicalIndicators.validate_indicators(df)

        assert validation['valid'] is True
        assert len(validation['indicators_present']) > 0
        assert 'sma_50' in validation['indicators_present']

    def test_bollinger_bands(self, sample_data):
        """Test Bollinger Bands calculation."""
        indicators = TechnicalIndicators()
        df = indicators.add_bollinger_bands(sample_data.copy(), period=20)

        assert 'bb_upper' in df.columns
        assert 'bb_middle' in df.columns
        assert 'bb_lower' in df.columns

        # Upper should be greater than middle, middle greater than lower
        valid_rows = df.dropna()
        assert (valid_rows['bb_upper'] >= valid_rows['bb_middle']).all()
        assert (valid_rows['bb_middle'] >= valid_rows['bb_lower']).all()

    def test_macd(self, sample_data):
        """Test MACD calculation."""
        indicators = TechnicalIndicators()
        df = indicators.add_macd(sample_data.copy())

        assert 'macd' in df.columns
        assert 'macd_signal' in df.columns
        assert 'macd_histogram' in df.columns

        # Histogram should be MACD - Signal
        valid_rows = df.dropna()
        calculated_histogram = valid_rows['macd'] - valid_rows['macd_signal']
        assert np.allclose(valid_rows['macd_histogram'], calculated_histogram, rtol=1e-5)


class TestIndicatorEdgeCases:
    """Test edge cases for indicators."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame()
        indicators = TechnicalIndicators()

        # Should not raise an error
        try:
            result = indicators.add_sma(df)
            assert len(result) == 0
        except Exception as e:
            pytest.fail(f"Empty DataFrame should be handled gracefully: {e}")

    def test_insufficient_data(self):
        """Test with insufficient data for indicators."""
        # Create data with only 10 rows (less than most indicator periods)
        df = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=10, freq='5min'),
            'close': [100 + i for i in range(10)],
            'high': [101 + i for i in range(10)],
            'low': [99 + i for i in range(10)],
            'volume': [1000000] * 10
        })

        indicators = TechnicalIndicators()
        result = indicators.add_sma(df, period=50)

        # Should have NaN for insufficient data
        assert result['sma_50'].isna().all()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
