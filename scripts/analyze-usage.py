#!/usr/bin/env python3
"""Analyze context usage and generate token inventory.

This script scans a context directory and generates:
- Token inventory CSV
- Summary report
- Baseline measurements
"""

import argparse
import csv
import sys
from pathlib import Path

# Add skills/analyze/scripts to path so we can import token_counter
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "analyze" / "scripts"))

from token_counter import format_summary, scan_directory


def main() -> None:
    """Analyze context usage and generate token inventory.

    Examples:

        # Scan context directory and save inventory
        python analyze-usage.py -d context -o inventory.csv

        # Generate baseline report
        python analyze-usage.py -d context --baseline

        # Show summary report
        python analyze-usage.py -d context --report
    """
    parser = argparse.ArgumentParser(
        description="Analyze context usage and generate token inventory"
    )
    parser.add_argument(
        "--directory",
        "-d",
        type=Path,
        help="Directory to scan (default: ./context or current directory)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output CSV file (default: ~/.claude/analytics/context-inventory.csv)",
    )
    parser.add_argument(
        "--extensions",
        "-e",
        action="append",
        help="File extensions to include (e.g., -e .md -e .txt)",
    )
    parser.add_argument(
        "--report",
        "-r",
        action="store_true",
        help="Generate summary report",
    )
    parser.add_argument(
        "--baseline",
        "-b",
        action="store_true",
        help="Save baseline report to ~/.claude/analytics/baseline.txt",
    )

    args = parser.parse_args()

    # Set defaults
    directory = args.directory
    if directory is None:
        # Try common locations
        if Path("context").exists():
            directory = Path("context")
        else:
            directory = Path.cwd()

    # Validate directory
    if not directory.exists():
        print(f"Error: Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    if not directory.is_dir():
        print(f"Error: Not a directory: {directory}", file=sys.stderr)
        sys.exit(1)

    output = args.output
    if output is None:
        output = Path.home() / ".claude" / "analytics" / "context-inventory.csv"

    # Convert extensions list
    ext_list = args.extensions if args.extensions else None

    print(f"Scanning directory: {directory}")

    try:
        results = scan_directory(directory, extensions=ext_list)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("No files found matching criteria.")
        sys.exit(0)

    print(f"Found {len(results)} files")

    # Ensure output directory exists
    output.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    with open(output, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["file", "tokens", "lines", "bytes", "absolute_path"]
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"Wrote inventory to: {output}")

    # Generate summary report
    if args.report or args.baseline:
        summary = format_summary(results)
        print("\n" + summary)

    # Save baseline report
    if args.baseline:
        baseline_path = Path.home() / ".claude" / "analytics" / "baseline.txt"
        baseline_path.parent.mkdir(parents=True, exist_ok=True)

        with open(baseline_path, "w") as f:
            f.write(summary)

        print(f"\nBaseline report saved to: {baseline_path}")


if __name__ == "__main__":
    main()
