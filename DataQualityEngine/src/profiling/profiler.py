"""Data profiler for comprehensive statistical analysis."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class DataProfiler:
    """
    Comprehensive data profiling system.

    Analyzes datasets to extract statistical properties,
    distributions, and quality metrics.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize profiler.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        logger.info("Initialized DataProfiler")

    def profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Profile a dataset.

        Args:
            df: DataFrame to profile

        Returns:
            Comprehensive profile dictionary
        """
        logger.info(f"Profiling dataset with shape {df.shape}")

        profile = {
            'summary': self._profile_summary(df),
            'columns': {},
            'correlations': {},
            'warnings': []
        }

        # Profile each column
        for col in df.columns:
            profile['columns'][col] = self._profile_column(df[col])

        # Compute correlations for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            profile['correlations'] = self._compute_correlations(df[numeric_cols])

        # Generate warnings
        profile['warnings'] = self._generate_warnings(df, profile)

        logger.info("Profiling completed")
        return profile

    def _profile_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate dataset summary."""
        summary = {
            'n_rows': len(df),
            'n_columns': len(df.columns),
            'total_cells': df.size,
            'missing_cells': df.isnull().sum().sum(),
            'missing_cells_pct': (df.isnull().sum().sum() / df.size) * 100,
            'duplicate_rows': df.duplicated().sum(),
            'duplicate_rows_pct': (df.duplicated().sum() / len(df)) * 100,
            'memory_size_mb': df.memory_usage(deep=True).sum() / (1024 ** 2)
        }

        # Column type distribution
        type_counts = df.dtypes.value_counts()
        summary['column_types'] = {str(k): int(v) for k, v in type_counts.items()}

        return summary

    def _profile_column(self, series: pd.Series) -> Dict[str, Any]:
        """Profile a single column."""
        profile = {
            'dtype': str(series.dtype),
            'type': self._infer_type(series),
            'count': int(series.count()),
            'missing': int(series.isnull().sum()),
            'missing_pct': float(series.isnull().mean() * 100),
            'unique': int(series.nunique()),
            'unique_pct': float(series.nunique() / len(series) * 100)
        }

        # Type-specific profiling
        if pd.api.types.is_numeric_dtype(series):
            profile.update(self._profile_numeric(series))
        elif pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            profile.update(self._profile_categorical(series))
        elif pd.api.types.is_datetime64_any_dtype(series):
            profile.update(self._profile_datetime(series))

        return profile

    def _infer_type(self, series: pd.Series) -> str:
        """Infer semantic type beyond dtype."""
        if pd.api.types.is_numeric_dtype(series):
            # Check if it's actually categorical
            if series.nunique() < 10 and series.nunique() / len(series) < 0.05:
                return 'categorical_numeric'
            # Check if it's an ID
            if series.nunique() == len(series):
                return 'identifier'
            return 'numeric'

        elif pd.api.types.is_datetime64_any_dtype(series):
            return 'datetime'

        elif pd.api.types.is_bool_dtype(series):
            return 'boolean'

        else:
            # String/object type
            if series.nunique() < 50:
                return 'categorical'

            # Check for specific patterns
            sample = series.dropna().astype(str).head(100)

            # Email pattern
            if sample.str.contains(r'@.*\.', regex=True).mean() > 0.8:
                return 'email'

            # URL pattern
            if sample.str.contains(r'https?://', regex=True).mean() > 0.8:
                return 'url'

            # Phone pattern
            if sample.str.contains(r'\d{3}[-.]?\d{3}[-.]?\d{4}', regex=True).mean() > 0.8:
                return 'phone'

            return 'text'

    def _profile_numeric(self, series: pd.Series) -> Dict[str, Any]:
        """Profile numeric column."""
        clean_series = series.dropna()

        if len(clean_series) == 0:
            return {}

        profile = {
            'mean': float(clean_series.mean()),
            'std': float(clean_series.std()),
            'min': float(clean_series.min()),
            'max': float(clean_series.max()),
            'median': float(clean_series.median()),
            'q1': float(clean_series.quantile(0.25)),
            'q3': float(clean_series.quantile(0.75)),
            'skewness': float(clean_series.skew()),
            'kurtosis': float(clean_series.kurtosis()),
            'zeros': int((clean_series == 0).sum()),
            'zeros_pct': float((clean_series == 0).mean() * 100)
        }

        # IQR and outliers
        iqr = profile['q3'] - profile['q1']
        lower_bound = profile['q1'] - 1.5 * iqr
        upper_bound = profile['q3'] + 1.5 * iqr

        outliers = ((clean_series < lower_bound) | (clean_series > upper_bound)).sum()
        profile['outliers'] = int(outliers)
        profile['outliers_pct'] = float(outliers / len(clean_series) * 100)

        # Distribution detection
        profile['distribution'] = self._detect_distribution(clean_series)

        return profile

    def _profile_categorical(self, series: pd.Series) -> Dict[str, Any]:
        """Profile categorical column."""
        clean_series = series.dropna()

        if len(clean_series) == 0:
            return {}

        value_counts = clean_series.value_counts()

        profile = {
            'top_values': value_counts.head(10).to_dict(),
            'most_frequent': str(value_counts.index[0]),
            'most_frequent_count': int(value_counts.iloc[0]),
            'most_frequent_pct': float(value_counts.iloc[0] / len(clean_series) * 100)
        }

        # String-specific stats if text
        if pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            str_series = clean_series.astype(str)
            profile['avg_length'] = float(str_series.str.len().mean())
            profile['min_length'] = int(str_series.str.len().min())
            profile['max_length'] = int(str_series.str.len().max())

        return profile

    def _profile_datetime(self, series: pd.Series) -> Dict[str, Any]:
        """Profile datetime column."""
        clean_series = series.dropna()

        if len(clean_series) == 0:
            return {}

        profile = {
            'min_date': str(clean_series.min()),
            'max_date': str(clean_series.max()),
            'range_days': (clean_series.max() - clean_series.min()).days
        }

        return profile

    def _detect_distribution(self, series: pd.Series) -> str:
        """Detect the distribution type of numeric data."""
        if len(series) < 30:
            return 'unknown'

        # Normalize data
        normalized = (series - series.mean()) / (series.std() + 1e-8)

        # Test for normal distribution
        _, p_normal = stats.normaltest(normalized)

        if p_normal > 0.05:
            return 'normal'

        # Check skewness
        skew = series.skew()

        if skew > 1:
            return 'right_skewed'
        elif skew < -1:
            return 'left_skewed'

        # Check for uniform
        _, p_uniform = stats.kstest(normalized, 'uniform')
        if p_uniform > 0.05:
            return 'uniform'

        return 'other'

    def _compute_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute correlation matrix."""
        corr_matrix = df.corr()

        # Find highly correlated pairs
        high_corr = []

        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]

                if abs(corr_val) > 0.7:
                    high_corr.append({
                        'feature_1': corr_matrix.columns[i],
                        'feature_2': corr_matrix.columns[j],
                        'correlation': float(corr_val)
                    })

        return {
            'matrix': corr_matrix.to_dict(),
            'high_correlations': high_corr
        }

    def _generate_warnings(
        self,
        df: pd.DataFrame,
        profile: Dict[str, Any]
    ) -> List[str]:
        """Generate warnings based on profile."""
        warnings = []

        # High missing percentage
        if profile['summary']['missing_cells_pct'] > 20:
            warnings.append(
                f"High missing data: {profile['summary']['missing_cells_pct']:.1f}% of cells are missing"
            )

        # High duplicate percentage
        if profile['summary']['duplicate_rows_pct'] > 10:
            warnings.append(
                f"High duplicate rate: {profile['summary']['duplicate_rows_pct']:.1f}% of rows are duplicates"
            )

        # Columns with all missing
        for col, col_profile in profile['columns'].items():
            if col_profile['missing_pct'] == 100:
                warnings.append(f"Column '{col}' has all missing values")

        # High cardinality issues
        for col, col_profile in profile['columns'].items():
            if col_profile['unique_pct'] > 95 and col_profile['type'] != 'identifier':
                warnings.append(
                    f"Column '{col}' has very high cardinality ({col_profile['unique_pct']:.1f}%)"
                )

        return warnings


def main():
    """Example usage."""
    # Create sample data
    np.random.seed(42)

    df = pd.DataFrame({
        'id': range(1000),
        'age': np.random.randint(18, 80, 1000),
        'salary': np.random.exponential(50000, 1000),
        'category': np.random.choice(['A', 'B', 'C'], 1000),
        'score': np.random.randn(1000),
        'email': [f'user{i}@example.com' for i in range(1000)],
        'date': pd.date_range('2020-01-01', periods=1000)
    })

    # Add some missing values
    df.loc[np.random.choice(df.index, 50), 'age'] = np.nan
    df.loc[np.random.choice(df.index, 100), 'salary'] = np.nan

    print("=" * 80)
    print("DataProfiler - Example")
    print("=" * 80)

    # Profile dataset
    profiler = DataProfiler()
    profile = profiler.profile(df)

    # Print summary
    print("\n[1] Dataset Summary:")
    print(f"  Rows: {profile['summary']['n_rows']}")
    print(f"  Columns: {profile['summary']['n_columns']}")
    print(f"  Missing cells: {profile['summary']['missing_cells_pct']:.2f}%")
    print(f"  Duplicate rows: {profile['summary']['duplicate_rows_pct']:.2f}%")
    print(f"  Memory: {profile['summary']['memory_size_mb']:.2f} MB")

    # Print column profiles
    print("\n[2] Column Profiles:")
    for col in ['age', 'salary', 'category']:
        col_profile = profile['columns'][col]
        print(f"\n  {col}:")
        print(f"    Type: {col_profile['type']}")
        print(f"    Missing: {col_profile['missing_pct']:.2f}%")

        if col_profile['type'] == 'numeric':
            print(f"    Mean: {col_profile['mean']:.2f}")
            print(f"    Std: {col_profile['std']:.2f}")
            print(f"    Outliers: {col_profile['outliers_pct']:.2f}%")
            print(f"    Distribution: {col_profile['distribution']}")

    # Print warnings
    if profile['warnings']:
        print("\n[3] Warnings:")
        for warning in profile['warnings']:
            print(f"  ⚠️  {warning}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
