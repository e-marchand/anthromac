"""Data quality scoring."""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class QualityScorer:
    """
    Compute overall data quality scores.

    Aggregates multiple quality dimensions into a single score.
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize scorer.

        Args:
            weights: Custom weights for quality dimensions
        """
        if weights is None:
            self.weights = {
                'completeness': 0.3,
                'validity': 0.25,
                'consistency': 0.2,
                'uniqueness': 0.15,
                'accuracy': 0.1
            }
        else:
            self.weights = weights

        # Normalize weights
        total = sum(self.weights.values())
        self.weights = {k: v/total for k, v in self.weights.items()}

        logger.info(f"Initialized QualityScorer with weights: {self.weights}")

    def score(
        self,
        df: pd.DataFrame,
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compute quality score for dataset.

        Args:
            df: Dataset to score
            validation_rules: Optional validation rules

        Returns:
            Dictionary with overall score and dimension scores
        """
        logger.info(f"Computing quality score for {len(df)} rows, {len(df.columns)} columns")

        scores = {
            'completeness': self._score_completeness(df),
            'validity': self._score_validity(df, validation_rules),
            'consistency': self._score_consistency(df),
            'uniqueness': self._score_uniqueness(df),
            'accuracy': self._score_accuracy(df)
        }

        # Compute weighted overall score
        overall = sum(
            scores[dim] * self.weights[dim]
            for dim in self.weights.keys()
        )

        result = {
            'overall_score': overall,
            'dimension_scores': scores,
            'grade': self._get_grade(overall),
            'issues': self._identify_issues(scores)
        }

        logger.info(f"Quality score: {overall:.3f} ({result['grade']})")

        return result

    def _score_completeness(self, df: pd.DataFrame) -> float:
        """Score data completeness (non-missing values)."""
        total_cells = df.shape[0] * df.shape[1]
        non_missing = df.notna().sum().sum()

        score = non_missing / total_cells if total_cells > 0 else 0.0

        logger.debug(f"Completeness: {score:.3f} ({non_missing}/{total_cells} non-missing)")
        return float(score)

    def _score_validity(
        self,
        df: pd.DataFrame,
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> float:
        """Score data validity (correct types and ranges)."""
        if validation_rules is None:
            # Simple validity check: numeric values in numeric columns
            valid_count = 0
            total_count = 0

            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    # Check for inf and very large values
                    valid = ~df[col].isin([np.inf, -np.inf])
                    valid_count += valid.sum()
                    total_count += len(df[col])

            score = valid_count / total_count if total_count > 0 else 1.0
        else:
            # Apply custom validation rules
            valid_count = 0
            total_count = 0

            for col, rules in validation_rules.items():
                if col not in df.columns:
                    continue

                valid = pd.Series([True] * len(df))

                if 'min' in rules:
                    valid &= df[col] >= rules['min']
                if 'max' in rules:
                    valid &= df[col] <= rules['max']
                if 'allowed_values' in rules:
                    valid &= df[col].isin(rules['allowed_values'])

                valid_count += valid.sum()
                total_count += len(df)

            score = valid_count / total_count if total_count > 0 else 1.0

        logger.debug(f"Validity: {score:.3f}")
        return float(score)

    def _score_consistency(self, df: pd.DataFrame) -> float:
        """Score data consistency (uniform formats, no conflicts)."""
        consistency_issues = 0
        total_checks = 0

        for col in df.columns:
            # Check for mixed types in object columns
            if df[col].dtype == 'object':
                types = df[col].dropna().apply(type).unique()
                if len(types) > 1:
                    consistency_issues += 1
                total_checks += 1

            # Check for inconsistent casing in strings
            if df[col].dtype == 'object':
                str_values = df[col].dropna().astype(str)
                if len(str_values) > 0:
                    # Check if mixed case exists
                    has_upper = (str_values.str[0].str.isupper()).any()
                    has_lower = (str_values.str[0].str.islower()).any()
                    if has_upper and has_lower:
                        consistency_issues += 0.5  # Minor issue
                    total_checks += 1

        score = 1.0 - (consistency_issues / total_checks) if total_checks > 0 else 1.0
        score = max(0.0, score)

        logger.debug(f"Consistency: {score:.3f}")
        return float(score)

    def _score_uniqueness(self, df: pd.DataFrame) -> float:
        """Score data uniqueness (no unexpected duplicates)."""
        # Check for duplicate rows
        n_duplicates = df.duplicated().sum()
        score = 1.0 - (n_duplicates / len(df)) if len(df) > 0 else 1.0

        logger.debug(f"Uniqueness: {score:.3f} ({n_duplicates} duplicates)")
        return float(score)

    def _score_accuracy(self, df: pd.DataFrame) -> float:
        """
        Score data accuracy (correctness).

        Without ground truth, we use heuristics like outlier detection.
        """
        # Use outlier detection as proxy for accuracy
        outlier_count = 0
        total_count = 0

        for col in df.select_dtypes(include=[np.number]).columns:
            # IQR method
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR

            outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_count += outliers.sum()
            total_count += len(df[col])

        score = 1.0 - (outlier_count / total_count) if total_count > 0 else 1.0

        logger.debug(f"Accuracy: {score:.3f} ({outlier_count} outliers)")
        return float(score)

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B'
        elif score >= 0.7:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'

    def _identify_issues(self, scores: Dict[str, float]) -> list:
        """Identify quality issues based on dimension scores."""
        issues = []

        for dimension, score in scores.items():
            if score < 0.7:
                severity = 'critical' if score < 0.5 else 'warning'
                issues.append({
                    'dimension': dimension,
                    'score': score,
                    'severity': severity
                })

        return issues


def main():
    """Example usage."""
    # Generate sample data with quality issues
    np.random.seed(42)

    df = pd.DataFrame({
        'id': list(range(100)) + [5, 10],  # Duplicates
        'age': list(np.random.randint(18, 80, 95)) + [None] * 5 + [150, -10],  # Missing + outliers
        'name': ['User' + str(i) for i in range(100)] + ['user50', 'USER75'],  # Inconsistent casing
        'email': ['user{}@example.com'.format(i) for i in range(95)] + [None] * 5 + ['invalid', 'also_invalid'],
        'score': np.random.randn(102) * 10 + 50
    })

    print("=" * 80)
    print("Quality Scorer - Example")
    print("=" * 80)

    print(f"\nDataset: {len(df)} rows, {len(df.columns)} columns")
    print(f"Missing values: {df.isna().sum().sum()}")
    print(f"Duplicate rows: {df.duplicated().sum()}")

    # Initialize scorer
    scorer = QualityScorer()

    # Compute quality score
    print("\n[1] Computing quality score...")
    result = scorer.score(df)

    print(f"\nOverall Score: {result['overall_score']:.3f} (Grade: {result['grade']})")

    print("\nDimension Scores:")
    for dimension, score in result['dimension_scores'].items():
        grade = scorer._get_grade(score)
        print(f"  {dimension:15s}: {score:.3f} ({grade})")

    # Show issues
    if result['issues']:
        print("\nIdentified Issues:")
        for issue in result['issues']:
            print(f"  [{issue['severity'].upper()}] {issue['dimension']}: "
                  f"score={issue['score']:.3f}")

    # Test with validation rules
    print("\n[2] Testing with validation rules...")

    validation_rules = {
        'age': {'min': 0, 'max': 120},
        'score': {'min': 0, 'max': 100}
    }

    result_validated = scorer.score(df, validation_rules)

    print(f"\nOverall Score (with validation): {result_validated['overall_score']:.3f}")
    print(f"Validity Score: {result_validated['dimension_scores']['validity']:.3f}")

    # Test with custom weights
    print("\n[3] Testing with custom weights...")

    custom_scorer = QualityScorer(weights={
        'completeness': 0.5,
        'validity': 0.3,
        'consistency': 0.1,
        'uniqueness': 0.05,
        'accuracy': 0.05
    })

    result_custom = custom_scorer.score(df)

    print(f"\nOverall Score (custom weights): {result_custom['overall_score']:.3f}")
    print(f"Grade: {result_custom['grade']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
