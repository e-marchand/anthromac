"""Statistical time series models implementation."""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, Union, Tuple
import logging
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMA
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class SARIMAModel:
    """
    SARIMA (Seasonal AutoRegressive Integrated Moving Average) model.

    Handles both seasonal and non-seasonal time series forecasting.
    """

    def __init__(
        self,
        order: Tuple[int, int, int] = (1, 1, 1),
        seasonal_order: Tuple[int, int, int, int] = (1, 1, 1, 12),
        trend: Optional[str] = 'c'
    ):
        """
        Initialize SARIMA model.

        Args:
            order: (p, d, q) order of the model
            seasonal_order: (P, D, Q, s) seasonal order
            trend: Trend parameter ('n', 'c', 't', 'ct')
        """
        self.order = order
        self.seasonal_order = seasonal_order
        self.trend = trend
        self.model = None
        self.results = None

        logger.info(f"Initialized SARIMA{order}x{seasonal_order}")

    def fit(self, data: Union[pd.Series, np.ndarray]) -> 'SARIMAModel':
        """
        Fit the SARIMA model.

        Args:
            data: Time series data

        Returns:
            self: Fitted model
        """
        logger.info(f"Fitting SARIMA model on {len(data)} observations")

        # Convert to pandas Series if needed
        if isinstance(data, np.ndarray):
            data = pd.Series(data)

        # Fit model
        self.model = SARIMAX(
            data,
            order=self.order,
            seasonal_order=self.seasonal_order,
            trend=self.trend,
            enforce_stationarity=False,
            enforce_invertibility=False
        )

        self.results = self.model.fit(disp=False)

        logger.info(f"SARIMA model fitted. AIC: {self.results.aic:.2f}")

        return self

    def predict(
        self,
        steps: int,
        return_conf_int: bool = False,
        alpha: float = 0.05
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """
        Generate forecasts.

        Args:
            steps: Number of steps ahead to forecast
            return_conf_int: Whether to return confidence intervals
            alpha: Significance level for confidence intervals

        Returns:
            Predictions or (predictions, lower_bound, upper_bound)
        """
        if self.results is None:
            raise ValueError("Model must be fitted before prediction")

        logger.info(f"Generating {steps}-step forecast")

        # Generate forecast
        forecast_result = self.results.get_forecast(steps=steps)
        predictions = forecast_result.predicted_mean.values

        if return_conf_int:
            conf_int = forecast_result.conf_int(alpha=alpha)
            lower = conf_int.iloc[:, 0].values
            upper = conf_int.iloc[:, 1].values
            return predictions, lower, upper

        return predictions

    def get_params(self) -> Dict[str, Any]:
        """Get model parameters."""
        if self.results is None:
            return {}

        return {
            'aic': self.results.aic,
            'bic': self.results.bic,
            'params': self.results.params.to_dict(),
            'order': self.order,
            'seasonal_order': self.seasonal_order
        }


class ProphetModel:
    """
    Prophet model wrapper for time series forecasting.
    """

    def __init__(
        self,
        growth: str = 'linear',
        changepoint_prior_scale: float = 0.05,
        seasonality_mode: str = 'multiplicative',
        yearly_seasonality: Union[str, bool] = 'auto',
        weekly_seasonality: Union[str, bool] = 'auto',
        daily_seasonality: Union[str, bool] = 'auto'
    ):
        """
        Initialize Prophet model.

        Args:
            growth: 'linear' or 'logistic'
            changepoint_prior_scale: Flexibility of trend changes
            seasonality_mode: 'additive' or 'multiplicative'
            yearly_seasonality: Fit yearly seasonality
            weekly_seasonality: Fit weekly seasonality
            daily_seasonality: Fit daily seasonality
        """
        try:
            from prophet import Prophet
        except ImportError:
            raise ImportError("Prophet not installed. Run: pip install prophet")

        self.growth = growth
        self.changepoint_prior_scale = changepoint_prior_scale
        self.seasonality_mode = seasonality_mode
        self.yearly_seasonality = yearly_seasonality
        self.weekly_seasonality = weekly_seasonality
        self.daily_seasonality = daily_seasonality

        self.model = Prophet(
            growth=growth,
            changepoint_prior_scale=changepoint_prior_scale,
            seasonality_mode=seasonality_mode,
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality
        )

        logger.info("Initialized Prophet model")

    def fit(
        self,
        data: pd.Series,
        **kwargs
    ) -> 'ProphetModel':
        """
        Fit the Prophet model.

        Args:
            data: Time series data with DatetimeIndex

        Returns:
            self: Fitted model
        """
        logger.info(f"Fitting Prophet model on {len(data)} observations")

        # Prepare data in Prophet format
        df = pd.DataFrame({
            'ds': data.index,
            'y': data.values
        })

        # Fit model
        self.model.fit(df, **kwargs)

        logger.info("Prophet model fitted")

        return self

    def predict(
        self,
        steps: int,
        freq: Optional[str] = None,
        return_conf_int: bool = False
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """
        Generate forecasts.

        Args:
            steps: Number of steps ahead to forecast
            freq: Frequency string (e.g., 'D', 'W', 'M')
            return_conf_int: Whether to return confidence intervals

        Returns:
            Predictions or (predictions, lower_bound, upper_bound)
        """
        logger.info(f"Generating {steps}-step forecast")

        # Create future dataframe
        future = self.model.make_future_dataframe(
            periods=steps,
            freq=freq
        )

        # Generate forecast
        forecast = self.model.predict(future)

        # Get predictions (only future values)
        predictions = forecast['yhat'].iloc[-steps:].values

        if return_conf_int:
            lower = forecast['yhat_lower'].iloc[-steps:].values
            upper = forecast['yhat_upper'].iloc[-steps:].values
            return predictions, lower, upper

        return predictions

    def plot_components(self, forecast: pd.DataFrame):
        """
        Plot forecast components.

        Args:
            forecast: Forecast dataframe from predict()
        """
        try:
            self.model.plot_components(forecast)
        except Exception as e:
            logger.error(f"Error plotting components: {e}")


def auto_arima(
    data: Union[pd.Series, np.ndarray],
    seasonal: bool = True,
    m: int = 12,
    max_p: int = 5,
    max_q: int = 5,
    max_P: int = 2,
    max_Q: int = 2,
    max_d: int = 2,
    max_D: int = 1,
    information_criterion: str = 'aic',
    **kwargs
) -> SARIMAModel:
    """
    Automatic ARIMA order selection.

    Args:
        data: Time series data
        seasonal: Whether to fit seasonal ARIMA
        m: Seasonal period
        max_p, max_q, max_P, max_Q: Maximum orders
        max_d, max_D: Maximum differences
        information_criterion: 'aic' or 'bic'

    Returns:
        Best fitted SARIMA model
    """
    try:
        from pmdarima import auto_arima as pm_auto_arima
    except ImportError:
        logger.warning("pmdarima not installed, using default order")
        model = SARIMAModel()
        model.fit(data)
        return model

    logger.info("Running auto ARIMA order selection...")

    # Run auto ARIMA
    stepwise_model = pm_auto_arima(
        data,
        seasonal=seasonal,
        m=m,
        max_p=max_p,
        max_q=max_q,
        max_P=max_P,
        max_Q=max_Q,
        max_d=max_d,
        max_D=max_D,
        information_criterion=information_criterion,
        stepwise=True,
        suppress_warnings=True,
        **kwargs
    )

    # Get best order
    order = stepwise_model.order
    seasonal_order = stepwise_model.seasonal_order

    logger.info(f"Best order found: SARIMA{order}x{seasonal_order}")

    # Fit our model with best order
    model = SARIMAModel(order=order, seasonal_order=seasonal_order)
    model.fit(data)

    return model


def main():
    """Example usage of statistical models."""
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=365, freq='D')

    # Trend + seasonality + noise
    trend = np.linspace(100, 150, 365)
    seasonality = 10 * np.sin(2 * np.pi * np.arange(365) / 7)  # Weekly
    noise = np.random.randn(365) * 3

    data = pd.Series(trend + seasonality + noise, index=dates)

    # Split train/test
    train = data[:-30]
    test = data[-30:]

    print("=" * 60)
    print("SARIMA Model")
    print("=" * 60)

    # Fit SARIMA
    sarima = SARIMAModel(order=(1, 1, 1), seasonal_order=(1, 0, 1, 7))
    sarima.fit(train)

    # Predict
    pred, lower, upper = sarima.predict(steps=30, return_conf_int=True)

    # Evaluate
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    mae = mean_absolute_error(test, pred)
    rmse = np.sqrt(mean_squared_error(test, pred))

    print(f"MAE: {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"AIC: {sarima.results.aic:.2f}")

    print("\n" + "=" * 60)
    print("Prophet Model")
    print("=" * 60)

    # Fit Prophet
    prophet = ProphetModel(
        changepoint_prior_scale=0.05,
        seasonality_mode='additive'
    )
    prophet.fit(train)

    # Predict
    pred_prophet, lower_prophet, upper_prophet = prophet.predict(
        steps=30,
        freq='D',
        return_conf_int=True
    )

    # Evaluate
    mae_prophet = mean_absolute_error(test, pred_prophet)
    rmse_prophet = np.sqrt(mean_squared_error(test, pred_prophet))

    print(f"MAE: {mae_prophet:.2f}")
    print(f"RMSE: {rmse_prophet:.2f}")

    print("\nBoth models fitted and evaluated successfully!")


if __name__ == "__main__":
    main()
