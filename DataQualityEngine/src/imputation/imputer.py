"""Missing data imputation."""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, Union
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
import logging

logger = logging.getLogger(__name__)


class DataImputer:
    """
    Handle missing data with multiple imputation strategies.

    Supports mean/median/mode, KNN, and iterative imputation.
    """

    def __init__(
        self,
        strategy: str = 'mean',
        **kwargs
    ):
        """
        Initialize imputer.

        Args:
            strategy: Imputation strategy
                     'mean', 'median', 'mode', 'knn', 'iterative'
            **kwargs: Strategy-specific parameters
        """
        self.strategy = strategy
        self.kwargs = kwargs
        self.imputer = None
        self.fitted = False

        self.numeric_imputer = None
        self.categorical_imputer = None

        logger.info(f"Initialized DataImputer with strategy='{strategy}'")

    def fit(
        self,
        df: pd.DataFrame,
        columns: Optional[list] = None
    ) -> 'DataImputer':
        """
        Fit imputer on data.

        Args:
            df: Training data
            columns: Columns to impute (default: all with missing values)

        Returns:
            self: Fitted imputer
        """
        if columns is None:
            # Find columns with missing values
            columns = df.columns[df.isna().any()].tolist()

        logger.info(f"Fitting imputer on {len(columns)} columns")

        # Separate numeric and categorical columns
        numeric_cols = df[columns].select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df[columns].select_dtypes(exclude=[np.number]).columns.tolist()

        # Fit numeric imputer
        if numeric_cols:
            if self.strategy == 'knn':
                self.numeric_imputer = KNNImputer(
                    n_neighbors=self.kwargs.get('n_neighbors', 5)
                )
            elif self.strategy == 'iterative':
                self.numeric_imputer = IterativeImputer(
                    max_iter=self.kwargs.get('max_iter', 10),
                    random_state=self.kwargs.get('random_state', 42)
                )
            elif self.strategy in ['mean', 'median']:
                self.numeric_imputer = SimpleImputer(strategy=self.strategy)
            else:
                self.numeric_imputer = SimpleImputer(strategy='mean')

            self.numeric_imputer.fit(df[numeric_cols])
            logger.debug(f"Fitted numeric imputer on {len(numeric_cols)} columns")

        # Fit categorical imputer (always use mode)
        if categorical_cols:
            self.categorical_imputer = SimpleImputer(strategy='most_frequent')
            self.categorical_imputer.fit(df[categorical_cols])
            logger.debug(f"Fitted categorical imputer on {len(categorical_cols)} columns")

        self.fitted = True
        self.columns_to_impute = columns
        self.numeric_cols = numeric_cols
        self.categorical_cols = categorical_cols

        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Impute missing values.

        Args:
            df: Data to impute

        Returns:
            DataFrame with imputed values
        """
        if not self.fitted:
            raise ValueError("Imputer not fitted. Call fit() first.")

        logger.info(f"Imputing missing values in {len(df)} rows")

        df_imputed = df.copy()

        # Impute numeric columns
        if self.numeric_cols and self.numeric_imputer is not None:
            df_imputed[self.numeric_cols] = self.numeric_imputer.transform(
                df[self.numeric_cols]
            )

        # Impute categorical columns
        if self.categorical_cols and self.categorical_imputer is not None:
            df_imputed[self.categorical_cols] = self.categorical_imputer.transform(
                df[self.categorical_cols]
            )

        n_imputed = (df.isna().sum().sum() - df_imputed.isna().sum().sum())
        logger.info(f"Imputed {n_imputed} missing values")

        return df_imputed

    def fit_transform(self, df: pd.DataFrame, columns: Optional[list] = None) -> pd.DataFrame:
        """
        Fit and transform in one step.

        Args:
            df: Data to impute
            columns: Columns to impute

        Returns:
            DataFrame with imputed values
        """
        return self.fit(df, columns).transform(df)

    def get_statistics(self, df_before: pd.DataFrame, df_after: pd.DataFrame) -> Dict[str, Any]:
        """
        Get imputation statistics.

        Args:
            df_before: Data before imputation
            df_after: Data after imputation

        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_missing_before': df_before.isna().sum().sum(),
            'total_missing_after': df_after.isna().sum().sum(),
            'total_imputed': 0,
            'columns': {}
        }

        stats['total_imputed'] = stats['total_missing_before'] - stats['total_missing_after']

        for col in df_before.columns:
            missing_before = df_before[col].isna().sum()
            missing_after = df_after[col].isna().sum()

            if missing_before > 0:
                stats['columns'][col] = {
                    'missing_before': int(missing_before),
                    'missing_after': int(missing_after),
                    'imputed': int(missing_before - missing_after),
                    'imputed_pct': float((missing_before - missing_after) / len(df_before) * 100)
                }

        return stats


