"""Graph Attention Network (GAT) implementation."""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class GATLayer(nn.Module):
    """Single Graph Attention Layer."""

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        num_heads: int = 1,
        concat: bool = True,
        dropout: float = 0.6,
        alpha: float = 0.2
    ):
        """
        Initialize GAT layer.

        Args:
            input_dim: Input feature dimension
            output_dim: Output feature dimension per head
            num_heads: Number of attention heads
            concat: Whether to concatenate or average heads
            dropout: Dropout rate
            alpha: LeakyReLU negative slope
        """
        super(GATLayer, self).__init__()

        self.input_dim = input_dim
        self.output_dim = output_dim
        self.num_heads = num_heads
        self.concat = concat
        self.dropout = dropout
        self.alpha = alpha

        # Linear transformations (one per head)
        self.W = nn.Parameter(torch.zeros(size=(num_heads, input_dim, output_dim)))
        nn.init.xavier_uniform_(self.W.data, gain=1.414)

        # Attention parameters
        self.a = nn.Parameter(torch.zeros(size=(num_heads, 2 * output_dim, 1)))
        nn.init.xavier_uniform_(self.a.data, gain=1.414)

        self.leakyrelu = nn.LeakyReLU(self.alpha)

    def forward(
        self,
        x: torch.Tensor,
        adj: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Node features (N x input_dim)
            adj: Adjacency matrix (N x N)

        Returns:
            Output features (N x (output_dim * num_heads)) if concat
                         or (N x output_dim) if average
        """
        N = x.size(0)

        # Linear transformation: (num_heads, N, output_dim)
        h = torch.stack([torch.mm(x, self.W[i]) for i in range(self.num_heads)])

        # Compute attention coefficients
        # Self-attention on the nodes
        # (num_heads, N, N)
        a_input = self._prepare_attentional_mechanism_input(h)
        e = self.leakyrelu(torch.matmul(a_input, self.a).squeeze(3))

        # Mask attention for non-neighbors
        zero_vec = -9e15 * torch.ones_like(e)
        attention = torch.where(adj.unsqueeze(0) > 0, e, zero_vec)

        # Normalize attention coefficients
        attention = F.softmax(attention, dim=2)
        attention = F.dropout(attention, self.dropout, training=self.training)

        # Apply attention to features
        # (num_heads, N, output_dim)
        h_prime = torch.stack([
            torch.matmul(attention[i], h[i])
            for i in range(self.num_heads)
        ])

        # Concatenate or average heads
        if self.concat:
            # (N, num_heads * output_dim)
            return h_prime.transpose(0, 1).contiguous().view(N, -1)
        else:
            # (N, output_dim)
            return h_prime.mean(dim=0)

    def _prepare_attentional_mechanism_input(self, h: torch.Tensor) -> torch.Tensor:
        """
        Prepare input for attention mechanism.

        Args:
            h: Transformed features (num_heads, N, output_dim)

        Returns:
            Concatenated features for all pairs (num_heads, N, N, 2*output_dim)
        """
        num_heads, N, output_dim = h.shape

        # Repeat for all pairs
        # (num_heads, N, N, output_dim)
        h_repeat_1 = h.unsqueeze(2).repeat(1, 1, N, 1)
        h_repeat_2 = h.unsqueeze(1).repeat(1, N, 1, 1)

        # Concatenate
        # (num_heads, N, N, 2*output_dim)
        h_concat = torch.cat([h_repeat_1, h_repeat_2], dim=3)

        return h_concat


class GAT(nn.Module):
    """
    Graph Attention Network.

    Implements multi-head attention for graph neural networks.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        num_heads: int = 8,
        dropout: float = 0.6,
        alpha: float = 0.2
    ):
        """
        Initialize GAT.

        Args:
            input_dim: Input feature dimension
            hidden_dim: Hidden dimension per head
            output_dim: Output dimension
            num_heads: Number of attention heads
            dropout: Dropout rate
            alpha: LeakyReLU negative slope
        """
        super(GAT, self).__init__()

        self.dropout = dropout

        # First layer: multi-head attention
        self.layer1 = GATLayer(
            input_dim=input_dim,
            output_dim=hidden_dim,
            num_heads=num_heads,
            concat=True,
            dropout=dropout,
            alpha=alpha
        )

        # Output layer: single-head attention
        self.layer2 = GATLayer(
            input_dim=hidden_dim * num_heads,
            output_dim=output_dim,
            num_heads=1,
            concat=False,
            dropout=dropout,
            alpha=alpha
        )

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.to(self.device)

        logger.info(f"Initialized GAT: {input_dim} → {hidden_dim}x{num_heads} → {output_dim}")

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Node features
            adj: Adjacency matrix

        Returns:
            Output logits
        """
        # First layer
        x = F.dropout(x, self.dropout, training=self.training)
        x = self.layer1(x, adj)
        x = F.elu(x)

        # Output layer
        x = F.dropout(x, self.dropout, training=self.training)
        x = self.layer2(x, adj)

        return x

    def fit(
        self,
        adj: np.ndarray,
        features: np.ndarray,
        labels: np.ndarray,
        train_mask: np.ndarray,
        val_mask: Optional[np.ndarray] = None,
        epochs: int = 200,
        lr: float = 0.005,
        weight_decay: float = 5e-4
    ) -> 'GAT':
        """
        Train GAT.

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
        logger.info(f"Training GAT for {epochs} epochs")

        # Add self-loops
        adj = adj + np.eye(adj.shape[0])

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

            # Forward pass
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

        # Add self-loops
        adj = adj + np.eye(adj.shape[0])

        # Convert to tensors
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


def main():
    """Example usage."""
    # Generate synthetic graph
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

    # Labels with structure
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
    print("GAT - Example")
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

    # Initialize GAT
    print("\n[1] Training GAT...")

    model = GAT(
        input_dim=n_features,
        hidden_dim=8,
        output_dim=n_classes,
        num_heads=8,
        dropout=0.6
    )

    # Train
    model.fit(
        adj=adj,
        features=features,
        labels=labels,
        train_mask=train_mask,
        val_mask=val_mask,
        epochs=100,
        lr=0.005
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

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
