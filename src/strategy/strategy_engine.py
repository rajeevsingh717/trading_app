"""
Trading Strategy Rules Engine
Implements the rule-based trading strategy defined in specs.md
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time
import pandas as pd
import pytz

logger = logging.getLogger(__name__)


class Signal:
    """Represents a trading signal."""

    def __init__(
        self,
        ticker: str,
        signal_type: str,  # 'buy' or 'sell'
        timestamp: datetime,
        price: float,
        reason: str,
        confidence: float = 1.0
    ):
        self.ticker = ticker
        self.signal_type = signal_type
        self.timestamp = timestamp
        self.price = price
        self.reason = reason
        self.confidence = confidence

    def __repr__(self):
        return (
            f"Signal({self.signal_type.upper()} {self.ticker} @ ${self.price:.2f} "
            f"- {self.reason})"
        )

    def to_dict(self) -> dict:
        """Convert signal to dictionary."""
        return {
            'ticker': self.ticker,
            'signal_type': self.signal_type,
            'timestamp': self.timestamp,
            'price': self.price,
            'reason': self.reason,
            'confidence': self.confidence
        }


class TradingStrategy:
    """
    Implements the intraday trading strategy defined in specs.md

    Entry Conditions (ALL must be true):
    1. Trend Filter: Price > 50-period SMA
    2. Momentum: RSI(14) between 40-70
    3. Volume Confirmation: Current volume > 1.2× 20-period average volume
    4. Volatility: ATR(14) > minimum threshold
    5. Time Filter: Between 10:00 AM - 3:00 PM ET
    6. Price Filter: Stock price > $20

    Exit Conditions (ANY triggers exit):
    1. Stop Loss: -1.0% from entry price
    2. Take Profit: +1.5% from entry price
    3. Time Stop: 3:55 PM ET
    4. Trailing Stop: Optional
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize strategy with configuration.

        Args:
            config: Strategy configuration parameters
        """
        if config is None:
            config = {}

        # Entry parameters
        self.min_stock_price = config.get('min_stock_price', 20.0)
        self.max_stock_price = config.get('max_stock_price', 500.0)
        self.rsi_lower = config.get('rsi_lower', 40)
        self.rsi_upper = config.get('rsi_upper', 70)
        self.volume_multiplier = config.get('volume_multiplier', 1.2)
        self.min_atr = config.get('min_atr', 0.5)

        # Exit parameters
        self.stop_loss_pct = config.get('stop_loss_percent', 1.0)
        self.take_profit_pct = config.get('take_profit_percent', 1.5)
        self.trailing_stop_trigger_pct = config.get('trailing_stop_trigger_percent', 1.0)
        self.trailing_stop_pct = config.get('trailing_stop_percent', 0.5)

        # Time filters (Eastern Time)
        self.trading_start = time(10, 0)  # 10:00 AM ET
        self.trading_end = time(15, 0)    # 3:00 PM ET
        self.position_close_time = time(15, 55)  # 3:55 PM ET

        self.timezone = pytz.timezone('US/Eastern')

    def check_entry_conditions(
        self,
        ticker: str,
        current_data: pd.Series,
        timestamp: datetime
    ) -> Tuple[bool, str]:
        """
        Check if all entry conditions are met.

        Args:
            ticker: Stock ticker
            current_data: Current bar data with indicators
            timestamp: Current timestamp

        Returns:
            Tuple of (should_enter, reason)
        """
        reasons = []

        # 1. Price Filter: Stock price > $20 and < $500
        price = current_data['close']
        if price < self.min_stock_price:
            return False, f"Price ${price:.2f} below minimum ${self.min_stock_price}"
        if price > self.max_stock_price:
            return False, f"Price ${price:.2f} above maximum ${self.max_stock_price}"

        # 2. Time Filter: Between 10:00 AM - 3:00 PM ET
        if not self._is_trading_hours(timestamp):
            return False, f"Outside trading hours (10:00 AM - 3:00 PM ET)"

        # 3. Trend Filter: Price > 50-period SMA
        if 'sma_50' not in current_data or pd.isna(current_data['sma_50']):
            return False, "SMA not available"

        if price <= current_data['sma_50']:
            return False, f"Price ${price:.2f} not above SMA ${current_data['sma_50']:.2f}"
        reasons.append("Above SMA")

        # 4. Momentum: RSI(14) between 40-70
        if 'rsi' not in current_data or pd.isna(current_data['rsi']):
            return False, "RSI not available"

        rsi = current_data['rsi']
        if rsi < self.rsi_lower or rsi > self.rsi_upper:
            return False, f"RSI {rsi:.1f} outside range ({self.rsi_lower}-{self.rsi_upper})"
        reasons.append(f"RSI {rsi:.1f}")

        # 5. Volume Confirmation: Current volume > 1.2× average volume
        if 'volume_ma' not in current_data or pd.isna(current_data['volume_ma']):
            return False, "Volume MA not available"

        volume_ratio = current_data['volume'] / current_data['volume_ma']
        if volume_ratio < self.volume_multiplier:
            return False, f"Volume ratio {volume_ratio:.2f} below {self.volume_multiplier}"
        reasons.append(f"Vol {volume_ratio:.2f}x")

        # 6. Volatility: ATR > minimum threshold
        if 'atr' not in current_data or pd.isna(current_data['atr']):
            return False, "ATR not available"

        if current_data['atr'] < self.min_atr:
            return False, f"ATR {current_data['atr']:.2f} below minimum {self.min_atr}"
        reasons.append(f"ATR {current_data['atr']:.2f}")

        # All conditions met
        reason = " | ".join(reasons)
        return True, reason

    def check_exit_conditions(
        self,
        position: Dict,
        current_price: float,
        timestamp: datetime,
        highest_price: Optional[float] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if any exit conditions are met.

        Args:
            position: Position data with entry_price, etc.
            current_price: Current market price
            timestamp: Current timestamp
            highest_price: Highest price since entry (for trailing stop)

        Returns:
            Tuple of (should_exit, exit_reason)
        """
        entry_price = position['entry_price']

        # Calculate P&L percentage
        pnl_pct = ((current_price - entry_price) / entry_price) * 100

        # 1. Stop Loss: -1.0% from entry
        if pnl_pct <= -self.stop_loss_pct:
            return True, f"Stop Loss (${current_price:.2f}, {pnl_pct:.2f}%)"

        # 2. Take Profit: +1.5% from entry
        if pnl_pct >= self.take_profit_pct:
            return True, f"Take Profit (${current_price:.2f}, +{pnl_pct:.2f}%)"

        # 3. Time Stop: 3:55 PM ET (close all positions)
        if self._should_close_positions(timestamp):
            return True, f"Time Stop (EOD close, {pnl_pct:.2f}%)"

        # 4. Trailing Stop: Activate after +1% profit
        if highest_price is not None and pnl_pct > self.trailing_stop_trigger_pct:
            # Calculate drawdown from highest price
            drawdown_from_high = ((current_price - highest_price) / highest_price) * 100

            if drawdown_from_high <= -self.trailing_stop_pct:
                return True, f"Trailing Stop (${current_price:.2f}, {pnl_pct:.2f}%)"

        return False, None

    def generate_signals(
        self,
        ticker: str,
        df: pd.DataFrame,
        current_positions: Optional[List[Dict]] = None
    ) -> List[Signal]:
        """
        Generate trading signals for a ticker.

        Args:
            ticker: Stock ticker
            df: DataFrame with OHLCV data and indicators
            current_positions: List of current open positions

        Returns:
            List of Signal objects
        """
        signals = []

        if df.empty:
            logger.warning(f"Empty DataFrame for {ticker}")
            return signals

        # Get latest data
        latest = df.iloc[-1]
        timestamp = latest['timestamp']

        # Check if we already have a position in this ticker
        has_position = False
        if current_positions:
            for position in current_positions:
                # Support multiple position shapes (dict, dataclass, str ticker)
                if isinstance(position, str):
                    if position == ticker:
                        has_position = True
                        break
                elif isinstance(position, dict):
                    if position.get('ticker') == ticker:
                        has_position = True
                        break
                else:
                    ticker_attr = getattr(position, 'ticker', None)
                    if ticker_attr == ticker:
                        has_position = True
                        break

        # Only generate buy signals if we don't have a position
        if not has_position:
            should_enter, reason = self.check_entry_conditions(ticker, latest, timestamp)

            if should_enter:
                signal = Signal(
                    ticker=ticker,
                    signal_type='buy',
                    timestamp=timestamp,
                    price=latest['close'],
                    reason=reason,
                    confidence=1.0
                )
                signals.append(signal)
                logger.info(f"Generated BUY signal: {signal}")

        return signals

    def _is_trading_hours(self, timestamp: datetime) -> bool:
        """
        Check if timestamp is within trading hours (10:00 AM - 3:00 PM ET).

        Args:
            timestamp: Timestamp to check

        Returns:
            True if within trading hours
        """
        # Convert to Eastern Time
        if timestamp.tzinfo is None:
            timestamp = self.timezone.localize(timestamp)
        else:
            timestamp = timestamp.astimezone(self.timezone)

        current_time = timestamp.time()

        return self.trading_start <= current_time <= self.trading_end

    def _should_close_positions(self, timestamp: datetime) -> bool:
        """
        Check if it's time to close all positions (3:55 PM ET).

        Args:
            timestamp: Current timestamp

        Returns:
            True if positions should be closed
        """
        # Convert to Eastern Time
        if timestamp.tzinfo is None:
            timestamp = self.timezone.localize(timestamp)
        else:
            timestamp = timestamp.astimezone(self.timezone)

        current_time = timestamp.time()

        return current_time >= self.position_close_time

    def calculate_position_size(
        self,
        account_value: float,
        price: float,
        max_position_size: float = 1000.0
    ) -> int:
        """
        Calculate position size in shares.

        Args:
            account_value: Total account value
            price: Stock price
            max_position_size: Maximum dollar amount per position

        Returns:
            Number of shares to buy
        """
        # Use fixed position size
        position_value = min(max_position_size, account_value * 0.2)  # Max 20% per position
        shares = int(position_value / price)

        return max(shares, 1)  # At least 1 share

    def get_stop_loss_price(self, entry_price: float) -> float:
        """
        Calculate stop loss price.

        Args:
            entry_price: Entry price

        Returns:
            Stop loss price
        """
        return entry_price * (1 - self.stop_loss_pct / 100)

    def get_take_profit_price(self, entry_price: float) -> float:
        """
        Calculate take profit price.

        Args:
            entry_price: Entry price

        Returns:
            Take profit price
        """
        return entry_price * (1 + self.take_profit_pct / 100)


