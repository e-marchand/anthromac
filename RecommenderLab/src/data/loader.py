"""Data loading utilities for recommendation systems."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, Optional, Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class InteractionLoader:
    """
    Load and prepare user-item interaction data.

    Supports multiple data formats and common datasets.
    """

    def __init__(self, data_dir: Union[str, Path] = "data/raw"):
        """
        Initialize the interaction loader.

        Args:
            data_dir: Directory containing data files
        """
        self.data_dir = Path(data_dir)
        logger.info(f"Initialized InteractionLoader with data_dir: {self.data_dir}")

    def load_csv(
        self,
        filename: str,
        user_col: str = 'user_id',
        item_col: str = 'item_id',
        rating_col: Optional[str] = 'rating',
        timestamp_col: Optional[str] = 'timestamp',
        **kwargs
    ) -> pd.DataFrame:
        """
        Load interaction data from CSV.

        Args:
            filename: Name of CSV file
            user_col: Name of user column
            item_col: Name of item column
            rating_col: Name of rating column (None for implicit feedback)
            timestamp_col: Name of timestamp column
            **kwargs: Additional pandas read_csv parameters

        Returns:
            DataFrame with interactions
        """
        filepath = self.data_dir / filename
        logger.info(f"Loading interactions from {filepath}")

        df = pd.read_csv(filepath, **kwargs)

        # Rename columns to standard names
        rename_map = {user_col: 'user_id', item_col: 'item_id'}
        if rating_col:
            rename_map[rating_col] = 'rating'
        if timestamp_col:
            rename_map[timestamp_col] = 'timestamp'

        df = df.rename(columns=rename_map)

        logger.info(f"Loaded {len(df)} interactions")
        logger.info(f"Users: {df['user_id'].nunique()}, Items: {df['item_id'].nunique()}")

        return df

    def load_movielens(
        self,
        variant: str = '100k',
        min_rating: Optional[float] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load MovieLens dataset.

        Args:
            variant: Dataset variant ('100k', '1m', '10m', '25m')
            min_rating: Minimum rating threshold for implicit feedback

        Returns:
            Tuple of (train_df, test_df)
        """
        logger.info(f"Loading MovieLens {variant} dataset")

        # TODO: Implement actual MovieLens loading
        # This is a placeholder that generates synthetic data

        np.random.seed(42)

        # Dataset sizes
        sizes = {
            '100k': (943, 1682, 100000),
            '1m': (6040, 3706, 1000209),
            '10m': (69878, 10677, 10000054),
            '25m': (162541, 59047, 25000095)
        }

        n_users, n_items, n_interactions = sizes.get(variant, sizes['100k'])

        # Generate synthetic interactions
        df = pd.DataFrame({
            'user_id': np.random.randint(0, n_users, min(n_interactions, 10000)),
            'item_id': np.random.randint(0, n_items, min(n_interactions, 10000)),
            'rating': np.random.randint(1, 6, min(n_interactions, 10000)),
            'timestamp': pd.date_range('2020-01-01', periods=min(n_interactions, 10000), freq='min')
        })

        # Filter by minimum rating if specified
        if min_rating is not None:
            df = df[df['rating'] >= min_rating]
            logger.info(f"Filtered to {len(df)} interactions with rating >= {min_rating}")

        # Train/test split (80/20 temporal)
        split_idx = int(len(df) * 0.8)
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()

        logger.info(f"Train: {len(train_df)}, Test: {len(test_df)}")

        return train_df, test_df

    def generate_synthetic_data(
        self,
        n_users: int = 1000,
        n_items: int = 500,
        n_interactions: int = 10000,
        implicit: bool = False,
        seed: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Generate synthetic interaction data for testing.

        Args:
            n_users: Number of users
            n_items: Number of items
            n_interactions: Number of interactions
            implicit: Whether to generate implicit feedback (binary)
            seed: Random seed

        Returns:
            DataFrame with synthetic interactions
        """
        if seed is not None:
            np.random.seed(seed)

        logger.info(f"Generating synthetic data: {n_users} users, {n_items} items, {n_interactions} interactions")

        # Generate interactions with some structure
        # Popular items get more interactions
        item_popularity = np.random.power(2, n_items)
        item_probs = item_popularity / item_popularity.sum()

        df = pd.DataFrame({
            'user_id': np.random.randint(0, n_users, n_interactions),
            'item_id': np.random.choice(n_items, n_interactions, p=item_probs),
            'timestamp': pd.date_range('2023-01-01', periods=n_interactions, freq='min')
        })

        if implicit:
            df['rating'] = 1
        else:
            # Add some correlation between user and item
            df['rating'] = np.random.randint(1, 6, n_interactions)

        # Remove duplicates
        df = df.drop_duplicates(subset=['user_id', 'item_id'])

        logger.info(f"Generated {len(df)} unique interactions")

        return df

    def preprocess(
        self,
        df: pd.DataFrame,
        min_user_interactions: int = 5,
        min_item_interactions: int = 3,
        remove_duplicates: bool = True
    ) -> pd.DataFrame:
        """
        Preprocess interaction data.

        Args:
            df: Raw interaction DataFrame
            min_user_interactions: Minimum interactions per user
            min_item_interactions: Minimum interactions per item
            remove_duplicates: Whether to remove duplicate interactions

        Returns:
            Preprocessed DataFrame
        """
        logger.info(f"Preprocessing {len(df)} interactions")

        # Remove duplicates
        if remove_duplicates:
            df = df.drop_duplicates(subset=['user_id', 'item_id'])
            logger.info(f"After deduplication: {len(df)} interactions")

        # Filter by minimum interactions
        user_counts = df['user_id'].value_counts()
        valid_users = user_counts[user_counts >= min_user_interactions].index
        df = df[df['user_id'].isin(valid_users)]

        item_counts = df['item_id'].value_counts()
        valid_items = item_counts[item_counts >= min_item_interactions].index
        df = df[df['item_id'].isin(valid_items)]

        logger.info(f"After filtering: {len(df)} interactions")
        logger.info(f"Users: {df['user_id'].nunique()}, Items: {df['item_id'].nunique()}")

        return df

    def create_user_item_matrix(
        self,
        df: pd.DataFrame,
        value_col: str = 'rating'
    ) -> pd.DataFrame:
        """
        Create user-item interaction matrix.

        Args:
            df: Interaction DataFrame
            value_col: Column to use as matrix values

        Returns:
            User-item matrix (users x items)
        """
        logger.info("Creating user-item matrix")

        matrix = df.pivot_table(
            index='user_id',
            columns='item_id',
            values=value_col,
            fill_value=0
        )

        logger.info(f"Matrix shape: {matrix.shape}")
        logger.info(f"Sparsity: {(matrix == 0).sum().sum() / matrix.size:.2%}")

        return matrix

    def train_test_split_temporal(
        self,
        df: pd.DataFrame,
        test_ratio: float = 0.2,
        timestamp_col: str = 'timestamp'
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data temporally (older = train, newer = test).

        Args:
            df: Interaction DataFrame
            test_ratio: Fraction for test set
            timestamp_col: Name of timestamp column

        Returns:
            Tuple of (train_df, test_df)
        """
        logger.info(f"Temporal split with test_ratio={test_ratio}")

        df = df.sort_values(timestamp_col)
        split_idx = int(len(df) * (1 - test_ratio))

        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()

        logger.info(f"Train: {len(train_df)}, Test: {len(test_df)}")

        return train_df, test_df

    def train_test_split_user_based(
        self,
        df: pd.DataFrame,
        test_ratio: float = 0.2,
        seed: Optional[int] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data by holding out interactions per user.

        Args:
            df: Interaction DataFrame
            test_ratio: Fraction of each user's interactions for test
            seed: Random seed

        Returns:
            Tuple of (train_df, test_df)
        """
        logger.info(f"User-based split with test_ratio={test_ratio}")

        if seed is not None:
            np.random.seed(seed)

        train_list = []
        test_list = []

        for user_id, user_df in df.groupby('user_id'):
            n_test = max(1, int(len(user_df) * test_ratio))
            test_indices = np.random.choice(user_df.index, n_test, replace=False)

            test_list.append(user_df.loc[test_indices])
            train_list.append(user_df.loc[~user_df.index.isin(test_indices)])

        train_df = pd.concat(train_list)
        test_df = pd.concat(test_list)

        logger.info(f"Train: {len(train_df)}, Test: {len(test_df)}")

        return train_df, test_df


def main():
    """Example usage of InteractionLoader."""
    loader = InteractionLoader()

    # Generate synthetic data
    df = loader.generate_synthetic_data(
        n_users=100,
        n_items=50,
        n_interactions=1000,
        seed=42
    )

    print(f"Generated data shape: {df.shape}")
    print(f"\nFirst few rows:\n{df.head()}")

    # Preprocess
    df_clean = loader.preprocess(df)

    # Train/test split
    train, test = loader.train_test_split_temporal(df_clean)
    print(f"\nTrain size: {len(train)}, Test size: {len(test)}")


if __name__ == "__main__":
    main()
