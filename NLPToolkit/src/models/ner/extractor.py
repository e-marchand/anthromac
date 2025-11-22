"""Named Entity Recognition using transformers and spaCy."""

from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class NERExtractor:
    """
    Named Entity Recognition extractor.

    Uses transformers for multilingual NER with fallback to spaCy.
    """

    def __init__(
        self,
        model_name: str = 'dslim/bert-base-NER',
        language: str = 'en',
        device: str = 'auto'
    ):
        """
        Initialize NER extractor.

        Args:
            model_name: Hugging Face model name
            language: Language code
            device: Device to use
        """
        self.model_name = model_name
        self.language = language
        self.device = device
        self.pipeline = None
        self.spacy_model = None

        logger.info(f"Initialized NERExtractor with {model_name}")

    def _lazy_load(self):
        """Lazy load the model."""
        if self.pipeline is not None or self.spacy_model is not None:
            return

        # Try transformers first
        try:
            from transformers import pipeline
            import torch

            device = -1  # CPU
            if self.device == 'auto':
                device = 0 if torch.cuda.is_available() else -1
            elif self.device == 'cuda':
                device = 0

            self.pipeline = pipeline(
                'ner',
                model=self.model_name,
                device=device,
                aggregation_strategy='simple'
            )
            logger.info("Transformer NER model loaded")
            return
        except ImportError:
            logger.warning("transformers not available, trying spaCy")

        # Try spaCy as fallback
        try:
            import spacy

            model_map = {
                'en': 'en_core_web_sm',
                'fr': 'fr_core_news_sm',
                'de': 'de_core_news_sm',
                'es': 'es_core_news_sm'
            }

            model_name = model_map.get(self.language, 'en_core_web_sm')
            self.spacy_model = spacy.load(model_name)
            logger.info(f"spaCy model {model_name} loaded")
        except Exception as e:
            logger.warning(f"Could not load spaCy: {e}, using rule-based fallback")

    def extract(
        self,
        text: Union[str, List[str]]
    ) -> Union[List[Dict[str, Any]], List[List[Dict[str, Any]]]]:
        """
        Extract named entities from text.

        Args:
            text: Input text or list of texts

        Returns:
            List of entities or list of entity lists
        """
        self._lazy_load()

        if isinstance(text, str):
            return self._extract_single(text)
        else:
            return [self._extract_single(t) for t in text]

    def _extract_single(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from single text."""
        # Try transformer pipeline
        if self.pipeline is not None:
            try:
                results = self.pipeline(text)
                return [
                    {
                        'text': ent['word'],
                        'type': ent['entity_group'],
                        'start': ent['start'],
                        'end': ent['end'],
                        'confidence': float(ent['score'])
                    }
                    for ent in results
                ]
            except Exception as e:
                logger.error(f"Transformer NER error: {e}")

        # Try spaCy
        if self.spacy_model is not None:
            try:
                doc = self.spacy_model(text)
                return [
                    {
                        'text': ent.text,
                        'type': ent.label_,
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'confidence': 0.9  # spaCy doesn't provide scores by default
                    }
                    for ent in doc.ents
                ]
            except Exception as e:
                logger.error(f"spaCy NER error: {e}")

        # Fallback: rule-based entity extraction
        return self._rule_based_ner(text)

    def _rule_based_ner(self, text: str) -> List[Dict[str, Any]]:
        """Simple rule-based NER for fallback."""
        import re

        entities = []

        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            entities.append({
                'text': match.group(),
                'type': 'EMAIL',
                'start': match.start(),
                'end': match.end(),
                'confidence': 0.95
            })

        # URL pattern
        url_pattern = r'https?://[^\s]+'
        for match in re.finditer(url_pattern, text):
            entities.append({
                'text': match.group(),
                'type': 'URL',
                'start': match.start(),
                'end': match.end(),
                'confidence': 0.95
            })

        # Date pattern (simple)
        date_pattern = r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'
        for match in re.finditer(date_pattern, text):
            entities.append({
                'text': match.group(),
                'type': 'DATE',
                'start': match.start(),
                'end': match.end(),
                'confidence': 0.8
            })

        # Capitalized words (potential proper nouns)
        capitalized_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        for match in re.finditer(capitalized_pattern, text):
            # Skip if it's at sentence start
            if match.start() == 0 or text[match.start()-1] in '.!?':
                continue

            entities.append({
                'text': match.group(),
                'type': 'MISC',
                'start': match.start(),
                'end': match.end(),
                'confidence': 0.6
            })

        return entities


def main():
    """Example usage."""
    extractor = NERExtractor()

    text = """
    Apple Inc. was founded by Steve Jobs in California on April 1, 1976.
    Contact us at info@apple.com or visit https://www.apple.com.
    The next meeting is scheduled for 12/25/2024.
    """

    entities = extractor.extract(text)

    print("Named Entity Recognition Results:")
    print("=" * 60)
    print(f"\nText: {text}\n")
    print("Entities found:")
    for ent in entities:
        print(f"  - {ent['text']:20s} | {ent['type']:10s} | confidence: {ent['confidence']:.2f}")


if __name__ == "__main__":
    main()
