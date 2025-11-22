"""Main forecaster class for TimeSeriesForecaster."""

import numpy as np
import pandas as pd
from typing import List, Optional, Union, Dict, Any
import logging
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings

warnings.filterwarnings('ignore')

# Import our models
from .statistical import SARIMAModel, ProphetModel
from .ml_models import XGBoostForecaster, LightGBMForecaster
from .dl_models import LSTMForecaster

logger = logging.getLogger(__name__)


class TimeSeriesForecaster:
    """
    Advanced time series forecasting system combining multiple models.

    Supports statistical (SARIMA, Prophet), ML (XGBoost, LightGBM),
    and DL (LSTM) models with automatic model selection and ensembling.
    """

    def __init__(
        self,
        frequency: str = 'D',
        horizon: int = 30,
        ensemble: bool = False,
        models: Optional[List[str]] = None,
        auto_select: bool = False,
        **kwargs
    ):
        """
        Initialize the forecaster.

        Args:
            frequency: Time series frequency ('D', 'W', 'M', etc.)
            horizon: Default forecast horizon
            ensemble: Use ensemble of models
            models: List of models to use
            auto_select: Automatically select best model
            **kwargs: Additional configuration
        """
        self.frequency = frequency
        self.horizon = horizon
        self.ensemble = ensemble
        self.auto_select = auto_select
        self.models = models or ['prophet', 'xgboost']

        # Model instances
        self.fitted_models = {}
        self.best_model_ = None
        self.best_score_ = None
        self.training_data = None

        logger.info(f"Initialized TimeSeriesForecaster with models: {self.models}")

    def _initialize_model(self, model_name: str, **kwargs):
        """
        Initialize a specific model.

        Args:
            model_name: Name of the model
            **kwargs: Model-specific parameters

        Returns:
            Initialized model instance
        """
        if model_name == 'sarima':
            return SARIMAModel(**kwargs)
        elif model_name == 'prophet':
            return ProphetModel(**kwargs)
        elif model_name == 'xgboost':
            return XGBoostForecaster(**kwargs)
        elif model_name == 'lightgbm':
            return LightGBMForecaster(**kwargs)
        elif model_name == 'lstm':
            return LSTMForecaster(**kwargs)
        else:
            raise ValueError(f"Unknown model: {model_name}")

    def fit(
        self,
        y: Union[pd.Series, np.ndarray],
        X: Optional[pd.DataFrame] = None,
        validation_split: float = 0.2,
        **kwargs
    ) -> 'TimeSeriesForecaster':
        """
        Train the forecasting model(s).

        Args:
            y: Target time series
            X: Optional exogenous variables
            validation_split: Validation set size
            **kwargs: Additional fitting parameters

        Returns:
            self: Fitted forecaster
        """
        logger.info(f"Training forecaster on {len(y)} observations")

        # Convert to pandas Series if needed
        if isinstance(y, np.ndarray):
            if isinstance(y, np.ndarray) and len(y.shape) == 1:
                # Create date index
                dates = pd.date_range('2020-01-01', periods=len(y), freq=self.frequency)
                y = pd.Series(y, index=dates)
            else:
                y = pd.Series(y)

        self.training_data = y

        # Split train/validation
        split_idx = int(len(y) * (1 - validation_split))
        train_data = y.iloc[:split_idx]
        val_data = y.iloc[split_idx:]

        # Train each model
        for model_name in self.models:
            try:
                logger.info(f"Training {model_name}...")

                model = self._initialize_model(model_name)
                model.fit(train_data)

                # Evaluate on validation set
                val_pred = model.predict(steps=len(val_data))

                # Calculate score (negative MSE for minimization)
                if len(val_pred) == len(val_data):
                    score = -mean_squared_error(val_data, val_pred)
                else:
                    score = float('-inf')

                self.fitted_models[model_name] = {
                    'model': model,
                    'score': score
                }

                logger.info(f"{model_name} - Val RMSE: {np.sqrt(-score):.2f}")

            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
                continue

        # Select best model if auto_select
        if self.auto_select and self.fitted_models:
            best_name = max(self.fitted_models, key=lambda k: self.fitted_models[k]['score'])
            self.best_model_ = best_name
            self.best_score_ = self.fitted_models[best_name]['score']
            logger.info(f"Best model: {best_name} (RMSE: {np.sqrt(-self.best_score_):.2f})")

        logger.info("Training completed")
        return self

    def predict(
        self,
        steps: Optional[int] = None,
        model_name: Optional[str] = None,
        **kwargs
    ) -> np.ndarray:
        """
        Generate forecasts.

        Args:
            steps: Number of steps to forecast
            model_name: Specific model to use (uses best/ensemble if None)
            **kwargs: Additional prediction parameters

        Returns:
            Array of predictions
        """
        if not self.fitted_models:
            raise ValueError("No models have been fitted")

        if steps is None:
            steps = self.horizon

        logger.info(f"Generating {steps}-step forecast")

        # Use specific model
        if model_name is not None:
            if model_name not in self.fitted_models:
                raise ValueError(f"Model {model_name} not fitted")

            model = self.fitted_models[model_name]['model']

            # Handle different model interfaces
            if hasattr(model, 'predict'):
                if isinstance(model, (SARIMAModel,)):
                    predictions = model.predict(steps=steps)
                elif isinstance(model, (ProphetModel,)):
                    predictions = model.predict(steps=steps, freq=self.frequency)
                else:  # ML/DL models
                    predictions = model.predict(self.training_data, steps=steps)

            return predictions

        # Use ensemble
        if self.ensemble and len(self.fitted_models) > 1:
            all_predictions = []

            for name, model_dict in self.fitted_models.items():
                model = model_dict['model']

                try:
                    if isinstance(model, (SARIMAModel,)):
                        pred = model.predict(steps=steps)
                    elif isinstance(model, (ProphetModel,)):
                        pred = model.predict(steps=steps, freq=self.frequency)
                    else:
                        pred = model.predict(self.training_data, steps=steps)

                    all_predictions.append(pred)
                except Exception as e:
                    logger.warning(f"Error predicting with {name}: {e}")

            # Average predictions
            if all_predictions:
                predictions = np.mean(all_predictions, axis=0)
                return predictions

        # Use best model
        if self.best_model_ is not None:
            return self.predict(steps=steps, model_name=self.best_model_)

        # Fallback to first model
        first_model_name = list(self.fitted_models.keys())[0]
        return self.predict(steps=steps, model_name=first_model_name)

    def predict_interval(
        self,
        steps: Optional[int] = None,
        confidence: float = 0.95,
        model_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, np.ndarray]:
        """
        Generate forecasts with prediction intervals.

        Args:
            steps: Number of steps to forecast
            confidence: Confidence level for intervals
            model_name: Specific model to use
            **kwargs: Additional parameters

        Returns:
            Dictionary with predictions, lower and upper bounds
        """
        if steps is None:
            steps = self.horizon

        # Use specified model or best model
        if model_name is None:
            model_name = self.best_model_ or list(self.fitted_models.keys())[0]

        if model_name not in self.fitted_models:
            raise ValueError(f"Model {model_name} not fitted")

        model = self.fitted_models[model_name]['model']

        # Get predictions with intervals (only for statistical models)
        if isinstance(model, (SARIMAModel, ProphetModel)):
            if isinstance(model, SARIMAModel):
                predictions, lower, upper = model.predict(
                    steps=steps,
                    return_conf_int=True,
                    alpha=1 - confidence
                )
            else:  # Prophet
                predictions, lower, upper = model.predict(
                    steps=steps,
                    freq=self.frequency,
                    return_conf_int=True
                )

            return {
                'predictions': predictions,
                'lower': lower,
                'upper': upper
            }

        # For ML/DL models, use simple standard deviation-based intervals
        predictions = self.predict(steps=steps, model_name=model_name)

        # Estimate std from training residuals (simple approach)
        if len(self.training_data) > 10:
            std = np.std(np.diff(self.training_data.values))
            margin = 1.96 * std  # 95% confidence

            lower = predictions - margin
            upper = predictions + margin
        else:
            lower = predictions * 0.9
            upper = predictions * 1.1

        return {
            'predictions': predictions,
            'lower': lower,
            'upper': upper
        }

    def evaluate(
        self,
        y_true: Union[pd.Series, np.ndarray],
        y_pred: Optional[np.ndarray] = None,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Evaluate forecast performance.

        Args:
            y_true: True values
            y_pred: Predicted values (generates if None)
            metrics: List of metrics to compute

        Returns:
            Dictionary of metric values
        """
        if metrics is None:
            metrics = ['mae', 'rmse', 'mape', 'mse']

        if y_pred is None:
            y_pred = self.predict(steps=len(y_true))

        results = {}

        if isinstance(y_true, pd.Series):
            y_true = y_true.values

        # Ensure same length
        min_len = min(len(y_true), len(y_pred))
        y_true = y_true[:min_len]
        y_pred = y_pred[:min_len]

        # Calculate metrics
        if 'mae' in metrics:
            results['mae'] = mean_absolute_error(y_true, y_pred)

        if 'mse' in metrics:
            results['mse'] = mean_squared_error(y_true, y_pred)

        if 'rmse' in metrics:
            results['rmse'] = np.sqrt(mean_squared_error(y_true, y_pred))

        if 'mape' in metrics:
            # Avoid division by zero
            mask = y_true != 0
            if mask.any():
                results['mape'] = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
            else:
                results['mape'] = float('inf')

        return results

    def get_models_summary(self) -> pd.DataFrame:
        """
        Get summary of all fitted models.

        Returns:
            DataFrame with model names and scores
        """
        if not self.fitted_models:
            return pd.DataFrame()

        data = []
        for name, model_dict in self.fitted_models.items():
            data.append({
                'model': name,
                'val_rmse': np.sqrt(-model_dict['score']),
                'is_best': name == self.best_model_
            })

        return pd.DataFrame(data).sort_values('val_rmse')


def main():
    """Example usage of TimeSeriesForecaster."""
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=365, freq='D')

    trend = np.linspace(100, 150, 365)
    seasonality = 10 * np.sin(2 * np.pi * np.arange(365) / 7)
    noise = np.random.randn(365) * 3

    data = pd.Series(trend + seasonality + noise, index=dates)

    # Split train/test
    train = data[:-30]
    test = data[-30:]

    print("=" * 80)
    print("TimeSeriesForecaster - Complete Example")
    print("=" * 80)

    # Initialize forecaster with multiple models
    forecaster = TimeSeriesForecaster(
        frequency='D',
        horizon=30,
        models=['prophet', 'xgboost', 'lstm'],
        auto_select=True,
        ensemble=False
    )

    # Train
    print("\n[1] Training models...")
    forecaster.fit(train, validation_split=0.2)

    # Show models summary
    print("\n[2] Models Summary:")
    print(forecaster.get_models_summary())

    # Generate predictions
    print("\n[3] Generating predictions...")
    predictions = forecaster.predict(steps=30)

    # Get prediction intervals
    intervals = forecaster.predict_interval(steps=30, confidence=0.95)

    # Evaluate
    print("\n[4] Evaluation on test set:")
    metrics = forecaster.evaluate(test, predictions)
    for metric, value in metrics.items():
        print(f"  {metric.upper()}: {value:.2f}")

    # Show predictions
    print("\n[5] Sample predictions:")
    print(f"  First 5 predictions: {predictions[:5]}")
    print(f"  Last 5 predictions: {predictions[-5:]}")

    print("\n" + "=" * 80)
    print("Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
