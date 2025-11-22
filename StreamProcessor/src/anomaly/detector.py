"""Streaming anomaly detection."""

import numpy as np
from collections import deque
from typing import Tuple, Optional
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class StreamingAnomalyDetector:
    """
    Real-time anomaly detection for streaming data.

    Uses statistical methods and can adapt to concept drift.
    """

    def __init__(
        self,
        method: str = 'zscore',
        window_size: int = 100,
        threshold: float = 3.0,
        adapt: bool = True
    ):
        """
        Initialize anomaly detector.

        Args:
            method: Detection method ('zscore', 'iqr', 'isolation_forest')
            window_size: Size of sliding window
            threshold: Anomaly threshold
            adapt: Whether to adapt to concept drift
        """
        self.method = method
        self.window_size = window_size
        self.threshold = threshold
        self.adapt = adapt

        # Sliding window
        self.window = deque(maxlen=window_size)

        # Statistics
        self.mean = 0.0
        self.std = 1.0
        self.q1 = 0.0
        self.q3 = 0.0
        self.iqr = 1.0

        # Tracking
        self.n_seen = 0
        self.n_anomalies = 0

        logger.info(f"Initialized StreamingAnomalyDetector "
                   f"(method={method}, window={window_size}, threshold={threshold})")

    def fit(self, data: np.ndarray):
        """
        Initialize detector with normal data.

        Args:
            data: Normal data for initialization
        """
        logger.info(f"Initializing with {len(data)} normal samples")

        # Add to window
        for value in data[-self.window_size:]:
            self.window.append(value)

        # Compute initial statistics
        self._update_statistics()

        logger.info(f"Initialized - mean={self.mean:.4f}, std={self.std:.4f}")

    def detect(self, value: float) -> Tuple[bool, float]:
        """
        Detect if value is anomalous.

        Args:
            value: Value to check

        Returns:
            Tuple of (is_anomaly, anomaly_score)
        """
        # Compute anomaly score
        if self.method == 'zscore':
            score = self._zscore_score(value)
            is_anomaly = abs(score) > self.threshold

        elif self.method == 'iqr':
            score = self._iqr_score(value)
            is_anomaly = score > 0

        else:
            raise ValueError(f"Unknown method: {self.method}")

        # Update window and statistics
        self.window.append(value)
        self.n_seen += 1

        if is_anomaly:
            self.n_anomalies += 1

        # Adapt to concept drift
        if self.adapt and not is_anomaly:
            self._update_statistics()

        return is_anomaly, score

    def get_statistics(self) -> dict:
        """Get current statistics."""
        return {
            'mean': self.mean,
            'std': self.std,
            'q1': self.q1,
            'q3': self.q3,
            'iqr': self.iqr,
            'n_seen': self.n_seen,
            'n_anomalies': self.n_anomalies,
            'anomaly_rate': self.n_anomalies / max(self.n_seen, 1)
        }

    def _zscore_score(self, value: float) -> float:
        """Compute Z-score."""
        if self.std == 0:
            return 0.0

        return (value - self.mean) / self.std

    def _iqr_score(self, value: float) -> float:
        """
        Compute IQR-based score.

        Returns positive if anomalous, 0 otherwise.
        """
        if self.iqr == 0:
            return 0.0

        lower_bound = self.q1 - 1.5 * self.iqr
        upper_bound = self.q3 + 1.5 * self.iqr

        if value < lower_bound:
            return (lower_bound - value) / self.iqr
        elif value > upper_bound:
            return (value - upper_bound) / self.iqr
        else:
            return 0.0

    def _update_statistics(self):
        """Update statistics from window."""
        if len(self.window) < 2:
            return

        data = np.array(self.window)

        # Mean and std
        self.mean = data.mean()
        self.std = data.std()

        # Quartiles
        self.q1 = np.percentile(data, 25)
        self.q3 = np.percentile(data, 75)
        self.iqr = self.q3 - self.q1


class EWMADetector:
    """
    Exponentially Weighted Moving Average anomaly detector.

    Adapts quickly to trends while detecting anomalies.
    """

    def __init__(
        self,
        alpha: float = 0.3,
        threshold: float = 3.0
    ):
        """
        Initialize EWMA detector.

        Args:
            alpha: Smoothing factor (0-1)
            threshold: Anomaly threshold in standard deviations
        """
        self.alpha = alpha
        self.threshold = threshold

        self.ewma = None
        self.ewmvar = None

        logger.info(f"Initialized EWMADetector (alpha={alpha}, threshold={threshold})")

    def detect(self, value: float) -> Tuple[bool, float]:
        """
        Detect anomaly using EWMA.

        Args:
            value: Value to check

        Returns:
            Tuple of (is_anomaly, z_score)
        """
        # Initialize if needed
        if self.ewma is None:
            self.ewma = value
            self.ewmvar = 0.0
            return False, 0.0

        # Update EWMA
        delta = value - self.ewma
        self.ewma = self.alpha * value + (1 - self.alpha) * self.ewma

        # Update variance
        self.ewmvar = (1 - self.alpha) * (self.ewmvar + self.alpha * delta ** 2)

        # Compute z-score
        std = np.sqrt(self.ewmvar)

        if std > 0:
            z_score = abs(delta) / std
        else:
            z_score = 0.0

        is_anomaly = z_score > self.threshold

        return is_anomaly, z_score


