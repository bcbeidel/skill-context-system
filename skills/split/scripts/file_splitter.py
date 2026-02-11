"""File splitting utilities for managing large context files.

This module provides functionality to split large files (>500 lines) into
main + references/ structure to improve context organization.
"""

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class SplitResult:
    """Result of a file split operation."""

    original_file: Path
    main_file: Path
    reference_files: list[Path]
    backup_file: Path
    lines_in_main: int
    lines_in_references: int
    total_lines: int
    wikilinks_updated: int


def parse_wikilinks(content: str) -> list[str]:
    """Parse [[wikilinks]] from markdown content.

    Args:
        content: Markdown content to parse

    Returns:
        List of wikilink targets (without the [[ ]])

    Example:
        >>> parse_wikilinks("See [[other-file]] and [[another]]")
        ['other-file', 'another']
    """
    pattern = r"\[\[([^\]]+)\]\]"
    return re.findall(pattern, content)


def update_wikilinks(
    content: str, old_path: str, new_path: str, use_relative: bool = True
) -> tuple[str, int]:
    """Update wikilinks in content to reflect moved files.

    Args:
        content: Markdown content with wikilinks
        old_path: Old file path (e.g., "skills/file.md")
        new_path: New file path (e.g., "skills/references/file-details.md")
        use_relative: Whether to use relative paths in wikilinks

    Returns:
        Tuple of (updated_content, number_of_updates)

    Example:
        >>> content = "See [[skills/file]]"
        >>> updated, count = update_wikilinks(content, "skills/file", "skills/references/file-details")
        >>> print(updated)
        See [[skills/references/file-details]]
    """
    # Extract the link portion (without .md extension if present)
    old_link = old_path.replace(".md", "")
    new_link = new_path.replace(".md", "")

    # Pattern to match the old link in wikilinks
    pattern = re.escape(f"[[{old_link}]]")

    # Count occurrences
    count = len(re.findall(pattern, content))

    # Replace
    updated = content.replace(f"[[{old_link}]]", f"[[{new_link}]]")

    return updated, count


def create_backup(file_path: Path, backup_dir: Optional[Path] = None) -> Path:
    """Create a backup of a file before modification.

    Args:
        file_path: File to backup
        backup_dir: Directory for backups (default: .dewey/backups/)

    Returns:
        Path to the backup file

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if backup_dir is None:
        backup_dir = Path.cwd() / ".dewey" / "backups"

    backup_dir.mkdir(parents=True, exist_ok=True)

    # Create backup with timestamp
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    backup_path = backup_dir / backup_name

    shutil.copy2(file_path, backup_path)

    return backup_path


def split_file(
    file_path: Path,
    max_lines: int = 500,
    main_lines: int = 150,
    backup: bool = True,
) -> SplitResult:
    """Split a large file into main + references/ structure.

    Args:
        file_path: Path to the file to split
        max_lines: Maximum lines before splitting (default: 500)
        main_lines: Lines to keep in main file (default: 150)
        backup: Whether to create a backup (default: True)

    Returns:
        SplitResult with details of the split

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is too small to split

    Example:
        >>> result = split_file(Path("skills/large-guide.md"))
        >>> print(f"Split into {len(result.reference_files)} reference files")
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read the file
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    total_lines = len(lines)

    if total_lines <= max_lines:
        raise ValueError(
            f"File has {total_lines} lines, which is under the {max_lines} line threshold"
        )

    # Create backup
    backup_path = None
    if backup:
        backup_path = create_backup(file_path)

    # Determine split strategy
    # Keep first main_lines in main file
    # Move remaining to references/
    main_content = lines[:main_lines]
    reference_content = lines[main_lines:]

    # Create references directory
    references_dir = file_path.parent / "references" / file_path.stem
    references_dir.mkdir(parents=True, exist_ok=True)

    # Write main file (overwrite original)
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(main_content)
        # Add a reference to the additional content
        f.write(f"\n\n---\n\n")
        f.write(f"**Additional content moved to references:**\n\n")
        f.write(
            f"- [[{file_path.parent.name}/references/{file_path.stem}/details]]\n"
        )

    # Write reference file
    reference_file = references_dir / "details.md"
    with open(reference_file, "w", encoding="utf-8") as f:
        f.write(f"# {file_path.stem} - Details\n\n")
        f.write(
            f"*This content was split from the main file to improve organization.*\n\n"
        )
        f.write(f"**Main file**: [[{file_path.parent.name}/{file_path.stem}]]\n\n")
        f.write("---\n\n")
        f.writelines(reference_content)

    result = SplitResult(
        original_file=file_path,
        main_file=file_path,
        reference_files=[reference_file],
        backup_file=backup_path,
        lines_in_main=len(main_content),
        lines_in_references=len(reference_content),
        total_lines=total_lines,
        wikilinks_updated=0,  # Will be updated by scan_and_update_wikilinks
    )

    return result


def scan_and_update_wikilinks(
    directory: Path, old_path: str, new_paths: list[str]
) -> int:
    """Scan directory and update all wikilinks pointing to moved files.

    Args:
        directory: Root directory to scan
        old_path: Old file path (relative)
        new_paths: List of new file paths (relative)

    Returns:
        Total number of wikilinks updated

    Example:
        >>> updated = scan_and_update_wikilinks(
        ...     Path("context"),
        ...     "skills/guide",
        ...     ["skills/guide", "skills/references/guide/details"]
        ... )
    """
    total_updates = 0

    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and references directories
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for file in files:
            if not file.endswith(".md"):
                continue

            file_path = Path(root) / file

            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Update wikilinks for each new path
                updated_content = content
                for new_path in new_paths:
                    updated_content, count = update_wikilinks(
                        updated_content, old_path, new_path
                    )
                    total_updates += count

                # Write back if changed
                if updated_content != content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(updated_content)

            except (OSError, UnicodeDecodeError) as e:
                print(f"Warning: Skipping {file_path}: {e}")
                continue

    return total_updates


def generate_split_report(result: SplitResult) -> str:
    """Generate a human-readable report of the split operation.

    Args:
        result: SplitResult from split_file

    Returns:
        Formatted report string
    """
    report = f"""File Split Report
{'=' * 60}

Original File: {result.original_file}
Total Lines:   {result.total_lines}

Split Result:
  Main file:       {result.main_file} ({result.lines_in_main} lines)
  Reference files: {len(result.reference_files)} file(s) ({result.lines_in_references} lines)

Reference Files:
"""

    for ref_file in result.reference_files:
        report += f"  - {ref_file}\n"

    report += f"\nBackup: {result.backup_file}\n"
    report += f"Wikilinks updated: {result.wikilinks_updated}\n"

    report += f"""
Summary:
  Before: 1 file with {result.total_lines} lines
  After:  {1 + len(result.reference_files)} files
          ({result.lines_in_main} + {result.lines_in_references} lines)
"""

    return report
