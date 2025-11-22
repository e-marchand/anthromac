"""Neural collaborative filtering models."""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from typing import Optional, Tuple, Dict, List
import logging

logger = logging.getLogger(__name__)


class InteractionDataset(Dataset):
    """Dataset for user-item interactions."""

    def __init__(
        self,
        user_ids: np.ndarray,
        item_ids: np.ndarray,
        ratings: np.ndarray
    ):
        """
        Initialize dataset.

        Args:
            user_ids: Array of user IDs
            item_ids: Array of item IDs
            ratings: Array of ratings
        """
        self.user_ids = torch.LongTensor(user_ids)
        self.item_ids = torch.LongTensor(item_ids)
        self.ratings = torch.FloatTensor(ratings)

    def __len__(self) -> int:
        return len(self.user_ids)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.user_ids[idx], self.item_ids[idx], self.ratings[idx]


class NCFModel(nn.Module):
    """
    Neural Collaborative Filtering model.

    Combines Generalized Matrix Factorization (GMF) and Multi-Layer
    Perceptron (MLP) for collaborative filtering.

    Architecture:
        - GMF path: Element-wise product of user/item embeddings
        - MLP path: Multi-layer network on concatenated embeddings
        - Fusion: Concatenate GMF and MLP outputs, final prediction layer
    """

    def __init__(
        self,
        n_users: int,
        n_items: int,
        embedding_dim: int = 64,
        mlp_layers: List[int] = [128, 64, 32],
        dropout: float = 0.2
    ):
        """
        Initialize NCF model.

        Args:
            n_users: Number of users
            n_items: Number of items
            embedding_dim: Embedding dimension for GMF
            mlp_layers: Hidden layer sizes for MLP
            dropout: Dropout rate
        """
        super(NCFModel, self).__init__()

        self.n_users = n_users
        self.n_items = n_items
        self.embedding_dim = embedding_dim

        # GMF embeddings
        self.gmf_user_embedding = nn.Embedding(n_users, embedding_dim)
        self.gmf_item_embedding = nn.Embedding(n_items, embedding_dim)

        # MLP embeddings
        self.mlp_user_embedding = nn.Embedding(n_users, mlp_layers[0] // 2)
        self.mlp_item_embedding = nn.Embedding(n_items, mlp_layers[0] // 2)

        # MLP layers
        mlp_modules = []
        input_size = mlp_layers[0]

        for output_size in mlp_layers[1:]:
            mlp_modules.append(nn.Linear(input_size, output_size))
            mlp_modules.append(nn.ReLU())
            mlp_modules.append(nn.Dropout(dropout))
            input_size = output_size

        self.mlp = nn.Sequential(*mlp_modules)

        # Final prediction layer
        self.fc = nn.Linear(embedding_dim + mlp_layers[-1], 1)

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize model weights."""
        nn.init.normal_(self.gmf_user_embedding.weight, std=0.01)
        nn.init.normal_(self.gmf_item_embedding.weight, std=0.01)
        nn.init.normal_(self.mlp_user_embedding.weight, std=0.01)
        nn.init.normal_(self.mlp_item_embedding.weight, std=0.01)

        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    module.bias.data.zero_()

    def forward(
        self,
        user_ids: torch.Tensor,
        item_ids: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            user_ids: User ID tensor
            item_ids: Item ID tensor

        Returns:
            Predicted ratings
        """
        # GMF path
        gmf_user_emb = self.gmf_user_embedding(user_ids)
        gmf_item_emb = self.gmf_item_embedding(item_ids)
        gmf_output = gmf_user_emb * gmf_item_emb

        # MLP path
        mlp_user_emb = self.mlp_user_embedding(user_ids)
        mlp_item_emb = self.mlp_item_embedding(item_ids)
        mlp_input = torch.cat([mlp_user_emb, mlp_item_emb], dim=-1)
        mlp_output = self.mlp(mlp_input)

        # Fusion
        fusion = torch.cat([gmf_output, mlp_output], dim=-1)
        prediction = self.fc(fusion)

        return prediction.squeeze()


class NCFRecommender:
    """
    Neural Collaborative Filtering recommender.

    Wrapper around NCF model for training and inference.
    """

    def __init__(
        self,
        embedding_dim: int = 64,
        mlp_layers: List[int] = [128, 64, 32],
        dropout: float = 0.2,
        learning_rate: float = 0.001,
        batch_size: int = 256,
        epochs: int = 20,
        device: str = 'auto'
    ):
        """
        Initialize NCF recommender.

        Args:
            embedding_dim: Embedding dimension
            mlp_layers: MLP hidden layer sizes
            dropout: Dropout rate
            learning_rate: Learning rate
            batch_size: Batch size
            epochs: Number of training epochs
            device: Device ('cuda', 'cpu', or 'auto')
        """
        self.embedding_dim = embedding_dim
        self.mlp_layers = mlp_layers
        self.dropout = dropout
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs

        # Set device
        if device == 'auto':
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)

        self.model = None
        self.user_id_map = {}
        self.item_id_map = {}
        self.reverse_user_map = {}
        self.reverse_item_map = {}

        logger.info(f"Initialized NCF on {self.device}")

    def fit(
        self,
        interactions: pd.DataFrame,
        user_col: str = 'user_id',
        item_col: str = 'item_id',
        rating_col: str = 'rating',
        validation_split: float = 0.2
    ) -> 'NCFRecommender':
        """
        Train the NCF model.

        Args:
            interactions: DataFrame with user-item interactions
            user_col: Name of user ID column
            item_col: Name of item ID column
            rating_col: Name of rating column
            validation_split: Validation split ratio

        Returns:
            self: Trained model
        """
        logger.info(f"Training NCF on {len(interactions)} interactions")

        # Create mappings
        unique_users = interactions[user_col].unique()
        unique_items = interactions[item_col].unique()

        self.user_id_map = {uid: idx for idx, uid in enumerate(unique_users)}
        self.item_id_map = {iid: idx for idx, iid in enumerate(unique_items)}
        self.reverse_user_map = {idx: uid for uid, idx in self.user_id_map.items()}
        self.reverse_item_map = {idx: iid for iid, idx in self.item_id_map.items()}

        n_users = len(unique_users)
        n_items = len(unique_items)

        # Encode IDs
        user_indices = interactions[user_col].map(self.user_id_map).values
        item_indices = interactions[item_col].map(self.item_id_map).values
        ratings = interactions[rating_col].values

        # Normalize ratings to [0, 1]
        ratings = (ratings - ratings.min()) / (ratings.max() - ratings.min() + 1e-8)

        # Train/validation split
        n_samples = len(user_indices)
        indices = np.arange(n_samples)
        np.random.shuffle(indices)

        split_idx = int(n_samples * (1 - validation_split))
        train_indices = indices[:split_idx]
        val_indices = indices[split_idx:]

        # Create datasets
        train_dataset = InteractionDataset(
            user_indices[train_indices],
            item_indices[train_indices],
            ratings[train_indices]
        )

        val_dataset = InteractionDataset(
            user_indices[val_indices],
            item_indices[val_indices],
            ratings[val_indices]
        )

        train_loader = DataLoader(
            train_dataset,
            batch_size=self.batch_size,
            shuffle=True
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=self.batch_size,
            shuffle=False
        )

        # Initialize model
        self.model = NCFModel(
            n_users=n_users,
            n_items=n_items,
            embedding_dim=self.embedding_dim,
            mlp_layers=self.mlp_layers,
            dropout=self.dropout
        ).to(self.device)

        # Setup training
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)

        # Training loop
        best_val_loss = float('inf')

        for epoch in range(self.epochs):
            # Training
            self.model.train()
            train_loss = 0.0

            for user_ids, item_ids, ratings in train_loader:
                user_ids = user_ids.to(self.device)
                item_ids = item_ids.to(self.device)
                ratings = ratings.to(self.device)

                optimizer.zero_grad()
                predictions = self.model(user_ids, item_ids)
                loss = criterion(predictions, ratings)

                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            train_loss /= len(train_loader)

            # Validation
            self.model.eval()
            val_loss = 0.0

            with torch.no_grad():
                for user_ids, item_ids, ratings in val_loader:
                    user_ids = user_ids.to(self.device)
                    item_ids = item_ids.to(self.device)
                    ratings = ratings.to(self.device)

                    predictions = self.model(user_ids, item_ids)
                    loss = criterion(predictions, ratings)

                    val_loss += loss.item()

            val_loss /= len(val_loader)

            if val_loss < best_val_loss:
                best_val_loss = val_loss

            if (epoch + 1) % 5 == 0:
                logger.info(
                    f"Epoch {epoch + 1}/{self.epochs} - "
                    f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}"
                )

        logger.info(f"Training completed. Best val loss: {best_val_loss:.4f}")
        return self

    def predict(
        self,
        user_id: int,
        item_id: int
    ) -> float:
        """
        Predict rating for a user-item pair.

        Args:
            user_id: User ID
            item_id: Item ID

        Returns:
            Predicted rating
        """
        if user_id not in self.user_id_map or item_id not in self.item_id_map:
            return 0.0

        user_idx = self.user_id_map[user_id]
        item_idx = self.item_id_map[item_id]

        self.model.eval()
        with torch.no_grad():
            user_tensor = torch.LongTensor([user_idx]).to(self.device)
            item_tensor = torch.LongTensor([item_idx]).to(self.device)

            prediction = self.model(user_tensor, item_tensor)

        return float(prediction.cpu().numpy()[0])

    def recommend(
        self,
        user_id: int,
        n: int = 10,
        filter_seen: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Generate top-N recommendations for a user.

        Args:
            user_id: User ID
            n: Number of recommendations
            filter_seen: Array of item IDs to filter out

        Returns:
            Array of recommended item IDs
        """
        if user_id not in self.user_id_map:
            return np.array([])

        user_idx = self.user_id_map[user_id]
        n_items = len(self.item_id_map)

        # Predict scores for all items
        self.model.eval()
        with torch.no_grad():
            user_tensor = torch.LongTensor([user_idx] * n_items).to(self.device)
            item_tensor = torch.LongTensor(list(range(n_items))).to(self.device)

            scores = self.model(user_tensor, item_tensor).cpu().numpy()

        # Filter seen items
        if filter_seen is not None:
            seen_indices = [
                self.item_id_map[iid]
                for iid in filter_seen
                if iid in self.item_id_map
            ]
            scores[seen_indices] = -np.inf

        # Get top N
        top_indices = np.argsort(-scores)[:n]
        top_items = np.array([self.reverse_item_map[idx] for idx in top_indices])

        return top_items


def main():
    """Example usage of NCF recommender."""
    # Generate sample data
    np.random.seed(42)
    torch.manual_seed(42)

    n_users = 1000
    n_items = 500
    n_interactions = 10000

    interactions = pd.DataFrame({
        'user_id': np.random.randint(0, n_users, n_interactions),
        'item_id': np.random.randint(0, n_items, n_interactions),
        'rating': np.random.randint(1, 6, n_interactions)
    })

    interactions = interactions.groupby(['user_id', 'item_id'])['rating'].mean().reset_index()

    print("=" * 80)
    print("NCF Recommender - Complete Example")
    print("=" * 80)

    # Initialize and train
    print("\n[1] Training NCF model...")
    ncf = NCFRecommender(
        embedding_dim=64,
        mlp_layers=[128, 64, 32],
        epochs=20,
        batch_size=256
    )
    ncf.fit(interactions, validation_split=0.2)

    # Get recommendations
    print("\n[2] Generating recommendations...")
    test_user = 5
    recommendations = ncf.recommend(test_user, n=10)

    print(f"\nTop 10 recommendations for user {test_user}:")
    for rank, item_id in enumerate(recommendations, 1):
        score = ncf.predict(test_user, item_id)
        print(f"  {rank}. Item {item_id} (score: {score:.3f})")

    print("\n" + "=" * 80)
    print("Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