def main():
    """Example usage."""
    print("=" * 80)
    print("Streaming Anomaly Detection - Example")
    print("=" * 80)

    # Generate normal data
    np.random.seed(42)

    normal_data = np.random.normal(100, 10, 1000)

    # Generate test stream with anomalies
    test_stream = []

    for i in range(500):
        if i % 100 == 99:
            # Inject anomaly
            value = np.random.normal(100, 10) + np.random.choice([-50, 50])
        else:
            # Normal value
            value = np.random.normal(100, 10)

        test_stream.append(value)

    print(f"\nGenerated test stream: {len(test_stream)} values")
    print(f"  Injected anomalies: 5")

    # Test Z-score detector
    print("\n[1] Z-Score Detector:")

    detector_zscore = StreamingAnomalyDetector(
        method='zscore',
        window_size=50,
        threshold=3.0,
        adapt=True
    )

    # Initialize
    detector_zscore.fit(normal_data[:100])

    # Detect anomalies
    anomalies_zscore = []

    for i, value in enumerate(test_stream):
        is_anomaly, score = detector_zscore.detect(value)

        if is_anomaly:
            anomalies_zscore.append((i, value, score))

    stats = detector_zscore.get_statistics()

    print(f"  Detected: {stats['n_anomalies']} anomalies")
    print(f"  Anomaly rate: {stats['anomaly_rate']*100:.2f}%")

    print(f"\n  Sample anomalies:")
    for idx, value, score in anomalies_zscore[:5]:
        print(f"    Index {idx}: value={value:.2f}, z-score={score:.2f}")

    # Test IQR detector
    print("\n[2] IQR Detector:")

    detector_iqr = StreamingAnomalyDetector(
        method='iqr',
        window_size=50,
        threshold=1.5
    )

    detector_iqr.fit(normal_data[:100])

    anomalies_iqr = []

    for i, value in enumerate(test_stream):
        is_anomaly, score = detector_iqr.detect(value)

        if is_anomaly:
            anomalies_iqr.append((i, value, score))

    stats_iqr = detector_iqr.get_statistics()

    print(f"  Detected: {stats_iqr['n_anomalies']} anomalies")
    print(f"  Q1={stats_iqr['q1']:.2f}, Q3={stats_iqr['q3']:.2f}, IQR={stats_iqr['iqr']:.2f}")

    # Test EWMA detector
    print("\n[3] EWMA Detector:")

    detector_ewma = EWMADetector(alpha=0.3, threshold=3.0)

    anomalies_ewma = []

    for i, value in enumerate(test_stream):
        is_anomaly, score = detector_ewma.detect(value)

        if is_anomaly:
            anomalies_ewma.append((i, value, score))

    print(f"  Detected: {len(anomalies_ewma)} anomalies")

    # Test concept drift adaptation
    print("\n[4] Concept Drift Test:")

    # Generate data with shift
    stream_with_drift = []

    for i in range(1000):
        if i < 500:
            value = np.random.normal(100, 10)
        else:
            # Concept drift: mean shifts to 120
            value = np.random.normal(120, 10)

        stream_with_drift.append(value)

    # Non-adaptive detector
    detector_static = StreamingAnomalyDetector(
        method='zscore',
        window_size=50,
        threshold=3.0,
        adapt=False
    )

    detector_static.fit(normal_data[:100])

    anomalies_static = 0
    for value in stream_with_drift:
        is_anomaly, _ = detector_static.detect(value)
        if is_anomaly:
            anomalies_static += 1

    # Adaptive detector
    detector_adaptive = StreamingAnomalyDetector(
        method='zscore',
        window_size=50,
        threshold=3.0,
        adapt=True
    )

    detector_adaptive.fit(normal_data[:100])

    anomalies_adaptive = 0
    for value in stream_with_drift:
        is_anomaly, _ = detector_adaptive.detect(value)
        if is_anomaly:
            anomalies_adaptive += 1

    print(f"  Non-adaptive detector: {anomalies_static} anomalies")
    print(f"  Adaptive detector: {anomalies_adaptive} anomalies")
    print(f"  (Adaptive should detect fewer false positives after drift)")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
