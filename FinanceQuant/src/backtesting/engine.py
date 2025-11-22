"""Backtesting engine for trading strategies."""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Vectorized backtesting engine for trading strategies.

    Simulates strategy performance with transaction costs and slippage.
    """

    def __init__(
        self,
        initial_capital: float = 100000,
        commission: float = 0.001,
        slippage: float = 0.0005
    ):
        """
        Initialize backtest engine.

        Args:
            initial_capital: Starting capital
            commission: Commission rate (e.g., 0.001 = 0.1%)
            slippage: Slippage rate (e.g., 0.0005 = 0.05%)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

        logger.info(f"Initialized BacktestEngine (capital=${initial_capital:,.2f}, "
                   f"commission={commission:.4f}, slippage={slippage:.4f})")

    def run(
        self,
        signals: np.ndarray,
        prices: np.ndarray,
        dates: Optional[pd.DatetimeIndex] = None
    ) -> Dict[str, Any]:
        """
        Run backtest.

        Args:
            signals: Trading signals (-1, 0, 1)
            prices: Price data
            dates: Optional datetime index

        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Running backtest on {len(signals)} periods")

        # Initialize
        positions = np.zeros(len(signals))
        cash = np.zeros(len(signals))
        holdings = np.zeros(len(signals))
        equity = np.zeros(len(signals))

        cash[0] = self.initial_capital

        # Execute trades
        for i in range(1, len(signals)):
            # Previous position
            prev_position = positions[i-1]

            # New signal
            signal = signals[i]

            # Determine trade
            trade_size = signal - prev_position

            if trade_size != 0:
                # Execute trade with costs
                trade_value = abs(trade_size) * prices[i]
                cost = trade_value * (self.commission + self.slippage)

                # Update cash
                cash[i] = cash[i-1] - trade_size * prices[i] - cost
            else:
                cash[i] = cash[i-1]

            # Update position
            positions[i] = signal

            # Update holdings value
            holdings[i] = positions[i] * prices[i]

            # Total equity
            equity[i] = cash[i] + holdings[i]

        # Calculate metrics
        returns = self._calculate_returns(equity)
        metrics = self._calculate_metrics(equity, returns, dates)

        # Build results
        results = {
            'equity': equity,
            'positions': positions,
            'cash': cash,
            'holdings': holdings,
            'returns': returns,
            'metrics': metrics
        }

        logger.info(f"Backtest complete - Total Return: {metrics['total_return']:.2%}")

        return results

    def _calculate_returns(self, equity: np.ndarray) -> np.ndarray:
        """Calculate returns from equity curve."""
        returns = np.diff(equity) / equity[:-1]
        returns = np.insert(returns, 0, 0)  # First return is 0
        return returns

    def _calculate_metrics(
        self,
        equity: np.ndarray,
        returns: np.ndarray,
        dates: Optional[pd.DatetimeIndex] = None
    ) -> Dict[str, float]:
        """Calculate performance metrics."""
        # Total return
        total_return = (equity[-1] - self.initial_capital) / self.initial_capital

        # Annualized return
        n_periods = len(equity)
        years = n_periods / 252  # Assume 252 trading days per year

        if years > 0:
            annualized_return = (1 + total_return) ** (1 / years) - 1
        else:
            annualized_return = 0.0

        # Volatility
        volatility = returns.std() * np.sqrt(252)

        # Sharpe ratio (assuming 0% risk-free rate)
        if volatility > 0:
            sharpe_ratio = annualized_return / volatility
        else:
            sharpe_ratio = 0.0

        # Maximum drawdown
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max
        max_drawdown = drawdown.min()

        # Win rate
        winning_trades = (returns > 0).sum()
        total_trades = (returns != 0).sum()
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

        # Profit factor
        gross_profit = returns[returns > 0].sum()
        gross_loss = abs(returns[returns < 0].sum())

        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        else:
            profit_factor = 0.0

        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]

        if len(downside_returns) > 0:
            downside_dev = downside_returns.std() * np.sqrt(252)
            sortino_ratio = annualized_return / downside_dev if downside_dev > 0 else 0.0
        else:
            sortino_ratio = 0.0

        # Calmar ratio
        if max_drawdown < 0:
            calmar_ratio = annualized_return / abs(max_drawdown)
        else:
            calmar_ratio = 0.0

        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': int(total_trades)
        }


def main():
    """Example usage."""
    print("=" * 80)
    print("Backtest Engine - Example")
    print("=" * 80)

    # Generate synthetic price data
    np.random.seed(42)

    n_periods = 252 * 3  # 3 years
    prices = 100 * np.exp(np.cumsum(np.random.randn(n_periods) * 0.02))

    print(f"\nGenerated {n_periods} periods of price data")
    print(f"  Starting price: ${prices[0]:.2f}")
    print(f"  Ending price: ${prices[-1]:.2f}")

    # Test 1: Buy and hold
    print("\n[1] Buy and Hold Strategy:")

    signals_bh = np.ones(n_periods)  # Always long

    engine = BacktestEngine(
        initial_capital=100000,
        commission=0.001,
        slippage=0.0005
    )

    results_bh = engine.run(signals_bh, prices)

    metrics = results_bh['metrics']
    print(f"  Total Return: {metrics['total_return']:.2%}")
    print(f"  Annualized Return: {metrics['annualized_return']:.2%}")
    print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")

    # Test 2: Simple moving average crossover
    print("\n[2] Moving Average Crossover:")

    # Calculate moving averages
    fast_ma = pd.Series(prices).rolling(window=50).mean().values
    slow_ma = pd.Series(prices).rolling(window=200).mean().values

    # Generate signals
    signals_ma = np.zeros(n_periods)

    for i in range(200, n_periods):
        if fast_ma[i] > slow_ma[i]:
            signals_ma[i] = 1  # Long
        else:
            signals_ma[i] = 0  # Flat

    results_ma = engine.run(signals_ma, prices)

    metrics_ma = results_ma['metrics']
    print(f"  Total Return: {metrics_ma['total_return']:.2%}")
    print(f"  Sharpe Ratio: {metrics_ma['sharpe_ratio']:.2f}")
    print(f"  Total Trades: {metrics_ma['total_trades']}")
    print(f"  Win Rate: {metrics_ma['win_rate']:.2%}")

    # Test 3: Mean reversion
    print("\n[3] Mean Reversion Strategy:")

    # Calculate z-score
    window = 20
    rolling_mean = pd.Series(prices).rolling(window=window).mean().values
    rolling_std = pd.Series(prices).rolling(window=window).std().values

    signals_mr = np.zeros(n_periods)

    for i in range(window, n_periods):
        if rolling_std[i] > 0:
            z_score = (prices[i] - rolling_mean[i]) / rolling_std[i]

            if z_score < -2:
                signals_mr[i] = 1  # Buy when oversold
            elif z_score > 2:
                signals_mr[i] = -1  # Sell when overbought
            elif abs(z_score) < 0.5:
                signals_mr[i] = 0  # Exit when near mean

    results_mr = engine.run(signals_mr, prices)

    metrics_mr = results_mr['metrics']
    print(f"  Total Return: {metrics_mr['total_return']:.2%}")
    print(f"  Sharpe Ratio: {metrics_mr['sharpe_ratio']:.2f}")
    print(f"  Profit Factor: {metrics_mr['profit_factor']:.2f}")

    # Compare strategies
    print("\n[4] Strategy Comparison:")

    strategies = {
        'Buy & Hold': metrics,
        'MA Crossover': metrics_ma,
        'Mean Reversion': metrics_mr
    }

    print(f"\n  {'Strategy':<20} {'Return':>10} {'Sharpe':>8} {'MaxDD':>8}")
    print("  " + "-" * 50)

    for name, m in strategies.items():
        print(f"  {name:<20} {m['total_return']:>9.2%} {m['sharpe_ratio']:>7.2f} "
              f"{m['max_drawdown']:>7.2%}")

    # Analyze equity curves
    print("\n[5] Final Equity Values:")
    print(f"  Buy & Hold: ${results_bh['equity'][-1]:,.2f}")
    print(f"  MA Crossover: ${results_ma['equity'][-1]:,.2f}")
    print(f"  Mean Reversion: ${results_mr['equity'][-1]:,.2f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
