#!/usr/bin/env python3
"""Skill helper for /dewey-analyze - context analysis and recommendations."""

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

# Import from local module
from token_counter import scan_directory


@dataclass
class FileStats:
    """Statistics for a single file."""

    file: str
    absolute_path: str
    lines: int
    tokens: int
    bytes: int


@dataclass
class DistributionBucket:
    """Token distribution bucket."""

    range_label: str
    min_tokens: int
    max_tokens: Optional[int]
    count: int
    percentage: float


@dataclass
class AnalysisData:
    """Raw analysis data for the skill to process."""

    directory: Path
    total_files: int
    total_tokens: int
    total_lines: int
    total_bytes: int
    files: list[FileStats]
    distribution: list[DistributionBucket]
    large_files: list[FileStats]  # >500 lines
    timestamp: str


def analyze_directory(
    directory: Path,
    extensions: Optional[list[str]] = None,
    large_file_threshold: int = 500,
) -> AnalysisData:
    """Analyze directory and return structured data for skill processing.

    Args:
        directory: Directory to analyze
        extensions: File extensions to include (default: ['.md'])
        large_file_threshold: Line count threshold for "large file"

    Returns:
        AnalysisData with all metrics and file information
    """
    from datetime import datetime

    if extensions is None:
        extensions = [".md"]

    # Scan directory
    results = scan_directory(directory, extensions=extensions)

    if not results:
        return AnalysisData(
            directory=directory,
            total_files=0,
            total_tokens=0,
            total_lines=0,
            total_bytes=0,
            files=[],
            distribution=[],
            large_files=[],
            timestamp=datetime.now().isoformat(),
        )

    # Convert to FileStats
    files = [
        FileStats(
            file=r["file"],
            absolute_path=r["absolute_path"],
            lines=r["lines"],
            tokens=r["tokens"],
            bytes=r["bytes"],
        )
        for r in results
    ]

    # Calculate totals
    total_files = len(files)
    total_tokens = sum(f.tokens for f in files)
    total_lines = sum(f.lines for f in files)
    total_bytes = sum(f.bytes for f in files)

    # Create distribution buckets
    buckets = [
        (0, 500, "<500 tokens"),
        (500, 2000, "500-2000 tokens"),
        (2000, 5000, "2000-5000 tokens"),
        (5000, None, ">5000 tokens"),
    ]

    distribution = []
    for min_tok, max_tok, label in buckets:
        if max_tok is None:
            count = sum(1 for f in files if f.tokens >= min_tok)
        else:
            count = sum(1 for f in files if min_tok <= f.tokens < max_tok)

        percentage = (count / total_files * 100) if total_files > 0 else 0

        distribution.append(
            DistributionBucket(
                range_label=label,
                min_tokens=min_tok,
                max_tokens=max_tok,
                count=count,
                percentage=percentage,
            )
        )

    # Identify large files
    large_files = [f for f in files if f.lines > large_file_threshold]

    return AnalysisData(
        directory=directory,
        total_files=total_files,
        total_tokens=total_tokens,
        total_lines=total_lines,
        total_bytes=total_bytes,
        files=files,
        distribution=distribution,
        large_files=large_files,
        timestamp=datetime.now().isoformat(),
    )


def generate_analysis_prompt(data: AnalysisData, detailed: bool = False) -> str:
    """Generate prompt for Claude to analyze the data.

    Args:
        data: Analysis data from scan
        detailed: Include file-by-file breakdown

    Returns:
        Formatted prompt for skill
    """
    # Build file list
    file_list = []
    for i, file in enumerate(data.files[:20], 1):  # Top 20 by tokens
        file_list.append(f"{i:2}. {file.file:<50} {file.lines:>6} lines, {file.tokens:>8,} tokens")

    if len(data.files) > 20:
        file_list.append(f"... and {len(data.files) - 20} more files")

    # Build distribution
    dist_lines = []
    for bucket in data.distribution:
        bar = "█" * int(bucket.percentage / 5)  # 1 block per 5%
        dist_lines.append(
            f"{bucket.range_label:<18} {bucket.count:>5}    {bucket.percentage:>5.1f}%  {bar}"
        )

    # Build large files list
    large_files_lines = []
    for i, file in enumerate(data.large_files, 1):
        large_files_lines.append(f"{i}. {file.file} ({file.lines} lines)")

    prompt = f"""I need your help analyzing context usage for optimization opportunities.

**Directory Analyzed**: {data.directory}
**Timestamp**: {data.timestamp}

**Summary Statistics**:
- Total Files: {data.total_files:,}
- Total Tokens: {data.total_tokens:,}
- Total Lines: {data.total_lines:,}
- Total Bytes: {data.total_bytes:,}
- Average Tokens/File: {data.total_tokens // data.total_files if data.total_files > 0 else 0:,}

**Token Distribution**:
```
Size Range         Files    % of Total
─────────────────────────────────────────────────
{chr(10).join(dist_lines)}
```

**Largest Files** (by tokens):
```
{chr(10).join(file_list)}
```

**Large Files** (>{500} lines):
{chr(10).join(large_files_lines) if large_files_lines else "None"}

---

**Your Task**:

Analyze this context data and provide:

1. **Issues Detection** (categorized by priority):
   - 🔴 High Priority: Immediate action needed
   - 🟡 Medium Priority: Should address soon
   - 🟢 Low Priority: Optional improvements

2. **Specific Recommendations**:
   - Concrete `/dewey-*` commands to run
   - Estimated impact (tokens saved)
   - Time estimate for each action

3. **Optimization Potential**:
   - Current total tokens
   - Estimated tokens after optimization
   - Percentage reduction possible

4. **Next Steps** (prioritized list):
   - Quick wins first (high impact, low effort)
   - Then medium effort tasks
   - Finally, long-term improvements

**Format your response as a clear, actionable analysis report**:
- Use emojis for visual clarity (🔴 🟡 🟢 📊 💡 ⚠️)
- Be specific with file names and commands
- Quantify impact where possible
- Prioritize by impact/effort ratio

**Focus on**:
- Files that should be split (>500 lines)
- Potential duplicates (if you spot patterns in names/sizes)
- Inefficiencies in structure
- Token waste opportunities
- Best practices violations

Please generate the analysis report now."""

    return prompt


