#!/usr/bin/env python3
"""Quality validation script for context files.

Validates:
- File sizes (<500 lines)
- Dead links
- Content duplication
- Token budgets
"""

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class FileSizeViolation:
    """File size violation."""
    file: str
    lines: int
    threshold: int
    severity: str  # 'warn' or 'fail'


@dataclass
class DeadLink:
    """Dead link violation."""
    source_file: str
    line_number: int
    link_text: str
    target_path: str


@dataclass
class DuplicationInfo:
    """Duplication information."""
    percentage: float
    duplicate_blocks: int
    total_blocks: int
    examples: list[dict] = field(default_factory=list)


@dataclass
class ValidationResults:
    """Complete validation results."""
    summary: dict
    file_size_violations: list[FileSizeViolation]
    dead_links: list[DeadLink]
    duplication: Optional[DuplicationInfo]
    exit_code: int


def estimate_tokens(text: str) -> int:
    """Estimate token count using character heuristic.

    Args:
        text: Text to estimate

    Returns:
        Estimated token count (1 token ≈ 4 characters)
    """
    return len(text) // 4


def check_file_sizes(
    directory: Path,
    warn_threshold: int = 400,
    fail_threshold: int = 500,
    extensions: Optional[list[str]] = None,
) -> list[FileSizeViolation]:
    """Check file sizes against thresholds.

    Args:
        directory: Directory to check
        warn_threshold: Warning threshold in lines
        fail_threshold: Failure threshold in lines
        extensions: File extensions to check

    Returns:
        List of file size violations
    """
    if extensions is None:
        extensions = [".md"]

    violations = []

    for ext in extensions:
        for file_path in directory.rglob(f"*{ext}"):
            # Skip hidden files and excluded directories
            if any(part.startswith(".") for part in file_path.parts):
                continue
            if "node_modules" in file_path.parts or "archive" in file_path.parts:
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    lines = len(f.readlines())

                if lines > fail_threshold:
                    violations.append(
                        FileSizeViolation(
                            file=str(file_path.relative_to(directory)),
                            lines=lines,
                            threshold=fail_threshold,
                            severity="fail",
                        )
                    )
                elif lines > warn_threshold:
                    violations.append(
                        FileSizeViolation(
                            file=str(file_path.relative_to(directory)),
                            lines=lines,
                            threshold=warn_threshold,
                            severity="warn",
                        )
                    )
            except (IOError, UnicodeDecodeError):
                # Skip files that can't be read
                continue

    return violations


def check_links(
    directory: Path,
    extensions: Optional[list[str]] = None,
    fast_mode: bool = False,
) -> list[DeadLink]:
    """Check for dead internal links.

    Args:
        directory: Directory to check
        extensions: File extensions to check
        fast_mode: Skip if true (slow check)

    Returns:
        List of dead links
    """
    if fast_mode:
        return []  # Skip in fast mode

    if extensions is None:
        extensions = [".md"]

    dead_links = []
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    for ext in extensions:
        for file_path in directory.rglob(f"*{ext}"):
            # Skip hidden and excluded
            if any(part.startswith(".") for part in file_path.parts):
                continue
            if "node_modules" in file_path.parts or "archive" in file_path.parts:
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        for match in link_pattern.finditer(line):
                            link_text, target = match.groups()

                            # Skip external links and anchors
                            if target.startswith(("http://", "https://", "#")):
                                continue

                            # Resolve relative path
                            target_path = (file_path.parent / target).resolve()

                            if not target_path.exists():
                                dead_links.append(
                                    DeadLink(
                                        source_file=str(file_path.relative_to(directory)),
                                        line_number=line_num,
                                        link_text=link_text,
                                        target_path=target,
                                    )
                                )
            except (IOError, UnicodeDecodeError):
                continue

    return dead_links


