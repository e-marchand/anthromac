"""FastAPI application for TimeSeriesForecaster."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.forecaster import TimeSeriesForecaster

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TimeSeriesForecaster API",
    description="Production-ready time series forecasting system",
    version="1.0.0"
)

# Global forecaster instance
forecaster: Optional[TimeSeriesForecaster] = None


class TrainRequest(BaseModel):
    """Request schema for training."""
    data: List[float] = Field(..., description="Historical time series data")
    frequency: str = Field(default='D', description="Time series frequency (D, W, M, etc.)")
    horizon: int = Field(default=30, ge=1, le=365, description="Default forecast horizon")
    models: Optional[List[str]] = Field(default=['prophet', 'xgboost'], description="Models to train")
    auto_select: bool = Field(default=True, description="Auto-select best model")
    ensemble: bool = Field(default=False, description="Use ensemble of models")
    validation_split: float = Field(default=0.2, ge=0.1, le=0.4, description="Validation split ratio")


class PredictionRequest(BaseModel):
    """Request schema for predictions."""
    data: List[float] = Field(..., description="Historical time series data")
    steps: int = Field(default=30, ge=1, le=365, description="Number of steps to forecast")
    confidence: float = Field(default=0.95, ge=0.5, le=0.99, description="Confidence level for intervals")
    models: Optional[List[str]] = Field(default=None, description="Specific models to use")


class PredictionResponse(BaseModel):
    """Response schema for predictions."""
    predictions: List[float]
    lower_bound: Optional[List[float]] = None
    upper_bound: Optional[List[float]] = None
    model_used: str
    metadata: Dict[str, Any] = {}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "TimeSeriesForecaster API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Generate time series predictions.

    Args:
        request: Prediction request with historical data and parameters

    Returns:
        Predictions with confidence intervals
    """
    global forecaster

    try:
        logger.info(f"Prediction request: {len(request.data)} data points, {request.steps} steps")

        # Check if forecaster is trained
        if forecaster is None or not forecaster.fitted_models:
            # Train a quick forecaster if not available
            logger.warning("No trained forecaster available, training a quick model")
            data = pd.Series(request.data)
            forecaster = TimeSeriesForecaster(
                models=request.models or ['prophet', 'xgboost'],
                auto_select=True
            )
            forecaster.fit(data, validation_split=0.2)

        # Generate predictions with intervals
        intervals = forecaster.predict_interval(
            steps=request.steps,
            confidence=request.confidence
        )

        # Determine which model was used
        model_used = forecaster.best_model_ or list(forecaster.fitted_models.keys())[0]

        return PredictionResponse(
            predictions=intervals['predictions'].tolist(),
            lower_bound=intervals['lower'].tolist(),
            upper_bound=intervals['upper'].tolist(),
            model_used=model_used,
            metadata={
                "input_length": len(request.data),
                "forecast_horizon": request.steps,
                "confidence_level": request.confidence,
                "models_available": list(forecaster.fitted_models.keys())
            }
        )

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def list_models():
    """List available forecasting models."""
    global forecaster

    available_models = {
        "statistical": [
            {"name": "sarima", "description": "Seasonal ARIMA model", "type": "statistical"},
            {"name": "prophet", "description": "Facebook Prophet", "type": "statistical"}
        ],
        "machine_learning": [
            {"name": "xgboost", "description": "XGBoost with feature engineering", "type": "ml"},
            {"name": "lightgbm", "description": "LightGBM gradient boosting", "type": "ml"}
        ],
        "deep_learning": [
            {"name": "lstm", "description": "Long Short-Term Memory network", "type": "dl"}
        ]
    }

    response = {"available_models": available_models}

    # If forecaster is trained, add info about trained models
    if forecaster and forecaster.fitted_models:
        summary_df = forecaster.get_models_summary()
        response["trained_models"] = summary_df.to_dict('records') if not summary_df.empty else []
        response["best_model"] = forecaster.best_model_

    return response


@app.post("/train")
async def train_model(request: TrainRequest):
    """
    Train a new forecasting model.

    Args:
        request: Training configuration and data

    Returns:
        Training status and model summary
    """
    global forecaster

    try:
        logger.info(f"Training request: {len(request.data)} data points, models={request.models}")

        # Convert data to pandas Series
        data = pd.Series(request.data)

        # Initialize forecaster
        forecaster = TimeSeriesForecaster(
            frequency=request.frequency,
            horizon=request.horizon,
            ensemble=request.ensemble,
            models=request.models,
            auto_select=request.auto_select
        )

        # Train the forecaster
        forecaster.fit(data, validation_split=request.validation_split)

        # Get model summary
        summary_df = forecaster.get_models_summary()
        models_summary = summary_df.to_dict('records') if not summary_df.empty else []

        return {
            "status": "success",
            "message": "Training completed successfully",
            "models_trained": len(forecaster.fitted_models),
            "best_model": forecaster.best_model_,
            "models_summary": models_summary,
            "training_data_length": len(request.data)
        }

    except Exception as e:
        logger.error(f"Training error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate")
async def evaluate_model(data: Dict[str, Any]):
    """
    Evaluate forecasting performance.

    Args:
        data: Dictionary with 'y_true' and optional 'y_pred' arrays

    Returns:
        Evaluation metrics
    """
    global forecaster

    try:
        if forecaster is None or not forecaster.fitted_models:
            raise HTTPException(
                status_code=400,
                detail="No trained forecaster available. Please train a model first."
            )

        y_true = np.array(data.get('y_true', []))
        y_pred = np.array(data.get('y_pred')) if 'y_pred' in data else None

        if len(y_true) == 0:
            raise HTTPException(status_code=400, detail="y_true is required and cannot be empty")

        # Evaluate
        metrics = forecaster.evaluate(y_true, y_pred)

        return {
            "status": "success",
            "metrics": metrics,
            "model_used": forecaster.best_model_ or list(forecaster.fitted_models.keys())[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
