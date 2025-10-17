"""
Risk Management Module
Implements risk controls and position sizing for the trading system.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RiskLimits:
    """Risk limit configuration."""
    max_position_size: float = 1000.0  # Max $ per position
    max_positions: int = 5  # Max concurrent positions
    max_sector_positions: int = 2  # Max positions per sector
    daily_loss_limit: float = 100.0  # Max daily loss
    weekly_loss_limit: float = 300.0  # Max weekly loss
    max_drawdown_pct: float = 15.0  # Max portfolio drawdown %
    position_size_pct: float = 20.0  # Max % of capital per position


class RiskManager:
    """
    Manages risk controls for the trading system.

    Enforces:
    - Position size limits
    - Daily/weekly loss limits
    - Maximum drawdown
    - Position concentration limits
    - Circuit breakers
    """

    def __init__(self, limits: Optional[RiskLimits] = None):
        """
        Initialize risk manager.

        Args:
            limits: Risk limit configuration
        """
        self.limits = limits or RiskLimits()

        # Track daily/weekly P&L
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.current_date = None
        self.week_start_date = None

        # Track drawdown
        self.peak_equity = 0.0
        self.current_drawdown_pct = 0.0

        # Circuit breaker
        self.trading_halted = False
        self.halt_reason = None

    def reset_daily_pnl(self, current_date: datetime):
        """
        Reset daily P&L tracker.

        Args:
            current_date: Current date
        """
        if self.current_date is None or current_date.date() != self.current_date.date():
            logger.info(f"Resetting daily P&L. Previous: ${self.daily_pnl:.2f}")
            self.daily_pnl = 0.0
            self.current_date = current_date

    def reset_weekly_pnl(self, current_date: datetime):
        """
        Reset weekly P&L tracker.

        Args:
            current_date: Current date
        """
        if self.week_start_date is None:
            self.week_start_date = current_date
            return

        days_diff = (current_date - self.week_start_date).days
        if days_diff >= 7:
            logger.info(f"Resetting weekly P&L. Previous: ${self.weekly_pnl:.2f}")
            self.weekly_pnl = 0.0
            self.week_start_date = current_date

    def update_pnl(self, pnl: float, timestamp: datetime):
        """
        Update P&L trackers.

        Args:
            pnl: Profit/loss amount
            timestamp: Current timestamp
        """
        self.reset_daily_pnl(timestamp)
        self.reset_weekly_pnl(timestamp)

        self.daily_pnl += pnl
        self.weekly_pnl += pnl

        logger.debug(f"Updated P&L: Daily=${self.daily_pnl:.2f}, Weekly=${self.weekly_pnl:.2f}")

    def update_drawdown(self, current_equity: float):
        """
        Update drawdown tracker.

        Args:
            current_equity: Current portfolio equity
        """
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            self.current_drawdown_pct = 0.0
        else:
            self.current_drawdown_pct = (
                (self.peak_equity - current_equity) / self.peak_equity * 100
            )

        logger.debug(
            f"Drawdown: {self.current_drawdown_pct:.2f}% "
            f"(Peak: ${self.peak_equity:.2f}, Current: ${current_equity:.2f})"
        )

    def check_daily_loss_limit(self) -> bool:
        """
        Check if daily loss limit has been breached.

        Returns:
            True if limit breached
        """
        if abs(self.daily_pnl) >= self.limits.daily_loss_limit:
            logger.warning(
                f"Daily loss limit breached: ${self.daily_pnl:.2f} "
                f"(Limit: ${self.limits.daily_loss_limit})"
            )
            return True
        return False

    def check_weekly_loss_limit(self) -> bool:
        """
        Check if weekly loss limit has been breached.

        Returns:
            True if limit breached
        """
        if abs(self.weekly_pnl) >= self.limits.weekly_loss_limit:
            logger.warning(
                f"Weekly loss limit breached: ${self.weekly_pnl:.2f} "
                f"(Limit: ${self.limits.weekly_loss_limit})"
            )
            return True
        return False

    def check_drawdown_limit(self) -> bool:
        """
        Check if max drawdown has been breached.

        Returns:
            True if limit breached
        """
        if self.current_drawdown_pct >= self.limits.max_drawdown_pct:
            logger.warning(
                f"Max drawdown breached: {self.current_drawdown_pct:.2f}% "
                f"(Limit: {self.limits.max_drawdown_pct}%)"
            )
            return True
        return False

    def check_position_limits(
        self,
        current_positions: int,
        sector_positions: Optional[Dict[str, int]] = None
    ) -> bool:
        """
        Check if position limits would be breached.

        Args:
            current_positions: Number of current open positions
            sector_positions: Dictionary of positions per sector

        Returns:
            True if limits would be breached
        """
        # Check max positions
        if current_positions >= self.limits.max_positions:
            logger.warning(
                f"Max positions limit: {current_positions}/{self.limits.max_positions}"
            )
            return True

        # Check sector concentration
        if sector_positions:
            for sector, count in sector_positions.items():
                if count >= self.limits.max_sector_positions:
                    logger.warning(
                        f"Max sector positions for {sector}: "
                        f"{count}/{self.limits.max_sector_positions}"
                    )
                    return True

        return False

    def calculate_position_size(
        self,
        account_equity: float,
        stock_price: float
    ) -> int:
        """
        Calculate position size based on risk limits.

        Args:
            account_equity: Current account equity
            stock_price: Stock price

        Returns:
            Number of shares to buy
        """
        # Calculate position value based on percentage of equity
        max_by_percentage = account_equity * (self.limits.position_size_pct / 100)

        # Use the smaller of fixed limit or percentage limit
        position_value = min(self.limits.max_position_size, max_by_percentage)

        # Calculate shares
        shares = int(position_value / stock_price)

        # Ensure at least 1 share if we have enough capital
        if shares == 0 and account_equity >= stock_price:
            shares = 1

        logger.debug(
            f"Position size: {shares} shares @ ${stock_price:.2f} "
            f"= ${shares * stock_price:.2f}"
        )

        return shares

    def validate_trade(
        self,
        ticker: str,
        price: float,
        quantity: int,
        account_equity: float,
        current_positions: int,
        timestamp: datetime
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if a trade can be executed.

        Args:
            ticker: Stock ticker
            price: Trade price
            quantity: Number of shares
            account_equity: Current account equity
            current_positions: Number of open positions
            timestamp: Current timestamp

        Returns:
            Tuple of (is_valid, rejection_reason)
        """
        # Check if trading is halted
        if self.trading_halted:
            return False, f"Trading halted: {self.halt_reason}"

        # Update trackers
        self.reset_daily_pnl(timestamp)
        self.reset_weekly_pnl(timestamp)
        self.update_drawdown(account_equity)

        # Check daily loss limit
        if self.check_daily_loss_limit():
            self.halt_trading("Daily loss limit exceeded")
            return False, "Daily loss limit exceeded"

        # Check weekly loss limit
        if self.check_weekly_loss_limit():
            return False, "Weekly loss limit exceeded - review required"

        # Check drawdown limit
        if self.check_drawdown_limit():
            self.halt_trading("Max drawdown exceeded")
            return False, "Max drawdown exceeded"

        # Check position limits
        if self.check_position_limits(current_positions):
            return False, "Position limits exceeded"

        # Check position size
        position_value = price * quantity
        if position_value > self.limits.max_position_size:
            return False, f"Position size ${position_value:.2f} exceeds limit ${self.limits.max_position_size}"

        # Check if we have sufficient capital
        if position_value > account_equity:
            return False, "Insufficient capital"

        return True, None

    def halt_trading(self, reason: str):
        """
        Halt all trading (circuit breaker).

        Args:
            reason: Reason for halt
        """
        self.trading_halted = True
        self.halt_reason = reason
        logger.critical(f"TRADING HALTED: {reason}")

    def resume_trading(self):
        """Resume trading after manual review."""
        self.trading_halted = False
        self.halt_reason = None
        logger.info("Trading resumed")

    def get_risk_status(self) -> Dict:
        """
        Get current risk status.

        Returns:
            Dictionary with risk metrics
        """
        return {
            'trading_halted': self.trading_halted,
            'halt_reason': self.halt_reason,
            'daily_pnl': self.daily_pnl,
            'daily_loss_limit': self.limits.daily_loss_limit,
            'daily_limit_used_pct': (abs(self.daily_pnl) / self.limits.daily_loss_limit * 100),
            'weekly_pnl': self.weekly_pnl,
            'weekly_loss_limit': self.limits.weekly_loss_limit,
            'weekly_limit_used_pct': (abs(self.weekly_pnl) / self.limits.weekly_loss_limit * 100),
            'current_drawdown_pct': self.current_drawdown_pct,
            'max_drawdown_pct': self.limits.max_drawdown_pct,
            'peak_equity': self.peak_equity
        }