def detect_duplication(
    directory: Path,
    extensions: Optional[list[str]] = None,
    fast_mode: bool = False,
) -> Optional[DuplicationInfo]:
    """Detect content duplication across files.

    Args:
        directory: Directory to check
        extensions: File extensions to check
        fast_mode: Skip if true (slow check)

    Returns:
        Duplication information or None
    """
    if fast_mode:
        return None  # Skip in fast mode

    if extensions is None:
        extensions = [".md"]

    # Hash paragraph blocks (3+ lines)
    block_hashes = {}  # hash -> list of (file, line_num)

    for ext in extensions:
        for file_path in directory.rglob(f"*{ext}"):
            # Skip hidden and excluded
            if any(part.startswith(".") for part in file_path.parts):
                continue
            if "node_modules" in file_path.parts or "archive" in file_path.parts:
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    lines = f.readlines()

                # Extract paragraph blocks
                current_block = []
                block_start = 0

                for i, line in enumerate(lines, 1):
                    if line.strip():
                        if not current_block:
                            block_start = i
                        current_block.append(line)
                    else:
                        if len(current_block) >= 3:
                            # Hash this block
                            block_text = "".join(current_block).strip()
                            block_hash = hashlib.md5(block_text.encode()).hexdigest()

                            if block_hash not in block_hashes:
                                block_hashes[block_hash] = []

                            block_hashes[block_hash].append(
                                {
                                    "file": str(file_path.relative_to(directory)),
                                    "line": block_start,
                                }
                            )

                        current_block = []

                # Don't forget last block
                if len(current_block) >= 3:
                    block_text = "".join(current_block).strip()
                    block_hash = hashlib.md5(block_text.encode()).hexdigest()

                    if block_hash not in block_hashes:
                        block_hashes[block_hash] = []

                    block_hashes[block_hash].append(
                        {
                            "file": str(file_path.relative_to(directory)),
                            "line": block_start,
                        }
                    )

            except (IOError, UnicodeDecodeError):
                continue

    # Calculate duplication
    total_blocks = sum(len(locs) for locs in block_hashes.values())
    duplicate_blocks = sum(len(locs) - 1 for locs in block_hashes.values() if len(locs) > 1)

    percentage = (duplicate_blocks / total_blocks * 100) if total_blocks > 0 else 0

    # Get examples of duplicated blocks (up to 3)
    examples = []
    for block_hash, locations in block_hashes.items():
        if len(locations) > 1 and len(examples) < 3:
            examples.append(
                {
                    "locations": locations,
                    "count": len(locations),
                }
            )

    return DuplicationInfo(
        percentage=percentage,
        duplicate_blocks=duplicate_blocks,
        total_blocks=total_blocks,
        examples=examples,
    )


def check_token_budget(
    directory: Path,
    limit: int = 200000,
    extensions: Optional[list[str]] = None,
) -> tuple[int, float]:
    """Check token budget usage.

    Args:
        directory: Directory to check
        limit: Token limit
        extensions: File extensions to check

    Returns:
        Tuple of (total_tokens, percentage_of_limit)
    """
    if extensions is None:
        extensions = [".md"]

    total_tokens = 0

    for ext in extensions:
        for file_path in directory.rglob(f"*{ext}"):
            # Skip hidden and excluded
            if any(part.startswith(".") for part in file_path.parts):
                continue
            if "node_modules" in file_path.parts or "archive" in file_path.parts:
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                    total_tokens += estimate_tokens(content)
            except (IOError, UnicodeDecodeError):
                continue

    percentage = (total_tokens / limit * 100) if limit > 0 else 0

    return total_tokens, percentage


def determine_exit_code(
    file_violations: list[FileSizeViolation],
    dead_links: list[DeadLink],
    duplication: Optional[DuplicationInfo],
    token_percentage: float,
) -> int:
    """Determine exit code from validation results.

    Returns:
        0 = PASS
        1 = WARN
        2 = FAIL
    """
    # Check for failures
    has_file_failures = any(v.severity == "fail" for v in file_violations)
    has_many_dead_links = len(dead_links) > 2
    has_high_duplication = duplication and duplication.percentage > 20
    has_budget_exceeded = token_percentage > 100

    if has_file_failures or has_many_dead_links or has_high_duplication or has_budget_exceeded:
        return 2  # FAIL

    # Check for warnings
    has_file_warnings = any(v.severity == "warn" for v in file_violations)
    has_some_dead_links = len(dead_links) > 0
    has_moderate_duplication = duplication and duplication.percentage > 10
    has_high_budget = token_percentage > 80

    if has_file_warnings or has_some_dead_links or has_moderate_duplication or has_high_budget:
        return 1  # WARN

    return 0  # PASS


