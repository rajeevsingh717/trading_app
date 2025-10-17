"""
Unit tests for trading strategy module.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, time
import pytz
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from strategy.strategy_engine import TradingStrategy, Signal


@pytest.fixture
def strategy():
    """Create a strategy instance with default config."""
    return TradingStrategy()


@pytest.fixture
def valid_data():
    """Create valid market data that should trigger entry."""
    return pd.Series({
        'timestamp': datetime(2024, 1, 1, 11, 0),  # Within trading hours
        'close': 150.0,
        'volume': 1200000,
        'sma_50': 148.0,  # Price above SMA
        'rsi': 55.0,  # RSI in good range
        'atr': 1.5,  # Good volatility
        'volume_ma': 1000000  # Volume above average
    })


@pytest.fixture
def invalid_data_low_price():
    """Create data with price too low."""
    return pd.Series({
        'timestamp': datetime(2024, 1, 1, 11, 0),
        'close': 15.0,  # Below minimum $20
        'volume': 1200000,
        'sma_50': 14.0,
        'rsi': 55.0,
        'atr': 1.5,
        'volume_ma': 1000000
    })


class TestTradingStrategy:
    """Test trading strategy logic."""

    def test_strategy_initialization(self):
        """Test strategy initialization with default config."""
        strategy = TradingStrategy()

        assert strategy.min_stock_price == 20.0
        assert strategy.max_stock_price == 500.0
        assert strategy.rsi_lower == 40
        assert strategy.rsi_upper == 70
        assert strategy.stop_loss_pct == 1.0
        assert strategy.take_profit_pct == 1.5

    def test_strategy_custom_config(self):
        """Test strategy initialization with custom config."""
        config = {
            'min_stock_price': 50.0,
            'stop_loss_percent': 2.0,
            'take_profit_percent': 3.0
        }
        strategy = TradingStrategy(config)

        assert strategy.min_stock_price == 50.0
        assert strategy.stop_loss_pct == 2.0
        assert strategy.take_profit_pct == 3.0

    def test_entry_conditions_valid(self, strategy, valid_data):
        """Test entry conditions with valid data."""
        should_enter, reason = strategy.check_entry_conditions(
            'AAPL',
            valid_data,
            valid_data['timestamp']
        )

        assert should_enter is True
        assert 'Above SMA' in reason
        assert 'RSI' in reason

    def test_entry_conditions_low_price(self, strategy, invalid_data_low_price):
        """Test rejection due to low stock price."""
        should_enter, reason = strategy.check_entry_conditions(
            'PENNY',
            invalid_data_low_price,
            invalid_data_low_price['timestamp']
        )

        assert should_enter is False
        assert 'below minimum' in reason

    def test_entry_conditions_wrong_time(self, strategy, valid_data):
        """Test rejection outside trading hours."""
        # Before trading hours (9:00 AM)
        early_data = valid_data.copy()
        early_timestamp = datetime(2024, 1, 1, 9, 0)

        should_enter, reason = strategy.check_entry_conditions(
            'AAPL',
            early_data,
            early_timestamp
        )

        assert should_enter is False
        assert 'trading hours' in reason

    def test_entry_conditions_rsi_overbought(self, strategy, valid_data):
        """Test rejection when RSI is overbought."""
        data = valid_data.copy()
        data['rsi'] = 75.0  # Above upper bound of 70

        should_enter, reason = strategy.check_entry_conditions(
            'AAPL',
            data,
            data['timestamp']
        )

        assert should_enter is False
        assert 'RSI' in reason

    def test_entry_conditions_low_volume(self, strategy, valid_data):
        """Test rejection when volume is too low."""
        data = valid_data.copy()
        data['volume'] = 900000  # Below 1.2x of volume_ma (1,000,000)

        should_enter, reason = strategy.check_entry_conditions(
            'AAPL',
            data,
            data['timestamp']
        )

        assert should_enter is False
        assert 'Volume ratio' in reason

    def test_exit_stop_loss(self, strategy):
        """Test stop loss exit condition."""
        position = {
            'ticker': 'AAPL',
            'entry_price': 150.0,
            'quantity': 10
        }

        # Price drops 1% triggering stop loss
        should_exit, reason = strategy.check_exit_conditions(
            position,
            current_price=148.5,  # -1% loss
            timestamp=datetime(2024, 1, 1, 14, 0)
        )

        assert should_exit is True
        assert 'Stop Loss' in reason

    def test_exit_take_profit(self, strategy):
        """Test take profit exit condition."""
        position = {
            'ticker': 'AAPL',
            'entry_price': 150.0,
            'quantity': 10
        }

        # Price rises 1.5% triggering take profit
        should_exit, reason = strategy.check_exit_conditions(
            position,
            current_price=152.25,  # +1.5% profit
            timestamp=datetime(2024, 1, 1, 14, 0)
        )

        assert should_exit is True
        assert 'Take Profit' in reason

    def test_exit_time_stop(self, strategy):
        """Test time-based exit (end of day)."""
        position = {
            'ticker': 'AAPL',
            'entry_price': 150.0,
            'quantity': 10
        }

        # 3:55 PM ET - should close
        should_exit, reason = strategy.check_exit_conditions(
            position,
            current_price=150.50,
            timestamp=datetime(2024, 1, 1, 15, 55)
        )

        assert should_exit is True
        assert 'Time Stop' in reason

    def test_exit_trailing_stop(self, strategy):
        """Test trailing stop exit condition."""
        position = {
            'ticker': 'AAPL',
            'entry_price': 150.0,
            'quantity': 10
        }

        # Highest price was 152.0 (+1.33%), now at 151.25
        # Drawdown from high: (151.25 - 152.0) / 152.0 = -0.49%
        # Should trigger trailing stop at 0.5%
        should_exit, reason = strategy.check_exit_conditions(
            position,
            current_price=151.24,
            highest_price=152.0,
            timestamp=datetime(2024, 1, 1, 14, 0)
        )

        assert should_exit is True
        assert 'Trailing Stop' in reason

    def test_generate_signals(self, strategy):
        """Test signal generation."""
        # Create DataFrame with valid entry conditions
        df = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 11, 0)],
            'close': [150.0],
            'volume': [1200000],
            'sma_50': [148.0],
            'rsi': [55.0],
            'atr': [1.5],
            'volume_ma': [1000000]
        })

        signals = strategy.generate_signals('AAPL', df, current_positions=[])

        assert len(signals) == 1
        assert signals[0].ticker == 'AAPL'
        assert signals[0].signal_type == 'buy'
        assert signals[0].price == 150.0

    def test_no_signal_with_existing_position(self, strategy):
        """Test that no signal is generated if position already exists."""
        df = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 11, 0)],
            'close': [150.0],
            'volume': [1200000],
            'sma_50': [148.0],
            'rsi': [55.0],
            'atr': [1.5],
            'volume_ma': [1000000]
        })

        # Already have position in AAPL
        current_positions = [{'ticker': 'AAPL', 'quantity': 10}]

        signals = strategy.generate_signals('AAPL', df, current_positions=current_positions)

        assert len(signals) == 0

    def test_calculate_position_size(self, strategy):
        """Test position size calculation."""
        account_value = 10000.0
        stock_price = 150.0

        shares = strategy.calculate_position_size(account_value, stock_price)

        # Should be around $1000 worth / $150 = ~6 shares
        assert shares > 0
        assert shares * stock_price <= 1000.0 * 1.1  # Allow 10% margin

    def test_get_stop_loss_price(self, strategy):
        """Test stop loss price calculation."""
        entry_price = 150.0
        stop_loss = strategy.get_stop_loss_price(entry_price)

        # Should be 1% below entry
        expected = 150.0 * 0.99
        assert abs(stop_loss - expected) < 0.01

    def test_get_take_profit_price(self, strategy):
        """Test take profit price calculation."""
        entry_price = 150.0
        take_profit = strategy.get_take_profit_price(entry_price)

        # Should be 1.5% above entry
        expected = 150.0 * 1.015
        assert abs(take_profit - expected) < 0.01


class TestSignal:
    """Test Signal class."""

    def test_signal_creation(self):
        """Test creating a signal."""
        signal = Signal(
            ticker='AAPL',
            signal_type='buy',
            timestamp=datetime.now(),
            price=150.0,
            reason='Test signal'
        )

        assert signal.ticker == 'AAPL'
        assert signal.signal_type == 'buy'
        assert signal.price == 150.0

    def test_signal_to_dict(self):
        """Test converting signal to dictionary."""
        timestamp = datetime.now()
        signal = Signal(
            ticker='AAPL',
            signal_type='buy',
            timestamp=timestamp,
            price=150.0,
            reason='Test signal'
        )

        signal_dict = signal.to_dict()

        assert signal_dict['ticker'] == 'AAPL'
        assert signal_dict['signal_type'] == 'buy'
        assert signal_dict['price'] == 150.0
        assert signal_dict['timestamp'] == timestamp


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