def save_baseline(data: AnalysisData, output_path: Optional[Path] = None) -> Path:
    """Save analysis as baseline for future comparison.

    Args:
        data: Analysis data to save
        output_path: Optional custom output path

    Returns:
        Path where baseline was saved
    """
    if output_path is None:
        output_path = Path.home() / ".claude" / "analytics" / "baseline.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to JSON-serializable format
    baseline = {
        "directory": str(data.directory),
        "timestamp": data.timestamp,
        "total_files": data.total_files,
        "total_tokens": data.total_tokens,
        "total_lines": data.total_lines,
        "total_bytes": data.total_bytes,
        "distribution": [
            {
                "range": bucket.range_label,
                "count": bucket.count,
                "percentage": bucket.percentage,
            }
            for bucket in data.distribution
        ],
        "large_files": [
            {"file": f.file, "lines": f.lines, "tokens": f.tokens}
            for f in data.large_files
        ],
        "top_10_files": [
            {"file": f.file, "lines": f.lines, "tokens": f.tokens}
            for f in sorted(data.files, key=lambda x: x.tokens, reverse=True)[:10]
        ],
    }

    with open(output_path, "w") as f:
        json.dump(baseline, f, indent=2)

    return output_path


def load_baseline(baseline_path: Optional[Path] = None) -> Optional[dict]:
    """Load previously saved baseline for comparison.

    Args:
        baseline_path: Optional custom baseline path

    Returns:
        Baseline data or None if not found
    """
    if baseline_path is None:
        baseline_path = Path.home() / ".claude" / "analytics" / "baseline.json"

    if not baseline_path.exists():
        return None

    with open(baseline_path) as f:
        return json.load(f)


def compare_to_baseline(
    current: AnalysisData, baseline: dict
) -> dict[str, any]:
    """Compare current analysis to baseline.

    Args:
        current: Current analysis data
        baseline: Previously saved baseline

    Returns:
        Dictionary with comparison metrics
    """
    return {
        "files_change": current.total_files - baseline["total_files"],
        "tokens_change": current.total_tokens - baseline["total_tokens"],
        "tokens_change_percent": (
            (current.total_tokens - baseline["total_tokens"])
            / baseline["total_tokens"]
            * 100
            if baseline["total_tokens"] > 0
            else 0
        ),
        "lines_change": current.total_lines - baseline["total_lines"],
        "large_files_change": len(current.large_files) - len(baseline["large_files"]),
        "baseline_date": baseline["timestamp"],
        "improved": current.total_tokens < baseline["total_tokens"],
    }


def main():
    """CLI entry point for analyze_directory."""
    parser = argparse.ArgumentParser(
        description="Analyze directory context usage and generate optimization recommendations"
    )
    parser.add_argument(
        "directory",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Directory to analyze (default: current directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Include detailed file-by-file breakdown",
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Save analysis as baseline for future comparison",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=500,
        help="Custom 'large file' threshold in lines (default: 500)",
    )

    args = parser.parse_args()

    # Validate directory
    if not args.directory.exists():
        print(f"Error: Directory not found: {args.directory}", file=sys.stderr)
        sys.exit(1)

    if not args.directory.is_dir():
        print(f"Error: Not a directory: {args.directory}", file=sys.stderr)
        sys.exit(1)

    # Analyze directory
    data = analyze_directory(
        args.directory,
        large_file_threshold=args.threshold,
    )

    if args.json:
        # Output JSON for Claude to parse
        # Convert dataclasses to dict
        def dataclass_to_dict(obj):
            if hasattr(obj, "__dataclass_fields__"):
                result = {}
                for field_name, field_def in obj.__dataclass_fields__.items():
                    value = getattr(obj, field_name)
                    if isinstance(value, Path):
                        result[field_name] = str(value)
                    elif isinstance(value, list):
                        result[field_name] = [dataclass_to_dict(item) for item in value]
                    elif hasattr(value, "__dataclass_fields__"):
                        result[field_name] = dataclass_to_dict(value)
                    else:
                        result[field_name] = value
                return result
            return obj

        output = dataclass_to_dict(data)
        print(json.dumps(output, indent=2))
    else:
        # Generate prompt for Claude
        prompt = generate_analysis_prompt(data, detailed=args.detailed)
        print(prompt)

    # Save baseline if requested
    if args.baseline:
        baseline_path = save_baseline(data)
        print(f"\n✓ Baseline saved to: {baseline_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
