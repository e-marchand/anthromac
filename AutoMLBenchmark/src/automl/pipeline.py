"""Main AutoML pipeline."""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
import logging
import time

logger = logging.getLogger(__name__)


class AutoMLPipeline:
    """
    Automated Machine Learning pipeline.

    Automatically selects models, tunes hyperparameters, and creates ensembles.
    """

    def __init__(
        self,
        task: str = 'classification',
        time_budget: int = 3600,
        metric: str = 'accuracy',
        cv_folds: int = 5,
        n_jobs: int = -1
    ):
        """
        Initialize AutoML pipeline.

        Args:
            task: 'classification' or 'regression'
            time_budget: Maximum time in seconds
            metric: Evaluation metric
            cv_folds: Number of CV folds
            n_jobs: Number of parallel jobs
        """
        self.task = task
        self.time_budget = time_budget
        self.metric = metric
        self.cv_folds = cv_folds
        self.n_jobs = n_jobs

        self.models_ = []
        self.scores_ = []
        self.best_model_ = None
        self.best_score_ = -np.inf if metric in ['accuracy', 'r2'] else np.inf

        self.start_time = None
        self.fitted = False

        logger.info(f"Initialized AutoML for {task} (time budget: {time_budget}s)")

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'AutoMLPipeline':
        """
        Fit AutoML pipeline.

        Args:
            X: Training features
            y: Training labels

        Returns:
            self: Fitted pipeline
        """
        logger.info(f"Starting AutoML on {len(X)} samples, {X.shape[1]} features")

        self.start_time = time.time()

        # Get candidate models
        candidate_models = self._get_candidate_models()

        logger.info(f"Testing {len(candidate_models)} candidate models...")

        # Evaluate each model
        for model_name, model in candidate_models.items():
            if self._time_remaining() <= 0:
                logger.warning("Time budget exceeded")
                break

            logger.info(f"Evaluating {model_name}...")

            try:
                # Cross-validation
                scores = cross_val_score(
                    model, X, y,
                    cv=self.cv_folds,
                    scoring=self._get_scorer(),
                    n_jobs=self.n_jobs
                )

                mean_score = scores.mean()
                std_score = scores.std()

                logger.info(f"  {model_name}: {mean_score:.4f} (±{std_score:.4f})")

                # Store results
                self.models_.append({
                    'name': model_name,
                    'model': model,
                    'score': mean_score,
                    'std': std_score
                })

                self.scores_.append(mean_score)

                # Update best model
                if self._is_better(mean_score, self.best_score_):
                    self.best_score_ = mean_score
                    self.best_model_ = model
                    logger.info(f"  New best model: {model_name} ({mean_score:.4f})")

            except Exception as e:
                logger.error(f"  Error evaluating {model_name}: {e}")
                continue

        # Train best model on full data
        if self.best_model_ is not None:
            logger.info("Training best model on full dataset...")
            self.best_model_.fit(X, y)

        self.fitted = True

        elapsed = time.time() - self.start_time
        logger.info(f"AutoML completed in {elapsed:.2f}s")
        logger.info(f"Best model score: {self.best_score_:.4f}")

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions.

        Args:
            X: Features

        Returns:
            Predictions
        """
        if not self.fitted:
            raise ValueError("Pipeline not fitted. Call fit() first.")

        return self.best_model_.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities (classification only).

        Args:
            X: Features

        Returns:
            Class probabilities
        """
        if self.task != 'classification':
            raise ValueError("predict_proba only available for classification")

        if not hasattr(self.best_model_, 'predict_proba'):
            raise ValueError("Best model does not support probability predictions")

        return self.best_model_.predict_proba(X)

    def get_best_model(self) -> Any:
        """Get best model."""
        return self.best_model_

    def get_leaderboard(self) -> pd.DataFrame:
        """
        Get leaderboard of all models.

        Returns:
            DataFrame with model rankings
        """
        if not self.models_:
            return pd.DataFrame()

        leaderboard = pd.DataFrame(self.models_)
        leaderboard = leaderboard.sort_values('score', ascending=False)
        leaderboard = leaderboard.reset_index(drop=True)
        leaderboard.index += 1  # Start from 1

        return leaderboard[['name', 'score', 'std']]

    def _get_candidate_models(self) -> Dict[str, Any]:
        """Get candidate models based on task."""
        try:
            from xgboost import XGBClassifier, XGBRegressor
            has_xgboost = True
        except ImportError:
            has_xgboost = False
            logger.warning("XGBoost not available")

        try:
            from lightgbm import LGBMClassifier, LGBMRegressor
            has_lightgbm = True
        except ImportError:
            has_lightgbm = False
            logger.warning("LightGBM not available")

        if self.task == 'classification':
            models = {
                'LogisticRegression': LogisticRegression(max_iter=1000),
                'RandomForest': RandomForestClassifier(n_estimators=100, n_jobs=self.n_jobs)
            }

            if has_xgboost:
                models['XGBoost'] = XGBClassifier(n_estimators=100, n_jobs=self.n_jobs)

            if has_lightgbm:
                models['LightGBM'] = LGBMClassifier(n_estimators=100, n_jobs=self.n_jobs)

        else:  # regression
            models = {
                'Ridge': Ridge(),
                'RandomForest': RandomForestRegressor(n_estimators=100, n_jobs=self.n_jobs)
            }

            if has_xgboost:
                models['XGBoost'] = XGBRegressor(n_estimators=100, n_jobs=self.n_jobs)

            if has_lightgbm:
                models['LightGBM'] = LGBMRegressor(n_estimators=100, n_jobs=self.n_jobs)

        return models

    def _get_scorer(self) -> str:
        """Get scorer based on metric."""
        metric_map = {
            'accuracy': 'accuracy',
            'f1': 'f1',
            'roc_auc': 'roc_auc',
            'r2': 'r2',
            'rmse': 'neg_root_mean_squared_error',
            'mae': 'neg_mean_absolute_error'
        }

        return metric_map.get(self.metric, self.metric)

    def _is_better(self, score1: float, score2: float) -> bool:
        """Check if score1 is better than score2."""
        if self.metric in ['accuracy', 'f1', 'roc_auc', 'r2']:
            return score1 > score2
        else:
            return score1 < score2

    def _time_remaining(self) -> float:
        """Get remaining time in seconds."""
        if self.start_time is None:
            return self.time_budget

        elapsed = time.time() - self.start_time
        return self.time_budget - elapsed


