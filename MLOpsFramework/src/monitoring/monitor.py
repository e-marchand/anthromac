"""Model and data monitoring with drift detection."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime
from scipy import stats

logger = logging.getLogger(__name__)


class ModelMonitor:
    """
    Monitor model performance and data drift.

    Detects distribution shifts and performance degradation.
    """

    def __init__(
        self,
        drift_threshold: float = 0.05,
        performance_threshold: float = 0.1
    ):
        """
        Initialize monitor.

        Args:
            drift_threshold: P-value threshold for drift detection
            performance_threshold: Performance drop threshold for alerts
        """
        self.drift_threshold = drift_threshold
        self.performance_threshold = performance_threshold

        self.reference_data = None
        self.baseline_performance = None
        self.predictions_log = []

        logger.info(f"Initialized ModelMonitor (drift_threshold={drift_threshold})")

    def set_reference(self, reference_data: pd.DataFrame):
        """
        Set reference data for drift detection.

        Args:
            reference_data: Training or reference dataset
        """
        self.reference_data = reference_data.copy()
        logger.info(f"Set reference data: {len(reference_data)} samples")

    def detect_drift(
        self,
        current_data: pd.DataFrame,
        method: str = 'ks',
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect data drift between reference and current data.

        Args:
            current_data: Current production data
            method: Drift detection method ('ks', 'psi', 'chisquare')
            columns: Columns to check (all numeric if None)

        Returns:
            Drift detection report
        """
        if self.reference_data is None:
            raise ValueError("No reference data set. Call set_reference() first.")

        logger.info(f"Detecting drift using {method} test")

        if columns is None:
            # Use all numeric columns
            columns = self.reference_data.select_dtypes(include=[np.number]).columns.tolist()

        drift_report = {
            'timestamp': datetime.now().isoformat(),
            'method': method,
            'n_columns_tested': len(columns),
            'drifted_columns': [],
            'drift_scores': {}
        }

        for col in columns:
            if col not in current_data.columns:
                logger.warning(f"Column {col} not in current data, skipping")
                continue

            ref_values = self.reference_data[col].dropna()
            cur_values = current_data[col].dropna()

            if method == 'ks':
                statistic, p_value = self._kolmogorov_smirnov_test(
                    ref_values, cur_values
                )
                drift_score = statistic
            elif method == 'psi':
                drift_score = self._population_stability_index(
                    ref_values, cur_values
                )
                p_value = 1.0 if drift_score < 0.1 else 0.0  # PSI thresholds
            elif method == 'chisquare':
                if pd.api.types.is_numeric_dtype(ref_values):
                    # Bin numeric data for chi-square
                    ref_binned, bins = pd.cut(ref_values, bins=10, retbins=True, duplicates='drop')
                    cur_binned = pd.cut(cur_values, bins=bins, duplicates='drop')
                    statistic, p_value = stats.chisquare(
                        cur_binned.value_counts().sort_index(),
                        ref_binned.value_counts().sort_index()
                    )
                    drift_score = statistic
                else:
                    # Categorical data
                    ref_counts = ref_values.value_counts()
                    cur_counts = cur_values.value_counts()
                    # Align categories
                    all_cats = set(ref_counts.index) | set(cur_counts.index)
                    ref_aligned = ref_counts.reindex(all_cats, fill_value=0)
                    cur_aligned = cur_counts.reindex(all_cats, fill_value=0)
                    statistic, p_value = stats.chisquare(cur_aligned, ref_aligned)
                    drift_score = statistic
            else:
                raise ValueError(f"Unknown method: {method}")

            drift_report['drift_scores'][col] = {
                'score': float(drift_score),
                'p_value': float(p_value) if method != 'psi' else None,
                'drifted': p_value < self.drift_threshold if method != 'psi' else drift_score > 0.1
            }

            if drift_report['drift_scores'][col]['drifted']:
                drift_report['drifted_columns'].append(col)

        drift_report['has_drift'] = len(drift_report['drifted_columns']) > 0
        drift_report['drift_percentage'] = len(drift_report['drifted_columns']) / len(columns) * 100

        logger.info(
            f"Drift detection complete: {len(drift_report['drifted_columns'])}/{len(columns)} "
            f"columns drifted"
        )

        return drift_report

    def _kolmogorov_smirnov_test(
        self,
        ref: pd.Series,
        cur: pd.Series
    ) -> Tuple[float, float]:
        """Perform Kolmogorov-Smirnov test."""
        statistic, p_value = stats.ks_2samp(ref, cur)
        return statistic, p_value

    def _population_stability_index(
        self,
        ref: pd.Series,
        cur: pd.Series,
        bins: int = 10
    ) -> float:
        """
        Calculate Population Stability Index (PSI).

        PSI < 0.1: No significant change
        0.1 <= PSI < 0.2: Moderate change
        PSI >= 0.2: Significant change
        """
        # Bin the data
        ref_binned, bin_edges = pd.cut(ref, bins=bins, retbins=True, duplicates='drop')
        cur_binned = pd.cut(cur, bins=bin_edges, duplicates='drop')

        # Calculate proportions
        ref_props = ref_binned.value_counts(normalize=True).sort_index()
        cur_props = cur_binned.value_counts(normalize=True).sort_index()

        # Align indices
        all_bins = ref_props.index.union(cur_props.index)
        ref_props = ref_props.reindex(all_bins, fill_value=0.0001)  # Avoid log(0)
        cur_props = cur_props.reindex(all_bins, fill_value=0.0001)

        # Calculate PSI
        psi = np.sum((cur_props - ref_props) * np.log(cur_props / ref_props))

        return float(psi)

    def track_predictions(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track predictions for monitoring.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            metadata: Additional metadata
        """
        from sklearn.metrics import accuracy_score, mean_squared_error

        # Determine if classification or regression
        is_classification = len(np.unique(y_true)) < 20

        if is_classification:
            score = accuracy_score(y_true, y_pred)
            metric_name = 'accuracy'
        else:
            score = -mean_squared_error(y_true, y_pred)  # Negative for consistency
            metric_name = 'neg_mse'

        prediction_log = {
            'timestamp': datetime.now().isoformat(),
            'n_predictions': len(y_pred),
            metric_name: float(score),
            'metadata': metadata or {}
        }

        self.predictions_log.append(prediction_log)

        # Set baseline if not set
        if self.baseline_performance is None:
            self.baseline_performance = score
            logger.info(f"Set baseline performance: {score:.4f}")

        # Check for performance degradation
        performance_drop = self.baseline_performance - score
        if performance_drop > self.performance_threshold:
            logger.warning(
                f"Performance degradation detected! "
                f"Drop: {performance_drop:.4f}, "
                f"Baseline: {self.baseline_performance:.4f}, "
                f"Current: {score:.4f}"
            )

        logger.info(f"Tracked {len(y_pred)} predictions, {metric_name}: {score:.4f}")

    def get_performance_trends(self) -> pd.DataFrame:
        """
        Get performance trends over time.

        Returns:
            DataFrame with performance metrics over time
        """
        if not self.predictions_log:
            return pd.DataFrame()

        df = pd.DataFrame(self.predictions_log)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        return df

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive monitoring report.

        Returns:
            Monitoring report
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_predictions_tracked': len(self.predictions_log),
            'baseline_performance': self.baseline_performance
        }

        if self.predictions_log:
            trends = self.get_performance_trends()

            # Get metric name (first non-timestamp, non-metadata column)
            metric_cols = [c for c in trends.columns
                          if c not in ['timestamp', 'n_predictions', 'metadata']]

            if metric_cols:
                metric_name = metric_cols[0]
                report['current_performance'] = float(trends[metric_name].iloc[-1])
                report['mean_performance'] = float(trends[metric_name].mean())
                report['std_performance'] = float(trends[metric_name].std())

                if self.baseline_performance is not None:
                    report['performance_change'] = float(
                        report['current_performance'] - self.baseline_performance
                    )

        return report


def main():
    """Example usage."""
    np.random.seed(42)

    # Generate reference data
    n_samples = 1000
    reference_data = pd.DataFrame({
        'feature_1': np.random.normal(0, 1, n_samples),
        'feature_2': np.random.normal(5, 2, n_samples),
        'feature_3': np.random.exponential(2, n_samples)
    })

    # Generate current data with drift
    current_data = pd.DataFrame({
        'feature_1': np.random.normal(0.5, 1.2, n_samples),  # Shifted mean and std
        'feature_2': np.random.normal(5, 2, n_samples),      # No drift
        'feature_3': np.random.exponential(3, n_samples)     # Changed distribution
    })

    print("=" * 80)
    print("ModelMonitor - Example")
    print("=" * 80)

    monitor = ModelMonitor(drift_threshold=0.05)

    # Set reference
    print("\n[1] Setting reference data...")
    monitor.set_reference(reference_data)

    # Detect drift
    print("\n[2] Detecting drift...")
    drift_report = monitor.detect_drift(current_data, method='ks')

    print(f"Drift detected: {drift_report['has_drift']}")
    print(f"Drifted columns: {drift_report['drifted_columns']}")
    print("\nDrift scores:")
    for col, scores in drift_report['drift_scores'].items():
        status = "DRIFT" if scores['drifted'] else "OK"
        print(f"  {col:15s} - Score: {scores['score']:.4f}, p-value: {scores['p_value']:.4f} [{status}]")

    # Track predictions
    print("\n[3] Tracking predictions...")
    y_true = np.random.randint(0, 2, 100)
    y_pred = np.random.randint(0, 2, 100)

    monitor.track_predictions(y_true, y_pred)

    # Generate report
    print("\n[4] Monitoring report...")
    report = monitor.generate_report()
    for key, value in report.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
