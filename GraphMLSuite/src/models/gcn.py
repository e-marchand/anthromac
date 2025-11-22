"""Graph Convolutional Network (GCN) implementation."""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class GCNLayer(nn.Module):
    """Single Graph Convolutional Layer."""

    def __init__(self, input_dim: int, output_dim: int, use_bias: bool = True):
        """
        Initialize GCN layer.

        Args:
            input_dim: Input feature dimension
            output_dim: Output feature dimension
            use_bias: Whether to use bias
        """
        super(GCNLayer, self).__init__()
        self.linear = nn.Linear(input_dim, output_dim, bias=use_bias)

    def forward(self, x: torch.Tensor, adj: torch.sparse.FloatTensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Node features (N x input_dim)
            adj: Normalized adjacency matrix (N x N, sparse)

        Returns:
            Output features (N x output_dim)
        """
        # Message passing: Ã @ X
        support = torch.sparse.mm(adj, x)

        # Linear transformation: Ã @ X @ W
        output = self.linear(support)

        return output


class GCN(nn.Module):
    """
    Graph Convolutional Network.

    Implements the GCN from Kipf & Welling (2017).
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        num_layers: int = 2,
        dropout: float = 0.5
    ):
        """
        Initialize GCN.

        Args:
            input_dim: Input feature dimension
            hidden_dim: Hidden layer dimension
            output_dim: Output dimension (number of classes)
            num_layers: Number of GCN layers
            dropout: Dropout rate
        """
        super(GCN, self).__init__()

        self.num_layers = num_layers
        self.dropout = dropout

        # Build layers
        self.layers = nn.ModuleList()

        # First layer
        self.layers.append(GCNLayer(input_dim, hidden_dim))

        # Hidden layers
        for _ in range(num_layers - 2):
            self.layers.append(GCNLayer(hidden_dim, hidden_dim))

        # Output layer
        self.layers.append(GCNLayer(hidden_dim, output_dim))

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.to(self.device)

        logger.info(f"Initialized GCN: {input_dim} → {hidden_dim} → {output_dim} "
                   f"({num_layers} layers)")

    def forward(self, x: torch.Tensor, adj: torch.sparse.FloatTensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Node features
            adj: Normalized adjacency matrix

        Returns:
            Output logits
        """
        for i, layer in enumerate(self.layers[:-1]):
            x = layer(x, adj)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        # Output layer (no activation)
        x = self.layers[-1](x, adj)

        return x

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
    ) -> 'GCN':
        """
        Train GCN.

        Args:
            adj: Adjacency matrix
            features: Node features
            labels: Node labels
            train_mask: Training mask
            val_mask: Validation mask
            epochs: Number of epochs
            lr: Learning rate
            weight_decay: Weight decay (L2 regularization)

        Returns:
            self: Trained model
        """
        logger.info(f"Training GCN for {epochs} epochs")

        # Normalize adjacency matrix
        adj_norm = self._normalize_adj(adj)

        # Convert to tensors
        adj_norm = self._to_sparse_tensor(adj_norm).to(self.device)
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

            # Forward pass
            logits = self.forward(features, adj_norm)

            # Compute loss on training nodes
            loss = F.cross_entropy(logits[train_mask], labels[train_mask])

            # Backward pass
            loss.backward()
            optimizer.step()

            # Validation
            if val_mask is not None and epoch % 10 == 0:
                self.eval()
                with torch.no_grad():
                    val_logits = self.forward(features, adj_norm)
                    val_preds = val_logits.argmax(dim=1)
                    val_acc = (val_preds[val_mask] == labels[val_mask]).float().mean().item()

                    if val_acc > best_val_acc:
                        best_val_acc = val_acc

                logger.info(f"Epoch {epoch:3d}: Loss={loss.item():.4f}, "
                           f"Val Acc={val_acc:.4f}")

        logger.info(f"Training completed. Best val accuracy: {best_val_acc:.4f}")

        return self

    def predict(
        self,
        adj: np.ndarray,
        features: np.ndarray
    ) -> np.ndarray:
        """
        Predict node labels.

        Args:
            adj: Adjacency matrix
            features: Node features

        Returns:
            Predicted labels
        """
        self.eval()

        # Normalize adjacency
        adj_norm = self._normalize_adj(adj)

        # Convert to tensors
        adj_norm = self._to_sparse_tensor(adj_norm).to(self.device)
        features = torch.FloatTensor(features).to(self.device)

        with torch.no_grad():
            logits = self.forward(features, adj_norm)
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
        labels = labels[mask]
        preds = preds[mask]

        accuracy = (preds == labels).mean()

        logger.info(f"Accuracy: {accuracy:.4f}")

        return float(accuracy)

    def _normalize_adj(self, adj: np.ndarray) -> np.ndarray:
        """
        Normalize adjacency matrix: D^(-1/2) @ A @ D^(-1/2).

        Args:
            adj: Adjacency matrix

        Returns:
            Normalized adjacency matrix
        """
        # Add self-loops
        adj = adj + np.eye(adj.shape[0])

        # Compute degree matrix
        degree = np.array(adj.sum(axis=1)).flatten()
        degree_inv_sqrt = np.power(degree, -0.5)
        degree_inv_sqrt[np.isinf(degree_inv_sqrt)] = 0.

        # D^(-1/2) @ A @ D^(-1/2)
        degree_matrix = np.diag(degree_inv_sqrt)
        adj_normalized = degree_matrix @ adj @ degree_matrix

        return adj_normalized

    def _to_sparse_tensor(self, sparse_mx: np.ndarray) -> torch.sparse.FloatTensor:
        """Convert sparse matrix to sparse tensor."""
        # Convert to COO format
        import scipy.sparse as sp

        if not sp.issparse(sparse_mx):
            sparse_mx = sp.coo_matrix(sparse_mx)
        else:
            sparse_mx = sparse_mx.tocoo()

        indices = torch.LongTensor(np.vstack((sparse_mx.row, sparse_mx.col)))
        values = torch.FloatTensor(sparse_mx.data)
        shape = torch.Size(sparse_mx.shape)

        return torch.sparse.FloatTensor(indices, values, shape)


def main():
    """Example usage."""
    # Generate synthetic graph
    np.random.seed(42)
    torch.manual_seed(42)

    n_nodes = 100
    n_features = 10
    n_classes = 3

    # Random graph (Erdos-Renyi)
    adj = (np.random.rand(n_nodes, n_nodes) < 0.1).astype(float)
    adj = (adj + adj.T) / 2  # Symmetric

    # Random features
    features = np.random.randn(n_nodes, n_features)

    # Random labels (with some structure based on features)
    labels = (features[:, 0] > 0).astype(int) + (features[:, 1] > 0).astype(int)
    labels = labels % n_classes

    # Train/val/test masks
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
    print("GCN - Example")
    print("=" * 80)

    print(f"\nGraph:")
    print(f"  Nodes: {n_nodes}")
    print(f"  Edges: {adj.sum() / 2:.0f}")
    print(f"  Features: {n_features}")
    print(f"  Classes: {n_classes}")

    print(f"\nData split:")
    print(f"  Train: {train_mask.sum()}")
    print(f"  Val:   {val_mask.sum()}")
    print(f"  Test:  {test_mask.sum()}")

    # Initialize GCN
    print("\n[1] Training GCN...")

    model = GCN(
        input_dim=n_features,
        hidden_dim=32,
        output_dim=n_classes,
        num_layers=2,
        dropout=0.5
    )

    # Train
    model.fit(
        adj=adj,
        features=features,
        labels=labels,
        train_mask=train_mask,
        val_mask=val_mask,
        epochs=100,
        lr=0.01
    )

    # Evaluate
    print("\n[2] Evaluating...")

    train_acc = model.evaluate(adj, features, labels, train_mask)
    val_acc = model.evaluate(adj, features, labels, val_mask)
    test_acc = model.evaluate(adj, features, labels, test_mask)

    print(f"\nResults:")
    print(f"  Train Accuracy: {train_acc:.4f}")
    print(f"  Val Accuracy:   {val_acc:.4f}")
    print(f"  Test Accuracy:  {test_acc:.4f}")

    # Predict
    print("\n[3] Sample predictions:")
    preds = model.predict(adj, features)

    print("\n  Node | True | Pred")
    print("  " + "-" * 25)
    for i in range(min(10, n_nodes)):
        print(f"  {i:4d} | {labels[i]:4d} | {preds[i]:4d}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
