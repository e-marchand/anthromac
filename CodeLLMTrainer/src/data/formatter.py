"""Format code data for LLM training."""

import json
import random
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TrainingFormatter:
    """
    Format code samples for different training paradigms.

    Supports instruction, FIM, and completion formats.
    """

    def __init__(
        self,
        format_type: str = 'instruction',
        language: str = '4d'
    ):
        """
        Initialize formatter.

        Args:
            format_type: Format type ('instruction', 'fim', 'completion')
            language: Programming language
        """
        self.format_type = format_type
        self.language = language

        logger.info(f"Initialized TrainingFormatter (type={format_type}, lang={language})")

    def format(
        self,
        code_samples: List[Dict[str, Any]],
        **kwargs
    ) -> List[Dict[str, str]]:
        """
        Format code samples.

        Args:
            code_samples: List of code samples
            **kwargs: Format-specific arguments

        Returns:
            Formatted training samples
        """
        if self.format_type == 'instruction':
            return self._format_instruction(code_samples, **kwargs)
        elif self.format_type == 'fim':
            return self._format_fim(code_samples, **kwargs)
        elif self.format_type == 'completion':
            return self._format_completion(code_samples, **kwargs)
        else:
            raise ValueError(f"Unknown format type: {self.format_type}")

    def _format_instruction(
        self,
        code_samples: List[Dict[str, Any]],
        instruction_template: Optional[str] = None,
        include_context: bool = False
    ) -> List[Dict[str, str]]:
        """Format as instruction-response pairs."""
        logger.info("Formatting as instruction pairs...")

        if instruction_template is None:
            instruction_template = f"Complete the following {self.language} code:\n{{code}}"

        formatted = []

        for sample in code_samples:
            content = sample['content']

            # Split into prefix and suffix
            lines = content.split('\n')

            if len(lines) < 5:
                continue

            # Random split point
            split_point = random.randint(2, len(lines) - 2)

            prefix = '\n'.join(lines[:split_point])
            suffix = '\n'.join(lines[split_point:])

            # Create instruction
            instruction = instruction_template.format(code=prefix)

            formatted_sample = {
                'instruction': instruction,
                'input': '',
                'output': suffix,
                'language': self.language
            }

            if include_context and 'file_path' in sample:
                formatted_sample['context'] = sample['file_path']

            formatted.append(formatted_sample)

        logger.info(f"Formatted {len(formatted)} instruction samples")

        return formatted

    def _format_fim(
        self,
        code_samples: List[Dict[str, Any]],
        fim_rate: float = 0.9
    ) -> List[Dict[str, str]]:
        """Format as Fill-in-the-Middle (FIM)."""
        logger.info("Formatting as FIM...")

        formatted = []

        for sample in code_samples:
            content = sample['content']
            lines = content.split('\n')

            if len(lines) < 10:
                continue

            # Random middle section
            middle_start = random.randint(2, len(lines) - 5)
            middle_end = random.randint(middle_start + 1, min(middle_start + 10, len(lines)))

            prefix = '\n'.join(lines[:middle_start])
            middle = '\n'.join(lines[middle_start:middle_end])
            suffix = '\n'.join(lines[middle_end:])

            # FIM format with special tokens
            formatted_sample = {
                'text': f"<fim_prefix>{prefix}<fim_suffix>{suffix}<fim_middle>{middle}",
                'prefix': prefix,
                'middle': middle,
                'suffix': suffix,
                'language': self.language
            }

            formatted.append(formatted_sample)

        logger.info(f"Formatted {len(formatted)} FIM samples")

        return formatted

    def _format_completion(
        self,
        code_samples: List[Dict[str, Any]],
        max_length: int = 2048
    ) -> List[Dict[str, str]]:
        """Format for standard completion."""
        logger.info("Formatting for completion...")

        formatted = []

        for sample in code_samples:
            content = sample['content']

            # Truncate if too long
            if len(content) > max_length:
                content = content[:max_length]

            formatted_sample = {
                'text': content,
                'language': self.language
            }

            formatted.append(formatted_sample)

        logger.info(f"Formatted {len(formatted)} completion samples")

        return formatted

    def save(
        self,
        formatted_data: List[Dict[str, str]],
        output_path: str,
        format: str = 'jsonl'
    ):
        """
        Save formatted data.

        Args:
            formatted_data: Formatted training data
            output_path: Output file path
            format: Output format ('jsonl', 'json')
        """
        logger.info(f"Saving {len(formatted_data)} samples to {output_path}")

        if format == 'jsonl':
            with open(output_path, 'w') as f:
                for sample in formatted_data:
                    f.write(json.dumps(sample) + '\n')

        elif format == 'json':
            with open(output_path, 'w') as f:
                json.dump(formatted_data, f, indent=2)

        else:
            raise ValueError(f"Unknown format: {format}")

        logger.info(f"Saved to {output_path}")

    def load(
        self,
        input_path: str,
        format: str = 'jsonl'
    ) -> List[Dict[str, str]]:
        """
        Load formatted data.

        Args:
            input_path: Input file path
            format: Input format ('jsonl', 'json')

        Returns:
            Loaded data
        """
        logger.info(f"Loading from {input_path}")

        if format == 'jsonl':
            data = []
            with open(input_path, 'r') as f:
                for line in f:
                    data.append(json.loads(line))

        elif format == 'json':
            with open(input_path, 'r') as f:
                data = json.load(f)

        else:
            raise ValueError(f"Unknown format: {format}")

        logger.info(f"Loaded {len(data)} samples")

        return data


