"""Tests for data loading and preprocessing."""

import pytest
import pandas as pd
import numpy as np
from src.data.loader import TimeSeriesLoader


class TestTimeSeriesLoader:
    """Test suite for TimeSeriesLoader."""

    @pytest.fixture
    def loader(self):
        """Create a TimeSeriesLoader instance."""
        return TimeSeriesLoader()

    def test_initialization(self, loader):
        """Test loader initialization."""
        assert loader is not None
        assert loader.data_dir.name == "raw"

    def test_generate_sample_data(self, loader):
        """Test sample data generation."""
        data = loader.generate_sample_data(n_periods=100, seed=42)

        assert isinstance(data, pd.Series)
        assert len(data) == 100
        assert data.name == 'value'
        assert isinstance(data.index, pd.DatetimeIndex)

    def test_generate_sample_data_with_trend(self, loader):
        """Test sample data generation with trend."""
        data = loader.generate_sample_data(
            n_periods=100,
            trend=True,
            seasonality=False,
            noise=0.0,
            seed=42
        )

        # Check that values generally increase (trend)
        assert data.iloc[-1] > data.iloc[0]

    def test_generate_sample_data_reproducibility(self, loader):
        """Test that same seed produces same data."""
        data1 = loader.generate_sample_data(n_periods=100, seed=42)
        data2 = loader.generate_sample_data(n_periods=100, seed=42)

        pd.testing.assert_series_equal(data1, data2)

    def test_train_test_split(self, loader):
        """Test train-test split."""
        data = loader.generate_sample_data(n_periods=100, seed=42)
        train, test = loader.train_test_split(data, test_size=0.2)

        assert len(train) == 80
        assert len(test) == 20
        assert train.index[-1] < test.index[0]  # No overlap

    def test_train_val_test_split(self, loader):
        """Test train-validation-test split."""
        data = loader.generate_sample_data(n_periods=100, seed=42)
        train, val, test = loader.train_test_split(
            data,
            test_size=0.2,
            validation_size=0.2
        )

        assert len(train) == 60
        assert len(val) == 20
        assert len(test) == 20

    def test_train_test_split_absolute(self, loader):
        """Test train-test split with absolute sizes."""
        data = loader.generate_sample_data(n_periods=100, seed=42)
        train, test = loader.train_test_split(data, test_size=20)

        assert len(train) == 80
        assert len(test) == 20
