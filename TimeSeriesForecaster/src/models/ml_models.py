"""Machine Learning models for time series forecasting."""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, Union, List
import logging
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb

logger = logging.getLogger(__name__)


class XGBoostForecaster:
    """
    XGBoost model for time series forecasting with engineered features.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        lags: Optional[List[int]] = None,
        rolling_windows: Optional[List[int]] = None,
        **kwargs
    ):
        """
        Initialize XGBoost forecaster.

        Args:
            n_estimators: Number of boosting rounds
            max_depth: Maximum tree depth
            learning_rate: Learning rate
            lags: List of lag features to create
            rolling_windows: List of rolling window sizes
            **kwargs: Additional XGBoost parameters
        """
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate

        # Feature engineering parameters
        self.lags = lags or [1, 7, 14, 30]
        self.rolling_windows = rolling_windows or [7, 14, 30]

        # Model and preprocessing
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []

        logger.info(f"Initialized XGBoost with lags={self.lags}, windows={self.rolling_windows}")

    def _create_features(
        self,
        data: pd.Series,
        is_training: bool = True
    ) -> pd.DataFrame:
        """
        Create lag and rolling window features.

        Args:
            data: Time series data
            is_training: Whether this is for training (affects feature names)

        Returns:
            DataFrame with engineered features
        """
        df = pd.DataFrame({'value': data.values}, index=data.index)

        # Lag features
        for lag in self.lags:
            df[f'lag_{lag}'] = df['value'].shift(lag)

        # Rolling statistics
        for window in self.rolling_windows:
            df[f'rolling_mean_{window}'] = df['value'].rolling(window).mean()
            df[f'rolling_std_{window}'] = df['value'].rolling(window).std()
            df[f'rolling_min_{window}'] = df['value'].rolling(window).min()
            df[f'rolling_max_{window}'] = df['value'].rolling(window).max()

        # Time-based features
        if isinstance(data.index, pd.DatetimeIndex):
            df['day_of_week'] = data.index.dayofweek
            df['day_of_month'] = data.index.day
            df['month'] = data.index.month
            df['quarter'] = data.index.quarter
            df['is_weekend'] = (data.index.dayofweek >= 5).astype(int)

        # Drop the original value column and NaN rows
        df = df.drop('value', axis=1)
        df = df.dropna()

        if is_training:
            self.feature_names = df.columns.tolist()

        return df

    def fit(
        self,
        data: Union[pd.Series, np.ndarray],
        verbose: bool = False
    ) -> 'XGBoostForecaster':
        """
        Fit the XGBoost model.

        Args:
            data: Time series training data
            verbose: Whether to print training progress

        Returns:
            self: Fitted model
        """
        logger.info(f"Fitting XGBoost on {len(data)} observations")

        if isinstance(data, np.ndarray):
            data = pd.Series(data)

        # Create features
        X = self._create_features(data, is_training=True)

        # Align target with features (shift by 1 to predict next value)
        y = data.loc[X.index].shift(-1).dropna()
        X = X.loc[y.index]

        logger.info(f"Created {X.shape[1]} features from {len(X)} samples")

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train model
        self.model = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=42
        )

        self.model.fit(
            X_scaled,
            y,
            verbose=verbose
        )

        logger.info("XGBoost model fitted successfully")

        return self

    def predict(
        self,
        data: Union[pd.Series, np.ndarray],
        steps: int = 1
    ) -> np.ndarray:
        """
        Generate forecasts.

        Args:
            data: Historical data to use for features
            steps: Number of steps ahead to forecast

        Returns:
            Array of predictions
        """
        if self.model is None:
            raise ValueError("Model must be fitted before prediction")

        logger.info(f"Generating {steps}-step forecast")

        if isinstance(data, np.ndarray):
            data = pd.Series(data)

        predictions = []
        current_data = data.copy()

        for step in range(steps):
            # Create features from current data
            X = self._create_features(current_data, is_training=False)

            # Use last row for prediction
            X_last = X.iloc[[-1]][self.feature_names]

            # Scale
            X_scaled = self.scaler.transform(X_last)

            # Predict
            pred = self.model.predict(X_scaled)[0]
            predictions.append(pred)

            # Update data with prediction for next iteration
            new_index = current_data.index[-1] + (current_data.index[-1] - current_data.index[-2])
            current_data = pd.concat([
                current_data,
                pd.Series([pred], index=[new_index])
            ])

        return np.array(predictions)

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importances.

        Returns:
            DataFrame with feature names and importances
        """
        if self.model is None:
            raise ValueError("Model must be fitted first")

        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        return importance


