"""Count-Min Sketch for frequency estimation."""

import numpy as np
import hashlib
from typing import Any
import logging

logger = logging.getLogger(__name__)


class CountMinSketch:
    """
    Count-Min Sketch probabilistic data structure.

    Provides approximate frequency counts with sub-linear space.
    """

    def __init__(self, width: int = 1000, depth: int = 5):
        """
        Initialize Count-Min Sketch.

        Args:
            width: Number of counters per hash function
            depth: Number of hash functions
        """
        self.width = width
        self.depth = depth

        # Initialize counter matrix
        self.counters = np.zeros((depth, width), dtype=np.int64)

        # Total count
        self.total = 0

        logger.info(f"Initialized CountMinSketch (width={width}, depth={depth})")

    def add(self, item: Any, count: int = 1):
        """
        Add item to sketch.

        Args:
            item: Item to add
            count: Count to add (default: 1)
        """
        # Hash item with different seeds
        for i in range(self.depth):
            hash_val = self._hash(item, i)
            self.counters[i, hash_val] += count

        self.total += count

    def estimate(self, item: Any) -> int:
        """
        Estimate frequency of item.

        Args:
            item: Item to estimate

        Returns:
            Estimated frequency
        """
        # Take minimum across all hash functions
        min_count = float('inf')

        for i in range(self.depth):
            hash_val = self._hash(item, i)
            count = self.counters[i, hash_val]
            min_count = min(min_count, count)

        return int(min_count)

    def merge(self, other: 'CountMinSketch'):
        """
        Merge another sketch into this one.

        Args:
            other: Another Count-Min Sketch
        """
        if self.width != other.width or self.depth != other.depth:
            raise ValueError("Cannot merge sketches with different dimensions")

        self.counters += other.counters
        self.total += other.total

    def _hash(self, item: Any, seed: int) -> int:
        """
        Hash item with seed.

        Args:
            item: Item to hash
            seed: Hash seed

        Returns:
            Hash value in range [0, width)
        """
        # Convert item to string
        item_str = str(item)

        # Hash with seed
        hash_obj = hashlib.md5((item_str + str(seed)).encode())
        hash_int = int(hash_obj.hexdigest(), 16)

        # Map to range
        return hash_int % self.width

    def get_top_k(self, k: int = 10) -> list:
        """
        Get approximate top-k items.

        Note: This is not exact - sketch doesn't store items.
        Returns list of (hash, count) tuples.

        Args:
            k: Number of top items

        Returns:
            List of top items by count
        """
        # Get maximum count for each position
        max_counts = self.counters.max(axis=0)

        # Get top k indices
        top_indices = np.argsort(-max_counts)[:k]

        # Return (index, count) pairs
        return [(idx, max_counts[idx]) for idx in top_indices]

    def clear(self):
        """Clear all counters."""
        self.counters.fill(0)
        self.total = 0


def main():
    """Example usage."""
    print("=" * 80)
    print("Count-Min Sketch - Example")
    print("=" * 80)

    # Initialize sketch
    cms = CountMinSketch(width=1000, depth=5)

    print(f"\nSketch dimensions: {cms.depth} x {cms.width}")

    # Generate data with zipfian distribution
    print("\n[1] Adding items to sketch...")

    np.random.seed(42)

    # Zipfian distribution: few items very frequent
    n_unique = 100
    n_samples = 10000

    # Create zipf distribution
    zipf_alpha = 1.5
    items = []
    counts = {}

    for _ in range(n_samples):
        # Sample from zipf
        rank = np.random.zipf(zipf_alpha)
        item = f"item_{min(rank, n_unique)}"

        items.append(item)
        counts[item] = counts.get(item, 0) + 1

        cms.add(item)

    print(f"  Added {n_samples} items ({n_unique} unique)")
    print(f"  Total in sketch: {cms.total}")

    # Test frequency estimation
    print("\n[2] Frequency estimation accuracy:")

    test_items = sorted(counts.items(), key=lambda x: -x[1])[:10]

    print(f"\n  {'Item':<15} {'True Count':>12} {'Estimated':>12} {'Error':>10}")
    print("  " + "-" * 55)

    for item, true_count in test_items:
        estimated = cms.estimate(item)
        error = abs(estimated - true_count) / true_count * 100

        print(f"  {item:<15} {true_count:>12} {estimated:>12} {error:>9.2f}%")

    # Test with unseen items
    print("\n[3] Estimating unseen items:")

    unseen_items = [f"unseen_{i}" for i in range(5)]

    for item in unseen_items:
        estimated = cms.estimate(item)
        print(f"  {item}: estimated count = {estimated}")

    # Test merging
    print("\n[4] Merging sketches:")

    cms2 = CountMinSketch(width=1000, depth=5)

    for _ in range(1000):
        item = f"item_{np.random.randint(0, n_unique)}"
        cms2.add(item)

    print(f"  Sketch 1 total: {cms.total}")
    print(f"  Sketch 2 total: {cms2.total}")

    cms.merge(cms2)

    print(f"  Merged total: {cms.total}")

    # Memory usage
    print("\n[5] Memory usage:")

    memory_bytes = cms.counters.nbytes
    memory_mb = memory_bytes / (1024 * 1024)

    print(f"  Counter matrix: {memory_mb:.2f} MB")
    print(f"  Average bytes per item: {memory_bytes / n_samples:.2f}")

    # Compare to exact counting
    exact_memory = len(counts) * (50 + 8)  # Approx string + int
    print(f"  Exact counting would use: {exact_memory / (1024 * 1024):.2f} MB")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
