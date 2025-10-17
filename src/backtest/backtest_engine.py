"""
Backtesting Engine
Simulates trading strategy on historical data with realistic assumptions.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for backtest runs."""
    starting_capital: float = 10000.0
    max_positions: int = 5
    max_position_size: float = 1000.0
    commission_per_trade: float = 0.0  # Commission-free broker
    slippage_pct: float = 0.05  # 0.05% slippage per trade
    daily_loss_limit: float = 100.0
    max_drawdown_pct: float = 15.0


@dataclass
class Position:
    """Represents an open position."""
    ticker: str
    entry_time: datetime
    entry_price: float
    quantity: int
    stop_loss: float
    take_profit: float
    highest_price: float = field(default=0.0)

    def __post_init__(self):
        if self.highest_price == 0.0:
            self.highest_price = self.entry_price

    @property
    def position_value(self) -> float:
        """Current position value at entry."""
        return self.entry_price * self.quantity

    def update_highest_price(self, current_price: float):
        """Update the highest price seen since entry."""
        self.highest_price = max(self.highest_price, current_price)

    def calculate_pnl(self, current_price: float) -> float:
        """Calculate current P&L."""
        return (current_price - self.entry_price) * self.quantity

    def calculate_pnl_pct(self, current_price: float) -> float:
        """Calculate current P&L percentage."""
        return ((current_price - self.entry_price) / self.entry_price) * 100


@dataclass
class Trade:
    """Represents a completed trade."""
    ticker: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    pnl_pct: float
    exit_reason: str
    commission: float = 0.0
    slippage: float = 0.0


