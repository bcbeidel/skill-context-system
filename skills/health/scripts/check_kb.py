"""Health check runner for the knowledge base.

Discovers all .md files under knowledge/ (excluding _proposals/),
runs Tier 1 deterministic validators on each, and returns a
structured report.

Only stdlib is used.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from skills.health.scripts.validators import (
        check_coverage,
        check_cross_references,
        check_freshness,
        check_frontmatter,
        check_section_ordering,
        check_size_bounds,
        check_source_urls,
    )
except ModuleNotFoundError:
    _project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)
    from skills.health.scripts.validators import (
        check_coverage,
        check_cross_references,
        check_freshness,
        check_frontmatter,
        check_section_ordering,
        check_size_bounds,
        check_source_urls,
    )


def _discover_md_files(kb_root: Path) -> list[Path]:
    """Return all .md files under knowledge/, excluding _proposals/."""
    knowledge_dir = kb_root / "knowledge"
    if not knowledge_dir.is_dir():
        return []

    md_files: list[Path] = []
    for md_file in sorted(knowledge_dir.rglob("*.md")):
        # Skip files inside directories that start with _
        parts = md_file.relative_to(knowledge_dir).parts
        if any(part.startswith("_") for part in parts):
            continue
        md_files.append(md_file)

    return md_files


def run_health_check(kb_root: Path) -> dict:
    """Run all Tier 1 validators and return a structured report.

    Parameters
    ----------
    kb_root:
        Root directory containing the ``knowledge/`` folder.

    Returns
    -------
    dict
        ``{"issues": [...], "summary": {...}}``
    """
    all_issues: list[dict] = []
    md_files = _discover_md_files(kb_root)

    # Per-file validators
    for md_file in md_files:
        all_issues.extend(check_frontmatter(md_file))
        all_issues.extend(check_section_ordering(md_file))
        all_issues.extend(check_cross_references(md_file, kb_root))
        all_issues.extend(check_size_bounds(md_file))
        all_issues.extend(check_source_urls(md_file))
        all_issues.extend(check_freshness(md_file))

    # Structural validators (run once)
    all_issues.extend(check_coverage(kb_root))

    # Build summary
    files_with_fails = set()
    files_with_warns = set()
    all_mentioned_files = set()

    for issue in all_issues:
        f = issue.get("file", "")
        all_mentioned_files.add(f)
        if issue["severity"] == "fail":
            files_with_fails.add(f)
        elif issue["severity"] == "warn":
            files_with_warns.add(f)

    fail_count = sum(1 for i in all_issues if i["severity"] == "fail")
    warn_count = sum(1 for i in all_issues if i["severity"] == "warn")

    return {
        "issues": all_issues,
        "summary": {
            "total_files": len(md_files),
            "fail_count": fail_count,
            "warn_count": warn_count,
            "pass_count": len(md_files) - len(files_with_fails),
        },
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run KB health checks.")
    parser.add_argument(
        "--kb-root",
        required=True,
        help="Root directory containing the knowledge/ folder.",
    )
    args = parser.parse_args()

    report = run_health_check(Path(args.kb_root))
    print(json.dumps(report, indent=2))
