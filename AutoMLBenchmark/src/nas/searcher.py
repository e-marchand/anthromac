"""Neural Architecture Search implementation."""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class Architecture:
    """Represents a neural network architecture."""

    def __init__(
        self,
        layers: List[Dict[str, Any]],
        input_dim: int,
        output_dim: int
    ):
        """
        Initialize architecture.

        Args:
            layers: List of layer specifications
            input_dim: Input dimension
            output_dim: Output dimension
        """
        self.layers = layers
        self.input_dim = input_dim
        self.output_dim = output_dim

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'input_dim': self.input_dim,
            'output_dim': self.output_dim,
            'layers': self.layers
        }

    def __repr__(self):
        return f"Architecture({len(self.layers)} layers)"


class NeuralArchitectureSearch:
    """
    Neural Architecture Search for automated network design.

    Searches for optimal architecture using evolutionary or random search.
    """

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        max_layers: int = 5,
        max_units: int = 256,
        search_algorithm: str = 'random',
        task: str = 'classification'
    ):
        """
        Initialize NAS.

        Args:
            input_dim: Input dimension
            output_dim: Output dimension (number of classes)
            max_layers: Maximum number of layers
            max_units: Maximum units per layer
            search_algorithm: 'random' or 'evolutionary'
            task: 'classification' or 'regression'
        """
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.max_layers = max_layers
        self.max_units = max_units
        self.search_algorithm = search_algorithm
        self.task = task

        self.architectures_tried_ = []
        self.scores_ = []
        self.best_architecture_ = None
        self.best_score_ = -np.inf

        logger.info(f"Initialized NAS (max_layers={max_layers}, "
                   f"max_units={max_units}, algorithm={search_algorithm})")

    def search(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        num_trials: int = 50,
        epochs_per_trial: int = 10
    ) -> Architecture:
        """
        Search for best architecture.

        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            num_trials: Number of architectures to try
            epochs_per_trial: Training epochs per architecture

        Returns:
            Best architecture found
        """
        logger.info(f"Starting NAS with {num_trials} trials...")

        if self.search_algorithm == 'random':
            best_arch = self._random_search(
                X_train, y_train, X_val, y_val,
                num_trials, epochs_per_trial
            )
        elif self.search_algorithm == 'evolutionary':
            best_arch = self._evolutionary_search(
                X_train, y_train, X_val, y_val,
                num_trials, epochs_per_trial
            )
        else:
            raise ValueError(f"Unknown search algorithm: {self.search_algorithm}")

        logger.info(f"NAS complete. Best score: {self.best_score_:.4f}")

        return best_arch

    def build_model(self, architecture: Architecture) -> Any:
        """
        Build model from architecture.

        Args:
            architecture: Architecture specification

        Returns:
            Built model
        """
        try:
            import torch
            import torch.nn as nn

            class DynamicNet(nn.Module):
                def __init__(self, arch):
                    super().__init__()
                    layers = []
                    prev_dim = arch.input_dim

                    for layer_spec in arch.layers:
                        if layer_spec['type'] == 'dense':
                            layers.append(nn.Linear(prev_dim, layer_spec['units']))
                            layers.append(nn.ReLU())
                            prev_dim = layer_spec['units']

                        elif layer_spec['type'] == 'dropout':
                            layers.append(nn.Dropout(layer_spec['rate']))

                    # Output layer
                    layers.append(nn.Linear(prev_dim, arch.output_dim))

                    self.network = nn.Sequential(*layers)

                def forward(self, x):
                    return self.network(x)

            return DynamicNet(architecture)

        except ImportError:
            # Fallback to sklearn
            logger.warning("PyTorch not available, using sklearn MLPClassifier")
            from sklearn.neural_network import MLPClassifier, MLPRegressor

            hidden_layers = tuple(
                layer['units'] for layer in architecture.layers
                if layer['type'] == 'dense'
            )

            if self.task == 'classification':
                return MLPClassifier(hidden_layer_sizes=hidden_layers, max_iter=100)
            else:
                return MLPRegressor(hidden_layer_sizes=hidden_layers, max_iter=100)

    def _random_search(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        num_trials: int,
        epochs: int
    ) -> Architecture:
        """Random architecture search."""
        logger.info("Running random search...")

        for i in range(num_trials):
            # Sample random architecture
            arch = self._sample_architecture()

            # Evaluate
            score = self._evaluate_architecture(
                arch, X_train, y_train, X_val, y_val, epochs
            )

            logger.info(f"  Trial {i+1}/{num_trials}: {arch}, score={score:.4f}")

            # Update best
            if score > self.best_score_:
                self.best_score_ = score
                self.best_architecture_ = arch
                logger.info(f"  New best architecture found!")

            self.architectures_tried_.append(arch)
            self.scores_.append(score)

        return self.best_architecture_

    def _evolutionary_search(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        num_generations: int,
        epochs: int,
        population_size: int = 10
    ) -> Architecture:
        """Evolutionary architecture search."""
        logger.info(f"Running evolutionary search ({num_generations} generations, "
                   f"population={population_size})...")

        # Initial population
        population = [self._sample_architecture() for _ in range(population_size)]

        for gen in range(num_generations):
            logger.info(f"Generation {gen+1}/{num_generations}")

            # Evaluate population
            scores = []
            for arch in population:
                score = self._evaluate_architecture(
                    arch, X_train, y_train, X_val, y_val, epochs
                )
                scores.append(score)

                self.architectures_tried_.append(arch)
                self.scores_.append(score)

                if score > self.best_score_:
                    self.best_score_ = score
                    self.best_architecture_ = arch

            # Selection: keep top 50%
            sorted_indices = np.argsort(scores)[::-1]
            top_k = population_size // 2
            parents = [population[i] for i in sorted_indices[:top_k]]

            logger.info(f"  Best score: {max(scores):.4f}, "
                       f"Avg: {np.mean(scores):.4f}")

            # Create next generation
            population = parents.copy()

            # Mutation and crossover
            while len(population) < population_size:
                if np.random.rand() < 0.5:
                    # Mutation
                    parent = parents[np.random.randint(len(parents))]
                    child = self._mutate_architecture(parent)
                else:
                    # Crossover
                    parent1 = parents[np.random.randint(len(parents))]
                    parent2 = parents[np.random.randint(len(parents))]
                    child = self._crossover_architectures(parent1, parent2)

                population.append(child)

        return self.best_architecture_

    def _sample_architecture(self) -> Architecture:
        """Sample random architecture."""
        num_layers = np.random.randint(1, self.max_layers + 1)
        layers = []

        for i in range(num_layers):
            # Dense layer
            units = np.random.choice([32, 64, 128, 256])
            units = min(units, self.max_units)

            layers.append({
                'type': 'dense',
                'units': units
            })

            # Optional dropout
            if np.random.rand() < 0.3:
                dropout_rate = np.random.choice([0.1, 0.2, 0.3, 0.5])
                layers.append({
                    'type': 'dropout',
                    'rate': dropout_rate
                })

        return Architecture(layers, self.input_dim, self.output_dim)

    def _evaluate_architecture(
        self,
        architecture: Architecture,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int
    ) -> float:
        """Evaluate architecture."""
        try:
            # Build model
            model = self.build_model(architecture)

            # Train
            model.fit(X_train, y_train)

            # Evaluate
            score = model.score(X_val, y_val)

            return score

        except Exception as e:
            logger.error(f"Error evaluating architecture: {e}")
            return -np.inf

    def _mutate_architecture(self, architecture: Architecture) -> Architecture:
        """Mutate architecture."""
        new_layers = architecture.layers.copy()

        mutation_type = np.random.choice(['add', 'remove', 'modify'])

        if mutation_type == 'add' and len(new_layers) < self.max_layers * 2:
            # Add layer
            units = np.random.choice([32, 64, 128, 256])
            new_layers.append({'type': 'dense', 'units': units})

        elif mutation_type == 'remove' and len(new_layers) > 1:
            # Remove layer
            idx = np.random.randint(len(new_layers))
            new_layers.pop(idx)

        elif mutation_type == 'modify' and new_layers:
            # Modify layer
            idx = np.random.randint(len(new_layers))
            if new_layers[idx]['type'] == 'dense':
                new_layers[idx]['units'] = np.random.choice([32, 64, 128, 256])

        return Architecture(new_layers, self.input_dim, self.output_dim)

    def _crossover_architectures(
        self,
        arch1: Architecture,
        arch2: Architecture
    ) -> Architecture:
        """Crossover two architectures."""
        # Take layers from both parents
        layers1 = arch1.layers
        layers2 = arch2.layers

        # Random split point
        if len(layers1) == 0:
            new_layers = layers2
        elif len(layers2) == 0:
            new_layers = layers1
        else:
            split1 = np.random.randint(0, len(layers1) + 1)
            split2 = np.random.randint(0, len(layers2) + 1)

            new_layers = layers1[:split1] + layers2[split2:]

        return Architecture(new_layers, self.input_dim, self.output_dim)


