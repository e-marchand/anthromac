"""Value at Risk (VaR) calculations."""

import numpy as np
from scipy import stats
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ValueAtRisk:
    """
    Calculate Value at Risk using multiple methods.

    Estimates potential loss in portfolio value at given confidence level.
    """

    def __init__(
        self,
        method: str = 'historical',
        confidence: float = 0.95
    ):
        """
        Initialize VaR calculator.

        Args:
            method: Calculation method ('historical', 'parametric', 'monte_carlo')
            confidence: Confidence level (e.g., 0.95 for 95%)
        """
        self.method = method
        self.confidence = confidence

        logger.info(f"Initialized ValueAtRisk (method={method}, confidence={confidence})")

    def calculate(
        self,
        returns: np.ndarray,
        portfolio_value: float,
        holding_period: int = 1
    ) -> float:
        """
        Calculate VaR.

        Args:
            returns: Historical returns
            portfolio_value: Current portfolio value
            holding_period: Holding period in days

        Returns:
            VaR (positive number representing potential loss)
        """
        if self.method == 'historical':
            var = self._historical_var(returns, holding_period)

        elif self.method == 'parametric':
            var = self._parametric_var(returns, holding_period)

        elif self.method == 'monte_carlo':
            var = self._monte_carlo_var(returns, holding_period)

        else:
            raise ValueError(f"Unknown method: {self.method}")

        # Convert to dollar amount
        var_dollar = abs(var * portfolio_value)

        logger.info(f"VaR ({self.confidence:.0%}, {holding_period}d): ${var_dollar:,.2f}")

        return var_dollar

    def calculate_cvar(
        self,
        returns: np.ndarray,
        portfolio_value: float,
        holding_period: int = 1
    ) -> float:
        """
        Calculate Conditional Value at Risk (CVaR / Expected Shortfall).

        CVaR is the expected loss given that loss exceeds VaR.

        Args:
            returns: Historical returns
            portfolio_value: Current portfolio value
            holding_period: Holding period

        Returns:
            CVaR
        """
        if holding_period > 1:
            returns = returns * np.sqrt(holding_period)

        # Get VaR threshold
        var_percentile = 1 - self.confidence
        var_threshold = np.percentile(returns, var_percentile * 100)

        # Calculate CVaR as mean of returns below VaR
        tail_returns = returns[returns <= var_threshold]

        if len(tail_returns) > 0:
            cvar = abs(tail_returns.mean())
        else:
            cvar = abs(var_threshold)

        cvar_dollar = cvar * portfolio_value

        logger.info(f"CVaR ({self.confidence:.0%}): ${cvar_dollar:,.2f}")

        return cvar_dollar

    def _historical_var(
        self,
        returns: np.ndarray,
        holding_period: int
    ) -> float:
        """Calculate VaR using historical simulation."""
        # Scale returns for holding period
        if holding_period > 1:
            returns = returns * np.sqrt(holding_period)

        # Find percentile
        var_percentile = (1 - self.confidence) * 100
        var = np.percentile(returns, var_percentile)

        return var

    def _parametric_var(
        self,
        returns: np.ndarray,
        holding_period: int
    ) -> float:
        """Calculate VaR using parametric (variance-covariance) method."""
        # Assume normal distribution
        mean = returns.mean()
        std = returns.std()

        # Z-score for confidence level
        z_score = stats.norm.ppf(1 - self.confidence)

        # VaR formula
        var = mean + z_score * std

        # Scale for holding period
        if holding_period > 1:
            var = var * np.sqrt(holding_period)

        return var

    def _monte_carlo_var(
        self,
        returns: np.ndarray,
        holding_period: int,
        n_simulations: int = 10000
    ) -> float:
        """Calculate VaR using Monte Carlo simulation."""
        # Estimate parameters from historical data
        mean = returns.mean()
        std = returns.std()

        # Simulate returns
        simulated_returns = np.random.normal(mean, std, n_simulations)

        # Scale for holding period
        if holding_period > 1:
            simulated_returns = simulated_returns * np.sqrt(holding_period)

        # Calculate VaR from simulations
        var_percentile = (1 - self.confidence) * 100
        var = np.percentile(simulated_returns, var_percentile)

        return var


