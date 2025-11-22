"""Black-Scholes options pricing model."""

import numpy as np
from scipy import stats
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class BlackScholes:
    """
    Black-Scholes option pricing model.

    Prices European call and put options and calculates Greeks.
    """

    def __init__(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0.0
    ):
        """
        Initialize Black-Scholes model.

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate (annual)
            sigma: Volatility (annual)
            q: Dividend yield (annual)
        """
        self.S = S
        self.K = K
        self.T = T
        self.r = r
        self.sigma = sigma
        self.q = q

        logger.info(f"Initialized BlackScholes (S={S}, K={K}, T={T}, "
                   f"r={r}, sigma={sigma})")

    def call_price(self) -> float:
        """
        Calculate European call option price.

        Returns:
            Call price
        """
        d1, d2 = self._d1_d2()

        call = (self.S * np.exp(-self.q * self.T) * stats.norm.cdf(d1) -
                self.K * np.exp(-self.r * self.T) * stats.norm.cdf(d2))

        return call

    def put_price(self) -> float:
        """
        Calculate European put option price.

        Returns:
            Put price
        """
        d1, d2 = self._d1_d2()

        put = (self.K * np.exp(-self.r * self.T) * stats.norm.cdf(-d2) -
               self.S * np.exp(-self.q * self.T) * stats.norm.cdf(-d1))

        return put

    def greeks(self) -> Dict[str, float]:
        """
        Calculate option Greeks.

        Returns:
            Dictionary with delta, gamma, vega, theta, rho
        """
        d1, d2 = self._d1_d2()

        # Delta
        call_delta = np.exp(-self.q * self.T) * stats.norm.cdf(d1)
        put_delta = -np.exp(-self.q * self.T) * stats.norm.cdf(-d1)

        # Gamma (same for calls and puts)
        gamma = (np.exp(-self.q * self.T) * stats.norm.pdf(d1) /
                (self.S * self.sigma * np.sqrt(self.T)))

        # Vega (same for calls and puts)
        vega = (self.S * np.exp(-self.q * self.T) *
                stats.norm.pdf(d1) * np.sqrt(self.T))

        # Theta
        call_theta = (
            -self.S * stats.norm.pdf(d1) * self.sigma * np.exp(-self.q * self.T) /
            (2 * np.sqrt(self.T)) -
            self.r * self.K * np.exp(-self.r * self.T) * stats.norm.cdf(d2) +
            self.q * self.S * np.exp(-self.q * self.T) * stats.norm.cdf(d1)
        )

        put_theta = (
            -self.S * stats.norm.pdf(d1) * self.sigma * np.exp(-self.q * self.T) /
            (2 * np.sqrt(self.T)) +
            self.r * self.K * np.exp(-self.r * self.T) * stats.norm.cdf(-d2) -
            self.q * self.S * np.exp(-self.q * self.T) * stats.norm.cdf(-d1)
        )

        # Rho
        call_rho = (self.K * self.T * np.exp(-self.r * self.T) *
                    stats.norm.cdf(d2))

        put_rho = (-self.K * self.T * np.exp(-self.r * self.T) *
                   stats.norm.cdf(-d2))

        return {
            'call_delta': call_delta,
            'put_delta': put_delta,
            'gamma': gamma,
            'vega': vega,
            'call_theta': call_theta / 365,  # Per day
            'put_theta': put_theta / 365,
            'call_rho': call_rho / 100,  # Per 1% change
            'put_rho': put_rho / 100
        }

    def implied_volatility(
        self,
        option_price: float,
        option_type: str = 'call',
        max_iterations: int = 100,
        tolerance: float = 1e-5
    ) -> float:
        """
        Calculate implied volatility using Newton-Raphson method.

        Args:
            option_price: Market price of option
            option_type: 'call' or 'put'
            max_iterations: Maximum iterations
            tolerance: Convergence tolerance

        Returns:
            Implied volatility
        """
        # Initial guess
        sigma = 0.5

        for i in range(max_iterations):
            # Save original sigma
            orig_sigma = self.sigma
            self.sigma = sigma

            # Calculate price and vega
            if option_type == 'call':
                price = self.call_price()
            else:
                price = self.put_price()

            vega = self.greeks()['vega']

            # Restore original sigma
            self.sigma = orig_sigma

            # Newton-Raphson update
            diff = option_price - price

            if abs(diff) < tolerance:
                logger.info(f"Implied volatility converged: {sigma:.4f}")
                return sigma

            if vega != 0:
                sigma = sigma + diff / vega
            else:
                break

            # Ensure sigma stays positive
            sigma = max(sigma, 0.01)

        logger.warning(f"Implied volatility did not converge")
        return sigma

    def _d1_d2(self) -> tuple:
        """Calculate d1 and d2 parameters."""
        d1 = ((np.log(self.S / self.K) +
              (self.r - self.q + 0.5 * self.sigma ** 2) * self.T) /
              (self.sigma * np.sqrt(self.T)))

        d2 = d1 - self.sigma * np.sqrt(self.T)

        return d1, d2