if __name__ == "__main__":
    # Test the strategy
    logging.basicConfig(level=logging.INFO)

    # Create sample data with indicators
    dates = pd.date_range(start='2024-01-01 10:00', periods=50, freq='5min')
    test_df = pd.DataFrame({
        'timestamp': dates,
        'close': [150.0 + i * 0.1 for i in range(50)],
        'volume': [1000000] * 50,
        'sma_50': [149.0] * 50,  # Price is above SMA
        'rsi': [55.0] * 50,  # RSI in good range
        'atr': [1.5] * 50,  # Good volatility
        'volume_ma': [800000] * 50  # Volume above average
    })

    strategy = TradingStrategy()

    # Test signal generation
    signals = strategy.generate_signals('TEST', test_df)

    if signals:
        print(f"Generated {len(signals)} signals:")
        for signal in signals:
            print(f"  {signal}")
    else:
        print("No signals generated")

    # Test exit conditions
    test_position = {
        'ticker': 'TEST',
        'entry_price': 150.0,
        'quantity': 10
    }

    # Test stop loss
    should_exit, reason = strategy.check_exit_conditions(
        test_position,
        current_price=148.5,  # -1% loss
        timestamp=datetime.now()
    )
    print(f"\nStop loss test: Exit={should_exit}, Reason={reason}")

    # Test take profit
    should_exit, reason = strategy.check_exit_conditions(
        test_position,
        current_price=152.3,  # +1.5% profit
        timestamp=datetime.now()
    )
    print(f"Take profit test: Exit={should_exit}, Reason={reason}")
