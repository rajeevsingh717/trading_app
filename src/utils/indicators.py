"""
Technical Indicators Module
Calculates technical indicators for trading strategy.
Uses pandas for efficient calculations.
"""
import logging
from typing import Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calculate technical indicators for trading strategies."""

    @staticmethod
    def add_sma(
        df: pd.DataFrame,
        column: str = 'close',
        period: int = 50,
        column_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Add Simple Moving Average to DataFrame.

        Args:
            df: DataFrame with price data
            column: Column to calculate SMA on
            period: Number of periods for SMA
            column_name: Name for new column. If None, uses f'sma_{period}'

        Returns:
            DataFrame with SMA column added
        """
        if column_name is None:
            column_name = f'sma_{period}'

        df[column_name] = df[column].rolling(window=period).mean()
        return df

    @staticmethod
    def add_ema(
        df: pd.DataFrame,
        column: str = 'close',
        period: int = 12,
        column_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Add Exponential Moving Average to DataFrame.

        Args:
            df: DataFrame with price data
            column: Column to calculate EMA on
            period: Number of periods for EMA
            column_name: Name for new column

        Returns:
            DataFrame with EMA column added
        """
        if column_name is None:
            column_name = f'ema_{period}'

        df[column_name] = df[column].ewm(span=period, adjust=False).mean()
        return df

    @staticmethod
    def add_rsi(
        df: pd.DataFrame,
        column: str = 'close',
        period: int = 14,
        column_name: str = 'rsi'
    ) -> pd.DataFrame:
        """
        Add Relative Strength Index (RSI) to DataFrame.

        Args:
            df: DataFrame with price data
            column: Column to calculate RSI on
            period: Number of periods for RSI
            column_name: Name for new column

        Returns:
            DataFrame with RSI column added
        """
        # Calculate price changes
        delta = df[column].diff()

        # Separate gains and losses
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        # Calculate RS and RSI
        rs = gain / loss
        df[column_name] = 100 - (100 / (1 + rs))

        # Fill initial NaN values
        df[column_name] = df[column_name].fillna(50)

        return df

    @staticmethod
    def add_atr(
        df: pd.DataFrame,
        period: int = 14,
        column_name: str = 'atr'
    ) -> pd.DataFrame:
        """
        Add Average True Range (ATR) to DataFrame.

        Args:
            df: DataFrame with OHLC data
            period: Number of periods for ATR
            column_name: Name for new column

        Returns:
            DataFrame with ATR column added
        """
        # Calculate True Range
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # Calculate ATR as moving average of True Range
        df[column_name] = true_range.rolling(window=period).mean()

        return df

    @staticmethod
    def add_volume_ma(
        df: pd.DataFrame,
        period: int = 20,
        column_name: str = 'volume_ma'
    ) -> pd.DataFrame:
        """
        Add Volume Moving Average to DataFrame.

        Args:
            df: DataFrame with volume data
            period: Number of periods for volume MA
            column_name: Name for new column

        Returns:
            DataFrame with volume MA column added
        """
        df[column_name] = df['volume'].rolling(window=period).mean()
        return df

    @staticmethod
    def add_bollinger_bands(
        df: pd.DataFrame,
        column: str = 'close',
        period: int = 20,
        std_dev: float = 2.0
    ) -> pd.DataFrame:
        """
        Add Bollinger Bands to DataFrame.

        Args:
            df: DataFrame with price data
            column: Column to calculate bands on
            period: Number of periods for moving average
            std_dev: Number of standard deviations for bands

        Returns:
            DataFrame with BB columns added
        """
        # Calculate middle band (SMA)
        df['bb_middle'] = df[column].rolling(window=period).mean()

        # Calculate standard deviation
        rolling_std = df[column].rolling(window=period).std()

        # Calculate upper and lower bands
        df['bb_upper'] = df['bb_middle'] + (rolling_std * std_dev)
        df['bb_lower'] = df['bb_middle'] - (rolling_std * std_dev)

        # Calculate bandwidth
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

        return df

    @staticmethod
    def add_macd(
        df: pd.DataFrame,
        column: str = 'close',
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> pd.DataFrame:
        """
        Add MACD (Moving Average Convergence Divergence) to DataFrame.

        Args:
            df: DataFrame with price data
            column: Column to calculate MACD on
            fast_period: Period for fast EMA
            slow_period: Period for slow EMA
            signal_period: Period for signal line

        Returns:
            DataFrame with MACD columns added
        """
        # Calculate EMAs
        ema_fast = df[column].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df[column].ewm(span=slow_period, adjust=False).mean()

        # Calculate MACD line
        df['macd'] = ema_fast - ema_slow

        # Calculate signal line
        df['macd_signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()

        # Calculate histogram
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        return df

    @staticmethod
    def add_all_indicators(
        df: pd.DataFrame,
        sma_period: int = 50,
        rsi_period: int = 14,
        atr_period: int = 14,
        volume_ma_period: int = 20
    ) -> pd.DataFrame:
        """
        Add all standard indicators to DataFrame.

        Args:
            df: DataFrame with OHLCV data
            sma_period: Period for SMA
            rsi_period: Period for RSI
            atr_period: Period for ATR
            volume_ma_period: Period for volume MA

        Returns:
            DataFrame with all indicators added
        """
        indicators = TechnicalIndicators()

        # Add all indicators
        df = indicators.add_sma(df, period=sma_period)
        df = indicators.add_rsi(df, period=rsi_period)
        df = indicators.add_atr(df, period=atr_period)
        df = indicators.add_volume_ma(df, period=volume_ma_period)

        # Add volume ratio
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        logger.info(f"Added all technical indicators to DataFrame")
        return df

    @staticmethod
    def validate_indicators(df: pd.DataFrame) -> dict:
        """
        Validate that indicators are calculated correctly.

        Args:
            df: DataFrame with indicators

        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'indicators_present': [],
            'missing_indicators': [],
            'nan_counts': {}
        }

        # Check for expected indicator columns
        expected_indicators = ['sma_50', 'rsi', 'atr', 'volume_ma', 'volume_ratio']

        for indicator in expected_indicators:
            if indicator in df.columns:
                results['indicators_present'].append(indicator)
                # Count NaN values
                nan_count = df[indicator].isna().sum()
                results['nan_counts'][indicator] = int(nan_count)
            else:
                results['missing_indicators'].append(indicator)
                results['valid'] = False

        # Check RSI bounds (should be between 0 and 100)
        if 'rsi' in df.columns:
            rsi_out_of_bounds = ((df['rsi'] < 0) | (df['rsi'] > 100)).sum()
            if rsi_out_of_bounds > 0:
                results['valid'] = False
                results['rsi_out_of_bounds'] = int(rsi_out_of_bounds)

        # Check for excessive NaN values (>20% of data)
        total_rows = len(df)
        for indicator, nan_count in results['nan_counts'].items():
            if nan_count > total_rows * 0.2:
                results['valid'] = False
                results[f'{indicator}_excessive_nans'] = True

        return results


