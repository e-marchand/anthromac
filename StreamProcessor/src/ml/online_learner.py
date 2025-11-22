"""Online learning for streaming data."""

import numpy as np
from typing import Optional, Dict, Any
from collections import deque
import logging

logger = logging.getLogger(__name__)


class OnlineLearner:
    """
    Online machine learning for streaming data.

    Incrementally updates model as new data arrives.
    """

    def __init__(
        self,
        model_type: str = 'perceptron',
        learning_rate: float = 0.01,
        window_size: int = 1000
    ):
        """
        Initialize online learner.

        Args:
            model_type: Type of model ('perceptron', 'linear_regression')
            learning_rate: Learning rate
            window_size: Size of sliding window for evaluation
        """
        self.model_type = model_type
        self.learning_rate = learning_rate
        self.window_size = window_size

        # Model weights
        self.weights = None
        self.bias = 0.0

        # Tracking
        self.n_samples = 0
        self.recent_predictions = deque(maxlen=window_size)
        self.recent_labels = deque(maxlen=window_size)

        logger.info(f"Initialized OnlineLearner (type={model_type}, lr={learning_rate})")

    def partial_fit(
        self,
        X: np.ndarray,
        y: np.ndarray
    ):
        """
        Incrementally train on batch.

        Args:
            X: Features (batch_size, n_features) or (n_features,)
            y: Labels (batch_size,) or scalar
        """
        # Handle single sample
        if X.ndim == 1:
            X = X.reshape(1, -1)

        if np.isscalar(y):
            y = np.array([y])

        # Initialize weights
        if self.weights is None:
            self.weights = np.zeros(X.shape[1])

        # Update for each sample
        for xi, yi in zip(X, y):
            self._update(xi, yi)

        self.n_samples += len(y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions.

        Args:
            X: Features

        Returns:
            Predictions
        """
        if self.weights is None:
            raise ValueError("Model not fitted")

        # Handle single sample
        if X.ndim == 1:
            X = X.reshape(1, -1)

        # Linear prediction
        scores = X @ self.weights + self.bias

        # Apply activation based on model type
        if self.model_type == 'perceptron':
            return (scores >= 0).astype(int)
        else:  # linear regression
            return scores

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Evaluate model.

        Args:
            X: Features
            y: True labels

        Returns:
            Accuracy (classification) or R² (regression)
        """
        predictions = self.predict(X)

        if self.model_type == 'perceptron':
            # Accuracy
            return (predictions == y).mean()
        else:
            # R² score
            ss_res = np.sum((y - predictions) ** 2)
            ss_tot = np.sum((y - y.mean()) ** 2)

            if ss_tot == 0:
                return 0.0

            return 1 - (ss_res / ss_tot)

    def get_metrics(self) -> Dict[str, Any]:
        """Get recent performance metrics."""
        if not self.recent_predictions:
            return {}

        predictions = np.array(self.recent_predictions)
        labels = np.array(self.recent_labels)

        if self.model_type == 'perceptron':
            accuracy = (predictions == labels).mean()

            return {
                'accuracy': accuracy,
                'n_samples': self.n_samples
            }
        else:
            mse = np.mean((predictions - labels) ** 2)

            return {
                'mse': mse,
                'n_samples': self.n_samples
            }

    def _update(self, x: np.ndarray, y: float):
        """
        Update model with single sample.

        Args:
            x: Features
            y: Label
        """
        # Predict
        prediction = self.predict(x.reshape(1, -1))[0]

        # Track recent performance
        self.recent_predictions.append(prediction)
        self.recent_labels.append(y)

        # Compute error
        if self.model_type == 'perceptron':
            # Perceptron update rule
            error = y - prediction

            if error != 0:
                self.weights += self.learning_rate * error * x
                self.bias += self.learning_rate * error

        else:  # linear regression
            # Gradient descent update
            error = y - prediction

            self.weights += self.learning_rate * error * x
            self.bias += self.learning_rate * error


class HoeffdingTree:
    """
    Simplified Hoeffding Tree for streaming classification.

    Makes splits based on Hoeffding bound.
    """

    def __init__(
        self,
        delta: float = 0.01,
        min_samples_split: int = 100
    ):
        """
        Initialize Hoeffding Tree.

        Args:
            delta: Confidence parameter
            min_samples_split: Minimum samples before split
        """
        self.delta = delta
        self.min_samples_split = min_samples_split

        # Root node
        self.root = {
            'is_leaf': True,
            'n_samples': 0,
            'class_counts': {},
            'feature_stats': {}
        }

        logger.info(f"Initialized HoeffdingTree (delta={delta})")

    def partial_fit(self, X: np.ndarray, y: np.ndarray):
        """
        Incrementally train tree.

        Args:
            X: Features
            y: Labels
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)

        if np.isscalar(y):
            y = np.array([y])

        for xi, yi in zip(X, y):
            self._update_node(self.root, xi, yi)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        if X.ndim == 1:
            X = X.reshape(1, -1)

        predictions = []

        for xi in X:
            node = self._traverse(self.root, xi)

            # Predict most common class
            if node['class_counts']:
                prediction = max(node['class_counts'].items(), key=lambda x: x[1])[0]
            else:
                prediction = 0

            predictions.append(prediction)

        return np.array(predictions)

    def _update_node(self, node: dict, x: np.ndarray, y: int):
        """Update node with sample."""
        # Update counts
        node['n_samples'] += 1

        if y not in node['class_counts']:
            node['class_counts'][y] = 0

        node['class_counts'][y] += 1

        # If leaf, consider splitting
        if node['is_leaf'] and node['n_samples'] >= self.min_samples_split:
            # Simplified: just track we could split
            pass

    def _traverse(self, node: dict, x: np.ndarray) -> dict:
        """Traverse to leaf node."""
        # Simplified: always return root for now
        return node


def main():
    """Example usage."""
    from sklearn.datasets import make_classification, make_regression

    print("=" * 80)
    print("Online Learning - Example")
    print("=" * 80)

    # Test 1: Online Classification
    print("\n[1] Online Classification (Perceptron):")

    X, y = make_classification(
        n_samples=1000,
        n_features=20,
        n_informative=15,
        random_state=42
    )

    # Split into stream
    learner = OnlineLearner(
        model_type='perceptron',
        learning_rate=0.01,
        window_size=100
    )

    # Process in mini-batches
    batch_size = 50

    for i in range(0, len(X), batch_size):
        X_batch = X[i:i + batch_size]
        y_batch = y[i:i + batch_size]

        # Train
        learner.partial_fit(X_batch, y_batch)

        # Evaluate on batch
        accuracy = learner.score(X_batch, y_batch)

        if i % 200 == 0:
            metrics = learner.get_metrics()
            print(f"  Batch {i//batch_size}: accuracy={accuracy:.4f}, "
                  f"recent_acc={metrics.get('accuracy', 0):.4f}")

    # Final evaluation
    final_metrics = learner.get_metrics()
    print(f"\n  Final accuracy: {final_metrics['accuracy']:.4f}")
    print(f"  Total samples: {learner.n_samples}")

    # Test 2: Online Regression
    print("\n[2] Online Regression:")

    X_reg, y_reg = make_regression(
        n_samples=1000,
        n_features=20,
        noise=10,
        random_state=42
    )

    learner_reg = OnlineLearner(
        model_type='linear_regression',
        learning_rate=0.001,
        window_size=100
    )

    for i in range(0, len(X_reg), batch_size):
        X_batch = X_reg[i:i + batch_size]
        y_batch = y_reg[i:i + batch_size]

        learner_reg.partial_fit(X_batch, y_batch)

        r2 = learner_reg.score(X_batch, y_batch)

        if i % 200 == 0:
            metrics = learner_reg.get_metrics()
            print(f"  Batch {i//batch_size}: R²={r2:.4f}, "
                  f"recent_MSE={metrics.get('mse', 0):.2f}")

    final_metrics = learner_reg.get_metrics()
    print(f"\n  Final MSE: {final_metrics['mse']:.4f}")

    # Test 3: Concept Drift
    print("\n[3] Concept Drift Test:")

    # Generate data with drift
    n_samples = 2000

    X_drift = []
    y_drift = []

    for i in range(n_samples):
        x = np.random.randn(10)

        # Concept drift at halfway point
        if i < n_samples // 2:
            # Original concept: sum of features
            y = 1 if x.sum() > 0 else 0
        else:
            # New concept: reversed
            y = 1 if x.sum() < 0 else 0

        X_drift.append(x)
        y_drift.append(y)

    X_drift = np.array(X_drift)
    y_drift = np.array(y_drift)

    # Online learner adapts to drift
    learner_drift = OnlineLearner(
        model_type='perceptron',
        learning_rate=0.05,  # Higher LR for faster adaptation
        window_size=50  # Smaller window
    )

    accuracies = []

    for i in range(0, len(X_drift), 10):
        X_batch = X_drift[i:i + 10]
        y_batch = y_drift[i:i + 10]

        # Evaluate before update
        if learner_drift.weights is not None:
            acc = learner_drift.score(X_batch, y_batch)
            accuracies.append(acc)

        # Update
        learner_drift.partial_fit(X_batch, y_batch)

    print(f"  Accuracy before drift: {np.mean(accuracies[:50]):.4f}")
    print(f"  Accuracy during drift: {np.mean(accuracies[45:55]):.4f}")
    print(f"  Accuracy after adaptation: {np.mean(accuracies[-50:]):.4f}")

    # Test 4: Hoeffding Tree
    print("\n[4] Hoeffding Tree:")

    tree = HoeffdingTree(delta=0.01, min_samples_split=50)

    # Train on stream
    for i in range(0, len(X), batch_size):
        X_batch = X[i:i + batch_size]
        y_batch = y[i:i + batch_size]

        tree.partial_fit(X_batch, y_batch)

    # Evaluate
    predictions = tree.predict(X[-100:])
    accuracy = (predictions == y[-100:]).mean()

    print(f"  Tree accuracy: {accuracy:.4f}")
    print(f"  Samples seen: {tree.root['n_samples']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
