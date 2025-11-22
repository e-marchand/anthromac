"""Data validation using Pandera and custom checks."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Data validation system for ML pipelines.

    Validates schema, data quality, and detects anomalies.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize validator.

        Args:
            config: Validation configuration
        """
        self.config = config or {}
        self.validation_results = []

        logger.info("Initialized DataValidator")

    def validate_schema(
        self,
        df: pd.DataFrame,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate DataFrame schema.

        Args:
            df: DataFrame to validate
            schema: Expected schema definition

        Returns:
            Validation results
        """
        logger.info(f"Validating schema for DataFrame with shape {df.shape}")

        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        if schema is None:
            # Basic validation without schema
            results['warnings'].append("No schema provided, performing basic validation")

            # Check for null columns
            null_cols = df.columns[df.isnull().all()].tolist()
            if null_cols:
                results['errors'].append(f"Columns with all null values: {null_cols}")
                results['valid'] = False

            # Check for duplicate columns
            dup_cols = df.columns[df.columns.duplicated()].tolist()
            if dup_cols:
                results['errors'].append(f"Duplicate column names: {dup_cols}")
                results['valid'] = False

            return results

        # Validate with schema
        try:
            # Check required columns
            if 'required_columns' in schema:
                required = set(schema['required_columns'])
                actual = set(df.columns)
                missing = required - actual

                if missing:
                    results['errors'].append(f"Missing required columns: {list(missing)}")
                    results['valid'] = False

            # Check column types
            if 'column_types' in schema:
                for col, expected_type in schema['column_types'].items():
                    if col not in df.columns:
                        continue

                    actual_dtype = str(df[col].dtype)

                    # Map pandas dtypes to expected types
                    if expected_type == 'numeric':
                        if not pd.api.types.is_numeric_dtype(df[col]):
                            results['errors'].append(
                                f"Column '{col}' expected numeric, got {actual_dtype}"
                            )
                            results['valid'] = False
                    elif expected_type == 'categorical':
                        if not (pd.api.types.is_categorical_dtype(df[col]) or
                               pd.api.types.is_object_dtype(df[col])):
                            results['warnings'].append(
                                f"Column '{col}' expected categorical, got {actual_dtype}"
                            )

            # Check value ranges
            if 'value_ranges' in schema:
                for col, range_spec in schema['value_ranges'].items():
                    if col not in df.columns:
                        continue

                    col_min = df[col].min()
                    col_max = df[col].max()

                    if 'min' in range_spec and col_min < range_spec['min']:
                        results['errors'].append(
                            f"Column '{col}' has values below minimum {range_spec['min']}"
                        )
                        results['valid'] = False

                    if 'max' in range_spec and col_max > range_spec['max']:
                        results['errors'].append(
                            f"Column '{col}' has values above maximum {range_spec['max']}"
                        )
                        results['valid'] = False

        except Exception as e:
            results['errors'].append(f"Schema validation error: {str(e)}")
            results['valid'] = False

        logger.info(f"Schema validation: {'PASSED' if results['valid'] else 'FAILED'}")
        return results

    def quality_check(
        self,
        df: pd.DataFrame,
        checks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform data quality checks.

        Args:
            df: DataFrame to check
            checks: List of checks to perform

        Returns:
            Quality report
        """
        if checks is None:
            checks = ['missing', 'duplicates', 'outliers', 'cardinality']

        logger.info(f"Running quality checks: {checks}")

        report = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'checks': {}
        }

        # Missing values check
        if 'missing' in checks:
            missing_stats = {
                col: {
                    'count': int(df[col].isnull().sum()),
                    'percentage': float(df[col].isnull().mean() * 100)
                }
                for col in df.columns
            }

            report['checks']['missing_values'] = {
                'total_missing': sum(s['count'] for s in missing_stats.values()),
                'columns_with_missing': {
                    col: stats for col, stats in missing_stats.items()
                    if stats['count'] > 0
                }
            }

        # Duplicate rows check
        if 'duplicates' in checks:
            dup_count = df.duplicated().sum()
            report['checks']['duplicates'] = {
                'count': int(dup_count),
                'percentage': float(dup_count / len(df) * 100)
            }

        # Outliers check (for numeric columns)
        if 'outliers' in checks:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            outliers = {}

            for col in numeric_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1

                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
                outlier_count = outlier_mask.sum()

                if outlier_count > 0:
                    outliers[col] = {
                        'count': int(outlier_count),
                        'percentage': float(outlier_count / len(df) * 100),
                        'bounds': {
                            'lower': float(lower_bound),
                            'upper': float(upper_bound)
                        }
                    }

            report['checks']['outliers'] = outliers

        # Cardinality check
        if 'cardinality' in checks:
            cardinality = {}

            for col in df.columns:
                unique_count = df[col].nunique()
                cardinality[col] = {
                    'unique_values': int(unique_count),
                    'cardinality_ratio': float(unique_count / len(df))
                }

            report['checks']['cardinality'] = cardinality

        logger.info("Quality check completed")
        return report

    def detect_anomalies(
        self,
        df: pd.DataFrame,
        method: str = 'zscore',
        threshold: float = 3.0
    ) -> Dict[str, pd.DataFrame]:
        """
        Detect anomalies in numeric columns.

        Args:
            df: DataFrame to check
            method: Detection method ('zscore', 'iqr')
            threshold: Threshold for anomaly detection

        Returns:
            Dictionary of anomalous rows per column
        """
        logger.info(f"Detecting anomalies using {method} method")

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        anomalies = {}

        for col in numeric_cols:
            if method == 'zscore':
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                anomaly_mask = z_scores > threshold
            elif method == 'iqr':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - threshold * IQR
                upper = Q3 + threshold * IQR
                anomaly_mask = (df[col] < lower) | (df[col] > upper)
            else:
                raise ValueError(f"Unknown method: {method}")

            if anomaly_mask.any():
                anomalies[col] = df[anomaly_mask]

        logger.info(f"Found anomalies in {len(anomalies)} columns")
        return anomalies


def main():
    """Example usage."""
    # Create sample data
    np.random.seed(42)
    df = pd.DataFrame({
        'feature_1': np.random.randn(1000),
        'feature_2': np.random.randint(0, 100, 1000),
        'feature_3': np.random.choice(['A', 'B', 'C'], 1000),
        'target': np.random.randint(0, 2, 1000)
    })

    # Add some missing values
    df.loc[np.random.choice(df.index, 50), 'feature_1'] = np.nan

    print("=" * 80)
    print("DataValidator - Example")
    print("=" * 80)

    validator = DataValidator()

    # Schema validation
    print("\n[1] Schema Validation")
    schema = {
        'required_columns': ['feature_1', 'feature_2', 'target'],
        'column_types': {
            'feature_1': 'numeric',
            'feature_2': 'numeric',
            'target': 'numeric'
        }
    }

    results = validator.validate_schema(df, schema)
    print(f"Valid: {results['valid']}")
    if results['errors']:
        print(f"Errors: {results['errors']}")

    # Quality check
    print("\n[2] Quality Check")
    quality_report = validator.quality_check(df)
    print(f"Total rows: {quality_report['total_rows']}")
    print(f"Missing values: {quality_report['checks']['missing_values']['total_missing']}")
    print(f"Duplicates: {quality_report['checks']['duplicates']['count']}")

    # Anomaly detection
    print("\n[3] Anomaly Detection")
    anomalies = validator.detect_anomalies(df, method='zscore', threshold=3.0)
    for col, anom_df in anomalies.items():
        print(f"  {col}: {len(anom_df)} anomalies")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
