"""MLOps trainer with experiment tracking and model registry."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import json
import pickle
from datetime import datetime

logger = logging.getLogger(__name__)


class MLOpsTrainer:
    """
    ML training pipeline with experiment tracking.

    Integrates model training, versioning, and tracking.
    """

    def __init__(
        self,
        experiment_name: str = "default",
        tracking_uri: str = "mlruns",
        auto_log: bool = True
    ):
        """
        Initialize trainer.

        Args:
            experiment_name: Name of the experiment
            tracking_uri: URI for experiment tracking
            auto_log: Whether to auto-log metrics
        """
        self.experiment_name = experiment_name
        self.tracking_uri = Path(tracking_uri)
        self.auto_log = auto_log

        self.model = None
        self.run_id = None
        self.metrics = {}
        self.params = {}

        # Create tracking directory
        self.tracking_uri.mkdir(parents=True, exist_ok=True)
        self.experiment_dir = self.tracking_uri / experiment_name
        self.experiment_dir.mkdir(exist_ok=True)

        logger.info(f"Initialized MLOpsTrainer: {experiment_name}")

    def start_run(self, run_name: Optional[str] = None) -> str:
        """
        Start a new training run.

        Args:
            run_name: Name of the run

        Returns:
            Run ID
        """
        if run_name is None:
            run_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.run_id = run_name
        self.run_dir = self.experiment_dir / run_name
        self.run_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.run_dir / "models").mkdir(exist_ok=True)
        (self.run_dir / "metrics").mkdir(exist_ok=True)
        (self.run_dir / "artifacts").mkdir(exist_ok=True)

        logger.info(f"Started run: {run_name}")
        return self.run_id

    def log_params(self, params: Dict[str, Any]):
        """
        Log parameters.

        Args:
            params: Parameters to log
        """
        self.params.update(params)

        if self.run_id:
            params_file = self.run_dir / "params.json"
            with open(params_file, 'w') as f:
                json.dump(self.params, f, indent=2)

        logger.info(f"Logged {len(params)} parameters")

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """
        Log metrics.

        Args:
            metrics: Metrics to log
            step: Training step
        """
        self.metrics.update(metrics)

        if self.run_id:
            metrics_file = self.run_dir / "metrics" / f"step_{step or 0}.json"
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)

        logger.info(f"Logged metrics: {metrics}")

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        model_type: str = 'xgboost',
        params: Optional[Dict[str, Any]] = None,
        run_name: Optional[str] = None
    ) -> 'MLOpsTrainer':
        """
        Train a model.

        Args:
            X_train: Training features
            y_train: Training labels
            model_type: Type of model to train
            params: Model parameters
            run_name: Name of the training run

        Returns:
            self: Trained trainer
        """
        # Start run
        self.start_run(run_name)

        # Default parameters
        if params is None:
            params = self._get_default_params(model_type)

        self.log_params({
            'model_type': model_type,
            'n_samples': len(X_train),
            'n_features': X_train.shape[1],
            **params
        })

        logger.info(f"Training {model_type} model on {len(X_train)} samples")

        # Train model
        start_time = datetime.now()

        if model_type == 'xgboost':
            self.model = self._train_xgboost(X_train, y_train, params)
        elif model_type == 'lightgbm':
            self.model = self._train_lightgbm(X_train, y_train, params)
        elif model_type == 'random_forest':
            self.model = self._train_random_forest(X_train, y_train, params)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        training_time = (datetime.now() - start_time).total_seconds()

        # Log training metrics
        self.log_metrics({
            'training_time_seconds': training_time,
            'model_type': model_type
        })

        # Evaluate on training data
        train_score = self.model.score(X_train, y_train)
        self.log_metrics({'train_score': train_score})

        logger.info(f"Training completed in {training_time:.2f}s, score: {train_score:.4f}")

        return self

    def _get_default_params(self, model_type: str) -> Dict[str, Any]:
        """Get default parameters for model type."""
        defaults = {
            'xgboost': {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1
            },
            'lightgbm': {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1
            },
            'random_forest': {
                'n_estimators': 100,
                'max_depth': 10
            }
        }

        return defaults.get(model_type, {})

    def _train_xgboost(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        params: Dict[str, Any]
    ):
        """Train XGBoost model."""
        try:
            from xgboost import XGBClassifier, XGBRegressor

            # Determine task type
            is_classification = len(np.unique(y)) < 20

            if is_classification:
                model = XGBClassifier(**params, random_state=42)
            else:
                model = XGBRegressor(**params, random_state=42)

            model.fit(X, y)
            return model

        except ImportError:
            logger.warning("XGBoost not available, using sklearn fallback")
            return self._train_random_forest(X, y, params)

    def _train_lightgbm(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        params: Dict[str, Any]
    ):
        """Train LightGBM model."""
        try:
            from lightgbm import LGBMClassifier, LGBMRegressor

            is_classification = len(np.unique(y)) < 20

            if is_classification:
                model = LGBMClassifier(**params, random_state=42, verbose=-1)
            else:
                model = LGBMRegressor(**params, random_state=42, verbose=-1)

            model.fit(X, y)
            return model

        except ImportError:
            logger.warning("LightGBM not available, using sklearn fallback")
            return self._train_random_forest(X, y, params)

    def _train_random_forest(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        params: Dict[str, Any]
    ):
        """Train Random Forest model."""
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

        is_classification = len(np.unique(y)) < 20

        if is_classification:
            model = RandomForestClassifier(**params, random_state=42)
        else:
            model = RandomForestRegressor(**params, random_state=42)

        model.fit(X, y)
        return model

    def evaluate(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Evaluate model on test data.

        Args:
            X_test: Test features
            y_test: Test labels
            metrics: Metrics to compute

        Returns:
            Evaluation metrics
        """
        if self.model is None:
            raise ValueError("No model trained")

        logger.info(f"Evaluating on {len(X_test)} test samples")

        results = {}

        # Basic score
        test_score = self.model.score(X_test, y_test)
        results['test_score'] = test_score

        # Additional metrics if requested
        if metrics:
            from sklearn.metrics import (
                accuracy_score, precision_score, recall_score,
                f1_score, mean_squared_error, mean_absolute_error
            )

            y_pred = self.model.predict(X_test)

            if 'accuracy' in metrics:
                results['accuracy'] = accuracy_score(y_test, y_pred)

            if 'precision' in metrics:
                results['precision'] = precision_score(y_test, y_pred, average='weighted')

            if 'recall' in metrics:
                results['recall'] = recall_score(y_test, y_pred, average='weighted')

            if 'f1' in metrics:
                results['f1'] = f1_score(y_test, y_pred, average='weighted')

            if 'mse' in metrics:
                results['mse'] = mean_squared_error(y_test, y_pred)

            if 'mae' in metrics:
                results['mae'] = mean_absolute_error(y_test, y_pred)

        self.log_metrics(results)
        logger.info(f"Evaluation results: {results}")

        return results

    def save_model(self, model_name: str = "model.pkl"):
        """
        Save trained model.

        Args:
            model_name: Name of the model file
        """
        if self.model is None:
            raise ValueError("No model to save")

        if not self.run_id:
            self.start_run()

        model_path = self.run_dir / "models" / model_name

        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)

        logger.info(f"Model saved to {model_path}")

        # Save model metadata
        metadata = {
            'model_name': model_name,
            'model_type': type(self.model).__name__,
            'saved_at': datetime.now().isoformat(),
            'params': self.params,
            'metrics': self.metrics
        }

        metadata_path = self.run_dir / "models" / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        return model_path

    def load_model(self, model_path: str):
        """
        Load a trained model.

        Args:
            model_path: Path to model file
        """
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

        logger.info(f"Model loaded from {model_path}")


def main():
    """Example usage."""
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split

    # Generate sample data
    X, y = make_classification(
        n_samples=1000,
        n_features=20,
        n_informative=15,
        random_state=42
    )

    X = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(20)])
    y = pd.Series(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("=" * 80)
    print("MLOpsTrainer - Example")
    print("=" * 80)

    # Initialize trainer
    trainer = MLOpsTrainer(
        experiment_name="classification_example",
        tracking_uri="mlruns"
    )

    # Train model
    print("\n[1] Training model...")
    trainer.train(
        X_train, y_train,
        model_type='xgboost',
        params={'n_estimators': 100, 'max_depth': 6}
    )

    # Evaluate
    print("\n[2] Evaluating model...")
    results = trainer.evaluate(
        X_test, y_test,
        metrics=['accuracy', 'precision', 'recall', 'f1']
    )
    print("Results:")
    for metric, value in results.items():
        print(f"  {metric}: {value:.4f}")

    # Save model
    print("\n[3] Saving model...")
    model_path = trainer.save_model("best_model.pkl")
    print(f"Model saved to: {model_path}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
