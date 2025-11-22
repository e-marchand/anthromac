"""Anomaly detection using multiple methods."""

import numpy as np
import pandas as pd
from typing import Optional, Union
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Multi-method anomaly detector.

    Supports Isolation Forest, LOF, and statistical methods.
    """

    def __init__(
        self,
        method: str = 'isolation_forest',
        contamination: float = 0.1,
        **kwargs
    ):
        """
        Initialize detector.

        Args:
            method: Detection method ('isolation_forest', 'lof', 'zscore')
            contamination: Expected proportion of anomalies
            **kwargs: Method-specific parameters
        """
        self.method = method
        self.contamination = contamination
        self.kwargs = kwargs

        self.detector = None
        self.scaler = StandardScaler()
        self.fitted = False

        logger.info(f"Initialized AnomalyDetector with method='{method}'")

    def fit(self, X: Union[pd.DataFrame, np.ndarray]) -> 'AnomalyDetector':
        """
        Fit anomaly detector.

        Args:
            X: Training data

        Returns:
            self: Fitted detector
        """
        logger.info(f"Fitting {self.method} on {len(X)} samples")

        # Convert to numpy if DataFrame
        if isinstance(X, pd.DataFrame):
            # Use only numeric columns
            X_numeric = X.select_dtypes(include=[np.number])
            X_array = X_numeric.values
        else:
            X_array = X

        # Scale data
        X_scaled = self.scaler.fit_transform(X_array)

        # Initialize and fit detector
        if self.method == 'isolation_forest':
            self.detector = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                **self.kwargs
            )
            self.detector.fit(X_scaled)

        elif self.method == 'lof':
            self.detector = LocalOutlierFactor(
                contamination=self.contamination,
                novelty=True,
                **self.kwargs
            )
            self.detector.fit(X_scaled)

        elif self.method == 'zscore':
            # Statistical method doesn't need fitting
            self.detector = None

        else:
            raise ValueError(f"Unknown method: {self.method}")

        self.fitted = True
        logger.info("Fitting completed")

        return self

    def detect(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """
        Detect anomalies.

        Args:
            X: Data to check

        Returns:
            Boolean array (True = anomaly)
        """
        if not self.fitted and self.method != 'zscore':
            raise ValueError("Detector not fitted. Call fit() first.")

        logger.info(f"Detecting anomalies in {len(X)} samples")

        # Convert to numpy if DataFrame
        if isinstance(X, pd.DataFrame):
            X_numeric = X.select_dtypes(include=[np.number])
            X_array = X_numeric.values
        else:
            X_array = X

        # Scale data
        if self.method != 'zscore':
            X_scaled = self.scaler.transform(X_array)

        # Detect anomalies
        if self.method in ['isolation_forest', 'lof']:
            predictions = self.detector.predict(X_scaled)
            anomalies = predictions == -1

        elif self.method == 'zscore':
            # Z-score method
            z_scores = np.abs(stats.zscore(X_array, axis=0, nan_policy='omit'))
            # Consider anomaly if any feature has |z| > 3
            anomalies = (z_scores > 3).any(axis=1)

        else:
            raise ValueError(f"Unknown method: {self.method}")

        n_anomalies = anomalies.sum()
        anomaly_rate = n_anomalies / len(X) * 100

        logger.info(f"Found {n_anomalies} anomalies ({anomaly_rate:.2f}%)")

        return anomalies

    def get_scores(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """
        Get anomaly scores.

        Args:
            X: Data to score

        Returns:
            Array of anomaly scores (higher = more anomalous)
        """
        if not self.fitted and self.method != 'zscore':
            raise ValueError("Detector not fitted. Call fit() first.")

        # Convert to numpy if DataFrame
        if isinstance(X, pd.DataFrame):
            X_numeric = X.select_dtypes(include=[np.number])
            X_array = X_numeric.values
        else:
            X_array = X

        # Scale data
        if self.method != 'zscore':
            X_scaled = self.scaler.transform(X_array)

        # Get scores
        if self.method == 'isolation_forest':
            # decision_function returns negative scores (lower = more anomalous)
            scores = -self.detector.decision_function(X_scaled)

        elif self.method == 'lof':
            # score_samples returns negative LOF scores
            scores = -self.detector.score_samples(X_scaled)

        elif self.method == 'zscore':
            # Use maximum absolute z-score across features
            from scipy import stats as scipy_stats
            z_scores = np.abs(scipy_stats.zscore(X_array, axis=0, nan_policy='omit'))
            scores = np.max(z_scores, axis=1)

        else:
            raise ValueError(f"Unknown method: {self.method}")

        return scores


def main():
    """Example usage."""
    from sklearn.datasets import make_classification

    # Generate data with anomalies
    np.random.seed(42)

    # Normal data
    X_normal, _ = make_classification(
        n_samples=900,
        n_features=10,
        n_informative=7,
        random_state=42
    )

    # Anomalous data (different distribution)
    X_anomaly = np.random.uniform(low=-10, high=10, size=(100, 10))

    # Combine
    X = np.vstack([X_normal, X_anomaly])
    true_labels = np.array([0] * 900 + [1] * 100)

    print("=" * 80)
    print("AnomalyDetector - Example")
    print("=" * 80)

    print(f"\nData: {len(X)} samples, {X.shape[1]} features")
    print(f"True anomalies: {true_labels.sum()} ({true_labels.mean()*100:.1f}%)")

    # Test different methods
    methods = ['isolation_forest', 'lof']

    for method in methods:
        print(f"\n[{method.upper()}]")

        # Initialize and fit
        detector = AnomalyDetector(method=method, contamination=0.1)
        detector.fit(X)

        # Detect anomalies
        predictions = detector.detect(X)

        # Evaluate
        from sklearn.metrics import precision_score, recall_score, f1_score

        precision = precision_score(true_labels, predictions)
        recall = recall_score(true_labels, predictions)
        f1 = f1_score(true_labels, predictions)

        print(f"  Detected: {predictions.sum()} anomalies")
        print(f"  Precision: {precision:.3f}")
        print(f"  Recall: {recall:.3f}")
        print(f"  F1-Score: {f1:.3f}")

        # Get top anomalies by score
        scores = detector.get_scores(X)
        top_indices = np.argsort(-scores)[:10]

        print(f"\n  Top 10 anomaly scores:")
        for i, idx in enumerate(top_indices, 1):
            actual = "ANOMALY" if true_labels[idx] == 1 else "Normal"
            print(f"    {i}. Index {idx}: score={scores[idx]:.3f} [{actual}]")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
