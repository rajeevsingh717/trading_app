"""
Configuration management for the trading system.
Loads settings from environment variables and provides defaults.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
(DATA_DIR / "historical").mkdir(exist_ok=True)
(DATA_DIR / "live").mkdir(exist_ok=True)


class Config:
    """Main configuration class."""

    # API Configuration
    ALPACA_API_KEY: str = os.getenv("ALPACA_API_KEY", "")
    ALPACA_SECRET_KEY: str = os.getenv("ALPACA_SECRET_KEY", "")
    ALPACA_BASE_URL: str = os.getenv(
        "ALPACA_BASE_URL",
        "https://paper-api.alpaca.markets"
    )

    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    POLYGON_API_KEY: Optional[str] = os.getenv("POLYGON_API_KEY")

    # Database
    DATABASE_PATH: Path = Path(
        os.getenv("DATABASE_PATH", str(DATA_DIR / "trading.db"))
    )

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: Path = Path(os.getenv("LOG_DIR", str(LOG_DIR)))

    # Trading Parameters
    PAPER_TRADING: bool = os.getenv("PAPER_TRADING", "true").lower() == "true"
    STARTING_CAPITAL: float = float(os.getenv("STARTING_CAPITAL", "10000"))
    MAX_POSITION_SIZE: float = float(os.getenv("MAX_POSITION_SIZE", "1000"))
    MAX_POSITIONS: int = int(os.getenv("MAX_POSITIONS", "5"))
    DAILY_LOSS_LIMIT: float = float(os.getenv("DAILY_LOSS_LIMIT", "100"))
    WEEKLY_LOSS_LIMIT: float = float(os.getenv("WEEKLY_LOSS_LIMIT", "300"))
    MAX_DRAWDOWN_PERCENT: float = 15.0

    # Market Hours (Eastern Time)
    MARKET_OPEN_HOUR: int = int(os.getenv("MARKET_OPEN_HOUR", "9"))
    MARKET_OPEN_MINUTE: int = int(os.getenv("MARKET_OPEN_MINUTE", "30"))
    MARKET_CLOSE_HOUR: int = int(os.getenv("MARKET_CLOSE_HOUR", "16"))
    MARKET_CLOSE_MINUTE: int = int(os.getenv("MARKET_CLOSE_MINUTE", "0"))

    # Strategy Parameters
    TRADING_START_HOUR: int = 10  # Start trading at 10:00 AM ET
    TRADING_START_MINUTE: int = 0
    TRADING_END_HOUR: int = 15  # Stop trading at 3:00 PM ET
    TRADING_END_MINUTE: int = 0
    POSITION_CLOSE_HOUR: int = 15  # Close all positions by 3:55 PM ET
    POSITION_CLOSE_MINUTE: int = 55

    # Stock Selection Criteria
    MIN_STOCK_PRICE: float = 20.0
    MAX_STOCK_PRICE: float = 500.0
    MIN_VOLUME: int = 500000
    MAX_SPREAD_PERCENT: float = 0.2

    # Technical Indicator Periods
    SMA_PERIOD: int = 50
    RSI_PERIOD: int = 14
    ATR_PERIOD: int = 14
    VOLUME_MA_PERIOD: int = 20

    # Entry/Exit Rules
    RSI_LOWER_BOUND: int = 40
    RSI_UPPER_BOUND: int = 70
    VOLUME_MULTIPLIER: float = 1.2
    STOP_LOSS_PERCENT: float = 1.0
    TAKE_PROFIT_PERCENT: float = 1.5
    TRAILING_STOP_TRIGGER_PERCENT: float = 1.0
    TRAILING_STOP_PERCENT: float = 0.5

    # Data Collection
    HISTORICAL_YEARS: int = 3
    BAR_TIMEFRAME: str = "5Min"  # 5-minute bars
    DATA_FETCH_INTERVAL: int = 300  # 5 minutes in seconds
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5  # seconds

    # Notifications
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    EMAIL_ADDRESS: Optional[str] = os.getenv("EMAIL_ADDRESS")
    TELEGRAM_ENABLED: bool = bool(os.getenv("TELEGRAM_BOT_TOKEN"))
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")

    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        if cls.PAPER_TRADING:
            # For paper trading, we still need API keys
            if not cls.ALPACA_API_KEY or not cls.ALPACA_SECRET_KEY:
                print("Warning: Alpaca API keys not configured")
                return False

        return True

    @classmethod
    def display_config(cls) -> str:
        """Display non-sensitive configuration."""
        config_str = f"""
Trading System Configuration:
{'=' * 50}
Environment: {'Paper Trading' if cls.PAPER_TRADING else 'Live Trading'}
Starting Capital: ${cls.STARTING_CAPITAL:,.2f}
Max Position Size: ${cls.MAX_POSITION_SIZE:,.2f}
Max Positions: {cls.MAX_POSITIONS}
Daily Loss Limit: ${cls.DAILY_LOSS_LIMIT:,.2f}
Weekly Loss Limit: ${cls.WEEKLY_LOSS_LIMIT:,.2f}

Trading Hours:
  Market: {cls.MARKET_OPEN_HOUR:02d}:{cls.MARKET_OPEN_MINUTE:02d} - {cls.MARKET_CLOSE_HOUR:02d}:{cls.MARKET_CLOSE_MINUTE:02d} ET
  Strategy: {cls.TRADING_START_HOUR:02d}:{cls.TRADING_START_MINUTE:02d} - {cls.TRADING_END_HOUR:02d}:{cls.TRADING_END_MINUTE:02d} ET
  Close All By: {cls.POSITION_CLOSE_HOUR:02d}:{cls.POSITION_CLOSE_MINUTE:02d} ET

Stock Criteria:
  Price Range: ${cls.MIN_STOCK_PRICE:.2f} - ${cls.MAX_STOCK_PRICE:.2f}
  Min Volume: {cls.MIN_VOLUME:,}

Strategy Parameters:
  SMA Period: {cls.SMA_PERIOD}
  RSI Period: {cls.RSI_PERIOD} (Range: {cls.RSI_LOWER_BOUND}-{cls.RSI_UPPER_BOUND})
  ATR Period: {cls.ATR_PERIOD}
  Stop Loss: {cls.STOP_LOSS_PERCENT}%
  Take Profit: {cls.TAKE_PROFIT_PERCENT}%

Database: {cls.DATABASE_PATH}
Log Level: {cls.LOG_LEVEL}
{'=' * 50}
"""
        return config_str


# Create a singleton config instance
config = Config()
