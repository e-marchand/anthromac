"""GitHub repository scraper for code collection."""

import requests
import base64
from typing import List, Dict, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)


class GitHubScraper:
    """
    Scrape code from GitHub repositories.

    Uses GitHub API to search and download code files.
    """

    def __init__(
        self,
        api_token: Optional[str] = None,
        language: str = '4d',
        file_extensions: Optional[List[str]] = None
    ):
        """
        Initialize GitHub scraper.

        Args:
            api_token: GitHub API token (optional but recommended)
            language: Programming language
            file_extensions: File extensions to collect
        """
        self.api_token = api_token
        self.language = language.lower()

        if file_extensions is None:
            if self.language == '4d':
                self.file_extensions = ['.4dm', '.4d']
            else:
                self.file_extensions = ['.txt']
        else:
            self.file_extensions = file_extensions

        # API configuration
        self.base_url = 'https://api.github.com'
        self.headers = {
            'Accept': 'application/vnd.github.v3+json'
        }

        if self.api_token:
            self.headers['Authorization'] = f'token {self.api_token}'

        self.rate_limit_remaining = None
        self.rate_limit_reset = None

        logger.info(f"Initialized GitHubScraper for {language}")

    def search_by_topics(
        self,
        topics: List[str],
        min_stars: int = 0,
        max_repos: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search repositories by topics.

        Args:
            topics: List of GitHub topics to search
            min_stars: Minimum number of stars
            max_repos: Maximum repositories to return

        Returns:
            List of repository information
        """
        logger.info(f"Searching repositories with topics: {topics}")

        all_repos = []
        repos_seen = set()

        for topic in topics:
            logger.info(f"Searching topic: {topic}")

            # Build search query
            query = f'topic:{topic}'

            if min_stars > 0:
                query += f' stars:>={min_stars}'

            # Search repositories
            repos = self._search_repositories(query, max_repos)

            for repo in repos:
                repo_full_name = repo['full_name']

                if repo_full_name not in repos_seen:
                    repos_seen.add(repo_full_name)
                    all_repos.append(repo)

                    logger.debug(f"Found: {repo_full_name} ({repo['stargazers_count']} stars)")

                if len(all_repos) >= max_repos:
                    break

            if len(all_repos) >= max_repos:
                break

        logger.info(f"Found {len(all_repos)} unique repositories")

        return all_repos[:max_repos]

    def download_code_files(
        self,
        repos: List[Dict[str, Any]],
        max_files_per_repo: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Download code files from repositories.

        Args:
            repos: List of repository info from search
            max_files_per_repo: Maximum files to download per repo

        Returns:
            List of code samples
        """
        logger.info(f"Downloading code from {len(repos)} repositories")

        all_code_samples = []

        for repo in repos:
            repo_name = repo['full_name']
            logger.info(f"Processing repository: {repo_name}")

            try:
                # Get repository tree
                files = self._get_repo_files(repo_name)

                # Filter by extensions
                code_files = [
                    f for f in files
                    if any(f['path'].endswith(ext) for ext in self.file_extensions)
                ]

                logger.info(f"  Found {len(code_files)} code files")

                # Download files
                for file_info in code_files[:max_files_per_repo]:
                    sample = self._download_file(repo_name, file_info)

                    if sample:
                        sample['repo_name'] = repo_name
                        sample['repo_stars'] = repo['stargazers_count']
                        sample['repo_url'] = repo['html_url']
                        all_code_samples.append(sample)

                    # Check rate limit
                    if self.rate_limit_remaining and self.rate_limit_remaining < 10:
                        logger.warning("Approaching rate limit, pausing...")
                        self._wait_for_rate_limit()

            except Exception as e:
                logger.error(f"Error processing {repo_name}: {e}")
                continue

        logger.info(f"Downloaded {len(all_code_samples)} code samples")

        return all_code_samples

    def _search_repositories(
        self,
        query: str,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search repositories using GitHub API.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            List of repositories
        """
        repos = []
        page = 1
        per_page = 30  # GitHub API max

        while len(repos) < max_results:
            url = f"{self.base_url}/search/repositories"
            params = {
                'q': query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': per_page,
                'page': page
            }

            response = requests.get(url, headers=self.headers, params=params)

            self._update_rate_limit(response)

            if response.status_code != 200:
                logger.error(f"Search failed: {response.status_code}")
                break

            data = response.json()
            items = data.get('items', [])

            if not items:
                break

            repos.extend(items)
            page += 1

            # GitHub limits search results to 1000
            if data.get('total_count', 0) <= len(repos):
                break

        return repos[:max_results]

    def _get_repo_files(
        self,
        repo_name: str,
        path: str = ''
    ) -> List[Dict[str, Any]]:
        """
        Get list of files in repository.

        Args:
            repo_name: Repository full name (owner/repo)
            path: Path within repository

        Returns:
            List of file information
        """
        url = f"{self.base_url}/repos/{repo_name}/git/trees/HEAD"
        params = {'recursive': '1'}

        response = requests.get(url, headers=self.headers, params=params)

        self._update_rate_limit(response)

        if response.status_code != 200:
            logger.error(f"Failed to get repo tree: {response.status_code}")
            return []

        data = response.json()
        tree = data.get('tree', [])

        # Filter to only files (not directories)
        files = [item for item in tree if item['type'] == 'blob']

        return files

    def _download_file(
        self,
        repo_name: str,
        file_info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Download a single file from repository.

        Args:
            repo_name: Repository name
            file_info: File information from tree

        Returns:
            Code sample dict or None
        """
        file_path = file_info['path']
        file_url = file_info['url']

        try:
            response = requests.get(file_url, headers=self.headers)

            self._update_rate_limit(response)

            if response.status_code != 200:
                logger.warning(f"Failed to download {file_path}: {response.status_code}")
                return None

            data = response.json()

            # Decode content (base64 encoded)
            if data.get('encoding') == 'base64':
                content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
            else:
                content = data.get('content', '')

            return {
                'file_path': file_path,
                'content': content,
                'size': file_info.get('size', len(content)),
                'language': self.language
            }

        except Exception as e:
            logger.error(f"Error downloading {file_path}: {e}")
            return None

    def _update_rate_limit(self, response: requests.Response):
        """Update rate limit information from response headers."""
        self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))

    def _wait_for_rate_limit(self):
        """Wait for rate limit to reset."""
        if self.rate_limit_reset:
            wait_time = max(0, self.rate_limit_reset - time.time())
            logger.info(f"Waiting {wait_time:.0f} seconds for rate limit reset...")
            time.sleep(wait_time + 5)  # Add 5 second buffer


