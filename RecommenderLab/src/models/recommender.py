"""Main recommender system interface."""

import numpy as np
import pandas as pd
from typing import List, Optional, Dict, Any, Union
import logging

from .collaborative import ALSRecommender
from .neural import NCFRecommender

logger = logging.getLogger(__name__)


class RecommenderSystem:
    """
    Unified interface for recommendation models.

    This class provides a common API for different recommendation algorithms,
    handling model loading, inference, and post-processing.

    Attributes:
        model_type: Type of model (als, ncf, two_tower, etc.)
        model_path: Path to saved model
        config: Model configuration
    """

    def __init__(
        self,
        model_type: str = 'ncf',
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the recommender system.

        Args:
            model_type: Type of recommendation model (als, ncf)
            model_path: Path to pre-trained model
            config: Configuration dictionary
        """
        self.model_type = model_type
        self.model_path = model_path
        self.config = config or {}

        self.model = None
        self.user_encoder = None
        self.item_encoder = None
        self.training_data = None
        self.user_item_matrix = None

        logger.info(f"Initialized RecommenderSystem with model_type={model_type}")

    def _initialize_model(self):
        """Initialize the model based on model_type."""
        if self.model_type == 'als':
            self.model = ALSRecommender(
                n_factors=self.config.get('n_factors', 50),
                regularization=self.config.get('regularization', 0.01),
                iterations=self.config.get('iterations', 15),
                alpha=self.config.get('alpha', 40.0)
            )
        elif self.model_type == 'ncf':
            self.model = NCFRecommender(
                embedding_dim=self.config.get('embedding_dim', 64),
                mlp_layers=self.config.get('mlp_layers', [128, 64, 32]),
                dropout=self.config.get('dropout', 0.2),
                learning_rate=self.config.get('learning_rate', 0.001),
                batch_size=self.config.get('batch_size', 256),
                epochs=self.config.get('epochs', 20)
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def load_model(self, path: str):
        """
        Load a pre-trained model.

        Args:
            path: Path to model file
        """
        logger.info(f"Loading model from {path}")
        # TODO: Implement model loading
        pass

    def fit(
        self,
        interactions: pd.DataFrame,
        user_features: Optional[pd.DataFrame] = None,
        item_features: Optional[pd.DataFrame] = None,
        **kwargs
    ):
        """
        Train the recommendation model.

        Args:
            interactions: User-item interaction data (must have 'user_id', 'item_id', 'rating')
            user_features: Optional user features
            item_features: Optional item features
            **kwargs: Additional training parameters

        Returns:
            self: Trained recommender
        """
        logger.info(f"Training {self.model_type} model")
        logger.info(f"Interactions shape: {interactions.shape}")

        # Store training data
        self.training_data = interactions

        # Initialize model if not already done
        if self.model is None:
            self._initialize_model()

        # Train the model
        self.model.fit(interactions, **kwargs)

        logger.info("Training completed")
        return self

    def recommend(
        self,
        user_id: Union[int, List[int]],
        n: int = 10,
        filter_seen: bool = True,
        diversity: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Union[List[Dict[str, Any]], Dict[int, List[Dict[str, Any]]]]:
        """
        Generate recommendations for user(s).

        Args:
            user_id: Single user ID or list of user IDs
            n: Number of recommendations
            filter_seen: Whether to filter already seen items
            diversity: Diversity parameter (0-1)
            context: Contextual information

        Returns:
            List of recommendations or dict of recommendations per user
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")

        # Handle batch recommendations
        if isinstance(user_id, list):
            return self._batch_recommend(user_id, n, filter_seen, diversity, context)

        logger.info(f"Generating {n} recommendations for user {user_id}")

        # Get seen items for filtering
        seen_items = None
        if filter_seen and self.training_data is not None:
            user_interactions = self.training_data[
                self.training_data['user_id'] == user_id
            ]
            seen_items = user_interactions['item_id'].values

        # Get recommendations from model
        if isinstance(self.model, ALSRecommender):
            recommended_items = self.model.recommend(user_id, n, filter_seen=filter_seen)
        elif isinstance(self.model, NCFRecommender):
            recommended_items = self.model.recommend(user_id, n, filter_seen=seen_items)
        else:
            recommended_items = np.array([])

        # Format recommendations
        recommendations = []
        for rank, item_id in enumerate(recommended_items, 1):
            score = self.model.predict(user_id, item_id)
            recommendations.append({
                'item_id': int(item_id),
                'score': float(score),
                'rank': rank
            })

        # Apply diversity if requested
        if diversity is not None:
            recommendations = self._apply_diversity(recommendations, diversity)

        return recommendations

    def _batch_recommend(
        self,
        user_ids: List[int],
        n: int,
        filter_seen: bool,
        diversity: Optional[float],
        context: Optional[Dict[str, Any]]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """Generate recommendations for multiple users."""
        logger.info(f"Batch recommendation for {len(user_ids)} users")

        results = {}
        for user_id in user_ids:
            results[user_id] = self.recommend(
                user_id=user_id,
                n=n,
                filter_seen=filter_seen,
                diversity=diversity,
                context=context
            )

        return results

    def predict_score(
        self,
        user_id: Union[int, List[int]],
        item_id: Union[int, List[int]]
    ) -> Union[float, np.ndarray]:
        """
        Predict score for user-item pair(s).

        Args:
            user_id: User ID or list of user IDs
            item_id: Item ID or list of item IDs

        Returns:
            Predicted score(s)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")

        # Handle single pair
        if isinstance(user_id, int) and isinstance(item_id, int):
            return self.model.predict(user_id, item_id)

        # Handle batch prediction
        if isinstance(user_id, list) and isinstance(item_id, list):
            scores = []
            for uid, iid in zip(user_id, item_id):
                scores.append(self.model.predict(uid, iid))
            return np.array(scores)

        raise ValueError("user_id and item_id must both be int or both be list")

    def similar_items(
        self,
        item_id: int,
        n: int = 10,
        method: str = 'embedding'
    ) -> List[Dict[str, Any]]:
        """
        Find items similar to a given item.

        Args:
            item_id: Item ID
            n: Number of similar items
            method: Similarity method ('embedding', 'collaborative', 'content')

        Returns:
            List of similar items with similarity scores
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")

        logger.info(f"Finding {n} items similar to {item_id}")

        # Only ALS has similar_items implementation
        if isinstance(self.model, ALSRecommender):
            similar_item_ids, similarities = self.model.similar_items(item_id, n)

            similar = []
            for iid, sim in zip(similar_item_ids, similarities):
                similar.append({
                    'item_id': int(iid),
                    'similarity': float(sim)
                })

            return similar
        else:
            # For neural models, would need to implement based on embeddings
            logger.warning(f"Similar items not implemented for {self.model_type}")
            return []

    def similar_users(
        self,
        user_id: int,
        n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find users similar to a given user.

        Args:
            user_id: User ID
            n: Number of similar users

        Returns:
            List of similar users with similarity scores
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")

        logger.info(f"Finding {n} users similar to {user_id}")

        # Only ALS has similar_users implementation
        if isinstance(self.model, ALSRecommender):
            similar_user_ids, similarities = self.model.similar_users(user_id, n)

            similar = []
            for uid, sim in zip(similar_user_ids, similarities):
                similar.append({
                    'user_id': int(uid),
                    'similarity': float(sim)
                })

            return similar
        else:
            logger.warning(f"Similar users not implemented for {self.model_type}")
            return []

    def _apply_diversity(
        self,
        recommendations: List[Dict[str, Any]],
        diversity: float
    ) -> List[Dict[str, Any]]:
        """
        Apply diversity to recommendations using MMR.

        Args:
            recommendations: List of recommendations
            diversity: Diversity parameter (0-1)

        Returns:
            Diversified recommendations
        """
        # TODO: Implement MMR or other diversity methods
        return recommendations

    def explain(
        self,
        user_id: int,
        item_id: int,
        method: str = 'feature_importance'
    ) -> Dict[str, Any]:
        """
        Generate explanation for a recommendation.

        Args:
            user_id: User ID
            item_id: Item ID
            method: Explanation method

        Returns:
            Explanation dictionary
        """
        logger.info(f"Generating explanation for user {user_id}, item {item_id}")

        # TODO: Implement explanation generation
        explanation = {
            'method': method,
            'reason': 'Popular with similar users',
            'confidence': 0.85
        }

        return explanation

    def evaluate(
        self,
        test_data: pd.DataFrame,
        metrics: Optional[List[str]] = None,
        k: int = 10
    ) -> Dict[str, float]:
        """
        Evaluate model performance.

        Args:
            test_data: Test interaction data (must have 'user_id', 'item_id')
            metrics: List of metrics to compute
            k: Cutoff for ranking metrics

        Returns:
            Dictionary of metric values
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")

        if metrics is None:
            metrics = ['precision', 'recall', 'ndcg', 'hit_rate']

        logger.info(f"Evaluating model on {len(test_data)} test samples")

        # Group test data by user
        test_by_user = test_data.groupby('user_id')['item_id'].apply(list).to_dict()

        results = {f'{metric}@{k}': [] for metric in metrics}

        # Evaluate for each user
        for user_id, true_items in test_by_user.items():
            try:
                # Get recommendations
                recs = self.recommend(user_id, n=k, filter_seen=True)
                predicted_items = [rec['item_id'] for rec in recs]

                # Calculate metrics
                if 'precision' in metrics:
                    precision = len(set(predicted_items) & set(true_items)) / len(predicted_items) if predicted_items else 0
                    results[f'precision@{k}'].append(precision)

                if 'recall' in metrics:
                    recall = len(set(predicted_items) & set(true_items)) / len(true_items) if true_items else 0
                    results[f'recall@{k}'].append(recall)

                if 'hit_rate' in metrics:
                    hit = 1.0 if any(item in true_items for item in predicted_items) else 0.0
                    results[f'hit_rate@{k}'].append(hit)

                if 'ndcg' in metrics:
                    # Calculate NDCG
                    dcg = 0.0
                    for i, item in enumerate(predicted_items, 1):
                        if item in true_items:
                            dcg += 1.0 / np.log2(i + 1)

                    # Ideal DCG
                    idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(true_items), k)))
                    ndcg = dcg / idcg if idcg > 0 else 0
                    results[f'ndcg@{k}'].append(ndcg)

            except Exception as e:
                logger.warning(f"Error evaluating user {user_id}: {e}")
                continue

        # Average metrics
        final_results = {}
        for metric_name, values in results.items():
            if values:
                final_results[metric_name] = float(np.mean(values))
            else:
                final_results[metric_name] = 0.0

        logger.info(f"Evaluation results: {final_results}")
        return final_results

    def save(self, path: str):
        """
        Save the trained model.

        Args:
            path: Path to save model
        """
        logger.info(f"Saving model to {path}")
        # TODO: Implement model saving
        pass


def main():
    """Example usage of RecommenderSystem."""
    # Create sample interaction data
    np.random.seed(42)

    interactions = pd.DataFrame({
        'user_id': np.random.randint(0, 100, 1000),
        'item_id': np.random.randint(0, 50, 1000),
        'rating': np.random.randint(1, 6, 1000),
        'timestamp': pd.date_range('2023-01-01', periods=1000, freq='h')
    })

    # Initialize recommender
    recommender = RecommenderSystem(model_type='ncf')

    # Train
    recommender.fit(interactions)

    # Get recommendations
    recs = recommender.recommend(user_id=5, n=10)
    print(f"Recommendations for user 5:")
    for rec in recs:
        print(f"  Item {rec['item_id']}: score={rec['score']:.3f}")


if __name__ == "__main__":
    main()
