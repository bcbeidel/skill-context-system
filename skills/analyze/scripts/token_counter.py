"""Token counting utilities for context files.

This module provides token estimation for text files using the 4 chars ≈ 1 token heuristic.
"""

import os
from pathlib import Path
from typing import Any, Optional


def estimate_tokens(text: str) -> int:
    """Estimate token count using 4 chars ≈ 1 token heuristic.

    Args:
        text: The text content to count tokens for

    Returns:
        Estimated token count

    Example:
        >>> estimate_tokens("Hello, world!")
        3
    """
    return len(text) // 4


def count_file_tokens(file_path: Path) -> dict[str, int]:
    """Count tokens, lines, and bytes for a single file.

    Args:
        file_path: Path to the file to analyze

    Returns:
        Dictionary with keys: tokens, lines, bytes

    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If the file can't be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try with latin-1 encoding for non-UTF-8 files
        with open(file_path, encoding="latin-1") as f:
            content = f.read()

    lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
    bytes_count = file_path.stat().st_size
    tokens = estimate_tokens(content)

    return {
        "tokens": tokens,
        "lines": lines,
        "bytes": bytes_count,
    }


def scan_directory(
    directory: Path,
    extensions: Optional[list[str]] = None,
    exclude_patterns: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """Scan a directory and count tokens for all matching files.

    Args:
        directory: Directory to scan
        extensions: List of file extensions to include (e.g., ['.md', '.txt'])
                   If None, includes all files
        exclude_patterns: List of patterns to exclude (e.g., ['node_modules', '.git'])

    Returns:
        List of dictionaries with file info: path, tokens, lines, bytes

    Example:
        >>> results = scan_directory(Path("context"), extensions=[".md"])
        >>> print(f"Total files: {len(results)}")
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    if extensions is None:
        extensions = [".md", ".txt", ".py", ".js", ".ts", ".json", ".yaml", ".yml"]

    if exclude_patterns is None:
        exclude_patterns = [
            ".git",
            "node_modules",
            "__pycache__",
            ".venv",
            "venv",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
        ]

    results = []

    for root, dirs, files in os.walk(directory):
        # Filter out excluded directories
        dirs[:] = [
            d for d in dirs if not any(pattern in d for pattern in exclude_patterns)
        ]

        for file in files:
            file_path = Path(root) / file

            # Check extension
            if extensions and file_path.suffix not in extensions:
                continue

            # Check exclude patterns in full path
            if any(pattern in str(file_path) for pattern in exclude_patterns):
                continue

            try:
                counts = count_file_tokens(file_path)
                results.append(
                    {
                        "file": str(file_path.relative_to(directory)),
                        "absolute_path": str(file_path),
                        "tokens": counts["tokens"],
                        "lines": counts["lines"],
                        "bytes": counts["bytes"],
                    }
                )
            except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
                # Skip files that can't be read
                print(f"Warning: Skipping {file_path}: {e}")
                continue

    # Sort by tokens (descending)
    results.sort(key=lambda x: x["tokens"], reverse=True)  # type: ignore[arg-type, return-value]

    return results


def format_summary(results: list[dict[str, Any]]) -> str:
    """Format a summary of token counting results.

    Args:
        results: List of file results from scan_directory

    Returns:
        Formatted summary string
    """
    if not results:
        return "No files found."

    total_files = len(results)
    total_tokens = sum(r["tokens"] for r in results)
    total_lines = sum(r["lines"] for r in results)
    total_bytes = sum(r["bytes"] for r in results)

    avg_tokens = total_tokens // total_files if total_files > 0 else 0

    summary = f"""Token Inventory Summary
{'=' * 50}
Total files:  {total_files:,}
Total tokens: {total_tokens:,}
Total lines:  {total_lines:,}
Total bytes:  {total_bytes:,}

Average tokens per file: {avg_tokens:,}

Top 10 largest files (by tokens):
"""

    for i, result in enumerate(results[:10], 1):
        summary += f"\n{i:2}. {result['file']:50} {result['tokens']:>8,} tokens"

    return summary
