"""Bayesian optimization for hyperparameter tuning."""

import numpy as np
from typing import Dict, Any, Tuple, Callable, Optional
from sklearn.model_selection import cross_val_score
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
import logging

logger = logging.getLogger(__name__)


class BayesianOptimizer:
    """
    Bayesian hyperparameter optimization.

    Uses Gaussian Process to model the objective function
    and acquisition function to select next parameters.
    """

    def __init__(
        self,
        model_class: Any,
        search_space: Dict[str, Tuple],
        n_iterations: int = 50,
        n_initial: int = 10,
        acquisition: str = 'ei',
        cv_folds: int = 5,
        random_state: Optional[int] = None
    ):
        """
        Initialize Bayesian optimizer.

        Args:
            model_class: Model class to optimize
            search_space: Dict mapping param name to (min, max) tuple
            n_iterations: Number of optimization iterations
            n_initial: Number of random initial points
            acquisition: Acquisition function ('ei', 'ucb', 'poi')
            cv_folds: Number of CV folds
            random_state: Random seed
        """
        self.model_class = model_class
        self.search_space = search_space
        self.n_iterations = n_iterations
        self.n_initial = n_initial
        self.acquisition = acquisition
        self.cv_folds = cv_folds
        self.random_state = random_state

        if random_state is not None:
            np.random.seed(random_state)

        # History
        self.X_tried_ = []
        self.y_tried_ = []
        self.best_params_ = None
        self.best_score_ = -np.inf

        # GP model
        self.gp_ = GaussianProcessRegressor(
            kernel=Matern(nu=2.5),
            alpha=1e-6,
            normalize_y=True,
            n_restarts_optimizer=5,
            random_state=random_state
        )

        logger.info(f"Initialized Bayesian optimizer ({n_iterations} iterations)")

    def optimize(
        self,
        X: np.ndarray,
        y: np.ndarray,
        scoring: str = 'accuracy'
    ) -> Dict[str, Any]:
        """
        Optimize hyperparameters.

        Args:
            X: Training features
            y: Training labels
            scoring: Scoring metric

        Returns:
            Best parameters found
        """
        logger.info("Starting Bayesian optimization...")

        # Random initialization
        logger.info(f"Random initialization ({self.n_initial} points)...")

        for i in range(self.n_initial):
            params = self._sample_random_params()
            score = self._evaluate_params(params, X, y, scoring)

            logger.info(f"  {i+1}/{self.n_initial}: score={score:.4f}")

        # Bayesian optimization
        logger.info(f"Bayesian optimization ({self.n_iterations - self.n_initial} iterations)...")

        for i in range(self.n_initial, self.n_iterations):
            # Fit GP on current data
            X_array = self._params_to_array(self.X_tried_)
            y_array = np.array(self.y_tried_)

            self.gp_.fit(X_array, y_array)

            # Select next parameters using acquisition function
            params = self._select_next_params()

            # Evaluate
            score = self._evaluate_params(params, X, y, scoring)

            logger.info(f"  {i+1}/{self.n_iterations}: score={score:.4f}, "
                       f"best={self.best_score_:.4f}")

        logger.info(f"Optimization complete. Best score: {self.best_score_:.4f}")
        logger.info(f"Best parameters: {self.best_params_}")

        return self.best_params_

    def get_optimization_history(self) -> Dict[str, Any]:
        """
        Get optimization history.

        Returns:
            Dictionary with history
        """
        return {
            'params': self.X_tried_,
            'scores': self.y_tried_,
            'best_params': self.best_params_,
            'best_score': self.best_score_
        }

    def _evaluate_params(
        self,
        params: Dict[str, Any],
        X: np.ndarray,
        y: np.ndarray,
        scoring: str
    ) -> float:
        """Evaluate parameters using cross-validation."""
        try:
            # Create model with params
            model = self.model_class(**params)

            # Cross-validation
            scores = cross_val_score(
                model, X, y,
                cv=self.cv_folds,
                scoring=scoring
            )

            score = scores.mean()

            # Store result
            self.X_tried_.append(params)
            self.y_tried_.append(score)

            # Update best
            if score > self.best_score_:
                self.best_score_ = score
                self.best_params_ = params

            return score

        except Exception as e:
            logger.error(f"Error evaluating params: {e}")
            # Return poor score for invalid params
            self.X_tried_.append(params)
            self.y_tried_.append(-np.inf)
            return -np.inf

    def _sample_random_params(self) -> Dict[str, Any]:
        """Sample random parameters from search space."""
        params = {}

        for param_name, (min_val, max_val) in self.search_space.items():
            if isinstance(min_val, int) and isinstance(max_val, int):
                # Integer parameter
                params[param_name] = np.random.randint(min_val, max_val + 1)
            else:
                # Float parameter
                params[param_name] = np.random.uniform(min_val, max_val)

        return params

    def _select_next_params(self) -> Dict[str, Any]:
        """
        Select next parameters using acquisition function.

        Returns:
            Next parameters to try
        """
        # Sample candidates
        n_candidates = 100
        candidates = [self._sample_random_params() for _ in range(n_candidates)]
        X_candidates = self._params_to_array(candidates)

        # Predict with GP
        mu, sigma = self.gp_.predict(X_candidates, return_std=True)

        # Compute acquisition function
        if self.acquisition == 'ei':
            acquisition_values = self._expected_improvement(mu, sigma)
        elif self.acquisition == 'ucb':
            acquisition_values = self._upper_confidence_bound(mu, sigma)
        elif self.acquisition == 'poi':
            acquisition_values = self._probability_of_improvement(mu, sigma)
        else:
            raise ValueError(f"Unknown acquisition: {self.acquisition}")

        # Select best candidate
        best_idx = np.argmax(acquisition_values)
        return candidates[best_idx]

    def _expected_improvement(self, mu: np.ndarray, sigma: np.ndarray) -> np.ndarray:
        """
        Expected Improvement acquisition function.

        Args:
            mu: Predicted mean
            sigma: Predicted std

        Returns:
            EI values
        """
        from scipy.stats import norm

        if self.best_score_ == -np.inf:
            return mu

        # Avoid division by zero
        sigma = np.maximum(sigma, 1e-8)

        z = (mu - self.best_score_) / sigma
        ei = (mu - self.best_score_) * norm.cdf(z) + sigma * norm.pdf(z)

        return ei

    def _upper_confidence_bound(
        self,
        mu: np.ndarray,
        sigma: np.ndarray,
        beta: float = 2.0
    ) -> np.ndarray:
        """
        Upper Confidence Bound acquisition function.

        Args:
            mu: Predicted mean
            sigma: Predicted std
            beta: Exploration parameter

        Returns:
            UCB values
        """
        return mu + beta * sigma

    def _probability_of_improvement(
        self,
        mu: np.ndarray,
        sigma: np.ndarray
    ) -> np.ndarray:
        """
        Probability of Improvement acquisition function.

        Args:
            mu: Predicted mean
            sigma: Predicted std

        Returns:
            POI values
        """
        from scipy.stats import norm

        if self.best_score_ == -np.inf:
            return np.ones_like(mu)

        # Avoid division by zero
        sigma = np.maximum(sigma, 1e-8)

        z = (mu - self.best_score_) / sigma
        poi = norm.cdf(z)

        return poi

    def _params_to_array(self, params_list: list) -> np.ndarray:
        """Convert list of parameter dicts to array."""
        if not params_list:
            return np.array([])

        # Get parameter names in consistent order
        param_names = sorted(self.search_space.keys())

        # Convert to array
        array = np.array([
            [params[name] for name in param_names]
            for params in params_list
        ])

        return array


