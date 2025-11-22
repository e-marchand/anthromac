"""Stacking ensemble implementation."""

import numpy as np
from typing import List, Any, Optional
from sklearn.model_selection import cross_val_predict
from sklearn.base import clone
import logging

logger = logging.getLogger(__name__)


class StackingEnsemble:
    """
    Stacking ensemble meta-learner.

    Combines predictions from multiple base models using a meta-learner.
    """

    def __init__(
        self,
        base_models: List[Any],
        meta_model: Any,
        use_features: bool = False,
        cv_folds: int = 5
    ):
        """
        Initialize stacking ensemble.

        Args:
            base_models: List of base models
            meta_model: Meta-learner model
            use_features: Whether to include original features
            cv_folds: Number of CV folds for out-of-fold predictions
        """
        self.base_models = base_models
        self.meta_model = meta_model
        self.use_features = use_features
        self.cv_folds = cv_folds

        self.fitted_base_models_ = []
        self.fitted_meta_model_ = None

        logger.info(f"Initialized StackingEnsemble with {len(base_models)} base models")

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'StackingEnsemble':
        """
        Fit ensemble.

        Args:
            X: Training features
            y: Training labels

        Returns:
            self: Fitted ensemble
        """
        logger.info(f"Fitting stacking ensemble on {len(X)} samples...")

        # Generate out-of-fold predictions for meta-features
        logger.info("Generating out-of-fold predictions...")
        meta_features = []

        for i, model in enumerate(self.base_models):
            logger.info(f"  Base model {i+1}/{len(self.base_models)}: "
                       f"{model.__class__.__name__}")

            # Out-of-fold predictions
            oof_preds = cross_val_predict(
                model, X, y,
                cv=self.cv_folds,
                method='predict_proba' if hasattr(model, 'predict_proba') else 'predict'
            )

            # If probabilities, use them; otherwise reshape predictions
            if len(oof_preds.shape) == 1:
                oof_preds = oof_preds.reshape(-1, 1)

            meta_features.append(oof_preds)

        # Concatenate meta-features
        meta_features = np.hstack(meta_features)

        # Optionally include original features
        if self.use_features:
            meta_features = np.hstack([X, meta_features])

        logger.info(f"Meta-features shape: {meta_features.shape}")

        # Train base models on full data
        logger.info("Training base models on full dataset...")
        self.fitted_base_models_ = []

        for i, model in enumerate(self.base_models):
            fitted_model = clone(model)
            fitted_model.fit(X, y)
            self.fitted_base_models_.append(fitted_model)

        # Train meta-model
        logger.info("Training meta-model...")
        self.fitted_meta_model_ = clone(self.meta_model)
        self.fitted_meta_model_.fit(meta_features, y)

        logger.info("Stacking ensemble training complete")

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions.

        Args:
            X: Features

        Returns:
            Predictions
        """
        meta_features = self._get_meta_features(X)
        return self.fitted_meta_model_.predict(meta_features)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict probabilities.

        Args:
            X: Features

        Returns:
            Class probabilities
        """
        if not hasattr(self.fitted_meta_model_, 'predict_proba'):
            raise ValueError("Meta-model does not support probability predictions")

        meta_features = self._get_meta_features(X)
        return self.fitted_meta_model_.predict_proba(meta_features)

    def _get_meta_features(self, X: np.ndarray) -> np.ndarray:
        """
        Get meta-features from base models.

        Args:
            X: Features

        Returns:
            Meta-features
        """
        meta_features = []

        for model in self.fitted_base_models_:
            if hasattr(model, 'predict_proba'):
                preds = model.predict_proba(X)
            else:
                preds = model.predict(X).reshape(-1, 1)

            meta_features.append(preds)

        meta_features = np.hstack(meta_features)

        if self.use_features:
            meta_features = np.hstack([X, meta_features])

        return meta_features