def main():
    """Example usage."""
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split

    print("=" * 80)
    print("Neural Architecture Search - Example")
    print("=" * 80)

    # Generate data
    X, y = make_classification(
        n_samples=500,
        n_features=20,
        n_informative=15,
        n_classes=3,
        random_state=42
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42
    )

    print(f"\nData:")
    print(f"  Train: {len(X_train)} samples")
    print(f"  Val:   {len(X_val)} samples")
    print(f"  Test:  {len(X_test)} samples")

    # Initialize NAS
    nas = NeuralArchitectureSearch(
        input_dim=X.shape[1],
        output_dim=len(np.unique(y)),
        max_layers=3,
        max_units=128,
        search_algorithm='random',
        task='classification'
    )

    # Search
    print("\n[1] Searching for best architecture...")
    best_arch = nas.search(
        X_train, y_train,
        X_val, y_val,
        num_trials=10,
        epochs_per_trial=10
    )

    print(f"\nBest architecture:")
    print(f"  Layers: {len(best_arch.layers)}")
    for i, layer in enumerate(best_arch.layers):
        if layer['type'] == 'dense':
            print(f"    {i+1}. Dense({layer['units']})")
        elif layer['type'] == 'dropout':
            print(f"    {i+1}. Dropout({layer['rate']})")

    print(f"\n  Validation score: {nas.best_score_:.4f}")

    # Build and test final model
    print("\n[2] Testing final model...")
    final_model = nas.build_model(best_arch)
    final_model.fit(X_train, y_train)
    test_score = final_model.score(X_test, y_test)

    print(f"  Test score: {test_score:.4f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
