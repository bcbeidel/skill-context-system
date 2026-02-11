#!/usr/bin/env python3
"""Identify files that need splitting - for use with /dewey:split skill.

This script identifies large files and prepares them for intelligent splitting
using Claude Code's native /dewey:split skill (no additional API key needed).
"""

import argparse
import sys
from pathlib import Path

# Add skills scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "split" / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "analyze" / "scripts"))

from skill_splitter import identify_large_files
from token_counter import estimate_tokens


def main() -> None:
    """Identify files that need splitting for use with /dewey:split skill.

    This tool scans for large files and shows you which ones need attention.
    Use the /dewey:split skill in Claude Code to intelligently refactor them.

    Examples:

        # Scan current directory
        python identify-large-files.py .

        # Scan specific directory
        python identify-large-files.py context/

        # Custom threshold
        python identify-large-files.py . --max-lines 1000
    """
    parser = argparse.ArgumentParser(
        description="Identify files that need splitting for use with /dewey:split skill"
    )
    parser.add_argument(
        "directory",
        type=Path,
        nargs="?",
        help="Directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--max-lines",
        "-m",
        type=int,
        default=500,
        help="Maximum lines threshold (default: 500)",
    )
    parser.add_argument(
        "--extensions",
        "-e",
        action="append",
        help="File extensions to check (can be used multiple times, default: .md)",
    )

    args = parser.parse_args()

    directory = args.directory if args.directory else Path.cwd()

    # Validate directory
    if not directory.exists():
        print(f"Error: Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    if not directory.is_dir():
        print(f"Error: Not a directory: {directory}", file=sys.stderr)
        sys.exit(1)

    # Set default extensions if none provided
    extensions = args.extensions if args.extensions else [".md"]

    print(f"Scanning: {directory}")
    print(f"Threshold: {args.max_lines} lines\n")

    # Identify large files
    large_files = identify_large_files(
        directory, max_lines=args.max_lines, extensions=extensions
    )

    if not large_files:
        print(f"✓ No files over {args.max_lines} lines found!")
        return

    # Display results
    print(f"Found {len(large_files)} file(s) that need splitting:\n")
    print(f"{'#':<4} {'File':<50} {'Lines':<8} {'Tokens':<10}")
    print("-" * 75)

    for i, file_info in enumerate(large_files, 1):
        file_path = Path(file_info["absolute_path"])
        rel_path = file_info["file"]
        lines = file_info["lines"]
        tokens = file_info["tokens"]

        print(f"{i:<4} {rel_path:<50} {lines:<8} {tokens:<10,}")

    # Show how to use the skill
    print("\n" + "=" * 75)
    print("Next Steps:")
    print("=" * 75)
    print("\nUse the /dewey:split skill in Claude Code to intelligently refactor:")
    print()

    for i, file_info in enumerate(large_files, 1):
        file_path = Path(file_info["absolute_path"])
        print(f"  {i}. /dewey:split {file_path}")

    print("\nOr analyze directory first:")
    print(f"  /dewey:analyze {directory}")

    print("\n" + "=" * 75)
    print("Benefits of /dewey:split:")
    print("=" * 75)
    print("  • No additional API key required")
    print("  • Uses your existing Claude Code session")
    print("  • Intelligent semantic refactoring")
    print("  • Follows Anthropic's best practices")
    print("  • Maintains all information with clear navigation")


if __name__ == "__main__":
    main()
