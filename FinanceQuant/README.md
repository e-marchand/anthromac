# FinanceQuant - Algorithmic Trading Research

Comprehensive backtesting framework and strategy development platform for algorithmic trading.

## Features

### Trading Strategies
- **Statistical Arbitrage**: Pairs trading, mean reversion
- **Machine Learning**: Random Forest, LSTM price prediction
- **Portfolio Optimization**: Black-Litterman, Risk Parity
- **Technical Analysis**: Moving averages, RSI, MACD, Bollinger Bands
- **Options**: Black-Scholes pricing, Greeks calculation

### Backtesting Engine
- Vectorized backtesting for speed
- Event-driven backtesting for accuracy
- Transaction costs and slippage modeling
- Position sizing and risk management
- Walk-forward optimization

### Risk Management
- Value at Risk (VaR) - Historical, Parametric, Monte Carlo
- Maximum drawdown constraints
- Position sizing with Kelly Criterion
- Correlation analysis
- Stress testing scenarios
- Portfolio rebalancing

### Data Management
- Multiple data sources support
- OHLCV data handling
- Order book data processing
- Alternative data integration
- Data cleaning and validation

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Simple Moving Average Crossover

```python
from src.strategies.moving_average import MovingAverageCrossover
from src.backtesting.engine import BacktestEngine
from src.data.loader import load_ohlcv

# Load data
data = load_ohlcv('AAPL', start='2020-01-01', end='2023-01-01')

# Initialize strategy
strategy = MovingAverageCrossover(
    fast_period=50,
    slow_period=200
)

# Create backtest engine
engine = BacktestEngine(
    initial_capital=100000,
    commission=0.001,
    slippage=0.0005
)

# Run backtest
results = engine.run(strategy, data)

# Print results
print(f"Total Return: {results['total_return']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2%}")
```

### Pairs Trading Strategy

```python
from src.strategies.pairs_trading import PairsTradingStrategy

# Initialize strategy
strategy = PairsTradingStrategy(
    symbol1='AAPL',
    symbol2='MSFT',
    window=30,
    entry_threshold=2.0,
    exit_threshold=0.5
)

# Run backtest
results = engine.run(strategy, data)
```

### Portfolio Optimization

```python
from src.portfolio.optimizer import PortfolioOptimizer

# Initialize optimizer
optimizer = PortfolioOptimizer(
    method='risk_parity',
    risk_aversion=2.0
)

# Get optimal weights
weights = optimizer.optimize(
    returns=historical_returns,
    constraints={'min_weight': 0.0, 'max_weight': 0.3}
)

print("Optimal weights:", weights)
```

### Value at Risk Calculation

```python
from src.risk.var import ValueAtRisk

# Calculate VaR
var_calculator = ValueAtRisk(method='historical', confidence=0.95)

var = var_calculator.calculate(
    returns=portfolio_returns,
    portfolio_value=1000000
)

print(f"95% VaR: ${var:,.2f}")
```

## Advanced Usage

### Machine Learning Strategy

```python
from src.strategies.ml.random_forest import RandomForestStrategy

# Initialize ML strategy
strategy = RandomForestStrategy(
    features=['returns', 'volume', 'volatility'],
    lookback=20,
    n_estimators=100
)

# Train on historical data
strategy.train(train_data)

# Backtest
results = engine.run(strategy, test_data)
```

### Options Pricing

```python
from src.options.black_scholes import BlackScholes

# Price European call option
bs = BlackScholes(
    S=100,  # Stock price
    K=105,  # Strike price
    T=0.5,  # Time to expiration (years)
    r=0.05,  # Risk-free rate
    sigma=0.2  # Volatility
)

call_price = bs.call_price()
put_price = bs.put_price()

# Calculate Greeks
greeks = bs.greeks()
print(f"Delta: {greeks['delta']:.4f}")
print(f"Gamma: {greeks['gamma']:.4f}")
print(f"Vega: {greeks['vega']:.4f}")
```

### Kelly Criterion Position Sizing

```python
from src.risk.position_sizing import KellyCriterion

kelly = KellyCriterion(
    win_rate=0.6,
    avg_win=0.05,
    avg_loss=0.03
)

# Get optimal position size
position_size = kelly.calculate_position_size(
    capital=100000,
    max_position=0.2  # Maximum 20% of capital
)
```

## Backtesting Features

### Performance Metrics

- **Returns**: Total, annualized, rolling
- **Risk**: Sharpe ratio, Sortino ratio, Calmar ratio
- **Drawdown**: Maximum, average, duration
- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Gross profit / gross loss

### Visualization

