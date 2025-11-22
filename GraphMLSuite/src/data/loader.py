"""Dataset loaders for common graph datasets."""

import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def load_cora() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load Cora citation network dataset (synthetic version).

    Returns:
        Tuple of (adjacency, features, labels, train_mask, test_mask)
    """
    logger.info("Loading Cora dataset (synthetic)")

    n_nodes = 2708
    n_features = 1433
    n_classes = 7

    # Generate synthetic data
    np.random.seed(42)

    # Random adjacency (citation network is sparse)
    adj = (np.random.rand(n_nodes, n_nodes) < 0.01).astype(float)
    adj = (adj + adj.T) / 2  # Symmetric

    # Random features (bag of words)
    features = (np.random.rand(n_nodes, n_features) < 0.05).astype(float)

    # Random labels with structure
    labels = np.random.randint(0, n_classes, n_nodes)

    # Masks
    train_mask = np.zeros(n_nodes, dtype=bool)
    test_mask = np.zeros(n_nodes, dtype=bool)

    train_mask[:int(0.6 * n_nodes)] = True
    test_mask[int(0.8 * n_nodes):] = True

    logger.info(f"Loaded Cora: {n_nodes} nodes, {n_classes} classes")

    return adj, features, labels, train_mask, test_mask


def load_citeseer() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load Citeseer citation network dataset (synthetic version).

    Returns:
        Tuple of (adjacency, features, labels, train_mask, test_mask)
    """
    logger.info("Loading Citeseer dataset (synthetic)")

    n_nodes = 3327
    n_features = 3703
    n_classes = 6

    np.random.seed(42)

    adj = (np.random.rand(n_nodes, n_nodes) < 0.008).astype(float)
    adj = (adj + adj.T) / 2

    features = (np.random.rand(n_nodes, n_features) < 0.04).astype(float)
    labels = np.random.randint(0, n_classes, n_nodes)

    train_mask = np.zeros(n_nodes, dtype=bool)
    test_mask = np.zeros(n_nodes, dtype=bool)

    train_mask[:int(0.6 * n_nodes)] = True
    test_mask[int(0.8 * n_nodes):] = True

    logger.info(f"Loaded Citeseer: {n_nodes} nodes, {n_classes} classes")

    return adj, features, labels, train_mask, test_mask


def load_graph_dataset(name: str) -> Tuple[list, np.ndarray]:
    """
    Load graph classification dataset (synthetic version).

    Args:
        name: Dataset name ('MUTAG', 'PROTEINS', 'ENZYMES')

    Returns:
        Tuple of (list of Graph objects, labels)
    """
    from .graph import Graph

    logger.info(f"Loading {name} dataset (synthetic)")

    if name == 'MUTAG':
        n_graphs = 188
        avg_nodes = 18
    elif name == 'PROTEINS':
        n_graphs = 1113
        avg_nodes = 40
    elif name == 'ENZYMES':
        n_graphs = 600
        avg_nodes = 32
    else:
        raise ValueError(f"Unknown dataset: {name}")

    np.random.seed(42)

    graphs = []
    labels = []

    for i in range(n_graphs):
        # Random graph size
        n_nodes = int(avg_nodes + np.random.randn() * 5)
        n_nodes = max(5, n_nodes)

        # Random edges
        n_edges = int(n_nodes * 1.5)
        edges = []

        for _ in range(n_edges):
            src = np.random.randint(0, n_nodes)
            dst = np.random.randint(0, n_nodes)
            if src != dst:
                edges.append((src, dst))

        graph = Graph(edges=edges, num_nodes=n_nodes)
        graphs.append(graph)

        # Random label
        labels.append(np.random.randint(0, 2))

    labels = np.array(labels)

    logger.info(f"Loaded {name}: {n_graphs} graphs, {len(set(labels))} classes")

    return graphs, labels