def calculate_indicators(df: pd.DataFrame, config: Optional[dict] = None) -> pd.DataFrame:
    """
    Convenience function to calculate all indicators.

    Args:
        df: DataFrame with OHLCV data
        config: Configuration dictionary with indicator parameters

    Returns:
        DataFrame with indicators added
    """
    if config is None:
        config = {
            'sma_period': 50,
            'rsi_period': 14,
            'atr_period': 14,
            'volume_ma_period': 20
        }

    indicators = TechnicalIndicators()
    df = indicators.add_all_indicators(
        df,
        sma_period=config.get('sma_period', 50),
        rsi_period=config.get('rsi_period', 14),
        atr_period=config.get('atr_period', 14),
        volume_ma_period=config.get('volume_ma_period', 20)
    )

    return df


if __name__ == "__main__":
    # Test the indicators module
    logging.basicConfig(level=logging.INFO)

    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='5min')
    np.random.seed(42)

    # Generate realistic price data
    price = 100
    prices = []
    for _ in range(100):
        price += np.random.randn() * 0.5
        prices.append(price)

    test_df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p + abs(np.random.randn() * 0.3) for p in prices],
        'low': [p - abs(np.random.randn() * 0.3) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 100)
    })

    print("Original DataFrame:")
    print(test_df.head())

    # Add indicators
    test_df = calculate_indicators(test_df)

    print("\nDataFrame with indicators:")
    print(test_df[['timestamp', 'close', 'sma_50', 'rsi', 'atr', 'volume_ratio']].tail())

    # Validate
    validation = TechnicalIndicators.validate_indicators(test_df)
    print(f"\nValidation results:")
    for key, value in validation.items():
        print(f"  {key}: {value}")
