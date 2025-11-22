"""Data loading utilities for NLP tasks."""

import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class TextDataLoader:
    """
    Load and prepare text data from various sources.

    Supports multiple formats including CSV, JSON, TXT, and standard NLP datasets.
    """

    def __init__(self, data_dir: Union[str, Path] = "data/raw"):
        """
        Initialize the data loader.

        Args:
            data_dir: Directory containing data files
        """
        self.data_dir = Path(data_dir)
        logger.info(f"Initialized TextDataLoader with data_dir: {self.data_dir}")

    def load_csv(
        self,
        filename: str,
        text_column: str = 'text',
        label_column: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Load text data from CSV file.

        Args:
            filename: Name of CSV file
            text_column: Name of text column
            label_column: Name of label column (optional)
            **kwargs: Additional pandas read_csv parameters

        Returns:
            DataFrame with text data
        """
        filepath = self.data_dir / filename
        logger.info(f"Loading CSV from {filepath}")

        df = pd.read_csv(filepath, **kwargs)

        # Validate columns
        if text_column not in df.columns:
            raise ValueError(f"Column '{text_column}' not found in CSV")

        logger.info(f"Loaded {len(df)} rows from {filename}")
        return df

    def load_json(
        self,
        filename: str,
        text_field: str = 'text',
        label_field: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Load text data from JSON file.

        Args:
            filename: Name of JSON file
            text_field: Name of text field
            label_field: Name of label field (optional)

        Returns:
            List of data dictionaries
        """
        filepath = self.data_dir / filename
        logger.info(f"Loading JSON from {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both list and single object
        if not isinstance(data, list):
            data = [data]

        logger.info(f"Loaded {len(data)} items from {filename}")
        return data

    def load_jsonl(self, filename: str) -> List[Dict[str, Any]]:
        """
        Load text data from JSONL (JSON Lines) file.

        Args:
            filename: Name of JSONL file

        Returns:
            List of data dictionaries
        """
        filepath = self.data_dir / filename
        logger.info(f"Loading JSONL from {filepath}")

        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))

        logger.info(f"Loaded {len(data)} items from {filename}")
        return data

    def load_txt(
        self,
        filename: str,
        split_paragraphs: bool = False
    ) -> Union[str, List[str]]:
        """
        Load text from plain text file.

        Args:
            filename: Name of text file
            split_paragraphs: Whether to split into paragraphs

        Returns:
            Text string or list of paragraphs
        """
        filepath = self.data_dir / filename
        logger.info(f"Loading TXT from {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        if split_paragraphs:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            logger.info(f"Split into {len(paragraphs)} paragraphs")
            return paragraphs
        else:
            logger.info(f"Loaded {len(text)} characters")
            return text

    def load_conll(
        self,
        filename: str,
        separator: str = '\t'
    ) -> List[List[Tuple[str, str]]]:
        """
        Load data in CoNLL format (for NER).

        Format: Each line contains token and tag separated by separator.
        Sentences separated by blank lines.

        Args:
            filename: Name of CoNLL file
            separator: Column separator

        Returns:
            List of sentences, each sentence is list of (token, tag) tuples
        """
        filepath = self.data_dir / filename
        logger.info(f"Loading CoNLL format from {filepath}")

        sentences = []
        current_sentence = []

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                if not line:
                    # Blank line indicates sentence boundary
                    if current_sentence:
                        sentences.append(current_sentence)
                        current_sentence = []
                else:
                    parts = line.split(separator)
                    if len(parts) >= 2:
                        token, tag = parts[0], parts[-1]  # Token is first, tag is last
                        current_sentence.append((token, tag))

            # Add last sentence if exists
            if current_sentence:
                sentences.append(current_sentence)

        logger.info(f"Loaded {len(sentences)} sentences")
        return sentences

    def load_squad(self, filename: str) -> List[Dict[str, Any]]:
        """
        Load data in SQuAD format (for QA).

        Args:
            filename: Name of SQuAD JSON file

        Returns:
            List of QA examples
        """
        filepath = self.data_dir / filename
        logger.info(f"Loading SQuAD format from {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        examples = []

        for article in data.get('data', []):
            for paragraph in article.get('paragraphs', []):
                context = paragraph['context']

                for qa in paragraph['qas']:
                    example = {
                        'id': qa['id'],
                        'question': qa['question'],
                        'context': context,
                        'answers': qa.get('answers', []),
                        'is_impossible': qa.get('is_impossible', False)
                    }
                    examples.append(example)

        logger.info(f"Loaded {len(examples)} QA examples")
        return examples

    def prepare_classification_data(
        self,
        df: pd.DataFrame,
        text_column: str = 'text',
        label_column: str = 'label',
        train_ratio: float = 0.8
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare data for classification task.

        Args:
            df: Input DataFrame
            text_column: Name of text column
            label_column: Name of label column
            train_ratio: Ratio for train split

        Returns:
            Tuple of (train_df, test_df)
        """
        logger.info(f"Preparing classification data: {len(df)} samples")

        # Shuffle
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)

        # Split
        split_idx = int(len(df) * train_ratio)
        train_df = df.iloc[:split_idx]
        test_df = df.iloc[split_idx:]

        logger.info(f"Train: {len(train_df)}, Test: {len(test_df)}")

        # Class distribution
        if label_column in df.columns:
            logger.info(f"Train class distribution:\n{train_df[label_column].value_counts()}")

        return train_df, test_df

    def prepare_ner_data(
        self,
        sentences: List[List[Tuple[str, str]]]
    ) -> Tuple[List[List[str]], List[List[str]]]:
        """
        Prepare NER data for training.

        Args:
            sentences: List of sentences with (token, tag) tuples

        Returns:
            Tuple of (token_sequences, tag_sequences)
        """
        logger.info(f"Preparing NER data: {len(sentences)} sentences")

        tokens = []
        tags = []

        for sentence in sentences:
            sent_tokens, sent_tags = zip(*sentence)
            tokens.append(list(sent_tokens))
            tags.append(list(sent_tags))

        return tokens, tags

    def save_to_jsonl(
        self,
        data: List[Dict[str, Any]],
        filename: str
    ):
        """
        Save data to JSONL format.

        Args:
            data: List of dictionaries
            filename: Output filename
        """
        filepath = self.data_dir / filename
        logger.info(f"Saving {len(data)} items to {filepath}")

        with open(filepath, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        logger.info("Save completed")


def main():
    """Example usage of TextDataLoader."""
    loader = TextDataLoader()

    # Example: Create and save sample data
    sample_data = [
        {
            "text": "This product is amazing!",
            "label": "positive",
            "language": "en"
        },
        {
            "text": "Terrible experience, would not recommend.",
            "label": "negative",
            "language": "en"
        }
    ]

    # Save sample data
    loader.save_to_jsonl(sample_data, "sample.jsonl")

    # Load it back
    loaded_data = loader.load_jsonl("sample.jsonl")
    print(f"Loaded {len(loaded_data)} samples")
    print(loaded_data[0])


if __name__ == "__main__":
    main()
