# S&P 500 Algorithmic Trading System

A rule-based algorithmic trading system for S&P 500 stocks with focus on simplicity, reliability, and risk management.

## Overview

This system implements an intraday day trading strategy that:
- Executes 2-5 trades per day
- Trades only S&P 500 constituent stocks
- Uses strict rule-based decision making
- Implements robust risk management
- Supports paper trading and live trading

## Features

- **Data Collection**: Historical and real-time market data via yfinance
- **Technical Analysis**: SMA, RSI, ATR, Volume indicators
- **Trading Strategy**: Rule-based entry/exit conditions
- **Backtesting**: Realistic simulation with slippage and commission
- **Risk Management**: Position sizing, stop-loss, daily loss limits
- **Monitoring**: Structured logging and performance tracking
- **Database**: SQLite for data persistence

## Project Structure

```
trading_app/
├── src/
│   ├── data/              # Data collection and S&P 500 tickers
│   │   ├── sp500_tickers.py
│   │   ├── data_collector.py
│   │   └── database.py
│   ├── strategy/          # Trading strategy implementation
│   │   └── strategy_engine.py
│   ├── backtest/          # Backtesting framework
│   │   └── backtest_engine.py
│   ├── utils/             # Utilities (indicators, risk management)
│   │   ├── indicators.py
│   │   └── risk_manager.py
│   └── monitoring/        # Logging and monitoring
│       └── logger.py
├── tests/                 # Unit tests
├── config/                # Configuration
├── data/                  # Data storage
├── logs/                  # Log files
└── requirements.txt       # Dependencies
```

## Installation

1. **Clone the repository** (if using git):
```bash
cd trading_app
```

2. **Create virtual environment**:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

Edit `.env` file with your settings:

```env
# Alpaca API (for paper/live trading)
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Trading Parameters
PAPER_TRADING=true
STARTING_CAPITAL=10000
MAX_POSITION_SIZE=1000
MAX_POSITIONS=5
DAILY_LOSS_LIMIT=100
```

## Trading Strategy

### Entry Conditions (ALL must be true):
1. **Trend Filter**: Price > 50-period SMA
2. **Momentum**: RSI(14) between 40-70
3. **Volume**: Current volume > 1.2× 20-period average
4. **Volatility**: ATR(14) > minimum threshold
5. **Time**: Between 10:00 AM - 3:00 PM ET
6. **Price**: Stock price $20 - $500

### Exit Conditions (ANY triggers exit):
1. **Stop Loss**: -1.0% from entry
2. **Take Profit**: +1.5% from entry
3. **Time Stop**: 3:55 PM ET (close all positions)
4. **Trailing Stop**: After +1% profit, trail by 0.5%

## Usage

### 1. Fetch S&P 500 Tickers
```python
from src.data.sp500_tickers import get_sp500_tickers

tickers = get_sp500_tickers(force_refresh=True)
print(f"Found {len(tickers)} tickers")
```

### 2. Collect Historical Data
```python
from src.data.data_collector import DataCollector
from datetime import datetime, timedelta

collector = DataCollector()
df = collector.fetch_historical_data(
    ticker='AAPL',
    start_date=datetime.now() - timedelta(days=30),
    interval='5m'
)
```

### 3. Calculate Indicators
```python
from src.utils.indicators import calculate_indicators

df = calculate_indicators(df)
print(df[['close', 'sma_50', 'rsi', 'atr']].tail())
```

### 4. Run Backtest
```python
from src.backtest.backtest_engine import BacktestEngine, BacktestConfig

config = BacktestConfig(starting_capital=10000)
engine = BacktestEngine(config)

# Run backtest (implementation in full script)
# ...

metrics = engine.get_performance_metrics()
print(f"Total Return: {metrics['total_return_pct']:.2f}%")
print(f"Win Rate: {metrics['win_rate']:.2f}%")
```

## Testing

Run unit tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## Risk Management

The system includes multiple safety features:

- **Position Limits**: Max 5 concurrent positions, $1000 per position
- **Daily Loss Limit**: Trading halts if daily loss exceeds $100
- **Weekly Loss Limit**: Review required if weekly loss exceeds $300
- **Max Drawdown**: System halts if drawdown exceeds 15%
- **Time Stops**: All positions closed by 3:55 PM ET

## Performance Metrics

The system tracks:
- Total return and annualized return
- Sharpe ratio and Sortino ratio
- Maximum drawdown
- Win rate and profit factor
- Average profit per trade
- Trade statistics (wins, losses, average holding time)

## Logging

Logs are organized by category:
- `application.log`: General application logs
- `trades.log`: Trade execution details
- `data.log`: Data collection events
- `errors.log`: Errors and exceptions
- `performance.log`: Performance metrics
- `structured.log`: JSON formatted logs for analysis

## Development Roadmap

### Phase 1: Foundation (Weeks 1-2) ✅
- [x] Project setup and environment
- [x] Data collection infrastructure
- [x] S&P 500 ticker management
- [x] Technical indicators
- [x] Strategy engine
- [x] Backtesting framework
- [x] Risk management
- [x] Logging system

### Phase 2: Testing (Weeks 3-4)
- [ ] Comprehensive unit tests
- [ ] Integration tests
- [ ] Backtest on historical data
- [ ] Strategy optimization
- [ ] Performance analysis

### Phase 3: Paper Trading (Weeks 7-16)
- [ ] Alpaca API integration
- [ ] Real-time data feed
- [ ] Paper trading execution
- [ ] Monitoring dashboard
- [ ] 8 weeks minimum paper trading

### Phase 4: Live Trading (Week 17+)
- [ ] Small capital deployment
- [ ] Intensive monitoring
- [ ] Gradual position scaling
- [ ] Continuous improvement

## Important Notes

⚠️ **Risk Disclosure**:
- Trading involves substantial risk of loss
- Past performance does not guarantee future results
- Start with capital you can afford to lose
- This system is for educational purposes
- Continuous monitoring required

## Contributing

This is a personal trading system. Contributions are not currently accepted.

## License

Private project. All rights reserved.

## Support

For issues or questions, refer to the documentation in `claude.md` and `specs.md`.

---

**Last Updated**: October 2024
**Version**: 1.0.0