def main():
    """Example usage."""
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier

    print("=" * 80)
    print("Bayesian Optimizer - Example")
    print("=" * 80)

    # Generate data
    X, y = make_classification(
        n_samples=500,
        n_features=20,
        n_informative=15,
        random_state=42
    )

    print(f"\nData: {len(X)} samples, {X.shape[1]} features")

    # Define search space
    search_space = {
        'n_estimators': (50, 200),
        'max_depth': (3, 15),
        'min_samples_split': (2, 10),
        'min_samples_leaf': (1, 5)
    }

    print("\nSearch space:")
    for param, (min_val, max_val) in search_space.items():
        print(f"  {param}: [{min_val}, {max_val}]")

    # Initialize optimizer
    optimizer = BayesianOptimizer(
        model_class=RandomForestClassifier,
        search_space=search_space,
        n_iterations=30,
        n_initial=10,
        acquisition='ei',
        cv_folds=5,
        random_state=42
    )

    # Optimize
    print("\n[1] Optimizing hyperparameters...")
    best_params = optimizer.optimize(X, y, scoring='accuracy')

    print(f"\nBest parameters found:")
    for param, value in best_params.items():
        print(f"  {param}: {value}")

    print(f"\nBest CV score: {optimizer.best_score_:.4f}")

    # Show optimization history
    print("\n[2] Optimization history:")
    history = optimizer.get_optimization_history()

    print(f"\n  Iteration | Score")
    print("  " + "-" * 25)
    for i, score in enumerate(history['scores'][:10], 1):
        print(f"  {i:9d} | {score:.4f}")
    print("  ...")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