class LightGBMForecaster:
    """
    LightGBM model for time series forecasting.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = -1,
        learning_rate: float = 0.1,
        lags: Optional[List[int]] = None,
        **kwargs
    ):
        """
        Initialize LightGBM forecaster.

        Args:
            n_estimators: Number of boosting rounds
            max_depth: Maximum tree depth (-1 for no limit)
            learning_rate: Learning rate
            lags: List of lag features to create
            **kwargs: Additional LightGBM parameters
        """
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.lags = lags or [1, 7, 14, 30]

        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []

        logger.info("Initialized LightGBM forecaster")

    def _create_features(self, data: pd.Series) -> pd.DataFrame:
        """Create lag features."""
        df = pd.DataFrame({'value': data.values}, index=data.index)

        for lag in self.lags:
            df[f'lag_{lag}'] = df['value'].shift(lag)

        # Time features
        if isinstance(data.index, pd.DatetimeIndex):
            df['day_of_week'] = data.index.dayofweek
            df['month'] = data.index.month

        df = df.drop('value', axis=1).dropna()
        return df

    def fit(
        self,
        data: Union[pd.Series, np.ndarray],
        verbose: int = -1
    ) -> 'LightGBMForecaster':
        """
        Fit the LightGBM model.

        Args:
            data: Time series training data
            verbose: Verbosity level

        Returns:
            self: Fitted model
        """
        logger.info(f"Fitting LightGBM on {len(data)} observations")

        if isinstance(data, np.ndarray):
            data = pd.Series(data)

        # Create features
        X = self._create_features(data)
        self.feature_names = X.columns.tolist()

        # Target (next value)
        y = data.loc[X.index].shift(-1).dropna()
        X = X.loc[y.index]

        # Scale
        X_scaled = self.scaler.fit_transform(X)

        # Train
        self.model = lgb.LGBMRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=42,
            verbose=verbose
        )

        self.model.fit(X_scaled, y)

        logger.info("LightGBM model fitted successfully")

        return self

    def predict(
        self,
        data: Union[pd.Series, np.ndarray],
        steps: int = 1
    ) -> np.ndarray:
        """Generate forecasts."""
        if self.model is None:
            raise ValueError("Model must be fitted before prediction")

        if isinstance(data, np.ndarray):
            data = pd.Series(data)

        predictions = []
        current_data = data.copy()

        for step in range(steps):
            X = self._create_features(current_data)
            X_last = X.iloc[[-1]][self.feature_names]
            X_scaled = self.scaler.transform(X_last)

            pred = self.model.predict(X_scaled)[0]
            predictions.append(pred)

            # Update data
            new_index = current_data.index[-1] + (current_data.index[-1] - current_data.index[-2])
            current_data = pd.concat([
                current_data,
                pd.Series([pred], index=[new_index])
            ])

        return np.array(predictions)


def main():
    """Example usage of ML models."""
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=365, freq='D')

    trend = np.linspace(100, 150, 365)
    seasonality = 10 * np.sin(2 * np.pi * np.arange(365) / 7)
    noise = np.random.randn(365) * 3

    data = pd.Series(trend + seasonality + noise, index=dates)

    # Split
    train = data[:-30]
    test = data[-30:]

    print("=" * 60)
    print("XGBoost Forecaster")
    print("=" * 60)

    # Fit XGBoost
    xgb_model = XGBoostForecaster(
        n_estimators=100,
        max_depth=6,
        lags=[1, 7, 14],
        rolling_windows=[7, 14]
    )
    xgb_model.fit(train)

    # Predict
    predictions = xgb_model.predict(train, steps=30)

    # Evaluate
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    mae = mean_absolute_error(test, predictions)
    rmse = np.sqrt(mean_squared_error(test, predictions))

    print(f"MAE: {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")

    # Feature importance
    print("\nTop 10 Features:")
    print(xgb_model.get_feature_importance().head(10))

    print("\n" + "=" * 60)
    print("LightGBM Forecaster")
    print("=" * 60)

    # Fit LightGBM
    lgb_model = LightGBMForecaster(
        n_estimators=100,
        lags=[1, 7, 14, 30]
    )
    lgb_model.fit(train)

    # Predict
    predictions_lgb = lgb_model.predict(train, steps=30)

    # Evaluate
    mae_lgb = mean_absolute_error(test, predictions_lgb)
    rmse_lgb = np.sqrt(mean_squared_error(test, predictions_lgb))

    print(f"MAE: {mae_lgb:.2f}")
    print(f"RMSE: {rmse_lgb:.2f}")

    print("\nBoth ML models trained and evaluated successfully!")


if __name__ == "__main__":
    main()