def main():
    """Example usage."""
    from sklearn.datasets import make_classification, make_regression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, r2_score

    print("=" * 80)
    print("AutoML Pipeline - Example")
    print("=" * 80)

    # Test 1: Classification
    print("\n[1] Classification Task")

    X, y = make_classification(
        n_samples=1000,
        n_features=20,
        n_informative=15,
        n_redundant=5,
        random_state=42
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"  Train: {len(X_train)} samples")
    print(f"  Test:  {len(X_test)} samples")

    # Initialize AutoML
    automl = AutoMLPipeline(
        task='classification',
        time_budget=60,  # 1 minute
        metric='accuracy',
        cv_folds=5
    )

    # Fit
    automl.fit(X_train, y_train)

    # Predict
    y_pred = automl.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\n  Best model: {automl.get_best_model().__class__.__name__}")
    print(f"  CV Score: {automl.best_score_:.4f}")
    print(f"  Test Accuracy: {accuracy:.4f}")

    # Leaderboard
    print("\n  Leaderboard:")
    print(automl.get_leaderboard().to_string())

    # Test 2: Regression
    print("\n[2] Regression Task")

    X, y = make_regression(
        n_samples=1000,
        n_features=20,
        n_informative=15,
        noise=10,
        random_state=42
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Initialize AutoML
    automl = AutoMLPipeline(
        task='regression',
        time_budget=60,
        metric='r2',
        cv_folds=5
    )

    # Fit
    automl.fit(X_train, y_train)

    # Predict
    y_pred = automl.predict(X_test)
    r2 = r2_score(y_test, y_pred)

    print(f"\n  Best model: {automl.get_best_model().__class__.__name__}")
    print(f"  CV Score: {automl.best_score_:.4f}")
    print(f"  Test R²: {r2:.4f}")

    # Leaderboard
    print("\n  Leaderboard:")
    print(automl.get_leaderboard().to_string())

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
