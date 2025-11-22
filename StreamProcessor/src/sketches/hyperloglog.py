"""HyperLogLog for cardinality estimation."""

import numpy as np
import hashlib
from typing import Any
import logging

logger = logging.getLogger(__name__)


class HyperLogLog:
    """
    HyperLogLog probabilistic cardinality estimator.

    Estimates distinct count with very low memory usage.
    """

    def __init__(self, precision: int = 14):
        """
        Initialize HyperLogLog.

        Args:
            precision: Precision parameter (4-16, higher = more accurate)
        """
        if precision < 4 or precision > 16:
            raise ValueError("Precision must be between 4 and 16")

        self.precision = precision
        self.m = 2 ** precision  # Number of registers
        self.registers = np.zeros(self.m, dtype=np.uint8)

        # Alpha constant for bias correction
        if self.m >= 128:
            self.alpha = 0.7213 / (1 + 1.079 / self.m)
        elif self.m >= 64:
            self.alpha = 0.709
        elif self.m >= 32:
            self.alpha = 0.697
        else:
            self.alpha = 0.673

        logger.info(f"Initialized HyperLogLog (precision={precision}, "
                   f"registers={self.m})")

    def add(self, item: Any):
        """
        Add item to HyperLogLog.

        Args:
            item: Item to add
        """
        # Hash item
        hash_val = self._hash(item)

        # Get register index from first p bits
        j = hash_val & ((1 << self.precision) - 1)

        # Get position of first 1-bit in remaining bits
        w = hash_val >> self.precision

        # Count leading zeros + 1
        leading_zeros = self._leading_zeros(w) + 1

        # Update register with maximum
        self.registers[j] = max(self.registers[j], leading_zeros)

    def count(self) -> int:
        """
        Estimate cardinality.

        Returns:
            Estimated number of distinct elements
        """
        # Harmonic mean of 2^register values
        raw_estimate = self.alpha * (self.m ** 2) / np.sum(2.0 ** (-self.registers))

        # Bias correction for small cardinalities
        if raw_estimate <= 2.5 * self.m:
            # Count zero registers
            zeros = np.sum(self.registers == 0)

            if zeros != 0:
                # Small range correction
                return int(self.m * np.log(self.m / zeros))

        # No correction needed
        if raw_estimate <= (1.0/30.0) * (2 ** 32):
            return int(raw_estimate)

        # Large range correction
        return int(-2 ** 32 * np.log(1 - raw_estimate / (2 ** 32)))

    def merge(self, other: 'HyperLogLog'):
        """
        Merge another HyperLogLog into this one.

        Args:
            other: Another HyperLogLog
        """
        if self.precision != other.precision:
            raise ValueError("Cannot merge HyperLogLogs with different precisions")

        # Take maximum of each register
        self.registers = np.maximum(self.registers, other.registers)

    def clear(self):
        """Clear all registers."""
        self.registers.fill(0)

    def _hash(self, item: Any) -> int:
        """
        Hash item to 64-bit integer.

        Args:
            item: Item to hash

        Returns:
            Hash value
        """
        item_str = str(item)
        hash_obj = hashlib.sha1(item_str.encode())
        hash_bytes = hash_obj.digest()[:8]  # Take first 8 bytes
        return int.from_bytes(hash_bytes, byteorder='big')

    def _leading_zeros(self, w: int) -> int:
        """
        Count leading zeros in binary representation.

        Args:
            w: Integer

        Returns:
            Number of leading zeros
        """
        if w == 0:
            return 64 - self.precision

        # Count leading zeros
        count = 0
        bit_length = 64 - self.precision

        for i in range(bit_length - 1, -1, -1):
            if w & (1 << i):
                break
            count += 1

        return count


def main():
    """Example usage."""
    print("=" * 80)
    print("HyperLogLog - Example")
    print("=" * 80)

    # Test different precisions
    precisions = [10, 12, 14]

    for p in precisions:
        print(f"\n[Precision {p}]")

        hll = HyperLogLog(precision=p)

        print(f"  Registers: {hll.m}")
        print(f"  Memory: {hll.registers.nbytes} bytes")

        # Add items
        n_items = 100000
        n_unique = 10000

        for i in range(n_items):
            item = f"item_{i % n_unique}"
            hll.add(item)

        # Estimate cardinality
        estimated = hll.count()
        error = abs(estimated - n_unique) / n_unique * 100

        print(f"  True cardinality: {n_unique}")
        print(f"  Estimated: {estimated}")
        print(f"  Error: {error:.2f}%")

    # Detailed test with precision 14
    print("\n" + "=" * 60)
    print("Detailed Test (Precision 14)")
    print("=" * 60)

    hll = HyperLogLog(precision=14)

    # Test with different cardinalities
    test_cases = [100, 1000, 10000, 100000, 1000000]

    print(f"\n{'True Count':>12} {'Estimated':>12} {'Error %':>10} {'Memory':>10}")
    print("-" * 50)

    for n_unique in test_cases:
        hll.clear()

        # Add items
        for i in range(n_unique):
            hll.add(f"item_{i}")

        estimated = hll.count()
        error = abs(estimated - n_unique) / n_unique * 100

        print(f"{n_unique:>12} {estimated:>12} {error:>9.2f}% {hll.registers.nbytes:>9}B")

    # Test merging
    print("\n[Merging HyperLogLogs]")

    hll1 = HyperLogLog(precision=12)
    hll2 = HyperLogLog(precision=12)

    # Add different items to each
    for i in range(5000):
        hll1.add(f"item_{i}")

    for i in range(5000, 10000):
        hll2.add(f"item_{i}")

    count1 = hll1.count()
    count2 = hll2.count()

    print(f"  HLL1 cardinality: {count1}")
    print(f"  HLL2 cardinality: {count2}")

    # Merge
    hll1.merge(hll2)
    merged_count = hll1.count()

    print(f"  Merged cardinality: {merged_count}")
    print(f"  True cardinality: 10000")
    print(f"  Error: {abs(merged_count - 10000) / 10000 * 100:.2f}%")

    # Streaming scenario
    print("\n[Streaming Scenario]")

    hll_stream = HyperLogLog(precision=14)

    # Simulate stream with duplicates
    stream_size = 1000000
    unique_items = 50000

    print(f"  Stream size: {stream_size:,}")
    print(f"  Unique items: {unique_items:,}")

    for i in range(stream_size):
        item = f"user_{np.random.randint(0, unique_items)}"
        hll_stream.add(item)

    estimated = hll_stream.count()
    error = abs(estimated - unique_items) / unique_items * 100

    print(f"  Estimated unique: {estimated:,}")
    print(f"  Error: {error:.2f}%")
    print(f"  Memory used: {hll_stream.registers.nbytes / 1024:.2f} KB")

    # Compare to exact counting
    exact_memory = unique_items * 50  # Approx 50 bytes per string
    print(f"  Exact counting would need: {exact_memory / 1024:.2f} KB")

    savings = (1 - hll_stream.registers.nbytes / exact_memory) * 100
    print(f"  Memory savings: {savings:.2f}%")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
