"""GraphSAGE implementation for inductive learning."""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class MeanAggregator(nn.Module):
    """Mean aggregator for GraphSAGE."""

    def forward(self, neighbor_features: torch.Tensor) -> torch.Tensor:
        """
        Aggregate neighbor features by taking mean.

        Args:
            neighbor_features: Features of neighbors (batch_size, num_neighbors, feature_dim)

        Returns:
            Aggregated features (batch_size, feature_dim)
        """
        return neighbor_features.mean(dim=1)


class PoolAggregator(nn.Module):
    """Pooling aggregator for GraphSAGE."""

    def __init__(self, input_dim: int, hidden_dim: int):
        """
        Initialize pooling aggregator.

        Args:
            input_dim: Input feature dimension
            hidden_dim: Hidden dimension for MLP
        """
        super(PoolAggregator, self).__init__()
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )

    def forward(self, neighbor_features: torch.Tensor) -> torch.Tensor:
        """
        Aggregate by max pooling after MLP.

        Args:
            neighbor_features: Features of neighbors

        Returns:
            Aggregated features
        """
        # Apply MLP
        h = self.mlp(neighbor_features)

        # Max pool
        return h.max(dim=1)[0]


class GraphSAGELayer(nn.Module):
    """Single GraphSAGE layer."""

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        aggregator: str = 'mean',
        dropout: float = 0.0
    ):
        """
        Initialize GraphSAGE layer.

        Args:
            input_dim: Input feature dimension
            output_dim: Output feature dimension
            aggregator: Aggregator type ('mean' or 'pool')
            dropout: Dropout rate
        """
        super(GraphSAGELayer, self).__init__()

        self.input_dim = input_dim
        self.output_dim = output_dim
        self.dropout = dropout

        # Aggregator
        if aggregator == 'mean':
            self.aggregator = MeanAggregator()
        elif aggregator == 'pool':
            self.aggregator = PoolAggregator(input_dim, output_dim)
        else:
            raise ValueError(f"Unknown aggregator: {aggregator}")

        # Linear transformation for concatenated features
        self.linear = nn.Linear(2 * input_dim, output_dim)

    def forward(
        self,
        self_features: torch.Tensor,
        neighbor_features: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            self_features: Features of target nodes (batch_size, input_dim)
            neighbor_features: Features of neighbors (batch_size, num_neighbors, input_dim)

        Returns:
            Output features (batch_size, output_dim)
        """
        # Aggregate neighbor features
        aggregated = self.aggregator(neighbor_features)

        # Concatenate self and aggregated neighbor features
        combined = torch.cat([self_features, aggregated], dim=1)

        # Apply linear transformation
        output = self.linear(combined)

        # Normalize
        output = F.normalize(output, p=2, dim=1)

        return output


class GraphSAGE(nn.Module):
    """
    GraphSAGE model for inductive learning on graphs.

    Implements sampling and aggregation for scalable graph learning.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        num_layers: int = 2,
        aggregator: str = 'mean',
        dropout: float = 0.5,
        num_samples: int = 10
    ):
        """
        Initialize GraphSAGE.

        Args:
            input_dim: Input feature dimension
            hidden_dim: Hidden dimension
            output_dim: Output dimension
            num_layers: Number of layers
            aggregator: Aggregator type
            dropout: Dropout rate
            num_samples: Number of neighbors to sample per layer
        """
        super(GraphSAGE, self).__init__()

        self.num_layers = num_layers
        self.dropout = dropout
        self.num_samples = num_samples

        # Build layers
        self.layers = nn.ModuleList()

        # First layer
        self.layers.append(GraphSAGELayer(input_dim, hidden_dim, aggregator, dropout))

        # Hidden layers
        for _ in range(num_layers - 2):
            self.layers.append(GraphSAGELayer(hidden_dim, hidden_dim, aggregator, dropout))

        # Output layer
        self.layers.append(GraphSAGELayer(hidden_dim, output_dim, aggregator, dropout))

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.to(self.device)

        logger.info(f"Initialized GraphSAGE: {input_dim} → {hidden_dim} → {output_dim} "
                   f"({num_layers} layers, {aggregator} aggregator)")

    def forward(
        self,
        features: torch.Tensor,
        adj: torch.Tensor,
        nodes: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            features: Node features (N x input_dim)
            adj: Adjacency matrix (N x N)
            nodes: Target nodes (optional, for mini-batch)

        Returns:
            Output features
        """
        if nodes is None:
            nodes = torch.arange(features.size(0), device=self.device)

        # Sample neighbors for each layer
        neighbor_samples = self._sample_neighbors(adj, nodes, self.num_layers)

        # Forward through layers
        h = features

        for layer_idx, layer in enumerate(self.layers):
            # Get neighbors for this layer
            neighbors = neighbor_samples[layer_idx]

            # Get features for target nodes and their neighbors
            self_feats = h[nodes]
            neighbor_feats = h[neighbors]  # (batch_size, num_samples, feature_dim)

            # Apply layer
            h_new = layer(self_feats, neighbor_feats)

            # Dropout
            h_new = F.dropout(h_new, p=self.dropout, training=self.training)

            # Update features for next layer
            h = h.clone()
            h[nodes] = h_new

        return h[nodes]

    def fit(
        self,
        adj: np.ndarray,
        features: np.ndarray,
        labels: np.ndarray,
        train_mask: np.ndarray,
        val_mask: Optional[np.ndarray] = None,
        epochs: int = 200,
        lr: float = 0.01,
        weight_decay: float = 5e-4
    ) -> 'GraphSAGE':
        """
        Train GraphSAGE.

        Args:
            adj: Adjacency matrix
            features: Node features
            labels: Node labels
            train_mask: Training mask
            val_mask: Validation mask
            epochs: Number of epochs
            lr: Learning rate
            weight_decay: Weight decay

        Returns:
            self: Trained model
        """
        logger.info(f"Training GraphSAGE for {epochs} epochs")

        # Convert to tensors
        adj = torch.FloatTensor(adj).to(self.device)
        features = torch.FloatTensor(features).to(self.device)
        labels = torch.LongTensor(labels).to(self.device)
        train_mask = torch.BoolTensor(train_mask).to(self.device)

        if val_mask is not None:
            val_mask = torch.BoolTensor(val_mask).to(self.device)

        # Optimizer
        optimizer = optim.Adam(self.parameters(), lr=lr, weight_decay=weight_decay)

        # Training loop
        best_val_acc = 0.0

        for epoch in range(epochs):
            self.train()
            optimizer.zero_grad()

            # Forward
            logits = self.forward(features, adj)

            # Loss
            loss = F.cross_entropy(logits[train_mask], labels[train_mask])

            # Backward
            loss.backward()
            optimizer.step()

            # Validation
            if val_mask is not None and epoch % 10 == 0:
                self.eval()
                with torch.no_grad():
                    val_logits = self.forward(features, adj)
                    val_preds = val_logits.argmax(dim=1)
                    val_acc = (val_preds[val_mask] == labels[val_mask]).float().mean().item()

                    if val_acc > best_val_acc:
                        best_val_acc = val_acc

                logger.info(f"Epoch {epoch:3d}: Loss={loss.item():.4f}, "
                           f"Val Acc={val_acc:.4f}")

        logger.info(f"Training completed. Best val accuracy: {best_val_acc:.4f}")

        return self

    def predict(self, adj: np.ndarray, features: np.ndarray) -> np.ndarray:
        """
        Predict node labels.

        Args:
            adj: Adjacency matrix
            features: Node features

        Returns:
            Predicted labels
        """
        self.eval()

        adj = torch.FloatTensor(adj).to(self.device)
        features = torch.FloatTensor(features).to(self.device)

        with torch.no_grad():
            logits = self.forward(features, adj)
            preds = logits.argmax(dim=1)

        return preds.cpu().numpy()

    def evaluate(
        self,
        adj: np.ndarray,
        features: np.ndarray,
        labels: np.ndarray,
        mask: np.ndarray
    ) -> float:
        """
        Evaluate model.

        Args:
            adj: Adjacency matrix
            features: Node features
            labels: True labels
            mask: Evaluation mask

        Returns:
            Accuracy
        """
        preds = self.predict(adj, features)
        accuracy = (preds[mask] == labels[mask]).mean()

        logger.info(f"Accuracy: {accuracy:.4f}")

        return float(accuracy)

    def _sample_neighbors(
        self,
        adj: torch.Tensor,
        nodes: torch.Tensor,
        num_layers: int
    ) -> List[torch.Tensor]:
        """
        Sample neighbors for each layer.

        Args:
            adj: Adjacency matrix
            nodes: Target nodes
            num_layers: Number of layers

        Returns:
            List of neighbor samples for each layer
        """
        samples = []
        current_nodes = nodes

        for _ in range(num_layers):
            # Get neighbors for current nodes
            neighbors = []

            for node in current_nodes:
                # Find neighbors
                node_neighbors = torch.nonzero(adj[node]).squeeze(1)

                if len(node_neighbors) == 0:
                    # No neighbors, sample self
                    sampled = torch.tensor([node] * self.num_samples, device=self.device)
                elif len(node_neighbors) < self.num_samples:
                    # Not enough neighbors, sample with replacement
                    indices = torch.randint(0, len(node_neighbors), (self.num_samples,), device=self.device)
                    sampled = node_neighbors[indices]
                else:
                    # Enough neighbors, sample without replacement
                    indices = torch.randperm(len(node_neighbors), device=self.device)[:self.num_samples]
                    sampled = node_neighbors[indices]

                neighbors.append(sampled)

            neighbors = torch.stack(neighbors)
            samples.append(neighbors)

            # Update current nodes for next layer
            current_nodes = neighbors.flatten().unique()

        return samples[::-1]  # Reverse for forward pass


def main():
    """Example usage."""
    np.random.seed(42)
    torch.manual_seed(42)

    n_nodes = 100
    n_features = 10
    n_classes = 3

    # Random graph
    adj = (np.random.rand(n_nodes, n_nodes) < 0.1).astype(float)
    adj = (adj + adj.T) / 2

    # Random features
    features = np.random.randn(n_nodes, n_features)

    # Labels
    labels = (features[:, 0] > 0).astype(int) + (features[:, 1] > 0).astype(int)
    labels = labels % n_classes

    # Masks
    n_train = int(0.6 * n_nodes)
    n_val = int(0.2 * n_nodes)

    indices = np.random.permutation(n_nodes)
    train_mask = np.zeros(n_nodes, dtype=bool)
    val_mask = np.zeros(n_nodes, dtype=bool)
    test_mask = np.zeros(n_nodes, dtype=bool)

    train_mask[indices[:n_train]] = True
    val_mask[indices[n_train:n_train + n_val]] = True
    test_mask[indices[n_train + n_val:]] = True

    print("=" * 80)
    print("GraphSAGE - Example")
    print("=" * 80)

    print(f"\nGraph:")
    print(f"  Nodes: {n_nodes}")
    print(f"  Edges: {adj.sum() / 2:.0f}")
    print(f"  Features: {n_features}")
    print(f"  Classes: {n_classes}")

    # Test different aggregators
    for aggregator in ['mean', 'pool']:
        print(f"\n[{aggregator.upper()}] Training GraphSAGE...")

        model = GraphSAGE(
            input_dim=n_features,
            hidden_dim=32,
            output_dim=n_classes,
            num_layers=2,
            aggregator=aggregator,
            dropout=0.5,
            num_samples=5
        )

        # Train
        model.fit(
            adj=adj,
            features=features,
            labels=labels,
            train_mask=train_mask,
            val_mask=val_mask,
            epochs=50,
            lr=0.01
        )

        # Evaluate
        test_acc = model.evaluate(adj, features, labels, test_mask)
        print(f"  Test Accuracy: {test_acc:.4f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
