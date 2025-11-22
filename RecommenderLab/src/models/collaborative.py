"""Collaborative filtering models for recommendations."""

import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict, Any
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


class ALSRecommender:
    """
    Alternating Least Squares (ALS) collaborative filtering.

    Matrix factorization approach that decomposes the user-item
    interaction matrix into user and item latent factor matrices.

    Attributes:
        n_factors: Number of latent factors
        regularization: L2 regularization parameter
        iterations: Number of ALS iterations
        user_factors: Learned user factor matrix
        item_factors: Learned item factor matrix
    """

    def __init__(
        self,
        n_factors: int = 50,
        regularization: float = 0.01,
        iterations: int = 15,
        alpha: float = 40.0,
        random_state: int = 42
    ):
        """
        Initialize ALS recommender.

        Args:
            n_factors: Number of latent factors
            regularization: L2 regularization parameter
            iterations: Number of training iterations
            alpha: Confidence parameter for implicit feedback
            random_state: Random seed
        """
        self.n_factors = n_factors
        self.regularization = regularization
        self.iterations = iterations
        self.alpha = alpha
        self.random_state = random_state

        self.user_factors = None
        self.item_factors = None
        self.user_id_map = {}
        self.item_id_map = {}
        self.reverse_user_map = {}
        self.reverse_item_map = {}
        self.interaction_matrix = None

        np.random.seed(random_state)

        logger.info(f"Initialized ALS with {n_factors} factors, {iterations} iterations")

    def fit(
        self,
        interactions: pd.DataFrame,
        user_col: str = 'user_id',
        item_col: str = 'item_id',
        rating_col: str = 'rating',
        implicit: bool = False
    ) -> 'ALSRecommender':
        """
        Train the ALS model.

        Args:
            interactions: DataFrame with user-item interactions
            user_col: Name of user ID column
            item_col: Name of item ID column
            rating_col: Name of rating column
            implicit: Whether to use implicit feedback formulation

        Returns:
            self: Trained model
        """
        logger.info(f"Training ALS on {len(interactions)} interactions")

        # Create mappings
        unique_users = interactions[user_col].unique()
        unique_items = interactions[item_col].unique()

        self.user_id_map = {uid: idx for idx, uid in enumerate(unique_users)}
        self.item_id_map = {iid: idx for idx, iid in enumerate(unique_items)}
        self.reverse_user_map = {idx: uid for uid, idx in self.user_id_map.items()}
        self.reverse_item_map = {idx: iid for iid, idx in self.item_id_map.items()}

        # Build interaction matrix
        n_users = len(unique_users)
        n_items = len(unique_items)

        user_indices = interactions[user_col].map(self.user_id_map).values
        item_indices = interactions[item_col].map(self.item_id_map).values
        ratings = interactions[rating_col].values

        # Convert to implicit feedback if needed
        if implicit:
            # Confidence: c = 1 + alpha * r
            confidence = 1 + self.alpha * ratings
            # Preference: p = 1 if r > 0 else 0
            ratings = (ratings > 0).astype(float)
        else:
            confidence = None

        self.interaction_matrix = csr_matrix(
            (ratings, (user_indices, item_indices)),
            shape=(n_users, n_items)
        )

        # Initialize factor matrices
        self.user_factors = np.random.normal(
            0, 0.1, (n_users, self.n_factors)
        )
        self.item_factors = np.random.normal(
            0, 0.1, (n_items, self.n_factors)
        )

        # ALS iterations
        for iteration in range(self.iterations):
            # Fix item factors, solve for user factors
            self._als_step(
                self.interaction_matrix,
                self.user_factors,
                self.item_factors,
                confidence,
                implicit
            )

            # Fix user factors, solve for item factors
            self._als_step(
                self.interaction_matrix.T,
                self.item_factors,
                self.user_factors,
                confidence,
                implicit
            )

            if (iteration + 1) % 5 == 0:
                loss = self._compute_loss(confidence, implicit)
                logger.info(f"Iteration {iteration + 1}/{self.iterations}, Loss: {loss:.4f}")

        logger.info("ALS training completed")
        return self

    def _als_step(
        self,
        ratings: csr_matrix,
        solve_vecs: np.ndarray,
        fixed_vecs: np.ndarray,
        confidence: Optional[np.ndarray],
        implicit: bool
    ):
        """Perform one ALS step."""
        YtY = fixed_vecs.T.dot(fixed_vecs)
        regularization_matrix = self.regularization * np.eye(self.n_factors)

        for u in range(ratings.shape[0]):
            # Get items rated by this user
            start_idx = ratings.indptr[u]
            end_idx = ratings.indptr[u + 1]

            if start_idx == end_idx:
                continue

            item_indices = ratings.indices[start_idx:end_idx]
            item_ratings = ratings.data[start_idx:end_idx]

            if implicit and confidence is not None:
                # Weighted ALS for implicit feedback
                item_confidence = confidence[start_idx:end_idx]
                Y = fixed_vecs[item_indices]

                # YtCY + lambda*I
                YtCY = Y.T.dot(np.diag(item_confidence)).dot(Y)
                A = YtCY + regularization_matrix

                # YtCp
                b = Y.T.dot(item_confidence * item_ratings)
            else:
                # Standard ALS for explicit feedback
                Y = fixed_vecs[item_indices]
                A = YtY + regularization_matrix
                b = Y.T.dot(item_ratings)

            # Solve for user factors
            solve_vecs[u] = np.linalg.solve(A, b)

    def _compute_loss(
        self,
        confidence: Optional[np.ndarray],
        implicit: bool
    ) -> float:
        """Compute reconstruction loss."""
        predicted = self.user_factors.dot(self.item_factors.T)

        # Convert to dense for loss calculation (expensive, only for monitoring)
        actual = self.interaction_matrix.toarray()

        diff = actual - predicted
        mse = np.mean(diff ** 2)

        # Add regularization term
        reg_term = self.regularization * (
            np.sum(self.user_factors ** 2) + np.sum(self.item_factors ** 2)
        )

        return mse + reg_term

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

        score = np.dot(
            self.user_factors[user_idx],
            self.item_factors[item_idx]
        )

        return float(score)

    def recommend(
        self,
        user_id: int,
        n: int = 10,
        filter_seen: bool = True
    ) -> np.ndarray:
        """
        Generate top-N recommendations for a user.

        Args:
            user_id: User ID
            n: Number of recommendations
            filter_seen: Whether to filter already seen items

        Returns:
            Array of item IDs sorted by predicted score
        """
        if user_id not in self.user_id_map:
            logger.warning(f"Unknown user {user_id}, returning popular items")
            # Return most popular items
            item_popularity = np.array(self.interaction_matrix.sum(axis=0)).flatten()
            top_items = np.argsort(-item_popularity)[:n]
            return np.array([self.reverse_item_map[idx] for idx in top_items])

        user_idx = self.user_id_map[user_id]

        # Compute scores for all items
        scores = self.user_factors[user_idx].dot(self.item_factors.T)

        # Filter seen items if requested
        if filter_seen:
            seen_items = self.interaction_matrix[user_idx].indices
            scores[seen_items] = -np.inf

        # Get top N items
        top_indices = np.argsort(-scores)[:n]

        # Map back to original item IDs
        top_items = np.array([self.reverse_item_map[idx] for idx in top_indices])

        return top_items

    def similar_items(
        self,
        item_id: int,
        n: int = 10
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Find similar items based on item factors.

        Args:
            item_id: Item ID
            n: Number of similar items

        Returns:
            Tuple of (item_ids, similarity_scores)
        """
        if item_id not in self.item_id_map:
            return np.array([]), np.array([])

        item_idx = self.item_id_map[item_id]

        # Compute cosine similarity with all items
        item_vec = self.item_factors[item_idx].reshape(1, -1)
        similarities = cosine_similarity(item_vec, self.item_factors)[0]

        # Exclude the item itself
        similarities[item_idx] = -1

        # Get top N
        top_indices = np.argsort(-similarities)[:n]
        top_similarities = similarities[top_indices]

        # Map back to original item IDs
        top_items = np.array([self.reverse_item_map[idx] for idx in top_indices])

        return top_items, top_similarities

    def similar_users(
        self,
        user_id: int,
        n: int = 10
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Find similar users based on user factors.

        Args:
            user_id: User ID
            n: Number of similar users

        Returns:
            Tuple of (user_ids, similarity_scores)
        """
        if user_id not in self.user_id_map:
            return np.array([]), np.array([])

        user_idx = self.user_id_map[user_id]

        # Compute cosine similarity with all users
        user_vec = self.user_factors[user_idx].reshape(1, -1)
        similarities = cosine_similarity(user_vec, self.user_factors)[0]

        # Exclude the user itself
        similarities[user_idx] = -1

        # Get top N
        top_indices = np.argsort(-similarities)[:n]
        top_similarities = similarities[top_indices]

        # Map back to original user IDs
        top_users = np.array([self.reverse_user_map[idx] for idx in top_indices])

        return top_users, top_similarities


def main():
    """Example usage of ALS recommender."""
    # Generate sample data
    np.random.seed(42)

    # Simulate user-item interactions
    n_users = 1000
    n_items = 500
    n_interactions = 10000

    interactions = pd.DataFrame({
        'user_id': np.random.randint(0, n_users, n_interactions),
        'item_id': np.random.randint(0, n_items, n_interactions),
        'rating': np.random.randint(1, 6, n_interactions)
    })

    # Remove duplicates
    interactions = interactions.groupby(['user_id', 'item_id'])['rating'].mean().reset_index()

    print("=" * 80)
    print("ALS Recommender - Complete Example")
    print("=" * 80)

    # Initialize and train
    print("\n[1] Training ALS model...")
    als = ALSRecommender(
        n_factors=50,
        regularization=0.01,
        iterations=15
    )
    als.fit(interactions)

    # Get recommendations
    print("\n[2] Generating recommendations...")
    test_user = 5
    recommendations = als.recommend(test_user, n=10)

    print(f"\nTop 10 recommendations for user {test_user}:")
    for rank, item_id in enumerate(recommendations, 1):
        score = als.predict(test_user, item_id)
        print(f"  {rank}. Item {item_id} (score: {score:.3f})")

    # Find similar items
    print("\n[3] Finding similar items...")
    test_item = 100
    similar_items, similarities = als.similar_items(test_item, n=5)

    print(f"\nItems similar to item {test_item}:")
    for item_id, sim in zip(similar_items, similarities):
        print(f"  Item {item_id} (similarity: {sim:.3f})")

    # Find similar users
    print("\n[4] Finding similar users...")
    similar_users, similarities = als.similar_users(test_user, n=5)

    print(f"\nUsers similar to user {test_user}:")
    for user_id, sim in zip(similar_users, similarities):
        print(f"  User {user_id} (similarity: {sim:.3f})")

    print("\n" + "=" * 80)
    print("Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
