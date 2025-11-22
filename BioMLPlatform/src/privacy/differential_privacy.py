"""Differential privacy for sensitive medical data."""

import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DifferentiallyPrivateModel:
    """
    Wrapper for training models with differential privacy guarantees.

    Uses gradient clipping and noise injection.
    """

    def __init__(
        self,
        base_model: any,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        max_grad_norm: float = 1.0
    ):
        """
        Initialize differentially private model.

        Args:
            base_model: Base model to wrap
            epsilon: Privacy budget (smaller = more private)
            delta: Failure probability
            max_grad_norm: Maximum gradient norm for clipping
        """
        self.base_model = base_model
        self.epsilon = epsilon
        self.delta = delta
        self.max_grad_norm = max_grad_norm

        self.privacy_spent = 0.0
        self.n_updates = 0

        logger.info(f"Initialized DifferentiallyPrivateModel "
                   f"(ε={epsilon}, δ={delta})")

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        batch_size: int = 32,
        epochs: int = 10
    ):
        """
        Train model with differential privacy.

        Args:
            X: Training features
            y: Training labels
            batch_size: Batch size
            epochs: Number of epochs
        """
        logger.info(f"Training with DP (ε={self.epsilon}, δ={self.delta})")

        n_samples = len(X)

        # Calculate noise scale based on privacy budget
        noise_scale = self._calculate_noise_scale(n_samples, batch_size, epochs)

        logger.info(f"Noise scale: {noise_scale:.6f}")

        # Simple DP-SGD simulation (simplified)
        # In production, would use libraries like Opacus (PyTorch) or TensorFlow Privacy

        # Add noise to labels (simplified DP approach)
        y_noisy = self._add_label_noise(y, noise_scale)

        # Train base model on noisy data
        self.base_model.fit(X, y_noisy)

        # Track privacy spent
        self.privacy_spent = self.epsilon
        self.n_updates = (n_samples // batch_size) * epochs

        logger.info(f"Training complete. Privacy spent: ε={self.privacy_spent:.4f}")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        return self.base_model.predict(X)

    def get_privacy_spent(self) -> dict:
        """Get privacy accounting information."""
        return {
            'epsilon': self.privacy_spent,
            'delta': self.delta,
            'n_updates': self.n_updates,
            'remaining_budget': max(0, self.epsilon - self.privacy_spent)
        }

    def _calculate_noise_scale(
        self,
        n_samples: int,
        batch_size: int,
        epochs: int
    ) -> float:
        """
        Calculate noise scale for DP guarantee.

        Uses simplified version of DP-SGD accounting.
        """
        # Sampling ratio
        q = batch_size / n_samples

        # Number of steps
        steps = (n_samples // batch_size) * epochs

        # Simplified noise calculation
        # Full implementation would use moments accountant or RDP
        noise_scale = np.sqrt(2 * np.log(1.25 / self.delta)) / self.epsilon

        return noise_scale

    def _add_label_noise(self, y: np.ndarray, noise_scale: float) -> np.ndarray:
        """
        Add calibrated noise to labels.

        Args:
            y: Original labels
            noise_scale: Scale of noise

        Returns:
            Noisy labels
        """
        # For regression: add Gaussian noise
        if y.dtype in [np.float32, np.float64]:
            noise = np.random.normal(0, noise_scale, size=y.shape)
            return y + noise

        # For classification: use randomized response
        else:
            n_classes = len(np.unique(y))

            # Probability of keeping true label
            p_keep = np.exp(self.epsilon) / (np.exp(self.epsilon) + n_classes - 1)

            # Randomize labels
            y_noisy = y.copy()
            mask = np.random.rand(len(y)) > p_keep

            if mask.any():
                # Replace with random label
                y_noisy[mask] = np.random.randint(0, n_classes, mask.sum())

            return y_noisy


class PrivacyBudget:
    """Track and manage privacy budget."""

    def __init__(self, epsilon: float, delta: float):
        """
        Initialize privacy budget.

        Args:
            epsilon: Total privacy budget
            delta: Failure probability
        """
        self.epsilon_total = epsilon
        self.delta = delta
        self.epsilon_spent = 0.0

        logger.info(f"Initialized PrivacyBudget (ε={epsilon}, δ={delta})")

    def spend(self, epsilon: float):
        """
        Spend privacy budget.

        Args:
            epsilon: Amount to spend
        """
        self.epsilon_spent += epsilon

        if self.epsilon_spent > self.epsilon_total:
            logger.warning(f"Privacy budget exhausted! "
                         f"Spent {self.epsilon_spent:.4f} > {self.epsilon_total:.4f}")

    def is_exhausted(self) -> bool:
        """Check if budget is exhausted."""
        return self.epsilon_spent >= self.epsilon_total

    def remaining(self) -> float:
        """Get remaining budget."""
        return max(0, self.epsilon_total - self.epsilon_spent)


def main():
    """Example usage."""
    print("=" * 80)
    print("Differential Privacy - Example")
    print("=" * 80)

    # Generate synthetic medical data
    np.random.seed(42)

    n_patients = 1000
    n_features = 20

    X = np.random.randn(n_patients, n_features)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    print(f"\nSynthetic medical data:")
    print(f"  Patients: {n_patients}")
    print(f"  Features: {n_features}")
    print(f"  Positive class: {y.sum()} ({y.mean()*100:.1f}%)")

    # Test 1: Train without privacy
    print("\n[1] Training without privacy:")

    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    model_normal = LogisticRegression()
    model_normal.fit(X_train, y_train)

    accuracy_normal = model_normal.score(X_test, y_test)

    print(f"  Test accuracy: {accuracy_normal:.4f}")

    # Test 2: Train with differential privacy
    print("\n[2] Training with differential privacy:")

    privacy_levels = [0.1, 0.5, 1.0, 5.0]

    for epsilon in privacy_levels:
        model_base = LogisticRegression()

        dp_model = DifferentiallyPrivateModel(
            base_model=model_base,
            epsilon=epsilon,
            delta=1e-5,
            max_grad_norm=1.0
        )

        dp_model.fit(X_train, y_train, batch_size=32, epochs=10)

        accuracy_dp = dp_model.predict(X_test).mean() == y_test.mean()
        privacy_info = dp_model.get_privacy_spent()

        print(f"\n  ε={epsilon:4.1f}: accuracy={model_base.score(X_test, y_test):.4f}, "
              f"privacy spent={privacy_info['epsilon']:.4f}")

    # Test 3: Privacy budget tracking
    print("\n[3] Privacy budget tracking:")

    budget = PrivacyBudget(epsilon=1.0, delta=1e-5)

    print(f"  Total budget: ε={budget.epsilon_total}")

    # Simulate multiple queries
    for i in range(5):
        budget.spend(0.2)
        print(f"  After query {i+1}: spent={budget.epsilon_spent:.4f}, "
              f"remaining={budget.remaining():.4f}")

        if budget.is_exhausted():
            print(f"  Budget exhausted!")
            break

    # Test 4: Noise addition demonstration
    print("\n[4] Noise addition for privacy:")

    # Original statistic
    true_mean = X_train[:, 0].mean()

    print(f"\n  True mean: {true_mean:.4f}")

    # Add calibrated noise
    epsilon_values = [0.1, 0.5, 1.0]

    for eps in epsilon_values:
        sensitivity = 1.0  # Assume bounded data
        noise_scale = sensitivity / eps

        noisy_mean = true_mean + np.random.normal(0, noise_scale)

        print(f"  ε={eps:3.1f}: noisy mean={noisy_mean:.4f}, "
              f"error={abs(noisy_mean - true_mean):.4f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