def main():
    """Example usage."""
    import tempfile
    import os

    print("=" * 80)
    print("Training Formatter - Example")
    print("=" * 80)

    # Create sample code
    sample_code = """
// 4D Method for calculating totals

Method CalculateTotals
C_LONGINT($total)
C_LONGINT($i)

$total:=0

For ($i;1;Size of array(arrValues))
    $total:=$total+arrValues{$i}
End for

ALERT("Total: "+String($total))
"""

    code_samples = [
        {
            'content': sample_code,
            'file_path': 'methods/calculate.4dm',
            'language': '4d'
        }
    ]

    # Test 1: Instruction format
    print("\n[1] Instruction Format:")

    formatter = TrainingFormatter(format_type='instruction', language='4d')

    instruction_data = formatter.format(
        code_samples,
        instruction_template="Complete this {language} code:\n{code}"
    )

    for sample in instruction_data:
        print(f"\nInstruction: {sample['instruction'][:80]}...")
        print(f"Output: {sample['output'][:80]}...")

    # Test 2: FIM format
    print("\n[2] Fill-in-the-Middle Format:")

    formatter_fim = TrainingFormatter(format_type='fim', language='4d')

    fim_data = formatter_fim.format(code_samples)

    for sample in fim_data:
        print(f"\nPrefix: {sample['prefix'][:60]}...")
        print(f"Middle: {sample['middle'][:60]}...")
        print(f"Suffix: {sample['suffix'][:60]}...")

    # Test 3: Completion format
    print("\n[3] Completion Format:")

    formatter_comp = TrainingFormatter(format_type='completion', language='4d')

    completion_data = formatter_comp.format(code_samples, max_length=500)

    for sample in completion_data:
        print(f"\nText: {sample['text'][:100]}...")

    # Test 4: Save and load
    print("\n[4] Save and Load:")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'training_data.jsonl')

        # Save
        formatter.save(instruction_data, output_file, format='jsonl')
        print(f"  Saved to {output_file}")

        # Load
        loaded_data = formatter.load(output_file, format='jsonl')
        print(f"  Loaded {len(loaded_data)} samples")

        # Verify
        print(f"  Match: {loaded_data == instruction_data}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
