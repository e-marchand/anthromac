"""Data loading utilities for time series data."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TimeSeriesLoader:
    """
    Load and prepare time series data from various sources.

    Supports CSV, Excel, Parquet, and other common formats.
    """

    def __init__(self, data_dir: Union[str, Path] = "data/raw"):
        """
        Initialize the data loader.

        Args:
            data_dir: Directory containing data files
        """
        self.data_dir = Path(data_dir)
        logger.info(f"Initialized TimeSeriesLoader with data_dir: {self.data_dir}")

    def load_csv(
        self,
        filename: str,
        date_column: str = 'date',
        target_column: str = 'value',
        parse_dates: bool = True,
        **kwargs
    ) -> pd.DataFrame:
        """
        Load time series data from CSV file.

        Args:
            filename: Name of the CSV file
            date_column: Name of the date column
            target_column: Name of the target column
            parse_dates: Whether to parse dates
            **kwargs: Additional pandas read_csv parameters

        Returns:
            DataFrame with time series data
        """
        filepath = self.data_dir / filename
        logger.info(f"Loading CSV from {filepath}")

        df = pd.read_csv(
            filepath,
            parse_dates=[date_column] if parse_dates else None,
            **kwargs
        )

        if date_column in df.columns:
            df = df.set_index(date_column)
            df = df.sort_index()

        logger.info(f"Loaded {len(df)} rows from {filename}")
        return df

    def load_excel(
        self,
        filename: str,
        sheet_name: Union[str, int] = 0,
        **kwargs
    ) -> pd.DataFrame:
        """
        Load time series data from Excel file.

        Args:
            filename: Name of the Excel file
            sheet_name: Sheet name or index
            **kwargs: Additional pandas read_excel parameters

        Returns:
            DataFrame with time series data
        """
        filepath = self.data_dir / filename
        logger.info(f"Loading Excel from {filepath}")

        df = pd.read_excel(filepath, sheet_name=sheet_name, **kwargs)
        logger.info(f"Loaded {len(df)} rows from {filename}")
        return df

    def load_parquet(self, filename: str, **kwargs) -> pd.DataFrame:
        """
        Load time series data from Parquet file.

        Args:
            filename: Name of the Parquet file
            **kwargs: Additional pandas read_parquet parameters

        Returns:
            DataFrame with time series data
        """
        filepath = self.data_dir / filename
        logger.info(f"Loading Parquet from {filepath}")

        df = pd.read_parquet(filepath, **kwargs)
        logger.info(f"Loaded {len(df)} rows from {filename}")
        return df

    def generate_sample_data(
        self,
        n_periods: int = 365,
        frequency: str = 'D',
        trend: bool = True,
        seasonality: bool = True,
        noise: float = 1.0,
        seed: Optional[int] = None
    ) -> pd.Series:
        """
        Generate synthetic time series data for testing.

        Args:
            n_periods: Number of time periods
            frequency: Frequency string ('D', 'W', 'M', etc.)
            trend: Include linear trend
            seasonality: Include seasonal component
            noise: Amount of random noise
            seed: Random seed for reproducibility

        Returns:
            Generated time series
        """
        if seed is not None:
            np.random.seed(seed)

        logger.info(f"Generating sample data: {n_periods} periods, frequency={frequency}")

        # Create date range
        dates = pd.date_range('2020-01-01', periods=n_periods, freq=frequency)

        # Initialize with base value
        values = np.ones(n_periods) * 100

        # Add trend
        if trend:
            values += np.linspace(0, 50, n_periods)

        # Add seasonality
        if seasonality:
            if frequency == 'D':
                # Weekly seasonality
                values += 10 * np.sin(2 * np.pi * np.arange(n_periods) / 7)
                # Yearly seasonality
                values += 20 * np.sin(2 * np.pi * np.arange(n_periods) / 365.25)
            elif frequency == 'W':
                # Yearly seasonality
                values += 20 * np.sin(2 * np.pi * np.arange(n_periods) / 52)
            elif frequency == 'M':
                # Yearly seasonality
                values += 20 * np.sin(2 * np.pi * np.arange(n_periods) / 12)

        # Add noise
        values += np.random.randn(n_periods) * noise

        series = pd.Series(values, index=dates, name='value')
        logger.info("Sample data generated successfully")

        return series

    def train_test_split(
        self,
        data: pd.Series,
        test_size: Union[int, float] = 0.2,
        validation_size: Union[int, float] = 0.0
    ) -> Tuple[pd.Series, ...]:
        """
        Split time series into train, validation, and test sets.

        Args:
            data: Time series data
            test_size: Size of test set (int or fraction)
            validation_size: Size of validation set (int or fraction)

        Returns:
            Tuple of (train, validation, test) or (train, test) if no validation
        """
        n = len(data)

        # Calculate split points
        if isinstance(test_size, float):
            test_size = int(n * test_size)

        if isinstance(validation_size, float):
            validation_size = int(n * validation_size)

        # Split indices
        train_end = n - test_size - validation_size
        val_end = n - test_size

        train = data.iloc[:train_end]
        test = data.iloc[val_end:]

        logger.info(f"Split data: train={len(train)}, test={len(test)}")

        if validation_size > 0:
            val = data.iloc[train_end:val_end]
            logger.info(f"Validation size: {len(val)}")
            return train, val, test
        else:
            return train, test


def main():
    """Example usage of TimeSeriesLoader."""
    loader = TimeSeriesLoader()

    # Generate sample data
    data = loader.generate_sample_data(n_periods=365, seed=42)
    print(f"Generated data shape: {data.shape}")
    print(f"First few values:\n{data.head()}")

    # Train-test split
    train, test = loader.train_test_split(data, test_size=0.2)
    print(f"\nTrain size: {len(train)}, Test size: {len(test)}")


if __name__ == "__main__":
    main()