if __name__ == "__main__":
    # Test the risk manager
    logging.basicConfig(level=logging.INFO)

    limits = RiskLimits(
        daily_loss_limit=100.0,
        max_positions=5,
        max_position_size=1000.0
    )

    risk_mgr = RiskManager(limits)

    print("Testing Risk Manager...")

    # Test position sizing
    account_equity = 10000.0
    stock_price = 150.0
    shares = risk_mgr.calculate_position_size(account_equity, stock_price)
    print(f"\nPosition size for ${stock_price}: {shares} shares")

    # Test trade validation
    is_valid, reason = risk_mgr.validate_trade(
        ticker='AAPL',
        price=150.0,
        quantity=shares,
        account_equity=account_equity,
        current_positions=2,
        timestamp=datetime.now()
    )
    print(f"Trade validation: {is_valid}, Reason: {reason}")

    # Simulate losses
    risk_mgr.update_pnl(-50, datetime.now())
    risk_mgr.update_pnl(-30, datetime.now())
    risk_mgr.update_pnl(-25, datetime.now())

    # Check status
    status = risk_mgr.get_risk_status()
    print(f"\nRisk Status:")
    for key, value in status.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    # Try to trade after hitting daily limit
    is_valid, reason = risk_mgr.validate_trade(
        ticker='MSFT',
        price=300.0,
        quantity=3,
        account_equity=account_equity,
        current_positions=2,
        timestamp=datetime.now()
    )
    print(f"\nTrade after limit: {is_valid}, Reason: {reason}")
