"""Sentiment analysis using transformers."""

from typing import Dict, List, Any, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Sentiment analysis using transformer models.

    Supports multiple languages and provides confidence scores.
    """

    def __init__(
        self,
        model_name: str = 'distilbert-base-uncased-finetuned-sst-2-english',
        device: str = 'auto'
    ):
        """
        Initialize sentiment analyzer.

        Args:
            model_name: Hugging Face model name
            device: Device to use ('cuda', 'cpu', or 'auto')
        """
        self.model_name = model_name
        self.device = device
        self.pipeline = None

        logger.info(f"Initialized SentimentAnalyzer with {model_name}")

    def _lazy_load(self):
        """Lazy load the model."""
        if self.pipeline is not None:
            return

        try:
            from transformers import pipeline
            import torch

            device = -1  # CPU
            if self.device == 'auto':
                device = 0 if torch.cuda.is_available() else -1
            elif self.device == 'cuda':
                device = 0

            self.pipeline = pipeline(
                'sentiment-analysis',
                model=self.model_name,
                device=device
            )
            logger.info("Model loaded successfully")
        except ImportError:
            logger.warning("transformers not available, using rule-based fallback")
            self.pipeline = None

    def analyze(
        self,
        text: Union[str, List[str]],
        return_all_scores: bool = False
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Analyze sentiment of text.

        Args:
            text: Input text or list of texts
            return_all_scores: Return scores for all labels

        Returns:
            Sentiment analysis result(s)
        """
        self._lazy_load()

        # Use transformer if available
        if self.pipeline is not None:
            try:
                results = self.pipeline(text, return_all_scores=return_all_scores)

                # Format results
                if isinstance(text, str):
                    return self._format_result(results[0])
                else:
                    return [self._format_result(r) for r in results]
            except Exception as e:
                logger.error(f"Transformer error: {e}, falling back to rule-based")

        # Fallback: rule-based sentiment
        if isinstance(text, str):
            return self._rule_based_sentiment(text)
        else:
            return [self._rule_based_sentiment(t) for t in text]

    def _format_result(self, result: Union[Dict, List[Dict]]) -> Dict[str, Any]:
        """Format transformer result."""
        if isinstance(result, list):
            # All scores mode
            scores = {item['label'].lower(): item['score'] for item in result}
            label = max(result, key=lambda x: x['score'])['label'].lower()
            confidence = max(item['score'] for item in result)
        else:
            # Single prediction mode
            label = result['label'].lower()
            confidence = result['score']
            scores = {label: confidence}

        return {
            'label': label,
            'confidence': float(confidence),
            'scores': scores
        }

    def _rule_based_sentiment(self, text: str) -> Dict[str, Any]:
        """Simple rule-based sentiment for fallback."""
        text_lower = text.lower()

        # Simple positive/negative word lists
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful',
            'fantastic', 'love', 'best', 'awesome', 'perfect'
        ]
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'worst',
            'hate', 'poor', 'disappointing', 'useless', 'failed'
        ]

        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)

        if pos_count > neg_count:
            label = 'positive'
            score = min(0.5 + (pos_count * 0.1), 0.95)
        elif neg_count > pos_count:
            label = 'negative'
            score = min(0.5 + (neg_count * 0.1), 0.95)
        else:
            label = 'neutral'
            score = 0.6

        return {
            'label': label,
            'confidence': float(score),
            'scores': {label: score}
        }


def main():
    """Example usage."""
    analyzer = SentimentAnalyzer()

    texts = [
        "I love this product! It's amazing!",
        "This is terrible and disappointing.",
        "It's okay, nothing special."
    ]

    print("Sentiment Analysis Results:")
    print("=" * 60)

    for text in texts:
        result = analyzer.analyze(text)
        print(f"\nText: {text}")
        print(f"Label: {result['label']}")
        print(f"Confidence: {result['confidence']:.3f}")


if __name__ == "__main__":
    main()
