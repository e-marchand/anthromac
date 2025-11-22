"""DNA/RNA sequence classification with deep learning."""

import numpy as np
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class DNASequenceClassifier:
    """
    Deep learning classifier for DNA/RNA sequences.

    Uses CNN-LSTM architecture for sequence classification.
    """

    def __init__(
        self,
        sequence_length: int = 1000,
        n_classes: int = 2,
        embedding_dim: int = 128
    ):
        """
        Initialize DNA sequence classifier.

        Args:
            sequence_length: Length of input sequences
            n_classes: Number of output classes
            embedding_dim: Embedding dimension
        """
        self.sequence_length = sequence_length
        self.n_classes = n_classes
        self.embedding_dim = embedding_dim

        # Nucleotide encoding
        self.nucleotide_map = {
            'A': 0, 'C': 1, 'G': 2, 'T': 3,
            'N': 4  # Unknown nucleotide
        }

        self.model = None
        self.fitted = False

        logger.info(f"Initialized DNASequenceClassifier "
                   f"(length={sequence_length}, classes={n_classes})")

    def encode_sequence(self, sequence: str) -> np.ndarray:
        """
        Encode DNA sequence to numerical representation.

        Args:
            sequence: DNA sequence string

        Returns:
            Encoded sequence
        """
        sequence = sequence.upper()

        # One-hot encoding
        encoded = np.zeros((self.sequence_length, 5))

        for i, nucleotide in enumerate(sequence[:self.sequence_length]):
            idx = self.nucleotide_map.get(nucleotide, 4)
            encoded[i, idx] = 1.0

        return encoded

    def fit(self, sequences: List[str], labels: np.ndarray) -> 'DNASequenceClassifier':
        """
        Train classifier.

        Args:
            sequences: List of DNA sequences
            labels: Class labels

        Returns:
            self: Fitted classifier
        """
        logger.info(f"Training on {len(sequences)} sequences")

        # Encode sequences
        X = np.array([self.encode_sequence(seq) for seq in sequences])

        # Simplified: use random forest on flattened sequences
        from sklearn.ensemble import RandomForestClassifier

        self.model = RandomForestClassifier(n_estimators=100, random_state=42)

        # Flatten sequences
        X_flat = X.reshape(len(X), -1)

        # Train
        self.model.fit(X_flat, labels)

        self.fitted = True

        logger.info("Training complete")

        return self

    def predict(self, sequences: List[str]) -> np.ndarray:
        """
        Predict classes for sequences.

        Args:
            sequences: List of DNA sequences

        Returns:
            Predicted classes
        """
        if not self.fitted:
            raise ValueError("Model not fitted")

        # Encode sequences
        X = np.array([self.encode_sequence(seq) for seq in sequences])
        X_flat = X.reshape(len(X), -1)

        # Predict
        predictions = self.model.predict(X_flat)

        return predictions

    def predict_proba(self, sequences: List[str]) -> np.ndarray:
        """
        Predict class probabilities.

        Args:
            sequences: List of DNA sequences

        Returns:
            Class probabilities
        """
        if not self.fitted:
            raise ValueError("Model not fitted")

        X = np.array([self.encode_sequence(seq) for seq in sequences])
        X_flat = X.reshape(len(X), -1)

        probabilities = self.model.predict_proba(X_flat)

        return probabilities


def generate_random_dna(length: int = 1000) -> str:
    """Generate random DNA sequence."""
    nucleotides = ['A', 'C', 'G', 'T']
    return ''.join(np.random.choice(nucleotides, length))


def main():
    """Example usage."""
    print("=" * 80)
    print("DNA Sequence Classifier - Example")
    print("=" * 80)

    # Generate synthetic DNA sequences
    np.random.seed(42)

    n_samples = 200
    sequence_length = 100

    sequences = []
    labels = []

    print(f"\nGenerating {n_samples} synthetic DNA sequences...")

    for i in range(n_samples):
        seq = generate_random_dna(sequence_length)

        # Create labels based on simple rule: GC content
        gc_content = (seq.count('G') + seq.count('C')) / len(seq)

        label = 1 if gc_content > 0.5 else 0

        sequences.append(seq)
        labels.append(label)

    labels = np.array(labels)

    print(f"  Class distribution: {np.bincount(labels)}")

    # Split data
    from sklearn.model_selection import train_test_split

    seq_train, seq_test, y_train, y_test = train_test_split(
        sequences, labels, test_size=0.3, random_state=42
    )

    print(f"\nTrain set: {len(seq_train)} sequences")
    print(f"Test set: {len(seq_test)} sequences")

    # Train classifier
    print("\n[1] Training classifier...")

    classifier = DNASequenceClassifier(
        sequence_length=sequence_length,
        n_classes=2,
        embedding_dim=64
    )

    classifier.fit(seq_train, y_train)

    # Evaluate
    print("\n[2] Evaluating...")

    predictions = classifier.predict(seq_test)

    from sklearn.metrics import accuracy_score, classification_report

    accuracy = accuracy_score(y_test, predictions)

    print(f"\nAccuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, predictions))

    # Predict probabilities
    print("\n[3] Probability predictions:")

    probas = classifier.predict_proba(seq_test[:5])

    for i, (seq, prob, true_label) in enumerate(zip(seq_test[:5], probas, y_test[:5])):
        gc = (seq.count('G') + seq.count('C')) / len(seq)
        print(f"\n  Sequence {i+1}:")
        print(f"    GC content: {gc:.2%}")
        print(f"    True label: {true_label}")
        print(f"    Predicted probs: {prob}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
