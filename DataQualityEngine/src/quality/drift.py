"""Data drift detection."""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class DriftDetector:
    """
    Detect data drift between reference and current datasets.

    Uses statistical tests like PSI and Kolmogorov-Smirnov.
    """

    def __init__(
        self,
        psi_threshold: float = 0.2,
        ks_threshold: float = 0.05
    ):
        """
        Initialize drift detector.

        Args:
            psi_threshold: Threshold for PSI (>0.2 indicates drift)
            ks_threshold: P-value threshold for KS test
        """
        self.psi_threshold = psi_threshold
        self.ks_threshold = ks_threshold

        logger.info(f"Initialized DriftDetector (PSI threshold={psi_threshold})")

    def detect(
        self,
        reference: pd.DataFrame,
        current: pd.DataFrame,
        columns: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Detect drift between reference and current data.

        Args:
            reference: Reference (baseline) dataset
            current: Current dataset to compare
            columns: Columns to check (default: all common columns)

        Returns:
            Dictionary with drift results
        """
        if columns is None:
            columns = list(set(reference.columns) & set(current.columns))

        logger.info(f"Detecting drift on {len(columns)} columns")

        results = {
            'has_drift': False,
            'columns': {},
            'summary': {
                'total_columns': len(columns),
                'drifted_columns': 0,
                'drift_score': 0.0
            }
        }

        drift_scores = []

        for col in columns:
            ref_col = reference[col].dropna()
            cur_col = current[col].dropna()

            if len(ref_col) == 0 or len(cur_col) == 0:
                logger.warning(f"Skipping column '{col}' - insufficient data")
                continue

            # Determine column type and apply appropriate test
            if pd.api.types.is_numeric_dtype(ref_col):
                drift_result = self._detect_numeric_drift(ref_col, cur_col, col)
            else:
                drift_result = self._detect_categorical_drift(ref_col, cur_col, col)

            results['columns'][col] = drift_result

            if drift_result['has_drift']:
                results['has_drift'] = True
                results['summary']['drifted_columns'] += 1

            drift_scores.append(drift_result['drift_score'])

        # Overall drift score
        results['summary']['drift_score'] = np.mean(drift_scores) if drift_scores else 0.0

        logger.info(f"Drift detection complete - {results['summary']['drifted_columns']}/{len(columns)} "
                   f"columns show drift")

        return results

    def _detect_numeric_drift(
        self,
        reference: pd.Series,
        current: pd.Series,
        col_name: str
    ) -> Dict[str, Any]:
        """Detect drift in numeric columns using KS test."""
        # Kolmogorov-Smirnov test
        ks_stat, p_value = stats.ks_2samp(reference, current)

        has_drift = p_value < self.ks_threshold

        # Also compute distribution shift metrics
        ref_mean = reference.mean()
        cur_mean = current.mean()
        ref_std = reference.std()
        cur_std = current.std()

        mean_shift = abs(cur_mean - ref_mean) / (ref_std + 1e-8)

        result = {
            'has_drift': has_drift,
            'method': 'kolmogorov_smirnov',
            'drift_score': float(ks_stat),
            'p_value': float(p_value),
            'statistics': {
                'reference_mean': float(ref_mean),
                'current_mean': float(cur_mean),
                'reference_std': float(ref_std),
                'current_std': float(cur_std),
                'mean_shift': float(mean_shift)
            }
        }

        if has_drift:
            logger.info(f"Drift detected in '{col_name}': KS={ks_stat:.4f}, p={p_value:.4f}")

        return result

    def _detect_categorical_drift(
        self,
        reference: pd.Series,
        current: pd.Series,
        col_name: str
    ) -> Dict[str, Any]:
        """Detect drift in categorical columns using PSI."""
        # Calculate Population Stability Index
        psi = self._calculate_psi(reference, current)

        has_drift = psi > self.psi_threshold

        # Get distribution changes
        ref_dist = reference.value_counts(normalize=True)
        cur_dist = current.value_counts(normalize=True)

        # Find categories with largest changes
        all_categories = set(ref_dist.index) | set(cur_dist.index)
        changes = {}

        for cat in all_categories:
            ref_pct = ref_dist.get(cat, 0.0)
            cur_pct = cur_dist.get(cat, 0.0)
            change = abs(cur_pct - ref_pct)
            changes[cat] = {
                'reference_pct': float(ref_pct),
                'current_pct': float(cur_pct),
                'change': float(change)
            }

        # Sort by change magnitude
        top_changes = sorted(
            changes.items(),
            key=lambda x: x[1]['change'],
            reverse=True
        )[:5]

        result = {
            'has_drift': has_drift,
            'method': 'population_stability_index',
            'drift_score': float(psi),
            'statistics': {
                'psi': float(psi),
                'top_changes': dict(top_changes)
            }
        }

        if has_drift:
            logger.info(f"Drift detected in '{col_name}': PSI={psi:.4f}")

        return result

    def _calculate_psi(
        self,
        reference: pd.Series,
        current: pd.Series,
        bins: int = 10
    ) -> float:
        """
        Calculate Population Stability Index.

        PSI = sum((current_pct - reference_pct) * ln(current_pct / reference_pct))

        Args:
            reference: Reference distribution
            current: Current distribution
            bins: Number of bins for numeric data

        Returns:
            PSI value
        """
        # Get distributions
        if pd.api.types.is_numeric_dtype(reference):
            # For numeric, bin the data
            breakpoints = np.percentile(
                reference,
                np.linspace(0, 100, bins + 1)
            )
            breakpoints = np.unique(breakpoints)

            ref_counts = pd.cut(reference, bins=breakpoints, include_lowest=True).value_counts()
            cur_counts = pd.cut(current, bins=breakpoints, include_lowest=True).value_counts()
        else:
            # For categorical, use value counts
            ref_counts = reference.value_counts()
            cur_counts = current.value_counts()

        # Convert to percentages
        ref_pct = ref_counts / len(reference)
        cur_pct = cur_counts.reindex(ref_pct.index, fill_value=0) / len(current)

        # Avoid log(0) by adding small epsilon
        epsilon = 1e-10
        ref_pct = ref_pct + epsilon
        cur_pct = cur_pct + epsilon

        # Calculate PSI
        psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))

        return float(psi)

    def get_drift_summary(self, drift_results: Dict[str, Any]) -> str:
        """
        Generate human-readable drift summary.

        Args:
            drift_results: Results from detect()

        Returns:
            Formatted summary string
        """
        summary = []
        summary.append("=" * 60)
        summary.append("DATA DRIFT SUMMARY")
        summary.append("=" * 60)

        summary.append(f"\nOverall Drift: {'DETECTED' if drift_results['has_drift'] else 'NOT DETECTED'}")
        summary.append(f"Drift Score: {drift_results['summary']['drift_score']:.4f}")
        summary.append(f"Columns Analyzed: {drift_results['summary']['total_columns']}")
        summary.append(f"Columns with Drift: {drift_results['summary']['drifted_columns']}")

        if drift_results['has_drift']:
            summary.append("\nColumns with Drift:")
            for col, result in drift_results['columns'].items():
                if result['has_drift']:
                    summary.append(f"  - {col}: {result['method']}, "
                                 f"score={result['drift_score']:.4f}")

        summary.append("=" * 60)

        return "\n".join(summary)


def main():
    """Example usage."""
    np.random.seed(42)

    # Generate reference data
    reference = pd.DataFrame({
        'age': np.random.normal(40, 10, 1000),
        'income': np.random.lognormal(10, 1, 1000),
        'category': np.random.choice(['A', 'B', 'C'], 1000, p=[0.5, 0.3, 0.2]),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 1000)
    })

    print("=" * 80)
    print("Drift Detector - Example")
    print("=" * 80)

    print(f"\nReference data: {len(reference)} rows")
    print(f"Columns: {list(reference.columns)}")

    # Test 1: No drift (similar distribution)
    print("\n[1] Testing with no drift...")

    current_no_drift = pd.DataFrame({
        'age': np.random.normal(40, 10, 1000),
        'income': np.random.lognormal(10, 1, 1000),
        'category': np.random.choice(['A', 'B', 'C'], 1000, p=[0.5, 0.3, 0.2]),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 1000)
    })

    detector = DriftDetector()
    results_no_drift = detector.detect(reference, current_no_drift)

    print(f"\nDrift detected: {results_no_drift['has_drift']}")
    print(f"Overall drift score: {results_no_drift['summary']['drift_score']:.4f}")
    print(f"Drifted columns: {results_no_drift['summary']['drifted_columns']}")

    # Test 2: With drift (shifted distribution)
    print("\n[2] Testing with drift...")

    current_with_drift = pd.DataFrame({
        'age': np.random.normal(50, 12, 1000),  # Mean shifted
        'income': np.random.lognormal(10.5, 1.2, 1000),  # Distribution changed
        'category': np.random.choice(['A', 'B', 'C'], 1000, p=[0.3, 0.4, 0.3]),  # Distribution changed
        'region': np.random.choice(['North', 'South', 'East', 'West'], 1000)
    })

    results_with_drift = detector.detect(reference, current_with_drift)

    print(f"\nDrift detected: {results_with_drift['has_drift']}")
    print(f"Overall drift score: {results_with_drift['summary']['drift_score']:.4f}")
    print(f"Drifted columns: {results_with_drift['summary']['drifted_columns']}")

    print("\nDetails by column:")
    for col, result in results_with_drift['columns'].items():
        status = "DRIFT" if result['has_drift'] else "OK"
        print(f"  {col:12s}: [{status:5s}] score={result['drift_score']:.4f}, "
              f"method={result['method']}")

    # Show detailed statistics for drifted numeric columns
    print("\n[3] Detailed statistics for numeric columns with drift:")
    for col, result in results_with_drift['columns'].items():
        if result['has_drift'] and result['method'] == 'kolmogorov_smirnov':
            stats = result['statistics']
            print(f"\n  {col}:")
            print(f"    Reference mean: {stats['reference_mean']:.2f} "
                  f"(std: {stats['reference_std']:.2f})")
            print(f"    Current mean:   {stats['current_mean']:.2f} "
                  f"(std: {stats['current_std']:.2f})")
            print(f"    Mean shift:     {stats['mean_shift']:.2f} std deviations")
            print(f"    KS statistic:   {result['drift_score']:.4f}")
            print(f"    P-value:        {result['p_value']:.4f}")

    # Show detailed statistics for drifted categorical columns
    print("\n[4] Detailed statistics for categorical columns with drift:")
    for col, result in results_with_drift['columns'].items():
        if result['has_drift'] and result['method'] == 'population_stability_index':
            print(f"\n  {col}:")
            print(f"    PSI: {result['statistics']['psi']:.4f}")
            print(f"    Top distribution changes:")
            for category, change_info in result['statistics']['top_changes'].items():
                print(f"      {category}: {change_info['reference_pct']*100:.1f}% → "
                      f"{change_info['current_pct']*100:.1f}% "
                      f"(Δ {change_info['change']*100:.1f}%)")

    # Generate summary
    print("\n[5] Summary Report:")
    print(detector.get_drift_summary(results_with_drift))

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
