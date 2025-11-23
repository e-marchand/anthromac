"""Code generation with fine-tuned models."""

import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CodeGenerator:
    """
    Generate code using fine-tuned LLM.

    Supports various generation strategies and post-processing.
    """

    def __init__(
        self,
        model_path: str,
        language: str = '4d',
        max_length: int = 512,
        temperature: float = 0.2,
        top_p: float = 0.95
    ):
        """
        Initialize code generator.

        Args:
            model_path: Path to fine-tuned model
            language: Programming language
            max_length: Maximum generation length
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
        """
        self.model_path = model_path
        self.language = language
        self.max_length = max_length
        self.temperature = temperature
        self.top_p = top_p

        self.model = None
        self.tokenizer = None

        logger.info(f"Initialized CodeGenerator from {model_path}")

    def generate(
        self,
        prompt: str,
        num_return_sequences: int = 1,
        **kwargs
    ) -> str:
        """
        Generate code from prompt.

        Args:
            prompt: Input prompt
            num_return_sequences: Number of sequences to generate
            **kwargs: Additional generation parameters

        Returns:
            Generated code
        """
        logger.info(f"Generating code for prompt: {prompt[:50]}...")

        # Simulate generation (in production would use actual model)
        # For demonstration, create plausible 4D code
        generated = self._simulate_generation(prompt)

        # Post-process
        generated = self._post_process(generated)

        logger.info(f"Generated {len(generated)} characters")

        return generated

    def generate_batch(
        self,
        prompts: List[str],
        **kwargs
    ) -> List[str]:
        """
        Generate code for multiple prompts.

        Args:
            prompts: List of prompts
            **kwargs: Generation parameters

        Returns:
            List of generated code
        """
        logger.info(f"Generating code for {len(prompts)} prompts...")

        results = []

        for prompt in prompts:
            generated = self.generate(prompt, **kwargs)
            results.append(generated)

        return results

    def _simulate_generation(self, prompt: str) -> str:
        """
        Simulate code generation.

        In production, this would use the actual model.
        """
        # Extract context from prompt
        if 'Method' in prompt:
            # Generate 4D method
            generated = """
C_LONGINT($result)
C_LONGINT($i)

$result:=0

For ($i;1;Size of array($array))
    $result:=$result+$array{$i}
End for

return $result
"""
        elif 'QUERY' in prompt or 'database' in prompt.lower():
            # Generate database query
            generated = """
ALL RECORDS([Table])
QUERY([Table];[Table]Field=$value)

If (Records in selection([Table])>0)
    ALERT("Found "+String(Records in selection([Table]))+" records")
End if
"""
        else:
            # Generic completion
            generated = """
// Implementation
C_TEXT($result)

$result:=""

// Process data
// ...

return $result
"""

        return generated.strip()

    def _post_process(self, generated: str) -> str:
        """
        Post-process generated code.

        Args:
            generated: Raw generated code

        Returns:
            Post-processed code
        """
        # Remove leading/trailing whitespace
        code = generated.strip()

        # Ensure proper indentation
        lines = code.split('\n')
        processed_lines = []

        indent_level = 0

        for line in lines:
            stripped = line.strip()

            # Decrease indent for closing keywords
            if stripped.startswith('End ') or stripped == 'End':
                indent_level = max(0, indent_level - 1)

            # Add line with proper indentation
            if stripped:
                processed_lines.append('    ' * indent_level + stripped)
            else:
                processed_lines.append('')

            # Increase indent for opening keywords
            if stripped.startswith('For ') or stripped.startswith('While ') or \
               stripped.startswith('If ') or stripped.startswith('Case of'):
                indent_level += 1

        return '\n'.join(processed_lines)

    def validate_syntax(self, code: str) -> Dict[str, Any]:
        """
        Validate generated code syntax.

        Args:
            code: Generated code

        Returns:
            Validation results
        """
        issues = []

        # Check for common syntax issues
        lines = code.split('\n')

        # Track control structures
        for_count = 0
        if_count = 0
        case_count = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check For/End for matching
            if stripped.startswith('For '):
                for_count += 1
            elif stripped == 'End for':
                for_count -= 1

            # Check If/End if matching
            if stripped.startswith('If '):
                if_count += 1
            elif stripped == 'End if':
                if_count -= 1

            # Check Case of/End case matching
            if stripped == 'Case of':
                case_count += 1
            elif stripped == 'End case':
                case_count -= 1

        # Check for unmatched structures
        if for_count != 0:
            issues.append(f"Unmatched For/End for (diff: {for_count})")

        if if_count != 0:
            issues.append(f"Unmatched If/End if (diff: {if_count})")

        if case_count != 0:
            issues.append(f"Unmatched Case of/End case (diff: {case_count})")

        return {
            'valid': len(issues) == 0,
            'issues': issues
        }


def main():
    """Example usage."""
    print("=" * 80)
    print("Code Generator - Example")
    print("=" * 80)

    # Initialize generator
    generator = CodeGenerator(
        model_path='models/codellama-4d-lora',
        language='4d',
        max_length=512,
        temperature=0.2
    )

    # Test 1: Generate method
    print("\n[1] Generating 4D method...")

    prompt1 = """
// Create a method to calculate the sum of an array
Method CalculateSum
"""

    generated1 = generator.generate(prompt1)

    print(f"\nPrompt:\n{prompt1}")
    print(f"\nGenerated:\n{generated1}")

    # Validate
    validation1 = generator.validate_syntax(generated1)
    print(f"\nValidation: {'✓ Valid' if validation1['valid'] else '✗ Invalid'}")
    if validation1['issues']:
        for issue in validation1['issues']:
            print(f"  - {issue}")

    # Test 2: Generate database query
    print("\n[2] Generating database query...")

    prompt2 = """
// Query active customers
Method QueryActiveCustomers
"""

    generated2 = generator.generate(prompt2)

    print(f"\nPrompt:\n{prompt2}")
    print(f"\nGenerated:\n{generated2}")

    # Test 3: Batch generation
    print("\n[3] Batch generation...")

    prompts = [
        "Method SortArray\n",
        "Method FindMaxValue\n",
        "Method CountRecords\n"
    ]

    results = generator.generate_batch(prompts)

    for i, (prompt, result) in enumerate(zip(prompts, results), 1):
        print(f"\nExample {i}:")
        print(f"Prompt: {prompt.strip()}")
        print(f"Generated: {result[:100]}...")

    # Test 4: Syntax validation
    print("\n[4] Syntax validation test...")

    # Valid code
    valid_code = """
For ($i;1;10)
    $sum:=$sum+$i
End for
"""

    validation = generator.validate_syntax(valid_code)
    print(f"\nValid code: {validation['valid']}")

    # Invalid code (missing End for)
    invalid_code = """
For ($i;1;10)
    $sum:=$sum+$i
"""

    validation = generator.validate_syntax(invalid_code)
    print(f"Invalid code: {validation['valid']}")
    print(f"Issues: {validation['issues']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
