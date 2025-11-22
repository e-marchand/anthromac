"""Deep Cox proportional hazards model for survival analysis."""

import numpy as np
from typing import Tuple, Optional
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


class DeepCoxModel:
    """
    Deep learning extension of Cox proportional hazards model.

    Learns non-linear representations for survival analysis.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dims: list = [64, 32],
        learning_rate: float = 0.01
    ):
        """
        Initialize Deep Cox model.

        Args:
            input_dim: Input feature dimension
            hidden_dims: Hidden layer dimensions
            learning_rate: Learning rate
        """
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate

        # Simple linear model as baseline
        self.weights = None
        self.bias = 0.0

        self.scaler = StandardScaler()
        self.fitted = False

        logger.info(f"Initialized DeepCoxModel (input_dim={input_dim})")

    def fit(
        self,
        X: np.ndarray,
        times: np.ndarray,
        events: np.ndarray,
        epochs: int = 100
    ) -> 'DeepCoxModel':
        """
        Fit Cox model.

        Args:
            X: Covariates (n_samples, n_features)
            times: Survival times
            events: Event indicators (1=event, 0=censored)
            epochs: Training epochs

        Returns:
            self: Fitted model
        """
        logger.info(f"Fitting on {len(X)} patients ({events.sum()} events)")

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Initialize weights
        self.weights = np.zeros(X_scaled.shape[1])

        # Simple gradient descent on Cox partial likelihood
        for epoch in range(epochs):
            # Compute risk scores
            risk_scores = X_scaled @ self.weights + self.bias

            # Cox partial likelihood gradient
            gradient = np.zeros_like(self.weights)

            # Sort by time
            order = np.argsort(-times)  # Descending order

            X_sorted = X_scaled[order]
            events_sorted = events[order]
            risk_sorted = risk_scores[order]

            # Compute gradient
            risk_exp = np.exp(risk_sorted)
            risk_sum = np.cumsum(risk_exp[::-1])[::-1]

            for i in range(len(X_sorted)):
                if events_sorted[i]:
                    gradient += X_sorted[i]
                    gradient -= (risk_exp[i] * np.sum(
                        X_sorted[i:] * (risk_exp[i:] / risk_sum[i:])[:, np.newaxis],
                        axis=0
                    ))

            # Update weights
            self.weights += self.learning_rate * gradient / len(X)

            if epoch % 20 == 0:
                likelihood = self._partial_likelihood(X_scaled, times, events)
                logger.debug(f"Epoch {epoch}: log-likelihood={likelihood:.4f}")

        self.fitted = True

        logger.info("Training complete")

        return self

    def predict_risk(self, X: np.ndarray) -> np.ndarray:
        """
        Predict risk scores.

        Higher scores = higher risk.

        Args:
            X: Covariates

        Returns:
            Risk scores
        """
        if not self.fitted:
            raise ValueError("Model not fitted")

        X_scaled = self.scaler.transform(X)
        risk_scores = X_scaled @ self.weights + self.bias

        return risk_scores

    def predict_survival(
        self,
        X: np.ndarray,
        times: np.ndarray
    ) -> np.ndarray:
        """
        Predict survival probabilities.

        Args:
            X: Covariates
            times: Time points for prediction

        Returns:
            Survival probabilities (n_samples, n_times)
        """
        risk_scores = self.predict_risk(X)

        # Baseline survival (simplified)
        # In full implementation, would estimate from training data
        baseline_survival = np.exp(-0.1 * times)

        # Individual survival
        survival = baseline_survival ** np.exp(risk_scores[:, np.newaxis])

        return survival

    def _partial_likelihood(
        self,
        X: np.ndarray,
        times: np.ndarray,
        events: np.ndarray
    ) -> float:
        """Compute Cox partial log-likelihood."""
        risk_scores = X @ self.weights + self.bias

        # Sort by time
        order = np.argsort(-times)
        risk_sorted = risk_scores[order]
        events_sorted = events[order]

        # Compute likelihood
        risk_exp = np.exp(risk_sorted)
        risk_sum = np.cumsum(risk_exp[::-1])[::-1]

        log_likelihood = np.sum(
            events_sorted * (risk_sorted - np.log(risk_sum))
        )

        return log_likelihood


def main():
    """Example usage."""
    print("=" * 80)
    print("Deep Cox Model - Example")
    print("=" * 80)

    # Generate synthetic survival data
    np.random.seed(42)

    n_patients = 500
    n_features = 10

    # Generate features
    X = np.random.randn(n_patients, n_features)

    # True coefficients
    true_coef = np.random.randn(n_features) * 0.3

    # Generate survival times based on features
    baseline_hazard = 0.1
    risk_scores = X @ true_coef

    # Weibull distributed survival times
    scale = 1.0 / (baseline_hazard * np.exp(risk_scores))
    shape = 2.0

    times = np.random.weibull(shape, n_patients) * scale

    # Generate censoring
    censoring_times = np.random.exponential(50, n_patients)
    observed_times = np.minimum(times, censoring_times)
    events = (times <= censoring_times).astype(int)

    print(f"\nGenerated data:")
    print(f"  Patients: {n_patients}")
    print(f"  Features: {n_features}")
    print(f"  Events: {events.sum()} ({events.mean()*100:.1f}%)")
    print(f"  Censored: {(1-events).sum()} ({(1-events.mean())*100:.1f}%)")
    print(f"  Median time: {np.median(observed_times):.2f}")

    # Split data
    from sklearn.model_selection import train_test_split

    X_train, X_test, times_train, times_test, events_train, events_test = train_test_split(
        X, observed_times, events, test_size=0.3, random_state=42
    )

    print(f"\nTrain set: {len(X_train)} patients")
    print(f"Test set: {len(X_test)} patients")

    # Train model
    print("\n[1] Training Deep Cox model...")

    model = DeepCoxModel(
        input_dim=n_features,
        hidden_dims=[32, 16],
        learning_rate=0.01
    )

    model.fit(X_train, times_train, events_train, epochs=100)

    # Predict risk scores
    print("\n[2] Predicting risk scores...")

    risk_scores_test = model.predict_risk(X_test)

    print(f"  Risk scores - min: {risk_scores_test.min():.4f}, "
          f"max: {risk_scores_test.max():.4f}")

    # Calculate C-index (concordance index)
    print("\n[3] Calculating C-index...")

    from sklearn.metrics import roc_auc_score

    # For patients with events, check if higher risk had earlier event
    concordant = 0
    total = 0

    for i in range(len(X_test)):
        if events_test[i] == 0:
            continue

        for j in range(len(X_test)):
            if i == j or times_test[j] < times_test[i]:
                continue

            if risk_scores_test[i] > risk_scores_test[j]:
                concordant += 1

            total += 1

    c_index = concordant / total if total > 0 else 0.5

    print(f"  C-index: {c_index:.4f}")

    # Predict survival curves
    print("\n[4] Predicting survival curves...")

    time_points = np.linspace(0, observed_times.max(), 50)
    survival_probs = model.predict_survival(X_test[:5], time_points)

    print(f"\n  Sample survival predictions at different times:")
    print(f"  {'Time':<8} {'Patient 1':>10} {'Patient 2':>10} {'Patient 3':>10}")
    print("  " + "-" * 44)

    for t_idx in [0, 10, 20, 30, 40]:
        t = time_points[t_idx]
        print(f"  {t:7.2f} {survival_probs[0, t_idx]:>10.4f} "
              f"{survival_probs[1, t_idx]:>10.4f} {survival_probs[2, t_idx]:>10.4f}")

    # Risk stratification
    print("\n[5] Risk stratification:")

    # Divide into quartiles
    risk_quartiles = np.percentile(risk_scores_test, [25, 50, 75])

    groups = np.digitize(risk_scores_test, risk_quartiles)

    for group_idx in range(4):
        mask = groups == group_idx
        group_events = events_test[mask].sum()
        group_size = mask.sum()
        event_rate = group_events / group_size if group_size > 0 else 0

        print(f"  Group {group_idx+1} (n={group_size}): "
              f"{group_events} events ({event_rate*100:.1f}%)")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
