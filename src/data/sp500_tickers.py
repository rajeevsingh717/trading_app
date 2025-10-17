"""
S&P 500 Ticker List Management Module
Fetches and maintains the list of S&P 500 constituent stocks.
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class SP500TickerManager:
    """Manages S&P 500 ticker list with automatic updates."""

    def __init__(self, cache_file: Optional[Path] = None):
        """
        Initialize the ticker manager.

        Args:
            cache_file: Path to cache the ticker list. If None, uses default location.
        """
        if cache_file is None:
            cache_file = Path(__file__).parent.parent.parent / "data" / "sp500_tickers.csv"

        self.cache_file = cache_file
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._tickers: List[str] = []
        self._last_updated: Optional[datetime] = None

    def get_tickers(self, force_refresh: bool = False) -> List[str]:
        """
        Get the list of S&P 500 tickers.

        Args:
            force_refresh: If True, fetch fresh data even if cache exists.

        Returns:
            List of ticker symbols.
        """
        # Check if we need to refresh
        if not force_refresh and self._should_use_cache():
            logger.info("Loading S&P 500 tickers from cache")
            return self._load_from_cache()

        # Fetch fresh data
        logger.info("Fetching fresh S&P 500 ticker list")
        try:
            tickers = self._fetch_from_wikipedia()
            self._save_to_cache(tickers)
            self._tickers = tickers
            self._last_updated = datetime.now()
            logger.info(f"Successfully fetched {len(tickers)} S&P 500 tickers")
            return tickers
        except Exception as e:
            logger.error(f"Failed to fetch tickers: {e}")
            # Fall back to cache if available
            if self.cache_file.exists():
                logger.warning("Falling back to cached ticker list")
                return self._load_from_cache()
            raise

    def _should_use_cache(self) -> bool:
        """
        Determine if cached data should be used.

        Returns:
            True if cache exists and is recent enough.
        """
        if not self.cache_file.exists():
            return False

        # Check cache age (refresh if older than 7 days)
        cache_age = datetime.now() - datetime.fromtimestamp(
            self.cache_file.stat().st_mtime
        )
        max_cache_age = timedelta(days=7)

        return cache_age < max_cache_age

    def _fetch_from_wikipedia(self) -> List[str]:
        """
        Fetch S&P 500 ticker list from Wikipedia.

        Returns:
            List of ticker symbols.

        Raises:
            Exception: If fetching fails.
        """
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

        try:
            # Read the table from Wikipedia
            tables = pd.read_html(url)
            sp500_table = tables[0]

            # Extract ticker symbols from the 'Symbol' column
            tickers = sp500_table['Symbol'].tolist()

            # Clean up ticker symbols (replace '.' with '-' for compatibility with Yahoo Finance)
            tickers = [ticker.replace('.', '-') for ticker in tickers]

            # Remove any potential duplicates
            tickers = list(set(tickers))

            # Sort for consistency
            tickers.sort()

            return tickers

        except Exception as e:
            logger.error(f"Error fetching from Wikipedia: {e}")
            raise

    def _load_from_cache(self) -> List[str]:
        """
        Load ticker list from cache file.

        Returns:
            List of ticker symbols.
        """
        try:
            df = pd.read_csv(self.cache_file)
            tickers = df['ticker'].tolist()
            self._tickers = tickers
            self._last_updated = datetime.fromtimestamp(
                self.cache_file.stat().st_mtime
            )
            return tickers
        except Exception as e:
            logger.error(f"Error loading from cache: {e}")
            raise

    def _save_to_cache(self, tickers: List[str]) -> None:
        """
        Save ticker list to cache file.

        Args:
            tickers: List of ticker symbols to cache.
        """
        try:
            df = pd.DataFrame({'ticker': tickers})
            df.to_csv(self.cache_file, index=False)
            logger.info(f"Saved {len(tickers)} tickers to cache")
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
            # Don't raise - caching is not critical

    def filter_tickers(
        self,
        tickers: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_volume: Optional[int] = None
    ) -> List[str]:
        """
        Filter tickers based on criteria (placeholder for future implementation).

        This method will be implemented when we have access to real-time pricing data.

        Args:
            tickers: List of tickers to filter. If None, uses all S&P 500 tickers.
            min_price: Minimum stock price.
            max_price: Maximum stock price.
            min_volume: Minimum average volume.

        Returns:
            Filtered list of tickers.
        """
        if tickers is None:
            tickers = self.get_tickers()

        # TODO: Implement filtering logic with real-time data
        logger.info(f"Filtering {len(tickers)} tickers (criteria not yet implemented)")

        return tickers

    def get_ticker_info(self) -> dict:
        """
        Get information about the ticker list.

        Returns:
            Dictionary with ticker list metadata.
        """
        if not self._tickers:
            self.get_tickers()

        return {
            "total_tickers": len(self._tickers),
            "last_updated": self._last_updated.isoformat() if self._last_updated else None,
            "cache_file": str(self.cache_file),
            "cache_exists": self.cache_file.exists()
        }


def get_sp500_tickers(force_refresh: bool = False) -> List[str]:
    """
    Convenience function to get S&P 500 tickers.

    Args:
        force_refresh: If True, fetch fresh data.

    Returns:
        List of S&P 500 ticker symbols.
    """
    manager = SP500TickerManager()
    return manager.get_tickers(force_refresh=force_refresh)


if __name__ == "__main__":
    # Test the module
    logging.basicConfig(level=logging.INFO)

    print("Fetching S&P 500 tickers...")
    tickers = get_sp500_tickers(force_refresh=True)

    print(f"\nTotal tickers: {len(tickers)}")
    print(f"First 10 tickers: {tickers[:10]}")
    print(f"Last 10 tickers: {tickers[-10:]}")
