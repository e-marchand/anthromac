"""T-Learner for CATE estimation."""

import numpy as np
from typing import Optional, Any
from sklearn.ensemble import RandomForestRegressor
import logging

logger = logging.getLogger(__name__)


class TLearner:
    """
    T-Learner (Two-Model Learner) for Conditional Average Treatment Effect.

    Trains separate models for treated and control groups.
    CATE(x) = E[Y|X=x, T=1] - E[Y|X=x, T=0]
    """

    def __init__(
        self,
        model_t: Optional[Any] = None,
        model_c: Optional[Any] = None
    ):
        """
        Initialize T-Learner.

        Args:
            model_t: Model for treated group (default: Random Forest)
            model_c: Model for control group (default: Random Forest)
        """
        if model_t is None:
            self.model_t = RandomForestRegressor(n_estimators=100, random_state=42)
        else:
            self.model_t = model_t

        if model_c is None:
            self.model_c = RandomForestRegressor(n_estimators=100, random_state=42)
        else:
            self.model_c = model_c

        logger.info("Initialized T-Learner")

    def fit(
        self,
        X: np.ndarray,
        treatment: np.ndarray,
        y: np.ndarray
    ) -> 'TLearner':
        """
        Fit T-Learner.

        Args:
            X: Covariates
            treatment: Treatment indicator (0/1)
            y: Outcomes

        Returns:
            self: Fitted learner
        """
        logger.info(f"Fitting T-Learner on {len(X)} samples")

        # Split data by treatment
        treated_mask = treatment == 1
        control_mask = treatment == 0

        X_t = X[treated_mask]
        y_t = y[treated_mask]

        X_c = X[control_mask]
        y_c = y[control_mask]

        logger.info(f"Treated samples: {len(X_t)}, Control samples: {len(X_c)}")

        # Train separate models
        logger.info("Training model for treated group...")
        self.model_t.fit(X_t, y_t)

        logger.info("Training model for control group...")
        self.model_c.fit(X_c, y_c)

        logger.info("T-Learner training completed")
        return self

    def predict_cate(self, X: np.ndarray) -> np.ndarray:
        """
        Predict CATE for new observations.

        Args:
            X: Covariates

        Returns:
            Array of CATE estimates
        """
        # Predict potential outcomes
        y1_pred = self.model_t.predict(X)  # E[Y|X, T=1]
        y0_pred = self.model_c.predict(X)  # E[Y|X, T=0]

        # CATE is the difference
        cate = y1_pred - y0_pred

        logger.info(f"Predicted CATE - mean: {cate.mean():.4f}, "
                   f"std: {cate.std():.4f}")

        return cate

    def predict_ate(self, X: np.ndarray) -> float:
        """
        Predict Average Treatment Effect.

        Args:
            X: Covariates

        Returns:
            ATE estimate
        """
        cate = self.predict_cate(X)
        ate = cate.mean()

        logger.info(f"ATE estimate: {ate:.4f}")
        return float(ate)


def main():
    """Example usage."""
    from sklearn.datasets import make_regression

    # Generate data
    np.random.seed(42)

    X, _ = make_regression(
        n_samples=1000,
        n_features=10,
        n_informative=7,
        noise=1.0,
        random_state=42
    )

    # Simulate treatment (random assignment)
    treatment = np.random.binomial(1, 0.5, len(X))

    # Simulate outcomes with heterogeneous treatment effect
    # Treatment effect depends on first feature
    treatment_effect = 2.0 + 0.5 * X[:, 0]
    y = X[:, 0] + 0.5 * X[:, 1] + treatment * treatment_effect + np.random.randn(len(X))

    # True CATE
    true_cate = treatment_effect

    print("=" * 80)
    print("T-Learner - Example")
    print("=" * 80)

    print(f"\nData:")
    print(f"  Samples: {len(X)}")
    print(f"  Treated: {treatment.sum()}")
    print(f"  Control: {(1 - treatment).sum()}")
    print(f"  True ATE: {true_cate.mean():.4f}")

    # Split data
    from sklearn.model_selection import train_test_split

    X_train, X_test, t_train, t_test, y_train, y_test, cate_test = train_test_split(
        X, treatment, y, true_cate, test_size=0.3, random_state=42
    )

    # Initialize T-Learner
    print("\n[1] Training T-Learner...")
    tlearner = TLearner()
    tlearner.fit(X_train, t_train, y_train)

    # Predict CATE
    print("\n[2] Predicting CATE...")
    cate_pred = tlearner.predict_cate(X_test)

    # Evaluate
    print("\n[3] Evaluation:")
    from sklearn.metrics import mean_squared_error, mean_absolute_error

    pehe = np.sqrt(mean_squared_error(cate_test, cate_pred))
    mae = mean_absolute_error(cate_test, cate_pred)

    ate_pred = cate_pred.mean()
    ate_true = cate_test.mean()

    print(f"  PEHE (Precision in Estimation of HTE): {pehe:.4f}")
    print(f"  MAE: {mae:.4f}")
    print(f"  ATE prediction: {ate_pred:.4f}")
    print(f"  ATE true: {ate_true:.4f}")
    print(f"  ATE bias: {abs(ate_pred - ate_true):.4f}")

    # Show individual predictions
    print("\n[4] Sample predictions:")
    print("  Index | True CATE | Pred CATE | Error")
    print("  " + "-" * 45)
    for i in range(min(5, len(X_test))):
        error = abs(cate_test[i] - cate_pred[i])
        print(f"  {i:5d} | {cate_test[i]:9.4f} | {cate_pred[i]:9.4f} | {error:5.4f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