class BacktestEngine:
    """
    Backtesting engine for trading strategies.
    Simulates realistic trading with slippage, commission, and risk management.
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        Initialize backtest engine.

        Args:
            config: Backtest configuration
        """
        self.config = config or BacktestConfig()

        # Portfolio state
        self.capital = self.config.starting_capital
        self.starting_capital = self.config.starting_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []

        # Performance tracking
        self.daily_pnl = 0.0
        self.peak_equity = self.config.starting_capital
        self.current_drawdown = 0.0

        # Statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

    def reset(self):
        """Reset backtest to initial state."""
        self.capital = self.config.starting_capital
        self.starting_capital = self.config.starting_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        self.daily_pnl = 0.0
        self.peak_equity = self.config.starting_capital
        self.current_drawdown = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

    def can_open_position(self) -> bool:
        """Check if we can open a new position."""
        if len(self.positions) >= self.config.max_positions:
            return False

        if self.capital < self.config.max_position_size:
            return False

        # Check daily loss limit
        if abs(self.daily_pnl) >= self.config.daily_loss_limit:
            logger.warning("Daily loss limit reached")
            return False

        # Check max drawdown
        if self.current_drawdown >= self.config.max_drawdown_pct:
            logger.warning("Max drawdown reached")
            return False

        return True

    def open_position(
        self,
        ticker: str,
        timestamp: datetime,
        price: float,
        quantity: int,
        stop_loss: float,
        take_profit: float
    ) -> bool:
        """
        Open a new position.

        Args:
            ticker: Stock ticker
            timestamp: Entry timestamp
            price: Entry price
            quantity: Number of shares
            stop_loss: Stop loss price
            take_profit: Take profit price

        Returns:
            True if position opened successfully
        """
        if ticker in self.positions:
            logger.warning(f"Already have position in {ticker}")
            return False

        if not self.can_open_position():
            return False

        # Apply slippage (worse fill price)
        slippage = price * (self.config.slippage_pct / 100)
        actual_entry_price = price + slippage

        # Calculate position cost
        position_cost = actual_entry_price * quantity
        total_cost = position_cost + self.config.commission_per_trade

        if total_cost > self.capital:
            logger.warning(f"Insufficient capital for {ticker}")
            return False

        # Create position
        position = Position(
            ticker=ticker,
            entry_time=timestamp,
            entry_price=actual_entry_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        # Update capital
        self.capital -= total_cost
        self.positions[ticker] = position

        logger.info(
            f"OPEN {ticker}: {quantity} shares @ ${actual_entry_price:.2f} "
            f"(SL: ${stop_loss:.2f}, TP: ${take_profit:.2f})"
        )

        return True

    def close_position(
        self,
        ticker: str,
        timestamp: datetime,
        price: float,
        reason: str
    ) -> Optional[Trade]:
        """
        Close an existing position.

        Args:
            ticker: Stock ticker
            timestamp: Exit timestamp
            price: Exit price
            reason: Reason for exit

        Returns:
            Trade object if position closed, None otherwise
        """
        if ticker not in self.positions:
            logger.warning(f"No position in {ticker} to close")
            return None

        position = self.positions[ticker]

        # Apply slippage (worse fill price)
        slippage = price * (self.config.slippage_pct / 100)
        actual_exit_price = price - slippage

        # Calculate P&L
        gross_pnl = (actual_exit_price - position.entry_price) * position.quantity
        net_pnl = gross_pnl - self.config.commission_per_trade
        pnl_pct = ((actual_exit_price - position.entry_price) / position.entry_price) * 100

        # Update capital
        proceeds = actual_exit_price * position.quantity
        self.capital += proceeds - self.config.commission_per_trade

        # Create trade record
        trade = Trade(
            ticker=ticker,
            entry_time=position.entry_time,
            exit_time=timestamp,
            entry_price=position.entry_price,
            exit_price=actual_exit_price,
            quantity=position.quantity,
            pnl=net_pnl,
            pnl_pct=pnl_pct,
            exit_reason=reason,
            commission=self.config.commission_per_trade * 2,  # Entry + exit
            slippage=slippage * position.quantity * 2
        )

        # Update statistics
        self.trades.append(trade)
        self.total_trades += 1
        self.daily_pnl += net_pnl

        if net_pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        # Remove position
        del self.positions[ticker]

        logger.info(
            f"CLOSE {ticker}: {position.quantity} shares @ ${actual_exit_price:.2f} "
            f"| P&L: ${net_pnl:.2f} ({pnl_pct:+.2f}%) | {reason}"
        )

        return trade

    def update_positions(self, current_prices: Dict[str, float], timestamp: datetime):
        """
        Update all positions with current prices.

        Args:
            current_prices: Dictionary mapping ticker to current price
            timestamp: Current timestamp
        """
        for ticker in list(self.positions.keys()):
            if ticker not in current_prices:
                continue

            current_price = current_prices[ticker]
            position = self.positions[ticker]

            # Update highest price for trailing stop
            position.update_highest_price(current_price)

    def record_equity(self, timestamp: datetime, current_prices: Dict[str, float]):
        """
        Record current equity for equity curve.

        Args:
            timestamp: Current timestamp
            current_prices: Current prices for open positions
        """
        # Calculate total position value
        position_value = 0.0
        for ticker, position in self.positions.items():
            if ticker in current_prices:
                position_value += current_prices[ticker] * position.quantity

        total_equity = self.capital + position_value

        # Update peak equity and drawdown
        if total_equity > self.peak_equity:
            self.peak_equity = total_equity
            self.current_drawdown = 0.0
        else:
            self.current_drawdown = ((self.peak_equity - total_equity) / self.peak_equity) * 100

        # Record equity point
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': total_equity,
            'capital': self.capital,
            'position_value': position_value,
            'drawdown': self.current_drawdown,
            'num_positions': len(self.positions)
        })

    def get_performance_metrics(self) -> Dict:
        """
        Calculate performance metrics.

        Returns:
            Dictionary with performance statistics
        """
        if not self.trades:
            return {
                'total_return': 0.0,
                'total_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0
            }

        # Convert equity curve to DataFrame
        equity_df = pd.DataFrame(self.equity_curve)

        # Calculate returns
        final_equity = equity_df['equity'].iloc[-1] if len(equity_df) > 0 else self.starting_capital
        total_return = ((final_equity - self.starting_capital) / self.starting_capital) * 100

        # Calculate trade statistics
        trade_pnls = [t.pnl for t in self.trades]
        winning_pnls = [t.pnl for t in self.trades if t.pnl > 0]
        losing_pnls = [abs(t.pnl) for t in self.trades if t.pnl < 0]

        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        # Profit factor
        total_wins = sum(winning_pnls) if winning_pnls else 0
        total_losses = sum(losing_pnls) if losing_pnls else 0
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0

        # Max drawdown
        max_drawdown = equity_df['drawdown'].max() if len(equity_df) > 0 else 0

        # Sharpe ratio (simplified - assuming daily data)
        if len(equity_df) > 1:
            equity_df['returns'] = equity_df['equity'].pct_change()
            sharpe_ratio = (
                equity_df['returns'].mean() / equity_df['returns'].std() * np.sqrt(252)
                if equity_df['returns'].std() > 0 else 0
            )
        else:
            sharpe_ratio = 0

        return {
            'starting_capital': self.starting_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'total_return_pct': total_return,
            'max_drawdown': max_drawdown,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': np.mean(winning_pnls) if winning_pnls else 0,
            'avg_loss': np.mean(losing_pnls) if losing_pnls else 0,
            'largest_win': max(winning_pnls) if winning_pnls else 0,
            'largest_loss': max(losing_pnls) if losing_pnls else 0,
            'sharpe_ratio': sharpe_ratio,
            'total_commission': sum(t.commission for t in self.trades),
            'total_slippage': sum(t.slippage for t in self.trades)
        }

    def get_trades_df(self) -> pd.DataFrame:
        """
        Get all trades as a DataFrame.

        Returns:
            DataFrame with trade history
        """
        if not self.trades:
            return pd.DataFrame()

        trades_data = []
        for trade in self.trades:
            trades_data.append({
                'ticker': trade.ticker,
                'entry_time': trade.entry_time,
                'exit_time': trade.exit_time,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'quantity': trade.quantity,
                'pnl': trade.pnl,
                'pnl_pct': trade.pnl_pct,
                'exit_reason': trade.exit_reason,
                'holding_time': (trade.exit_time - trade.entry_time).total_seconds() / 3600  # hours
            })

        return pd.DataFrame(trades_data)

    def get_equity_curve_df(self) -> pd.DataFrame:
        """
        Get equity curve as a DataFrame.

        Returns:
            DataFrame with equity curve
        """
        return pd.DataFrame(self.equity_curve)


if __name__ == "__main__":
    # Test the backtest engine
    logging.basicConfig(level=logging.INFO)

    config = BacktestConfig(starting_capital=10000)
    engine = BacktestEngine(config)

    # Simulate some trades
    print("Testing backtest engine...")

    # Open position
    engine.open_position(
        ticker='AAPL',
        timestamp=datetime(2024, 1, 1, 10, 0),
        price=150.0,
        quantity=6,
        stop_loss=148.5,
        take_profit=152.25
    )

    # Update with profit
    engine.update_positions({'AAPL': 152.5}, datetime(2024, 1, 1, 14, 0))
    engine.record_equity(datetime(2024, 1, 1, 14, 0), {'AAPL': 152.5})

    # Close with profit
    engine.close_position(
        ticker='AAPL',
        timestamp=datetime(2024, 1, 1, 14, 30),
        price=152.5,
        reason='Take Profit'
    )

    # Get performance
    metrics = engine.get_performance_metrics()
    print("\nPerformance Metrics:")
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
