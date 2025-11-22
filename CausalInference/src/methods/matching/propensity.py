"""Propensity score matching for causal inference."""

import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict, Any
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
import logging

logger = logging.getLogger(__name__)


class PropensityScoreMatcher:
    """
    Propensity score matching estimator.

    Matches treated and control units based on propensity scores
    to estimate treatment effects.
    """

    def __init__(
        self,
        caliper: Optional[float] = None,
        n_neighbors: int = 1,
        replace: bool = False,
        estimator: Optional[Any] = None
    ):
        """
        Initialize matcher.

        Args:
            caliper: Maximum allowed distance for matches
            n_neighbors: Number of matches per treated unit
            replace: Whether to sample controls with replacement
            estimator: Custom propensity score estimator
        """
        self.caliper = caliper
        self.n_neighbors = n_neighbors
        self.replace = replace

        if estimator is None:
            self.estimator = LogisticRegression(max_iter=1000)
        else:
            self.estimator = estimator

        self.propensity_scores = None
        self.matches = None

        logger.info(f"Initialized PropensityScoreMatcher (caliper={caliper})")

    def fit(self, X: np.ndarray, treatment: np.ndarray) -> 'PropensityScoreMatcher':
        """
        Fit propensity score model.

        Args:
            X: Covariates
            treatment: Treatment indicator (0/1)

        Returns:
            self: Fitted matcher
        """
        logger.info(f"Fitting propensity model on {len(X)} samples")

        # Fit propensity score model
        self.estimator.fit(X, treatment)

        # Predict propensity scores
        self.propensity_scores = self.estimator.predict_proba(X)[:, 1]

        logger.info(f"Propensity scores - min: {self.propensity_scores.min():.3f}, "
                   f"max: {self.propensity_scores.max():.3f}")

        return self

    def match(
        self,
        treatment: np.ndarray
    ) -> Dict[int, np.ndarray]:
        """
        Find matches for treated units.

        Args:
            treatment: Treatment indicator

        Returns:
            Dictionary mapping treated indices to control indices
        """
        if self.propensity_scores is None:
            raise ValueError("Must call fit() first")

        logger.info("Finding matches...")

        treated_idx = np.where(treatment == 1)[0]
        control_idx = np.where(treatment == 0)[0]

        treated_ps = self.propensity_scores[treated_idx].reshape(-1, 1)
        control_ps = self.propensity_scores[control_idx].reshape(-1, 1)

        # Find nearest neighbors
        nn = NearestNeighbors(n_neighbors=self.n_neighbors, metric='euclidean')
        nn.fit(control_ps)

        distances, indices = nn.kneighbors(treated_ps)

        # Apply caliper if specified
        matches = {}
        n_dropped = 0

        for i, t_idx in enumerate(treated_idx):
            if self.caliper is not None:
                # Filter by caliper
                valid_mask = distances[i] <= self.caliper
                if not valid_mask.any():
                    n_dropped += 1
                    continue

                valid_indices = indices[i][valid_mask]
            else:
                valid_indices = indices[i]

            # Map to original control indices
            matches[t_idx] = control_idx[valid_indices]

        if n_dropped > 0:
            logger.warning(f"Dropped {n_dropped}/{len(treated_idx)} treated units "
                          f"due to caliper constraint")

        logger.info(f"Found matches for {len(matches)} treated units")

        self.matches = matches
        return matches

    def estimate_ate(
        self,
        y: np.ndarray,
        treatment: Optional[np.ndarray] = None
    ) -> float:
        """
        Estimate Average Treatment Effect.

        Args:
            y: Outcomes
            treatment: Treatment indicator (if not using stored matches)

        Returns:
            ATE estimate
        """
        if self.matches is None:
            if treatment is None:
                raise ValueError("Must call match() first or provide treatment")
            self.match(treatment)

        # Calculate treatment effects
        effects = []

        for treated_idx, control_indices in self.matches.items():
            y_treated = y[treated_idx]
            y_control = y[control_indices].mean()

            effect = y_treated - y_control
            effects.append(effect)

        ate = np.mean(effects)
        logger.info(f"ATE estimate: {ate:.4f}")

        return float(ate)

    def estimate_att(
        self,
        y: np.ndarray,
        treatment: Optional[np.ndarray] = None
    ) -> float:
        """
        Estimate Average Treatment Effect on the Treated.

        Same as ATE for matching methods.

        Args:
            y: Outcomes
            treatment: Treatment indicator

        Returns:
            ATT estimate
        """
        return self.estimate_ate(y, treatment)

    def get_matched_data(
        self,
        X: np.ndarray,
        treatment: np.ndarray,
        y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get matched dataset.

        Args:
            X: Original covariates
            treatment: Original treatment
            y: Original outcomes

        Returns:
            Tuple of (X_matched, treatment_matched, y_matched)
        """
        if self.matches is None:
            self.match(treatment)

        matched_indices = []

        for treated_idx, control_indices in self.matches.items():
            # Add treated unit
            matched_indices.append(treated_idx)

            # Add matched controls
            matched_indices.extend(control_indices)

        matched_indices = np.array(matched_indices)

        return X[matched_indices], treatment[matched_indices], y[matched_indices]

    def check_balance(
        self,
        X: np.ndarray,
        treatment: np.ndarray
    ) -> Dict[str, float]:
        """
        Check covariate balance.

        Args:
            X: Covariates
            treatment: Treatment indicator

        Returns:
            Dictionary of balance statistics
        """
        if self.matches is None:
            self.match(treatment)

        # Get matched data
        X_matched, t_matched, _ = self.get_matched_data(X, treatment, np.zeros(len(X)))

        # Calculate standardized mean differences
        balance_stats = {}

        for i in range(X.shape[1]):
            # Before matching
            mean_t = X[treatment == 1, i].mean()
            mean_c = X[treatment == 0, i].mean()
            std_pooled = np.sqrt(
                (X[treatment == 1, i].var() + X[treatment == 0, i].var()) / 2
            )
            smd_before = (mean_t - mean_c) / (std_pooled + 1e-8)

            # After matching
            mean_t_matched = X_matched[t_matched == 1, i].mean()
            mean_c_matched = X_matched[t_matched == 0, i].mean()
            std_pooled_matched = np.sqrt(
                (X_matched[t_matched == 1, i].var() +
                 X_matched[t_matched == 0, i].var()) / 2
            )
            smd_after = (mean_t_matched - mean_c_matched) / (std_pooled_matched + 1e-8)

            balance_stats[f'feature_{i}'] = {
                'smd_before': float(smd_before),
                'smd_after': float(smd_after),
                'improvement': float(abs(smd_before) - abs(smd_after))
            }

        logger.info("Balance check completed")
        return balance_stats


def main():
    """Example usage."""
    from sklearn.datasets import make_classification

    # Generate data
    np.random.seed(42)

    X, _ = make_classification(
        n_samples=1000,
        n_features=10,
        n_informative=7,
        random_state=42
    )

    # Simulate treatment assignment (confounded)
    treatment_propensity = 1 / (1 + np.exp(-(X[:, 0] + 0.5 * X[:, 1])))
    treatment = (np.random.rand(len(X)) < treatment_propensity).astype(int)

    # Simulate outcomes with treatment effect
    true_effect = 2.0
    y = X[:, 0] + 0.5 * X[:, 1] + true_effect * treatment + np.random.randn(len(X))

    print("=" * 80)
    print("Propensity Score Matching - Example")
    print("=" * 80)

    print(f"\nData:")
    print(f"  Samples: {len(X)}")
    print(f"  Treated: {treatment.sum()}")
    print(f"  Control: {(1 - treatment).sum()}")
    print(f"  True effect: {true_effect}")

    # Initialize matcher
    matcher = PropensityScoreMatcher(caliper=0.1, n_neighbors=1)

    # Fit and match
    print("\n[1] Fitting propensity model...")
    matcher.fit(X, treatment)

    print("\n[2] Matching treated and control units...")
    matches = matcher.match(treatment)

    # Estimate ATE
    print("\n[3] Estimating treatment effect...")
    ate = matcher.estimate_ate(y)
    print(f"  Estimated ATE: {ate:.4f}")
    print(f"  True ATE: {true_effect:.4f}")
    print(f"  Bias: {abs(ate - true_effect):.4f}")

    # Check balance
    print("\n[4] Checking covariate balance...")
    balance = matcher.check_balance(X, treatment)

    print("  Feature | SMD Before | SMD After | Improvement")
    print("  " + "-" * 50)
    for feat, stats in list(balance.items())[:5]:  # Show first 5 features
        print(f"  {feat:8s} | {stats['smd_before']:10.4f} | "
              f"{stats['smd_after']:9.4f} | {stats['improvement']:11.4f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
