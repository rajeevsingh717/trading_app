"""
Database Layer for Trading System
Manages SQLite database for storing market data, trades, and performance metrics.
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime
import pandas as pd
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    Index, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path

logger = logging.getLogger(__name__)

Base = declarative_base()


class MarketData(Base):
    """Market data (OHLCV) table."""

    __tablename__ = 'market_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    interval = Column(String(10), nullable=False)

    __table_args__ = (
        Index('idx_ticker_timestamp', 'ticker', 'timestamp', unique=True),
    )


class Trade(Base):
    """Trade execution records."""

    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    side = Column(String(10), nullable=False)  # 'buy' or 'sell'
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    order_type = Column(String(20), nullable=False)  # 'market', 'limit', 'stop'
    status = Column(String(20), nullable=False)  # 'filled', 'partial', 'cancelled'
    commission = Column(Float, default=0.0)
    notes = Column(String(500))


class Position(Base):
    """Current and historical positions."""

    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    entry_timestamp = Column(DateTime, nullable=False)
    exit_timestamp = Column(DateTime)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    quantity = Column(Integer, nullable=False)
    side = Column(String(10), nullable=False)  # 'long' or 'short'
    stop_loss = Column(Float)
    take_profit = Column(Float)
    pnl = Column(Float)
    pnl_percent = Column(Float)
    status = Column(String(20), nullable=False, index=True)  # 'open' or 'closed'
    exit_reason = Column(String(50))  # 'stop_loss', 'take_profit', 'time_exit', etc.


class DailyPerformance(Base):
    """Daily performance metrics."""

    __tablename__ = 'daily_performance'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)
    starting_capital = Column(Float, nullable=False)
    ending_capital = Column(Float, nullable=False)
    pnl = Column(Float, nullable=False)
    pnl_percent = Column(Float, nullable=False)
    num_trades = Column(Integer, default=0)
    num_wins = Column(Integer, default=0)
    num_losses = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    largest_win = Column(Float, default=0.0)
    largest_loss = Column(Float, default=0.0)


class DatabaseManager:
    """Manages database operations for the trading system."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file. If None, uses default.
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "trading.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create engine
        self.engine = create_engine(
            f'sqlite:///{self.db_path}',
            echo=False,
            pool_pre_ping=True
        )

        # Create session maker
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        # Create tables
        self._create_tables()

    def _create_tables(self):
        """Create all database tables if they don't exist."""
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Database tables created/verified at {self.db_path}")

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def save_market_data(
        self,
        df: pd.DataFrame,
        interval: str = "5m",
        batch_size: int = 1000
    ) -> int:
        """
        Save market data to database.

        Args:
            df: DataFrame with columns: ticker, timestamp, open, high, low, close, volume
            interval: Data interval
            batch_size: Number of rows to insert at once

        Returns:
            Number of rows inserted
        """
        session = self.get_session()
        inserted = 0

        try:
            # Add interval column if not present
            if 'interval' not in df.columns:
                df['interval'] = interval

            # Convert DataFrame to list of dicts
            records = df.to_dict('records')

            # Insert in batches
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]

                # Use bulk insert with ignore duplicates
                for record in batch:
                    try:
                        market_data = MarketData(**record)
                        session.add(market_data)
                        inserted += 1
                    except Exception as e:
                        # Skip duplicates
                        continue

                session.commit()
                logger.info(f"Inserted batch {i // batch_size + 1}: {len(batch)} records")

            logger.info(f"Total records inserted: {inserted}")
            return inserted

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving market data: {e}")
            raise
        finally:
            session.close()

    def get_market_data(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "5m"
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve market data from database.

        Args:
            ticker: Stock ticker
            start_date: Start date filter
            end_date: End date filter
            interval: Data interval

        Returns:
            DataFrame with market data
        """
        session = self.get_session()

        try:
            query = session.query(MarketData).filter(
                MarketData.ticker == ticker,
                MarketData.interval == interval
            )

            if start_date:
                query = query.filter(MarketData.timestamp >= start_date)
            if end_date:
                query = query.filter(MarketData.timestamp <= end_date)

            query = query.order_by(MarketData.timestamp)

            # Execute query and convert to DataFrame
            df = pd.read_sql(query.statement, session.bind)

            if df.empty:
                logger.warning(f"No data found for {ticker}")
                return None

            logger.info(f"Retrieved {len(df)} rows for {ticker}")
            return df

        except Exception as e:
            logger.error(f"Error retrieving market data: {e}")
            return None
        finally:
            session.close()

    def save_trade(self, trade_data: Dict) -> int:
        """
        Save a trade record.

        Args:
            trade_data: Dictionary with trade information

        Returns:
            Trade ID
        """
        session = self.get_session()

        try:
            trade = Trade(**trade_data)
            session.add(trade)
            session.commit()
            logger.info(f"Saved trade: {trade_data['ticker']} {trade_data['side']}")
            return trade.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving trade: {e}")
            raise
        finally:
            session.close()

    def save_position(self, position_data: Dict) -> int:
        """
        Save a position record.

        Args:
            position_data: Dictionary with position information

        Returns:
            Position ID
        """
        session = self.get_session()

        try:
            position = Position(**position_data)
            session.add(position)
            session.commit()
            logger.info(f"Saved position: {position_data['ticker']}")
            return position.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving position: {e}")
            raise
        finally:
            session.close()

    def update_position(self, position_id: int, updates: Dict) -> bool:
        """
        Update an existing position.

        Args:
            position_id: Position ID to update
            updates: Dictionary with fields to update

        Returns:
            True if successful
        """
        session = self.get_session()

        try:
            position = session.query(Position).filter(Position.id == position_id).first()
            if not position:
                logger.warning(f"Position {position_id} not found")
                return False

            for key, value in updates.items():
                setattr(position, key, value)

            session.commit()
            logger.info(f"Updated position {position_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating position: {e}")
            return False
        finally:
            session.close()

    def get_open_positions(self) -> List[Position]:
        """
        Get all open positions.

        Returns:
            List of Position objects
        """
        session = self.get_session()

        try:
            positions = session.query(Position).filter(
                Position.status == 'open'
            ).all()
            return positions
        finally:
            session.close()

    def save_daily_performance(self, performance_data: Dict) -> int:
        """
        Save daily performance metrics.

        Args:
            performance_data: Dictionary with performance data

        Returns:
            Performance record ID
        """
        session = self.get_session()

        try:
            perf = DailyPerformance(**performance_data)
            session.add(perf)
            session.commit()
            logger.info(f"Saved daily performance for {performance_data['date']}")
            return perf.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving daily performance: {e}")
            raise
        finally:
            session.close()

    def get_performance_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get performance summary for a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with performance data
        """
        session = self.get_session()

        try:
            query = session.query(DailyPerformance)

            if start_date:
                query = query.filter(DailyPerformance.date >= start_date)
            if end_date:
                query = query.filter(DailyPerformance.date <= end_date)

            query = query.order_by(DailyPerformance.date)

            df = pd.read_sql(query.statement, session.bind)
            return df
        finally:
            session.close()


if __name__ == "__main__":
    # Test the database module
    logging.basicConfig(level=logging.INFO)

    db = DatabaseManager()
    print(f"Database created at: {db.db_path}")

    # Test market data insertion
    test_data = pd.DataFrame({
        'ticker': ['AAPL', 'AAPL', 'AAPL'],
        'timestamp': pd.date_range(start='2024-01-01 09:30', periods=3, freq='5min'),
        'open': [150.0, 150.5, 151.0],
        'high': [150.5, 151.0, 151.5],
        'low': [149.5, 150.0, 150.5],
        'close': [150.3, 150.8, 151.2],
        'volume': [1000000, 1100000, 1050000]
    })

    inserted = db.save_market_data(test_data, interval="5m")
    print(f"Inserted {inserted} test records")

    # Test retrieval
    retrieved = db.get_market_data('AAPL', interval="5m")
    if retrieved is not None:
        print(f"\nRetrieved data:\n{retrieved}")