def main():
    """Example usage."""
    print("=" * 80)
    print("Black-Scholes Options Pricing - Example")
    print("=" * 80)

    # Test 1: Basic pricing
    print("\n[1] European Call and Put Pricing:")

    bs = BlackScholes(
        S=100,
        K=105,
        T=0.5,
        r=0.05,
        sigma=0.25
    )

    call_price = bs.call_price()
    put_price = bs.put_price()

    print(f"  Stock Price: ${bs.S:.2f}")
    print(f"  Strike Price: ${bs.K:.2f}")
    print(f"  Time to Expiration: {bs.T} years")
    print(f"  Risk-free Rate: {bs.r:.2%}")
    print(f"  Volatility: {bs.sigma:.2%}")
    print(f"\n  Call Price: ${call_price:.2f}")
    print(f"  Put Price: ${put_price:.2f}")

    # Verify put-call parity
    parity_diff = call_price - put_price - (bs.S - bs.K * np.exp(-bs.r * bs.T))
    print(f"\n  Put-Call Parity Check: ${parity_diff:.6f} (should be ~0)")

    # Test 2: Greeks
    print("\n[2] Option Greeks:")

    greeks = bs.greeks()

    print(f"\n  Call Delta: {greeks['call_delta']:.4f}")
    print(f"  Put Delta: {greeks['put_delta']:.4f}")
    print(f"  Gamma: {greeks['gamma']:.4f}")
    print(f"  Vega: {greeks['vega']:.4f}")
    print(f"  Call Theta (per day): {greeks['call_theta']:.4f}")
    print(f"  Put Theta (per day): {greeks['put_theta']:.4f}")
    print(f"  Call Rho: {greeks['call_rho']:.4f}")
    print(f"  Put Rho: {greeks['put_rho']:.4f}")

    # Test 3: At-the-money, in-the-money, out-of-the-money
    print("\n[3] Moneyness Comparison:")

    strikes = [90, 100, 110]

    print(f"\n  {'Strike':<8} {'Call Price':>12} {'Put Price':>12} {'Call Delta':>12}")
    print("  " + "-" * 50)

    for K in strikes:
        bs_k = BlackScholes(S=100, K=K, T=0.5, r=0.05, sigma=0.25)

        call = bs_k.call_price()
        put = bs_k.put_price()
        delta = bs_k.greeks()['call_delta']

        print(f"  ${K:<7} ${call:>11.2f} ${put:>11.2f} {delta:>11.4f}")

    # Test 4: Time decay
    print("\n[4] Time Decay (Theta):")

    times = [1.0, 0.5, 0.25, 0.1, 0.05]

    print(f"\n  {'Time (years)':<15} {'Call Price':>12} {'Theta/day':>12}")
    print("  " + "-" * 42)

    for T in times:
        bs_t = BlackScholes(S=100, K=100, T=T, r=0.05, sigma=0.25)

        call = bs_t.call_price()
        theta = bs_t.greeks()['call_theta']

        print(f"  {T:<15.2f} ${call:>11.2f} {theta:>11.4f}")

    # Test 5: Volatility impact
    print("\n[5] Volatility Impact:")

    volatilities = [0.1, 0.2, 0.3, 0.4, 0.5]

    print(f"\n  {'Volatility':<12} {'Call Price':>12} {'Vega':>12}")
    print("  " + "-" * 40)

    for sigma in volatilities:
        bs_v = BlackScholes(S=100, K=100, T=0.5, r=0.05, sigma=sigma)

        call = bs_v.call_price()
        vega = bs_v.greeks()['vega']

        print(f"  {sigma:<12.2%} ${call:>11.2f} {vega:>11.4f}")

    # Test 6: Implied volatility
    print("\n[6] Implied Volatility:")

    # Price an option
    bs_iv = BlackScholes(S=100, K=100, T=0.5, r=0.05, sigma=0.25)
    market_price = bs_iv.call_price()

    print(f"  Market Price: ${market_price:.2f}")
    print(f"  True Volatility: {bs_iv.sigma:.2%}")

    # Calculate implied volatility
    bs_iv_calc = BlackScholes(S=100, K=100, T=0.5, r=0.05, sigma=0.3)  # Wrong initial guess

    implied_vol = bs_iv_calc.implied_volatility(market_price, 'call')

    print(f"  Implied Volatility: {implied_vol:.2%}")
    print(f"  Error: {abs(implied_vol - 0.25):.6f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