def generate_analysis_prompt(results: ValidationResults) -> str:
    """Generate prompt for Claude to analyze validation results.

    Args:
        results: Validation results

    Returns:
        Formatted prompt string
    """
    status_emoji = {0: "✅", 1: "⚠️", 2: "❌"}
    status_text = {0: "PASS", 1: "WARN", 2: "FAIL"}

    prompt = f"""I need your help analyzing context quality validation results.

**Directory**: {results.summary['directory']}
**Status**: {status_text[results.exit_code]} {status_emoji[results.exit_code]}
**Exit Code**: {results.exit_code}

**Summary**:
- Files Checked: {results.summary['files_checked']}
- Total Tokens: {results.summary['total_tokens']:,}
- Token Budget: {results.summary['token_budget_percentage']:.1f}% of {results.summary['token_limit']:,}
- Duplication: {results.summary.get('duplication_percentage', 'N/A')}%

"""

    # File size violations
    if results.file_size_violations:
        failures = [v for v in results.file_size_violations if v.severity == "fail"]
        warnings = [v for v in results.file_size_violations if v.severity == "warn"]

        if failures:
            prompt += "\n**File Size FAILURES** (>500 lines):\n"
            for v in failures:
                prompt += f"  • {v.file} ({v.lines} lines)\n"

        if warnings:
            prompt += "\n**File Size WARNINGS** (400-500 lines):\n"
            for v in warnings:
                prompt += f"  • {v.file} ({v.lines} lines)\n"

    # Dead links
    if results.dead_links:
        prompt += f"\n**Dead Links** ({len(results.dead_links)} found):\n"
        for link in results.dead_links[:5]:  # Show first 5
            prompt += f"  • {link.source_file}:{link.line_number} → {link.target_path}\n"
        if len(results.dead_links) > 5:
            prompt += f"  ... and {len(results.dead_links) - 5} more\n"

    # Duplication
    if results.duplication and results.duplication.percentage > 10:
        dup = results.duplication
        prompt += f"\n**Duplication**: {dup.percentage:.1f}%\n"
        prompt += f"  • {dup.duplicate_blocks} duplicate blocks out of {dup.total_blocks} total\n"

        if dup.examples:
            prompt += "  • Example duplicates:\n"
            for ex in dup.examples:
                files = ", ".join(f"{loc['file']}" for loc in ex["locations"][:3])
                prompt += f"    - Found in: {files}\n"

    prompt += """

**Your Task**:

Generate a comprehensive quality validation report following the format in the workflow.

The report should include:
1. Clear status (PASS/WARN/FAIL) with emoji
2. Summary statistics
3. Categorized issues (Failures vs Warnings)
4. Specific recommendations with exact commands
5. Next steps based on status
6. Exit code explanation

Follow the report format exactly as specified in workflows/check-standard.md.
"""

    return prompt


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Validate context quality")
    parser.add_argument(
        "directory",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Directory to validate (default: current directory)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode: skip slow checks (link validation, detailed duplication)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )
    parser.add_argument(
        "--token-limit",
        type=int,
        default=200000,
        help="Token budget limit (default: 200000)",
    )
    parser.add_argument(
        "--warn-threshold",
        type=int,
        default=400,
        help="File size warning threshold in lines (default: 400)",
    )
    parser.add_argument(
        "--fail-threshold",
        type=int,
        default=500,
        help="File size failure threshold in lines (default: 500)",
    )

    args = parser.parse_args()

    # Validate directory
    if not args.directory.exists():
        print(f"Error: Directory not found: {args.directory}", file=sys.stderr)
        sys.exit(3)

    if not args.directory.is_dir():
        print(f"Error: Not a directory: {args.directory}", file=sys.stderr)
        sys.exit(3)

    # Run validation checks
    file_violations = check_file_sizes(
        args.directory,
        warn_threshold=args.warn_threshold,
        fail_threshold=args.fail_threshold,
    )

    dead_links = check_links(args.directory, fast_mode=args.fast)

    duplication = detect_duplication(args.directory, fast_mode=args.fast)

    total_tokens, token_percentage = check_token_budget(args.directory, limit=args.token_limit)

    # Count files
    files_checked = sum(
        1
        for ext in [".md"]
        for _ in args.directory.rglob(f"*{ext}")
        if not any(part.startswith(".") for part in _.parts)
        and "node_modules" not in _.parts
        and "archive" not in _.parts
    )

    # Determine exit code
    exit_code = determine_exit_code(
        file_violations,
        dead_links,
        duplication,
        token_percentage,
    )

    # Build results
    results = ValidationResults(
        summary={
            "directory": str(args.directory),
            "files_checked": files_checked,
            "total_tokens": total_tokens,
            "token_limit": args.token_limit,
            "token_budget_percentage": token_percentage,
            "duplication_percentage": duplication.percentage if duplication else None,
            "fast_mode": args.fast,
        },
        file_size_violations=file_violations,
        dead_links=dead_links,
        duplication=duplication,
        exit_code=exit_code,
    )

    # Output
    if args.json:
        # JSON output for programmatic use
        output = {
            "summary": results.summary,
            "failures": [
                {"type": "file_size", **asdict(v)}
                for v in file_violations
                if v.severity == "fail"
            ]
            + [{"type": "dead_link", **asdict(link)} for link in dead_links],
            "warnings": [
                {"type": "file_size", **asdict(v)}
                for v in file_violations
                if v.severity == "warn"
            ],
            "duplication": asdict(duplication) if duplication else None,
            "exit_code": exit_code,
        }
        print(json.dumps(output, indent=2))
    else:
        # Generate prompt for Claude
        prompt = generate_analysis_prompt(results)
        print(prompt)

    # Exit with appropriate code
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