class VotingEnsemble:
    """
    Voting ensemble.

    Combines predictions by voting (hard) or averaging (soft).
    """

    def __init__(
        self,
        models: List[Any],
        voting: str = 'soft',
        weights: Optional[List[float]] = None
    ):
        """
        Initialize voting ensemble.

        Args:
            models: List of models
            voting: 'hard' (majority vote) or 'soft' (weighted average)
            weights: Optional weights for models
        """
        self.models = models
        self.voting = voting
        self.weights = weights if weights is not None else [1.0] * len(models)

        self.fitted_models_ = []

        logger.info(f"Initialized VotingEnsemble ({voting} voting, "
                   f"{len(models)} models)")

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'VotingEnsemble':
        """
        Fit ensemble.

        Args:
            X: Training features
            y: Training labels

        Returns:
            self: Fitted ensemble
        """
        logger.info("Fitting voting ensemble...")

        self.fitted_models_ = []

        for i, model in enumerate(self.models):
            logger.info(f"  Model {i+1}/{len(self.models)}: "
                       f"{model.__class__.__name__}")

            fitted_model = clone(model)
            fitted_model.fit(X, y)
            self.fitted_models_.append(fitted_model)

        logger.info("Voting ensemble training complete")

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        if self.voting == 'hard':
            return self._hard_vote(X)
        else:
            return self._soft_vote(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities."""
        if self.voting != 'soft':
            raise ValueError("predict_proba only available with soft voting")

        # Weighted average of probabilities
        probs = []

        for model, weight in zip(self.fitted_models_, self.weights):
            if hasattr(model, 'predict_proba'):
                probs.append(model.predict_proba(X) * weight)

        return np.sum(probs, axis=0) / sum(self.weights)

    def _hard_vote(self, X: np.ndarray) -> np.ndarray:
        """Hard voting (majority vote)."""
        predictions = []

        for model in self.fitted_models_:
            predictions.append(model.predict(X))

        predictions = np.array(predictions)

        # Majority vote
        from scipy.stats import mode
        return mode(predictions, axis=0)[0].flatten()

    def _soft_vote(self, X: np.ndarray) -> np.ndarray:
        """Soft voting (weighted average)."""
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)


def main():
    """Example usage."""
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score

    try:
        from xgboost import XGBClassifier
        has_xgboost = True
    except ImportError:
        has_xgboost = False

    print("=" * 80)
    print("Ensemble Methods - Example")
    print("=" * 80)

    # Generate data
    X, y = make_classification(
        n_samples=1000,
        n_features=20,
        n_informative=15,
        n_classes=3,
        random_state=42
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    print(f"\nData:")
    print(f"  Train: {len(X_train)} samples")
    print(f"  Test:  {len(X_test)} samples")
    print(f"  Classes: {len(np.unique(y))}")

    # Define base models
    base_models = [
        RandomForestClassifier(n_estimators=100, random_state=42),
        LogisticRegression(max_iter=1000)
    ]

    if has_xgboost:
        base_models.append(XGBClassifier(n_estimators=100, random_state=42))

    # Test individual models
    print("\n[1] Individual model performance:")
    for model in base_models:
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"  {model.__class__.__name__:25s}: {acc:.4f}")

    # Test stacking
    print("\n[2] Stacking Ensemble:")

    stacking = StackingEnsemble(
        base_models=base_models,
        meta_model=LogisticRegression(max_iter=1000),
        use_features=False,
        cv_folds=5
    )

    stacking.fit(X_train, y_train)
    y_pred_stacking = stacking.predict(X_test)
    acc_stacking = accuracy_score(y_test, y_pred_stacking)

    print(f"  Stacking accuracy: {acc_stacking:.4f}")

    # Test voting
    print("\n[3] Voting Ensemble:")

    for voting_type in ['hard', 'soft']:
        voting = VotingEnsemble(
            models=base_models,
            voting=voting_type
        )

        voting.fit(X_train, y_train)
        y_pred_voting = voting.predict(X_test)
        acc_voting = accuracy_score(y_test, y_pred_voting)

        print(f"  {voting_type.capitalize()} voting: {acc_voting:.4f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
