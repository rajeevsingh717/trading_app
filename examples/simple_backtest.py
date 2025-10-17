"""
Simple Backtest Example
Demonstrates how to run a basic backtest of the trading strategy.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data.data_collector import DataCollector
from data.database import DatabaseManager
from utils.indicators import calculate_indicators
from strategy.strategy_engine import TradingStrategy
from backtest.backtest_engine import BacktestEngine, BacktestConfig
from monitoring.logger import setup_logging

def run_simple_backtest():
    """Run a simple backtest on a few stocks."""

    # Setup logging
    logging_system = setup_logging(log_level="INFO")
    logger = logging_system.get_logger(__name__)

    logger.info("=" * 60)
    logger.info("Starting Simple Backtest Example")
    logger.info("=" * 60)

    # 1. Initialize components
    collector = DataCollector()
    strategy = TradingStrategy()
    config = BacktestConfig(
        starting_capital=10000.0,
        max_positions=3,
        max_position_size=1000.0
    )
    backtest = BacktestEngine(config)

    # 2. Select a few stocks to test
    test_tickers = ['AAPL', 'MSFT', 'GOOGL']
    logger.info(f"Testing strategy on: {', '.join(test_tickers)}")

    # 3. Collect data
    logger.info("\nCollecting historical data...")
    start_date = datetime.now() - timedelta(days=7)  # Last 7 days
    end_date = datetime.now()

    all_data = {}
    for ticker in test_tickers:
        logger.info(f"Fetching {ticker}...")
        df = collector.fetch_historical_data(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            interval='5m'
        )

        if df is not None and not df.empty:
            # Calculate indicators
            df = calculate_indicators(df)
            all_data[ticker] = df
            logger.info(f"  Loaded {len(df)} bars for {ticker}")
        else:
            logger.warning(f"  No data for {ticker}")

    if not all_data:
        logger.error("No data collected. Exiting.")
        return

    # 4. Run backtest simulation
    logger.info("\n" + "=" * 60)
    logger.info("Running Backtest Simulation")
    logger.info("=" * 60)

    # Get all timestamps (combine from all tickers and sort)
    all_timestamps = set()
    for df in all_data.values():
        all_timestamps.update(df['timestamp'].tolist())
    timestamps = sorted(all_timestamps)

    logger.info(f"Simulating {len(timestamps)} time periods...")

    for timestamp in timestamps:
        # Get current prices for all tickers
        current_prices = {}
        for ticker, df in all_data.items():
            ticker_data = df[df['timestamp'] == timestamp]
            if not ticker_data.empty:
                current_prices[ticker] = ticker_data.iloc[0]['close']

        # Update existing positions
        backtest.update_positions(current_prices, timestamp)

        # Check exit conditions for open positions
        for ticker in list(backtest.positions.keys()):
            if ticker not in current_prices:
                continue

            position = backtest.positions[ticker]
            current_price = current_prices[ticker]

            should_exit, reason = strategy.check_exit_conditions(
                position={'entry_price': position.entry_price, 'ticker': ticker},
                current_price=current_price,
                timestamp=timestamp,
                highest_price=position.highest_price
            )

            if should_exit:
                backtest.close_position(ticker, timestamp, current_price, reason)

        # Generate new signals
        for ticker, df in all_data.items():
            # Skip if already have position
            if ticker in backtest.positions:
                continue

            # Skip if can't open new position
            if not backtest.can_open_position():
                continue

            # Get data up to current timestamp
            historical_data = df[df['timestamp'] <= timestamp]
            if historical_data.empty:
                continue

            # Generate signals
            signals = strategy.generate_signals(
                ticker,
                historical_data,
                current_positions=list(backtest.positions.keys())
            )

            # Execute signals
            for signal in signals:
                if signal.signal_type == 'buy':
                    quantity = strategy.calculate_position_size(
                        backtest.capital,
                        signal.price
                    )

                    stop_loss = strategy.get_stop_loss_price(signal.price)
                    take_profit = strategy.get_take_profit_price(signal.price)

                    backtest.open_position(
                        ticker=ticker,
                        timestamp=timestamp,
                        price=signal.price,
                        quantity=quantity,
                        stop_loss=stop_loss,
                        take_profit=take_profit
                    )

        # Record equity
        backtest.record_equity(timestamp, current_prices)

    # 5. Close any remaining positions at end
    logger.info("\nClosing remaining positions...")
    final_prices = {ticker: df.iloc[-1]['close'] for ticker, df in all_data.items()}
    final_timestamp = timestamps[-1]

    for ticker in list(backtest.positions.keys()):
        if ticker in final_prices:
            backtest.close_position(
                ticker,
                final_timestamp,
                final_prices[ticker],
                "End of backtest"
            )

    # 6. Display results
    logger.info("\n" + "=" * 60)
    logger.info("Backtest Results")
    logger.info("=" * 60)

    metrics = backtest.get_performance_metrics()

    print(f"\n{'Metric':<30} {'Value':>15}")
    print("-" * 46)
    print(f"{'Starting Capital':<30} ${metrics['starting_capital']:>14,.2f}")
    print(f"{'Final Equity':<30} ${metrics['final_equity']:>14,.2f}")
    print(f"{'Total Return':<30} {metrics['total_return']:>14.2f}%")
    print(f"{'Max Drawdown':<30} {metrics['max_drawdown']:>14.2f}%")
    print()
    print(f"{'Total Trades':<30} {metrics['total_trades']:>15,}")
    print(f"{'Winning Trades':<30} {metrics['winning_trades']:>15,}")
    print(f"{'Losing Trades':<30} {metrics['losing_trades']:>15,}")
    print(f"{'Win Rate':<30} {metrics['win_rate']:>14.2f}%")
    print()
    print(f"{'Profit Factor':<30} {metrics['profit_factor']:>15.2f}")
    print(f"{'Sharpe Ratio':<30} {metrics['sharpe_ratio']:>15.2f}")
    print(f"{'Avg Win':<30} ${metrics['avg_win']:>14.2f}")
    print(f"{'Avg Loss':<30} ${metrics['avg_loss']:>14.2f}")
    print(f"{'Largest Win':<30} ${metrics['largest_win']:>14.2f}")
    print(f"{'Largest Loss':<30} ${metrics['largest_loss']:>14.2f}")
    print()
    print(f"{'Total Commission':<30} ${metrics['total_commission']:>14.2f}")
    print(f"{'Total Slippage':<30} ${metrics['total_slippage']:>14.2f}")

    # 7. Show trade history
    trades_df = backtest.get_trades_df()
    if not trades_df.empty:
        print("\n" + "=" * 60)
        print("Trade History")
        print("=" * 60)
        print(trades_df.to_string(index=False))

    logger.info("\nBacktest completed successfully!")


if __name__ == "__main__":
    run_simple_backtest()
