"""
Logging and Monitoring System
Configures structured logging for the trading system.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record

        Returns:
            Formatted JSON string
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add custom fields if present
        if hasattr(record, 'ticker'):
            log_data['ticker'] = record.ticker
        if hasattr(record, 'pnl'):
            log_data['pnl'] = record.pnl
        if hasattr(record, 'trade_type'):
            log_data['trade_type'] = record.trade_type

        return json.dumps(log_data)


class TradingLogger:
    """
    Centralized logging configuration for the trading system.

    Creates separate log files for:
    - General application logs
    - Data collection logs
    - Trade execution logs
    - System errors
    - Performance metrics
    """

    def __init__(self, log_dir: Optional[Path] = None, log_level: str = "INFO"):
        """
        Initialize logging system.

        Args:
            log_dir: Directory for log files. If None, uses default.
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "logs"

        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.log_level = getattr(logging, log_level.upper())

        # Create dated subdirectory
        date_str = datetime.now().strftime('%Y-%m-%d')
        self.daily_log_dir = self.log_dir / date_str
        self.daily_log_dir.mkdir(parents=True, exist_ok=True)

        self._setup_loggers()

    def _setup_loggers(self):
        """Configure all loggers."""
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        # Remove existing handlers
        root_logger.handlers.clear()

        # Console handler (human-readable)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        root_logger.addHandler(console_handler)

        # Main application log (human-readable)
        app_handler = logging.FileHandler(
            self.daily_log_dir / 'application.log'
        )
        app_handler.setLevel(self.log_level)
        app_handler.setFormatter(console_format)
        root_logger.addHandler(app_handler)

        # Structured JSON log (for parsing/analysis)
        json_handler = logging.FileHandler(
            self.daily_log_dir / 'structured.log'
        )
        json_handler.setLevel(self.log_level)
        json_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(json_handler)

        # Error log (errors and above only)
        error_handler = logging.FileHandler(
            self.daily_log_dir / 'errors.log'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(console_format)
        root_logger.addHandler(error_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance.

        Args:
            name: Logger name

        Returns:
            Logger instance
        """
        return logging.getLogger(name)

    def create_trade_logger(self) -> logging.Logger:
        """
        Create specialized logger for trade execution.

        Returns:
            Logger for trades
        """
        trade_logger = logging.getLogger('trades')
        trade_logger.setLevel(logging.INFO)

        # Dedicated trade log file
        trade_handler = logging.FileHandler(
            self.daily_log_dir / 'trades.log'
        )
        trade_format = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        trade_handler.setFormatter(trade_format)

        # Prevent propagation to root logger (avoid duplicate logs)
        trade_logger.propagate = False
        trade_logger.addHandler(trade_handler)

        return trade_logger

    def create_data_logger(self) -> logging.Logger:
        """
        Create specialized logger for data collection.

        Returns:
            Logger for data operations
        """
        data_logger = logging.getLogger('data')
        data_logger.setLevel(logging.INFO)

        # Dedicated data log file
        data_handler = logging.FileHandler(
            self.daily_log_dir / 'data.log'
        )
        data_format = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        data_handler.setFormatter(data_format)

        data_logger.propagate = False
        data_logger.addHandler(data_handler)

        return data_logger

    def create_performance_logger(self) -> logging.Logger:
        """
        Create specialized logger for performance metrics.

        Returns:
            Logger for performance data
        """
        perf_logger = logging.getLogger('performance')
        perf_logger.setLevel(logging.INFO)

        # Dedicated performance log file (CSV-like format)
        perf_handler = logging.FileHandler(
            self.daily_log_dir / 'performance.log'
        )
        perf_format = logging.Formatter('%(message)s')
        perf_handler.setFormatter(perf_format)

        perf_logger.propagate = False
        perf_logger.addHandler(perf_handler)

        return perf_logger


def setup_logging(log_dir: Optional[Path] = None, log_level: str = "INFO") -> TradingLogger:
    """
    Setup logging system for the trading application.

    Args:
        log_dir: Directory for log files
        log_level: Logging level

    Returns:
        TradingLogger instance
    """
    trading_logger = TradingLogger(log_dir=log_dir, log_level=log_level)

    # Log startup
    logger = trading_logger.get_logger(__name__)
    logger.info("=" * 60)
    logger.info("Trading System Logging Initialized")
    logger.info(f"Log Directory: {trading_logger.daily_log_dir}")
    logger.info(f"Log Level: {log_level}")
    logger.info("=" * 60)

    return trading_logger


def log_trade(
    logger: logging.Logger,
    action: str,
    ticker: str,
    quantity: int,
    price: float,
    pnl: Optional[float] = None,
    reason: Optional[str] = None
):
    """
    Log a trade execution.

    Args:
        logger: Logger instance
        action: Trade action (BUY/SELL)
        ticker: Stock ticker
        quantity: Number of shares
        price: Trade price
        pnl: Profit/loss (for sells)
        reason: Reason for trade
    """
    msg = f"{action} | {ticker} | {quantity} shares @ ${price:.2f}"

    if pnl is not None:
        msg += f" | P&L: ${pnl:.2f}"

    if reason:
        msg += f" | {reason}"

    # Create extra dict for structured logging
    extra = {
        'ticker': ticker,
        'trade_type': action,
        'quantity': quantity,
        'price': price
    }

    if pnl is not None:
        extra['pnl'] = pnl

    logger.info(msg, extra=extra)


def log_performance(
    logger: logging.Logger,
    timestamp: datetime,
    equity: float,
    daily_pnl: float,
    num_trades: int,
    num_positions: int,
    win_rate: Optional[float] = None
):
    """
    Log performance metrics.

    Args:
        logger: Logger instance
        timestamp: Timestamp
        equity: Current equity
        daily_pnl: Daily profit/loss
        num_trades: Number of trades today
        num_positions: Number of open positions
        win_rate: Win rate percentage
    """
    msg = (
        f"{timestamp.isoformat()} | "
        f"Equity: ${equity:.2f} | "
        f"Daily P&L: ${daily_pnl:+.2f} | "
        f"Trades: {num_trades} | "
        f"Positions: {num_positions}"
    )

    if win_rate is not None:
        msg += f" | Win Rate: {win_rate:.1f}%"

    logger.info(msg)


def log_signal(
    logger: logging.Logger,
    ticker: str,
    signal_type: str,
    price: float,
    reason: str,
    taken: bool = False
):
    """
    Log a trading signal.

    Args:
        logger: Logger instance
        ticker: Stock ticker
        signal_type: Signal type (BUY/SELL)
        price: Signal price
        reason: Signal reason
        taken: Whether signal was acted upon
    """
    status = "TAKEN" if taken else "IGNORED"
    msg = f"SIGNAL {status} | {signal_type} | {ticker} @ ${price:.2f} | {reason}"

    logger.info(msg, extra={
        'ticker': ticker,
        'trade_type': signal_type,
        'price': price
    })


if __name__ == "__main__":
    # Test the logging system
    print("Testing logging system...")

    # Setup logging
    trading_logger = setup_logging(log_level="DEBUG")

    # Test general logging
    main_logger = trading_logger.get_logger(__name__)
    main_logger.debug("This is a debug message")
    main_logger.info("This is an info message")
    main_logger.warning("This is a warning message")
    main_logger.error("This is an error message")

    # Test trade logging
    trade_logger = trading_logger.create_trade_logger()
    log_trade(
        trade_logger,
        action="BUY",
        ticker="AAPL",
        quantity=10,
        price=150.50,
        reason="Entry signal"
    )

    log_trade(
        trade_logger,
        action="SELL",
        ticker="AAPL",
        quantity=10,
        price=152.75,
        pnl=22.50,
        reason="Take profit"
    )

    # Test performance logging
    perf_logger = trading_logger.create_performance_logger()
    log_performance(
        perf_logger,
        timestamp=datetime.now(),
        equity=10250.00,
        daily_pnl=250.00,
        num_trades=5,
        num_positions=2,
        win_rate=60.0
    )

    # Test signal logging
    log_signal(
        main_logger,
        ticker="MSFT",
        signal_type="BUY",
        price=300.00,
        reason="Above SMA | RSI 55.0 | Vol 1.5x | ATR 2.5",
        taken=True
    )

    print(f"\nLog files created in: {trading_logger.daily_log_dir}")
    print("Check the following files:")
    print("  - application.log (main application log)")
    print("  - structured.log (JSON formatted)")
    print("  - errors.log (errors only)")
    print("  - trades.log (trade executions)")
    print("  - performance.log (performance metrics)")
