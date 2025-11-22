"""Synthetic data generation for causal inference benchmarking."""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SyntheticDataGenerator:
    """
    Generate synthetic data for causal inference with known ground truth.

    Allows benchmarking of causal inference methods.
    """

    def __init__(
        self,
        n_samples: int = 1000,
        n_features: int = 10,
        treatment_effect: float = 2.0,
        confounding_strength: float = 0.5,
        noise_std: float = 1.0,
        random_state: Optional[int] = None
    ):
        """
        Initialize generator.

        Args:
            n_samples: Number of samples to generate
            n_features: Number of covariates
            treatment_effect: Average treatment effect
            confounding_strength: Strength of confounding (0-1)
            noise_std: Standard deviation of outcome noise
            random_state: Random seed
        """
        self.n_samples = n_samples
        self.n_features = n_features
        self.treatment_effect = treatment_effect
        self.confounding_strength = confounding_strength
        self.noise_std = noise_std
        self.random_state = random_state

        if random_state is not None:
            np.random.seed(random_state)

        logger.info(f"Initialized SyntheticDataGenerator (n={n_samples}, "
                   f"effect={treatment_effect})")

    def generate(
        self,
        heterogeneous: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate synthetic data.

        Args:
            heterogeneous: Whether to include heterogeneous treatment effects

        Returns:
            Tuple of (X, treatment, y, true_cate)
        """
        logger.info(f"Generating {self.n_samples} samples...")

        # Generate covariates
        X = np.random.randn(self.n_samples, self.n_features)

        # Generate treatment (confounded by covariates)
        # Propensity depends on first few features
        logit_ps = (self.confounding_strength *
                   (X[:, 0] + 0.5 * X[:, 1] - 0.3 * X[:, 2]))

        propensity_scores = 1 / (1 + np.exp(-logit_ps))
        treatment = (np.random.rand(self.n_samples) < propensity_scores).astype(int)

        # Generate outcomes
        # Base outcome depends on covariates
        y_base = X[:, 0] + 0.5 * X[:, 1] - 0.3 * X[:, 2]

        if heterogeneous:
            # Treatment effect varies with covariates
            # Effect is larger for higher values of first covariate
            true_cate = self.treatment_effect + 0.5 * X[:, 0]
        else:
            # Constant treatment effect
            true_cate = np.full(self.n_samples, self.treatment_effect)

        # Add treatment effect
        y = y_base + treatment * true_cate

        # Add noise
        y += np.random.randn(self.n_samples) * self.noise_std

        logger.info(f"Generated data - Treatment rate: {treatment.mean():.3f}, "
                   f"ATE: {true_cate.mean():.3f}")

        return X, treatment, y, true_cate

    def generate_with_confounders(
        self,
        n_observed_confounders: int = 5,
        n_unobserved_confounders: int = 2
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        """
        Generate data with observed and unobserved confounders.

        Args:
            n_observed_confounders: Number of observed confounders
            n_unobserved_confounders: Number of unobserved confounders

        Returns:
            Tuple of (X_observed, treatment, y, true_cate, additional_info)
        """
        logger.info(f"Generating data with {n_unobserved_confounders} unobserved confounders")

        # Generate all confounders
        X_observed = np.random.randn(self.n_samples, n_observed_confounders)
        X_unobserved = np.random.randn(self.n_samples, n_unobserved_confounders)

        # Combine for treatment assignment
        X_all = np.hstack([X_observed, X_unobserved])

        # Treatment depends on both observed and unobserved
        logit_ps = (self.confounding_strength *
                   (X_all[:, 0] + 0.5 * X_all[:, 1]))

        if n_unobserved_confounders > 0:
            logit_ps += 0.3 * X_unobserved[:, 0]  # Unobserved confounding

        propensity_scores = 1 / (1 + np.exp(-logit_ps))
        treatment = (np.random.rand(self.n_samples) < propensity_scores).astype(int)

        # Outcome depends on both observed and unobserved
        y_base = X_all[:, 0] + 0.5 * X_all[:, 1]

        if n_unobserved_confounders > 0:
            y_base += 0.4 * X_unobserved[:, 0]  # Unobserved confounding

        true_cate = np.full(self.n_samples, self.treatment_effect)
        y = y_base + treatment * true_cate + np.random.randn(self.n_samples) * self.noise_std

        additional_info = {
            'X_unobserved': X_unobserved,
            'propensity_scores': propensity_scores
        }

        return X_observed, treatment, y, true_cate, additional_info

    def generate_rct(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate randomized controlled trial data (no confounding).

        Returns:
            Tuple of (X, treatment, y, true_cate)
        """
        logger.info("Generating RCT data (random treatment assignment)")

        X = np.random.randn(self.n_samples, self.n_features)

        # Random treatment assignment
        treatment = np.random.binomial(1, 0.5, self.n_samples)

        # Outcomes
        y_base = X[:, 0] + 0.5 * X[:, 1]
        true_cate = np.full(self.n_samples, self.treatment_effect)
        y = y_base + treatment * true_cate + np.random.randn(self.n_samples) * self.noise_std

        return X, treatment, y, true_cate


def main():
    """Example usage."""
    print("=" * 80)
    print("Synthetic Data Generator - Example")
    print("=" * 80)

    # Initialize generator
    generator = SyntheticDataGenerator(
        n_samples=1000,
        n_features=10,
        treatment_effect=3.0,
        confounding_strength=0.7,
        random_state=42
    )

    # Generate observational data
    print("\n[1] Observational Data (with confounding):")
    X, treatment, y, true_cate = generator.generate(heterogeneous=False)

    print(f"  Samples: {len(X)}")
    print(f"  Features: {X.shape[1]}")
    print(f"  Treatment rate: {treatment.mean():.3f}")
    print(f"  True ATE: {true_cate.mean():.3f}")
    print(f"  Outcome mean: {y.mean():.3f}, std: {y.std():.3f}")

    # Generate with heterogeneous effects
    print("\n[2] Heterogeneous Treatment Effects:")
    X_het, t_het, y_het, cate_het = generator.generate(heterogeneous=True)

    print(f"  True CATE - min: {cate_het.min():.3f}, max: {cate_het.max():.3f}")
    print(f"  True CATE - mean: {cate_het.mean():.3f}, std: {cate_het.std():.3f}")

    # Generate with unobserved confounders
    print("\n[3] Data with Unobserved Confounders:")
    X_obs, t_conf, y_conf, cate_conf, info = generator.generate_with_confounders(
        n_observed_confounders=5,
        n_unobserved_confounders=2
    )

    print(f"  Observed features: {X_obs.shape[1]}")
    print(f"  Unobserved confounders: {info['X_unobserved'].shape[1]}")
    print(f"  Propensity score range: [{info['propensity_scores'].min():.3f}, "
          f"{info['propensity_scores'].max():.3f}]")

    # Generate RCT
    print("\n[4] Randomized Controlled Trial:")
    X_rct, t_rct, y_rct, cate_rct = generator.generate_rct()

    print(f"  Treatment rate: {t_rct.mean():.3f} (should be ~0.5)")
    print(f"  True ATE: {cate_rct.mean():.3f}")

    # Compare naive estimates
    print("\n[5] Naive Treatment Effect Estimates:")

    def naive_estimate(y, t):
        return y[t == 1].mean() - y[t == 0].mean()

    obs_naive = naive_estimate(y, treatment)
    rct_naive = naive_estimate(y_rct, t_rct)

    print(f"  Observational (confounded): {obs_naive:.3f} (true: {true_cate.mean():.3f})")
    print(f"  RCT (unconfounded): {rct_naive:.3f} (true: {cate_rct.mean():.3f})")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