```python
from src.visualization.plotter import StrategyPlotter

plotter = StrategyPlotter(results)

# Plot equity curve
plotter.plot_equity()

# Plot drawdown
plotter.plot_drawdown()

# Plot monthly returns heatmap
plotter.plot_monthly_returns()
```

## Strategy Development

### Custom Strategy Template

```python
from src.strategies.base import Strategy

class MyStrategy(Strategy):
    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2

    def generate_signals(self, data):
        """Generate trading signals."""
        signals = []

        for i in range(len(data)):
            # Your logic here
            if self._should_buy(data[:i+1]):
                signals.append(1)  # Buy
            elif self._should_sell(data[:i+1]):
                signals.append(-1)  # Sell
            else:
                signals.append(0)  # Hold

        return signals

    def _should_buy(self, data):
        # Implement buy logic
        pass

    def _should_sell(self, data):
        # Implement sell logic
        pass
```

## Risk Management

### Portfolio Risk Metrics

```python
from src.risk.metrics import RiskMetrics

metrics = RiskMetrics(returns=portfolio_returns)

# Calculate various risk measures
print(f"Volatility: {metrics.volatility():.4f}")
print(f"Skewness: {metrics.skewness():.4f}")
print(f"Kurtosis: {metrics.kurtosis():.4f}")
print(f"VaR (95%): {metrics.var(0.95):.4f}")
print(f"CVaR (95%): {metrics.cvar(0.95):.4f}")
```

### Correlation Analysis

```python
from src.risk.correlation import CorrelationAnalyzer

analyzer = CorrelationAnalyzer(returns_matrix)

# Get correlation matrix
corr_matrix = analyzer.correlation_matrix()

# Find highly correlated pairs
pairs = analyzer.find_correlated_pairs(threshold=0.7)
```

## Performance Benchmarks

### Typical Backtest Performance

| Strategy Type | Sharpe Ratio | Max Drawdown | Annual Return |
|---------------|--------------|--------------|---------------|
| MA Crossover | 0.8-1.2 | 15-25% | 8-15% |
| Mean Reversion | 1.2-1.8 | 10-20% | 12-20% |
| ML-Based | 1.5-2.5 | 8-15% | 15-25% |
| Pairs Trading | 1.0-1.5 | 12-18% | 10-18% |

*Note: Past performance does not guarantee future results*

## Project Structure

```
FinanceQuant/
├── README.md
├── requirements.txt
├── src/
│   ├── strategies/
│   │   ├── base.py              # Base strategy class
│   │   ├── moving_average.py    # MA crossover
│   │   ├── mean_reversion.py    # Mean reversion
│   │   └── pairs_trading.py     # Pairs trading
│   ├── backtesting/
│   │   ├── engine.py            # Backtest engine
│   │   └── metrics.py           # Performance metrics
│   ├── portfolio/
│   │   ├── optimizer.py         # Portfolio optimization
│   │   └── rebalancer.py        # Rebalancing logic
│   ├── risk/
│   │   ├── var.py               # Value at Risk
│   │   ├── position_sizing.py   # Position sizing
│   │   └── metrics.py           # Risk metrics
│   ├── options/
│   │   └── black_scholes.py     # Options pricing
│   └── data/
│       └── loader.py            # Data loading
└── examples/
    ├── simple_backtest.py
    ├── portfolio_optimization.py
    └── risk_analysis.py
```

## Best Practices

1. **Data Quality**: Always validate and clean data before backtesting
2. **Overfitting**: Use walk-forward analysis and out-of-sample testing
3. **Transaction Costs**: Include realistic costs and slippage
4. **Position Sizing**: Never risk more than 1-2% per trade
5. **Diversification**: Maintain uncorrelated positions
6. **Risk Management**: Always use stop losses and position limits

## Common Pitfalls

- **Look-ahead bias**: Using future information in backtests
- **Survivorship bias**: Only testing on surviving stocks
- **Data-snooping**: Over-optimizing on historical data
- **Ignoring costs**: Not accounting for commissions and slippage
- **Curve fitting**: Creating strategies that work only on historical data

## Contributing

Contributions welcome! Priority areas:
- Additional strategy implementations
- Machine learning models for trading
- Multi-asset portfolio optimization
- Real-time trading integration
- Advanced risk models

## Disclaimer

This software is for educational and research purposes only. Trading carries significant risk. Never trade with money you cannot afford to lose. Past performance is not indicative of future results.

## References

- "Advances in Financial Machine Learning" by Marcos López de Prado
- "Quantitative Trading" by Ernest Chan
- "Algorithmic Trading" by Jeffrey Bacidore
- "Portfolio Management" by Eugene Fama

## License

MIT License
