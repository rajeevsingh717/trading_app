# Getting Started with the Trading System

## Quick Start Guide

### 1. Setup Environment

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 2. First Steps

#### Test S&P 500 Ticker Fetching
```bash
python src/data/sp500_tickers.py
```

#### Test Data Collection
```bash
python src/data/data_collector.py
```

#### Test Technical Indicators
```bash
python src/utils/indicators.py
```

#### Test Strategy Engine
```bash
python src/strategy/strategy_engine.py
```

#### Test Backtest Engine
```bash
python src/backtest/backtest_engine.py
```

### 3. Run Simple Backtest Example

```bash
python examples/simple_backtest.py
```

This will:
1. Fetch recent data for AAPL, MSFT, GOOGL
2. Calculate technical indicators
3. Run strategy simulation
4. Display performance metrics

### 4. Run Unit Tests

```bash
# Install pytest if not already installed
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Next Steps

### Phase 1: Learn the System (Week 1)
- [ ] Read through `specs.md` to understand strategy rules
- [ ] Review `claude.md` for coding standards
- [ ] Run all test modules individually
- [ ] Understand the data flow

### Phase 2: Data Collection (Week 2)
- [ ] Set up data collection for S&P 500 stocks
- [ ] Download historical data (5-minute bars)
- [ ] Verify data quality
- [ ] Store data in database

### Phase 3: Backtesting (Weeks 3-4)
- [ ] Run backtests on historical data (2+ years)
- [ ] Analyze performance metrics
- [ ] Optimize parameters if needed
- [ ] Validate strategy effectiveness

### Phase 4: Paper Trading Setup (Weeks 5-6)
- [ ] Get Alpaca API keys (paper trading)
- [ ] Integrate real-time data feed
- [ ] Build trading bot
- [ ] Create monitoring dashboard

### Phase 5: Paper Trading (Weeks 7-16)
- [ ] Run paper trading for 8+ weeks
- [ ] Monitor daily performance
- [ ] Compare to backtest results
- [ ] Fix any bugs
- [ ] Build confidence in system

### Phase 6: Live Trading (Week 17+)
- [ ] Start with small capital ($5,000-$10,000)
- [ ] Monitor intensively
- [ ] Gradually increase position sizes
- [ ] Keep detailed trading journal

## Important Files to Review

1. **specs.md** - Complete system specifications
2. **claude.md** - Coding standards and best practices
3. **README.md** - Project overview and usage
4. **config/config.py** - Configuration settings
5. **src/strategy/strategy_engine.py** - Trading strategy logic

## Common Commands

```bash
# Activate environment
source .venv/bin/activate

# Run backtest example
python examples/simple_backtest.py

# Run tests
pytest tests/ -v

# Check code style
flake8 src/

# Format code
black src/

# Type checking
mypy src/
```

## Configuration Tips

### Environment Variables (.env)

```env
# For Paper Trading
PAPER_TRADING=true
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# For Live Trading (BE CAREFUL!)
PAPER_TRADING=false
ALPACA_BASE_URL=https://api.alpaca.markets

# Risk Limits (adjust based on your capital)
STARTING_CAPITAL=10000
MAX_POSITION_SIZE=1000
MAX_POSITIONS=5
DAILY_LOSS_LIMIT=100
WEEKLY_LOSS_LIMIT=300
```

### Strategy Parameters (config/config.py)

Key parameters you can adjust:
- `MIN_STOCK_PRICE`: Minimum stock price (default: $20)
- `MAX_STOCK_PRICE`: Maximum stock price (default: $500)
- `RSI_LOWER_BOUND`: RSI lower threshold (default: 40)
- `RSI_UPPER_BOUND`: RSI upper threshold (default: 70)
- `STOP_LOSS_PERCENT`: Stop loss % (default: 1.0%)
- `TAKE_PROFIT_PERCENT`: Take profit % (default: 1.5%)

## Troubleshooting

### "No module named 'src'"
- Make sure you're in the project root directory
- Check that `__init__.py` files exist in all packages

### Data fetching errors
- Check internet connection
- yfinance has rate limits - add delays between requests
- 5-minute data only available for last 60 days

### Backtest shows no trades
- Check that data has sufficient history for indicators
- Verify entry conditions aren't too strict
- Review logs for rejection reasons

### Import errors
- Activate virtual environment: `source .venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

## Safety Checklist

Before going live:
- [ ] Tested extensively in backtest
- [ ] 8+ weeks successful paper trading
- [ ] All risk limits configured
- [ ] Emergency stop procedure documented
- [ ] Only using capital you can afford to lose
- [ ] Understand tax implications
- [ ] Have monitoring system in place
- [ ] Reviewed all code thoroughly

## Resources

- **Alpaca API Docs**: https://alpaca.markets/docs/
- **yfinance Docs**: https://pypi.org/project/yfinance/
- **Pandas Docs**: https://pandas.pydata.org/docs/
- **Project Issues**: See logs/ directory for error logs

## Support

For questions or issues:
1. Check the logs in `logs/` directory
2. Review `specs.md` and `claude.md`
3. Run unit tests to verify system integrity
4. Check configuration in `.env` file

---

**Remember**: This is real money (eventually). Start small, test thoroughly, and never risk more than you can afford to lose.
