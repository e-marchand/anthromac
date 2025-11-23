"""Code collection from various sources."""

import os
import glob
from typing import List, Dict, Any, Optional
import hashlib
import logging

logger = logging.getLogger(__name__)


class CodeCollector:
    """
    Collect code samples from various sources.

    Supports local files, GitHub repositories, and other sources.
    """

    def __init__(
        self,
        language: str,
        file_extensions: Optional[List[str]] = None,
        min_file_size: int = 100,
        max_file_size: int = 50000
    ):
        """
        Initialize code collector.

        Args:
            language: Programming language to collect
            file_extensions: File extensions to include
            min_file_size: Minimum file size in bytes
            max_file_size: Maximum file size in bytes
        """
        self.language = language.lower()
        self.min_file_size = min_file_size
        self.max_file_size = max_file_size

        # Default extensions for 4D language
        if file_extensions is None:
            if self.language == '4d':
                self.file_extensions = ['.4dm', '.4d']
            else:
                self.file_extensions = ['.txt']
        else:
            self.file_extensions = file_extensions

        self.collected_files = []
        self.file_hashes = set()

        logger.info(f"Initialized CodeCollector for {language}")

    def collect_from_directory(
        self,
        directory: str,
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Collect code files from directory.

        Args:
            directory: Directory path
            recursive: Whether to search recursively

        Returns:
            List of code samples
        """
        logger.info(f"Collecting from directory: {directory}")

        samples = []

        # Build glob pattern
        if recursive:
            patterns = [
                os.path.join(directory, '**', f'*{ext}')
                for ext in self.file_extensions
            ]
        else:
            patterns = [
                os.path.join(directory, f'*{ext}')
                for ext in self.file_extensions
            ]

        # Find files
        for pattern in patterns:
            files = glob.glob(pattern, recursive=recursive)

            for file_path in files:
                sample = self._read_file(file_path)

                if sample is not None:
                    samples.append(sample)

        logger.info(f"Collected {len(samples)} files from {directory}")

        return samples

    def collect_from_files(
        self,
        file_paths: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Collect from specific file paths.

        Args:
            file_paths: List of file paths

        Returns:
            List of code samples
        """
        samples = []

        for file_path in file_paths:
            sample = self._read_file(file_path)

            if sample is not None:
                samples.append(sample)

        logger.info(f"Collected {len(samples)} files")

        return samples

    def _read_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Read and validate code file.

        Args:
            file_path: Path to code file

        Returns:
            Code sample dict or None if invalid
        """
        try:
            # Check file size
            file_size = os.path.getsize(file_path)

            if file_size < self.min_file_size or file_size > self.max_file_size:
                logger.debug(f"Skipping {file_path}: size {file_size}")
                return None

            # Read content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Check for duplicates using hash
            content_hash = hashlib.md5(content.encode()).hexdigest()

            if content_hash in self.file_hashes:
                logger.debug(f"Skipping duplicate: {file_path}")
                return None

            self.file_hashes.add(content_hash)

            # Create sample
            sample = {
                'file_path': file_path,
                'content': content,
                'size': file_size,
                'hash': content_hash,
                'language': self.language
            }

            return sample

        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get collection statistics."""
        if not self.collected_files:
            return {}

        sizes = [f['size'] for f in self.collected_files]

        return {
            'total_files': len(self.collected_files),
            'total_size': sum(sizes),
            'avg_size': sum(sizes) / len(sizes),
            'min_size': min(sizes),
            'max_size': max(sizes)
        }


def main():
    """Example usage."""
    import tempfile
    import os

    print("=" * 80)
    print("Code Collector - Example")
    print("=" * 80)

    # Create temporary directory with sample 4D code
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample 4D files
        sample_files = {
            'utils.4dm': """
// 4D Utility Methods

Method CalculateSum
C_LONGINT($1)  // Array
C_LONGINT($0)  // Result

$0:=0
For ($i;1;Size of array($1))
    $0:=$0+$1{$i}
End for
""",
            'database.4dm': """
// Database Operations

Method QueryCustomers
C_TEXT($1)  // Search term
C_POINTER($2)  // Result array

ARRAY TEXT($2->;0)

ALL RECORDS([Customers])
QUERY([Customers];[Customers]Name=$1)

SELECTION TO ARRAY([Customers]Name;$2->)
""",
            'forms.4dm': """
// Form Handlers

Method OnFormLoad

ARRAY TEXT(arrCountries;0)
APPEND TO ARRAY(arrCountries;"USA")
APPEND TO ARRAY(arrCountries;"Canada")
APPEND TO ARRAY(arrCountries;"Mexico")
"""
        }

        # Write files
        for filename, content in sample_files.items():
            filepath = os.path.join(tmpdir, filename)
            with open(filepath, 'w') as f:
                f.write(content)

        print(f"\nCreated {len(sample_files)} sample 4D files")

        # Collect code
        print("\n[1] Collecting 4D code...")

        collector = CodeCollector(
            language='4d',
            file_extensions=['.4dm'],
            min_file_size=50,
            max_file_size=10000
        )

        samples = collector.collect_from_directory(tmpdir, recursive=False)

        print(f"  Collected: {len(samples)} files")

        # Show statistics
        stats = collector.get_statistics()

        print(f"\nStatistics:")
        print(f"  Total files: {stats['total_files']}")
        print(f"  Total size: {stats['total_size']} bytes")
        print(f"  Average size: {stats['avg_size']:.1f} bytes")

        # Show sample content
        print("\n[2] Sample collected code:")

        for i, sample in enumerate(samples[:2], 1):
            print(f"\nFile {i}: {os.path.basename(sample['file_path'])}")
            print(f"  Size: {sample['size']} bytes")
            print(f"  Hash: {sample['hash'][:16]}...")
            print(f"  Preview:")
            lines = sample['content'].split('\n')[:5]
            for line in lines:
                print(f"    {line}")

        # Test duplicate detection
        print("\n[3] Testing duplicate detection...")

        # Try to collect again (should skip duplicates)
        samples2 = collector.collect_from_directory(tmpdir, recursive=False)

        print(f"  Second collection: {len(samples2)} files (should be 0)")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