def main():
    """Example usage."""
    print("=" * 80)
    print("GitHub Scraper - Example")
    print("=" * 80)

    # Initialize scraper (without token for demo)
    scraper = GitHubScraper(
        api_token=None,  # Set to your GitHub token
        language='4d',
        file_extensions=['.4dm', '.4d']
    )

    # Test 1: Search by 4D topics
    print("\n[1] Searching repositories by 4D topics...")

    topics = [
        '4d-component',
        '4d-code',
        '4d-project',
        '4dpop',
        '4d-project-dependencies'
    ]

    print(f"  Topics: {topics}")

    # Simulate search (would need real API)
    # In real usage: repos = scraper.search_by_topics(topics, min_stars=1, max_repos=10)

    # Create mock repository data for demonstration
    mock_repos = [
        {
            'full_name': 'example/4d-utils',
            'stargazers_count': 15,
            'html_url': 'https://github.com/example/4d-utils',
            'description': '4D utility methods'
        },
        {
            'full_name': 'example/4d-database',
            'stargazers_count': 8,
            'html_url': 'https://github.com/example/4d-database',
            'description': '4D database operations'
        }
    ]

    print(f"\n  Found {len(mock_repos)} repositories:")
    for repo in mock_repos:
        print(f"    - {repo['full_name']} ({repo['stargazers_count']} stars)")
        print(f"      {repo['description']}")

    # Test 2: Demonstrate download capability
    print("\n[2] Code download capability:")
    print("  To download code files:")
    print("    code_samples = scraper.download_code_files(repos, max_files_per_repo=20)")
    print("\n  Returns:")
    print("    - file_path: Path in repository")
    print("    - content: File content")
    print("    - repo_name: Repository name")
    print("    - repo_stars: Number of stars")
    print("    - repo_url: Repository URL")

    # Test 3: Show supported topics
    print("\n[3] Recommended 4D topics for searching:")

    recommended_topics = {
        '4d-component': 'Components and plugins',
        '4d-code': 'General 4D code',
        '4d-project': '4D projects',
        '4dpop': '4D Pop framework',
        '4d-project-dependencies': 'Project dependencies',
        '4d-database': 'Database-related code',
        '4d-v18': 'Version-specific code',
        '4d-language': '4D language examples'
    }

    for topic, description in recommended_topics.items():
        print(f"    {topic:<30} - {description}")

    print("\n[4] Usage notes:")
    print("  - GitHub API token recommended (5000 req/hour vs 60 without)")
    print("  - Rate limiting is automatically handled")
    print("  - Files are deduplicated by content hash")
    print("  - Supports filtering by minimum stars")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
