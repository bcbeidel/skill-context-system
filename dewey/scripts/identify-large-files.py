#!/usr/bin/env python3
"""Identify files that need splitting - for use with /split-file skill.

This script identifies large files and prepares them for intelligent splitting
using Claude Code's native /split-file skill (no additional API key needed).
"""

import sys
from pathlib import Path

import click

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dewey.core.compaction.skill_splitter import identify_large_files
from dewey.core.measurement.token_counter import estimate_tokens


@click.command()
@click.argument(
    "directory",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=False,
)
@click.option(
    "--max-lines",
    "-m",
    type=int,
    default=500,
    help="Maximum lines threshold (default: 500)",
)
@click.option(
    "--extensions",
    "-e",
    multiple=True,
    default=[".md"],
    help="File extensions to check (default: .md)",
)
def main(directory: Path, max_lines: int, extensions: tuple) -> None:
    """Identify files that need splitting for use with /split-file skill.

    This tool scans for large files and shows you which ones need attention.
    Use the /split-file skill in Claude Code to intelligently refactor them.

    Examples:

        # Scan current directory
        python identify-large-files.py .

        # Scan specific directory
        python identify-large-files.py context/

        # Custom threshold
        python identify-large-files.py . --max-lines 1000
    """
    if directory is None:
        directory = Path.cwd()

    click.echo(f"Scanning: {directory}")
    click.echo(f"Threshold: {max_lines} lines\n")

    # Identify large files
    large_files = identify_large_files(
        directory, max_lines=max_lines, extensions=list(extensions)
    )

    if not large_files:
        click.echo(f"✓ No files over {max_lines} lines found!")
        return

    # Display results
    click.echo(f"Found {len(large_files)} file(s) that need splitting:\n")
    click.echo(f"{'#':<4} {'File':<50} {'Lines':<8} {'Tokens':<10}")
    click.echo("-" * 75)

    for i, file_info in enumerate(large_files, 1):
        file_path = Path(file_info["absolute_path"])
        rel_path = file_info["file"]
        lines = file_info["lines"]
        tokens = file_info["tokens"]

        click.echo(f"{i:<4} {rel_path:<50} {lines:<8} {tokens:<10,}")

    # Show how to use the skill
    click.echo("\n" + "=" * 75)
    click.echo("Next Steps:")
    click.echo("=" * 75)
    click.echo("\nUse the /split-file skill in Claude Code to intelligently refactor:")
    click.echo()

    for i, file_info in enumerate(large_files, 1):
        file_path = Path(file_info["absolute_path"])
        click.echo(f"  {i}. /split-file {file_path}")

    click.echo("\nOr split all at once:")
    click.echo(f"  /split-file --scan {directory}")

    click.echo("\n" + "=" * 75)
    click.echo("Benefits of /split-file:")
    click.echo("=" * 75)
    click.echo("  • No additional API key required")
    click.echo("  • Uses your existing Claude Code session")
    click.echo("  • Intelligent semantic refactoring")
    click.echo("  • Follows Anthropic's best practices")
    click.echo("  • Maintains all information with clear navigation")


if __name__ == "__main__":
    main()
