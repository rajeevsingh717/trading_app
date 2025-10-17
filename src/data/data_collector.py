"""
Data Collection Module for Historical and Real-time Market Data
Fetches OHLCV data using yfinance and stores it for analysis.
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from pathlib import Path
import time

logger = logging.getLogger(__name__)


class DataCollector:
    """Collects historical and real-time market data for stocks."""

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the data collector.

        Args:
            data_dir: Directory to store downloaded data. If None, uses default.
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "data" / "historical"

        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def fetch_historical_data(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "5m",
        max_retries: int = 3
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLCV data for a single ticker.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for data fetch. If None, fetches last 60 days.
            end_date: End date for data fetch. If None, uses today.
            interval: Data interval ('1m', '5m', '15m', '30m', '1h', '1d')
            max_retries: Maximum number of retry attempts

        Returns:
            DataFrame with OHLCV data, or None if fetch fails.
        """
        if end_date is None:
            end_date = datetime.now()

        if start_date is None:
            # yfinance limits: 5m data available for last 60 days only
            if interval in ['1m', '2m', '5m']:
                start_date = end_date - timedelta(days=59)
            else:
                start_date = end_date - timedelta(days=365 * 3)  # 3 years

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Fetching {ticker} data from {start_date.date()} to {end_date.date()} "
                    f"(interval: {interval}, attempt: {attempt + 1})"
                )

                # Download data
                stock = yf.Ticker(ticker)
                df = stock.history(
                    start=start_date,
                    end=end_date,
                    interval=interval,
                    actions=False  # Don't include dividends and splits
                )

                if df.empty:
                    logger.warning(f"No data returned for {ticker}")
                    return None

                # Clean and prepare data
                df = self._clean_data(df, ticker)

                logger.info(f"Successfully fetched {len(df)} rows for {ticker}")
                return df

            except Exception as e:
                logger.error(f"Error fetching {ticker} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {ticker} after {max_retries} attempts")
                    return None

        return None

    def fetch_batch_historical_data(
        self,
        tickers: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "5m",
        delay_seconds: float = 0.5
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple tickers.

        Args:
            tickers: List of ticker symbols
            start_date: Start date for data fetch
            end_date: End date for data fetch
            interval: Data interval
            delay_seconds: Delay between requests to avoid rate limiting

        Returns:
            Dictionary mapping ticker to DataFrame
        """
        results = {}
        total = len(tickers)

        logger.info(f"Starting batch download for {total} tickers")

        for idx, ticker in enumerate(tickers, 1):
            logger.info(f"Processing {ticker} ({idx}/{total})")

            df = self.fetch_historical_data(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )

            if df is not None and not df.empty:
                results[ticker] = df
                # Save to CSV
                self.save_to_csv(ticker, df, interval)

            # Rate limiting
            if idx < total:
                time.sleep(delay_seconds)

        logger.info(
            f"Batch download complete. Successfully fetched {len(results)}/{total} tickers"
        )
        return results

    def _clean_data(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """
        Clean and standardize OHLCV data.

        Args:
            df: Raw DataFrame from yfinance
            ticker: Ticker symbol

        Returns:
            Cleaned DataFrame
        """
        # Reset index to make datetime a column
        df = df.reset_index()

        # Rename columns to standardized names
        column_mapping = {
            'Date': 'timestamp',
            'Datetime': 'timestamp',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }
        df = df.rename(columns=column_mapping)

        # Keep only necessary columns
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        df = df[required_columns]

        # Add ticker column
        df['ticker'] = ticker

        # Remove rows with missing data
        df = df.dropna()

        # Sort by timestamp
        df = df.sort_values('timestamp')

        # Remove duplicates
        df = df.drop_duplicates(subset=['timestamp'], keep='last')

        return df

    def save_to_csv(
        self,
        ticker: str,
        df: pd.DataFrame,
        interval: str = "5m"
    ) -> Path:
        """
        Save DataFrame to CSV file.

        Args:
            ticker: Ticker symbol
            df: DataFrame to save
            interval: Data interval for filename

        Returns:
            Path to saved file
        """
        filename = f"{ticker}_{interval}.csv"
        filepath = self.data_dir / filename

        try:
            df.to_csv(filepath, index=False)
            logger.info(f"Saved {ticker} data to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving {ticker} to CSV: {e}")
            raise

    def load_from_csv(
        self,
        ticker: str,
        interval: str = "5m"
    ) -> Optional[pd.DataFrame]:
        """
        Load data from CSV file.

        Args:
            ticker: Ticker symbol
            interval: Data interval

        Returns:
            DataFrame if file exists, None otherwise
        """
        filename = f"{ticker}_{interval}.csv"
        filepath = self.data_dir / filename

        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return None

        try:
            df = pd.read_csv(filepath)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            logger.info(f"Loaded {len(df)} rows for {ticker} from {filepath}")
            return df
        except Exception as e:
            logger.error(f"Error loading {ticker} from CSV: {e}")
            return None

    def get_latest_data(
        self,
        ticker: str,
        interval: str = "5m",
        period: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Get latest intraday data for a ticker.

        Args:
            ticker: Ticker symbol
            interval: Data interval
            period: Time period ('1d', '5d', '1mo')

        Returns:
            DataFrame with latest data
        """
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval, actions=False)

            if df.empty:
                logger.warning(f"No recent data for {ticker}")
                return None

            df = self._clean_data(df, ticker)
            return df

        except Exception as e:
            logger.error(f"Error fetching latest data for {ticker}: {e}")
            return None

    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Validate data quality and completeness.

        Args:
            df: DataFrame to validate

        Returns:
            Dictionary with validation results
        """
        if df is None or df.empty:
            return {
                "valid": False,
                "reason": "Empty or None DataFrame"
            }

        results = {
            "valid": True,
            "total_rows": len(df),
            "missing_values": df.isnull().sum().to_dict(),
            "date_range": {
                "start": df['timestamp'].min(),
                "end": df['timestamp'].max()
            },
            "duplicates": df.duplicated(subset=['timestamp']).sum()
        }

        # Check for gaps in data
        df_sorted = df.sort_values('timestamp')
        time_diffs = df_sorted['timestamp'].diff()
        expected_diff = time_diffs.mode()[0] if len(time_diffs.mode()) > 0 else None

        if expected_diff:
            large_gaps = time_diffs[time_diffs > expected_diff * 2]
            results["gaps"] = len(large_gaps)
        else:
            results["gaps"] = 0

        # Check for price anomalies (extreme changes)
        df['price_change'] = df['close'].pct_change()
        extreme_changes = df[abs(df['price_change']) > 0.2]  # >20% change
        results["extreme_price_changes"] = len(extreme_changes)

        # Overall validity
        issues = []
        if results["missing_values"]["close"] > 0:
            issues.append("Missing close prices")
        if results["duplicates"] > 0:
            issues.append("Duplicate timestamps")
        if results["gaps"] > 10:
            issues.append(f"{results['gaps']} significant time gaps")

        if issues:
            results["valid"] = False
            results["issues"] = issues

        return results


if __name__ == "__main__":
    # Test the module
    logging.basicConfig(level=logging.INFO)

    collector = DataCollector()

    # Test single ticker fetch
    print("Testing single ticker fetch...")
    df = collector.fetch_historical_data(
        ticker="AAPL",
        start_date=datetime.now() - timedelta(days=7),
        interval="5m"
    )

    if df is not None:
        print(f"\nFetched {len(df)} rows for AAPL")
        print(df.head())
        print(f"\nData quality check:")
        quality = collector.validate_data_quality(df)
        for key, value in quality.items():
            print(f"  {key}: {value}")