class SmartImputer:
    """
    Intelligent imputer that selects strategy based on data characteristics.
    """

    def __init__(self):
        """Initialize smart imputer."""
        self.imputers = {}
        logger.info("Initialized SmartImputer")

    def fit(self, df: pd.DataFrame) -> 'SmartImputer':
        """
        Fit imputer by analyzing each column.

        Args:
            df: Training data

        Returns:
            self: Fitted imputer
        """
        logger.info("Analyzing data to select best imputation strategies...")

        for col in df.columns:
            if df[col].isna().any():
                strategy = self._select_strategy(df[col])
                self.imputers[col] = {
                    'strategy': strategy,
                    'imputer': self._create_imputer(df, col, strategy)
                }

                logger.debug(f"Column '{col}': selected strategy '{strategy}'")

        logger.info(f"Configured imputers for {len(self.imputers)} columns")
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Impute missing values using selected strategies.

        Args:
            df: Data to impute

        Returns:
            DataFrame with imputed values
        """
        df_imputed = df.copy()

        for col, config in self.imputers.items():
            if col in df.columns and df[col].isna().any():
                strategy = config['strategy']
                imputer = config['imputer']

                if strategy == 'drop':
                    # Don't impute, just mark for later
                    continue
                elif strategy in ['forward_fill', 'backward_fill']:
                    df_imputed[col] = df[col].fillna(method='ffill' if strategy == 'forward_fill' else 'bfill')
                else:
                    df_imputed[col] = imputer

        return df_imputed

    def _select_strategy(self, series: pd.Series) -> str:
        """
        Select best imputation strategy for a column.

        Args:
            series: Column to analyze

        Returns:
            Strategy name
        """
        missing_pct = series.isna().sum() / len(series)

        # If too many missing, consider dropping
        if missing_pct > 0.5:
            return 'drop'

        # Numeric columns
        if pd.api.types.is_numeric_dtype(series):
            # Check skewness
            skewness = series.dropna().skew()

            if abs(skewness) > 1:
                # Highly skewed - use median
                return 'median'
            else:
                # Normal-ish - use mean
                return 'mean'

        # Categorical columns
        else:
            # Use mode (most frequent)
            return 'mode'

    def _create_imputer(self, df: pd.DataFrame, col: str, strategy: str) -> Any:
        """
        Create imputer value based on strategy.

        Args:
            df: Data
            col: Column name
            strategy: Strategy name

        Returns:
            Imputed value
        """
        if strategy == 'mean':
            return df[col].mean()
        elif strategy == 'median':
            return df[col].median()
        elif strategy == 'mode':
            return df[col].mode()[0] if len(df[col].mode()) > 0 else None
        elif strategy in ['drop', 'forward_fill', 'backward_fill']:
            return None
        else:
            return df[col].mean()  # Default


def main():
    """Example usage."""
    np.random.seed(42)

    # Generate data with missing values
    n = 1000

    df = pd.DataFrame({
        'age': np.random.normal(40, 10, n),
        'income': np.random.lognormal(10, 1, n),
        'score': np.random.randn(n) * 10 + 50,
        'category': np.random.choice(['A', 'B', 'C', None], n),
        'region': np.random.choice(['North', 'South', 'East', 'West'], n)
    })

    # Introduce missing values
    missing_indices = np.random.choice(n, size=int(n * 0.1), replace=False)
    df.loc[missing_indices[:50], 'age'] = np.nan
    df.loc[missing_indices[50:100], 'income'] = np.nan
    df.loc[missing_indices[100:150], 'score'] = np.nan

    print("=" * 80)
    print("Data Imputer - Example")
    print("=" * 80)

    print(f"\nDataset: {len(df)} rows, {len(df.columns)} columns")
    print(f"\nMissing values by column:")
    for col in df.columns:
        missing = df[col].isna().sum()
        if missing > 0:
            pct = missing / len(df) * 100
            print(f"  {col:12s}: {missing:4d} ({pct:5.2f}%)")

    # Test 1: Mean imputation
    print("\n[1] Testing mean imputation...")

    imputer_mean = DataImputer(strategy='mean')
    df_mean = imputer_mean.fit_transform(df)

    stats_mean = imputer_mean.get_statistics(df, df_mean)
    print(f"  Total imputed: {stats_mean['total_imputed']}")
    print(f"  Remaining missing: {stats_mean['total_missing_after']}")

    # Test 2: Median imputation
    print("\n[2] Testing median imputation...")

    imputer_median = DataImputer(strategy='median')
    df_median = imputer_median.fit_transform(df)

    stats_median = imputer_median.get_statistics(df, df_median)
    print(f"  Total imputed: {stats_median['total_imputed']}")

    # Test 3: KNN imputation
    print("\n[3] Testing KNN imputation...")

    imputer_knn = DataImputer(strategy='knn', n_neighbors=5)
    df_knn = imputer_knn.fit_transform(df)

    stats_knn = imputer_knn.get_statistics(df, df_knn)
    print(f"  Total imputed: {stats_knn['total_imputed']}")

    # Test 4: Iterative imputation
    print("\n[4] Testing iterative imputation...")

    imputer_iterative = DataImputer(strategy='iterative', max_iter=10)
    df_iterative = imputer_iterative.fit_transform(df)

    stats_iterative = imputer_iterative.get_statistics(df, df_iterative)
    print(f"  Total imputed: {stats_iterative['total_imputed']}")

    # Compare imputed values for 'age' column
    print("\n[5] Comparing imputed values for 'age' column:")
    print(f"  Original mean: {df['age'].mean():.2f}")
    print(f"  Mean strategy: {df_mean['age'].mean():.2f}")
    print(f"  Median strategy: {df_median['age'].mean():.2f}")
    print(f"  KNN strategy: {df_knn['age'].mean():.2f}")
    print(f"  Iterative strategy: {df_iterative['age'].mean():.2f}")

    # Test 5: Smart imputation
    print("\n[6] Testing smart imputation...")

    smart_imputer = SmartImputer()
    smart_imputer.fit(df)

    print(f"  Selected strategies:")
    for col, config in smart_imputer.imputers.items():
        print(f"    {col:12s}: {config['strategy']}")

    df_smart = smart_imputer.transform(df)
    print(f"  Remaining missing: {df_smart.isna().sum().sum()}")

    # Show sample of imputed values
    print("\n[7] Sample of imputed values (first 5 originally missing):")
    sample_idx = df['age'].isna()
    if sample_idx.any():
        sample_indices = df[sample_idx].head(5).index

        print("\n  Index | Original | Mean    | Median  | KNN     | Iterative")
        print("  " + "-" * 65)
        for idx in sample_indices:
            print(f"  {idx:5d} | {str(df.loc[idx, 'age']):8s} | "
                  f"{df_mean.loc[idx, 'age']:7.2f} | "
                  f"{df_median.loc[idx, 'age']:7.2f} | "
                  f"{df_knn.loc[idx, 'age']:7.2f} | "
                  f"{df_iterative.loc[idx, 'age']:7.2f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