class PortfolioRiskMetrics:
    """Calculate various portfolio risk metrics."""

    def __init__(self, returns: np.ndarray):
        """
        Initialize risk metrics calculator.

        Args:
            returns: Return series
        """
        self.returns = returns

        logger.info(f"Initialized PortfolioRiskMetrics ({len(returns)} periods)")

    def volatility(self, annualize: bool = True) -> float:
        """
        Calculate volatility (standard deviation of returns).

        Args:
            annualize: Whether to annualize (assumes daily returns)

        Returns:
            Volatility
        """
        vol = self.returns.std()

        if annualize:
            vol = vol * np.sqrt(252)

        return vol

    def sharpe_ratio(
        self,
        risk_free_rate: float = 0.0,
        annualize: bool = True
    ) -> float:
        """
        Calculate Sharpe ratio.

        Args:
            risk_free_rate: Risk-free rate
            annualize: Whether to annualize

        Returns:
            Sharpe ratio
        """
        excess_return = self.returns.mean() - risk_free_rate / 252
        vol = self.returns.std()

        if vol == 0:
            return 0.0

        sharpe = excess_return / vol

        if annualize:
            sharpe = sharpe * np.sqrt(252)

        return sharpe

    def max_drawdown(self) -> float:
        """
        Calculate maximum drawdown.

        Returns:
            Maximum drawdown (positive number)
        """
        cumulative = (1 + self.returns).cumprod()
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max

        return abs(drawdown.min())

    def downside_deviation(self, target: float = 0.0) -> float:
        """
        Calculate downside deviation.

        Args:
            target: Target return (default: 0)

        Returns:
            Downside deviation
        """
        downside_returns = self.returns[self.returns < target] - target
        downside_dev = np.sqrt((downside_returns ** 2).mean())

        return downside_dev * np.sqrt(252)


def main():
    """Example usage."""
    print("=" * 80)
    print("Value at Risk - Example")
    print("=" * 80)

    # Generate synthetic returns
    np.random.seed(42)

    n_periods = 252 * 3
    returns = np.random.normal(0.0005, 0.02, n_periods)  # Daily returns

    portfolio_value = 1000000  # $1M portfolio

    print(f"\nPortfolio value: ${portfolio_value:,.2f}")
    print(f"Historical returns: {n_periods} days")
    print(f"  Mean daily return: {returns.mean():.4%}")
    print(f"  Daily volatility: {returns.std():.4%}")

    # Test different VaR methods
    print("\n[1] VaR Calculations (95% confidence, 1-day):")

    methods = ['historical', 'parametric', 'monte_carlo']

    for method in methods:
        var_calc = ValueAtRisk(method=method, confidence=0.95)

        var = var_calc.calculate(returns, portfolio_value, holding_period=1)
        cvar = var_calc.calculate_cvar(returns, portfolio_value, holding_period=1)

        print(f"\n  {method.title()} Method:")
        print(f"    VaR: ${var:,.2f}")
        print(f"    CVaR: ${cvar:,.2f}")

    # Test different confidence levels
    print("\n[2] VaR at Different Confidence Levels (Historical):")

    var_calc = ValueAtRisk(method='historical')

    confidences = [0.90, 0.95, 0.99]

    for conf in confidences:
        var_calc.confidence = conf
        var = var_calc.calculate(returns, portfolio_value)

        print(f"  {conf:.0%} confidence: ${var:,.2f}")

    # Test different holding periods
    print("\n[3] VaR for Different Holding Periods (95% confidence):")

    var_calc = ValueAtRisk(method='historical', confidence=0.95)

    periods = [1, 5, 10, 20]

    for period in periods:
        var = var_calc.calculate(returns, portfolio_value, holding_period=period)

        print(f"  {period:2d}-day VaR: ${var:,.2f}")

    # Portfolio risk metrics
    print("\n[4] Portfolio Risk Metrics:")

    risk_metrics = PortfolioRiskMetrics(returns)

    vol = risk_metrics.volatility()
    sharpe = risk_metrics.sharpe_ratio()
    max_dd = risk_metrics.max_drawdown()
    downside_dev = risk_metrics.downside_deviation()

    print(f"  Annualized Volatility: {vol:.2%}")
    print(f"  Sharpe Ratio: {sharpe:.2f}")
    print(f"  Maximum Drawdown: {max_dd:.2%}")
    print(f"  Downside Deviation: {downside_dev:.2%}")

    # Stress test scenario
    print("\n[5] Stress Test - Market Crash:")

    # Simulate crash: 5 consecutive down days with -5% each
    crash_returns = np.append(returns, [-0.05] * 5)

    var_stress = ValueAtRisk(method='historical', confidence=0.95)
    var_stressed = var_stress.calculate(crash_returns, portfolio_value)

    print(f"  Normal VaR: ${var:,.2f}")
    print(f"  Stressed VaR: ${var_stressed:,.2f}")
    print(f"  Increase: {(var_stressed - var) / var:.1%}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
