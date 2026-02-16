"""Health check runner for the knowledge base.

Discovers all .md files under docs/ (excluding _proposals/),
runs Tier 1 deterministic validators on each, and returns a
structured report.

Only stdlib is used.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# config.py lives in curate/scripts/ — add it to sys.path for cross-skill import.
_curate_scripts = str(Path(__file__).resolve().parent.parent.parent / "curate" / "scripts")
if _curate_scripts not in sys.path:
    sys.path.insert(0, _curate_scripts)

from config import read_knowledge_dir
from history import record_snapshot
from tier2_triggers import (
    trigger_citation_quality,
    trigger_concrete_examples,
    trigger_depth_accuracy,
    trigger_provenance_completeness,
    trigger_recommendation_coverage,
    trigger_source_authority,
    trigger_source_drift,
    trigger_source_primacy,
    trigger_why_quality,
)
from auto_fix import fix_curation_plan_checkmarks, fix_missing_cross_links, fix_missing_sections
from cross_validators import (
    check_curation_plan_sync,
    check_duplicate_content,
    check_link_graph,
    check_manifest_sync,
    check_naming_conventions,
    check_proposal_integrity,
)
from utilization import read_utilization
from validators import (
    check_citation_grounding,
    check_coverage,
    check_cross_references,
    check_freshness,
    check_frontmatter,
    check_go_deeper_links,
    check_heading_hierarchy,
    check_index_sync,
    check_inventory_regression,
    check_placeholder_comments,
    check_readability,
    check_ref_see_also,
    check_section_completeness,
    check_section_ordering,
    check_size_bounds,
    check_source_accessibility,
    check_source_diversity,
    check_source_urls,
    parse_frontmatter,
)


def _discover_md_files(knowledge_base_root: Path, knowledge_dir_name: str = "docs") -> list[Path]:
    """Return all .md files under the knowledge directory, excluding _proposals/ and index.md."""
    knowledge_dir = knowledge_base_root / knowledge_dir_name
    if not knowledge_dir.is_dir():
        return []

    md_files: list[Path] = []
    for md_file in sorted(knowledge_dir.rglob("*.md")):
        # Skip files inside directories that start with _
        parts = md_file.relative_to(knowledge_dir).parts
        if any(part.startswith("_") for part in parts):
            continue
        # Skip structural files (not knowledge topics)
        if md_file.name == "index.md":
            continue
        md_files.append(md_file)

    return md_files


def run_health_check(
    knowledge_base_root: Path,
    *,
    _persist_history: bool = True,
    fix: bool = False,
    dry_run: bool = False,
    check_links: bool = False,
) -> dict:
    """Run all Tier 1 validators and return a structured report.

    Parameters
    ----------
    knowledge_base_root:
        Root directory containing the ``docs/`` folder.
    _persist_history:
        When *True* (default), automatically persist a history snapshot.
        Set to *False* when called from ``run_combined_report`` to avoid
        duplicate entries.
    fix:
        When *True*, apply conservative auto-fixes for fixable issues.
    dry_run:
        When *True*, report what fixes *would* be applied without writing.

    Returns
    -------
    dict
        ``{"issues": [...], "summary": {...}}``
        When *fix* or *dry_run* is set, also includes ``"fixes": [...]``.
    """
    knowledge_dir_name = read_knowledge_dir(knowledge_base_root)
    all_issues: list[dict] = []
    md_files = _discover_md_files(knowledge_base_root, knowledge_dir_name)

    # Compute relative paths for history tracking
    knowledge_dir = knowledge_base_root / knowledge_dir_name
    file_list = [str(f.relative_to(knowledge_dir)) for f in md_files]

    # Per-file validators
    for md_file in md_files:
        all_issues.extend(check_frontmatter(md_file))
        all_issues.extend(check_section_ordering(md_file))
        all_issues.extend(check_cross_references(md_file, knowledge_base_root))
        all_issues.extend(check_size_bounds(md_file))
        all_issues.extend(check_source_urls(md_file))
        all_issues.extend(check_freshness(md_file))
        all_issues.extend(check_section_completeness(md_file))
        all_issues.extend(check_heading_hierarchy(md_file))
        all_issues.extend(check_go_deeper_links(md_file))
        all_issues.extend(check_ref_see_also(md_file))
        all_issues.extend(check_readability(md_file))
        all_issues.extend(check_placeholder_comments(md_file))
        all_issues.extend(check_source_diversity(md_file))
        all_issues.extend(check_citation_grounding(md_file))
        if check_links:
            all_issues.extend(check_source_accessibility(md_file))

    # Structural validators (run once)
    all_issues.extend(check_coverage(knowledge_base_root, knowledge_dir_name=knowledge_dir_name))
    all_issues.extend(check_index_sync(knowledge_base_root, knowledge_dir_name=knowledge_dir_name))
    all_issues.extend(check_inventory_regression(knowledge_base_root, file_list))

    # Cross-file consistency validators
    all_issues.extend(check_manifest_sync(knowledge_base_root, knowledge_dir_name=knowledge_dir_name))
    all_issues.extend(check_curation_plan_sync(knowledge_base_root, knowledge_dir_name=knowledge_dir_name))
    all_issues.extend(check_proposal_integrity(knowledge_base_root, knowledge_dir_name=knowledge_dir_name))
    all_issues.extend(check_link_graph(knowledge_base_root, knowledge_dir_name=knowledge_dir_name))
    all_issues.extend(check_duplicate_content(knowledge_base_root, knowledge_dir_name=knowledge_dir_name))
    all_issues.extend(check_naming_conventions(knowledge_base_root, knowledge_dir_name=knowledge_dir_name))

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

    result = {
        "issues": all_issues,
        "summary": {
            "total_files": len(md_files),
            "fail_count": fail_count,
            "warn_count": warn_count,
            "pass_count": len(md_files) - len(files_with_fails),
        },
    }

    # Auto-fix pass
    if fix or dry_run:
        fixes: list[dict] = []
        for md_file in md_files:
            file_issues = [i for i in all_issues if i.get("file") == str(md_file)]
            if not file_issues:
                continue
            if dry_run:
                # Report what would be done without writing
                for issue in file_issues:
                    msg = issue.get("message", "")
                    if "Missing required section:" in msg:
                        section = msg.split("Missing required section: ", 1)[1]
                        fixes.append({
                            "file": str(md_file),
                            "action": "would_insert_stub_section",
                            "section": section,
                        })
                    elif "See also" in msg or ("Go Deeper" in msg and "ref.md" in msg):
                        fixes.append({
                            "file": str(md_file),
                            "action": "would_insert_cross_link",
                            "detail": msg,
                        })
            else:
                fixes.extend(fix_missing_sections(md_file, file_issues))
                fixes.extend(fix_missing_cross_links(md_file, file_issues))

        # Curation plan auto-fix
        plan_issues = [
            i for i in all_issues
            if "should be checked off" in i.get("message", "")
        ]
        if dry_run:
            for issue in plan_issues:
                fixes.append({
                    "file": issue["file"],
                    "action": "would_check_plan_item",
                    "detail": issue["message"],
                })
        elif plan_issues:
            fixes.extend(fix_curation_plan_checkmarks(
                knowledge_base_root, knowledge_dir_name=knowledge_dir_name,
            ))

        result["fixes"] = fixes

    if _persist_history:
        record_snapshot(knowledge_base_root, result["summary"], None, file_list=file_list)
    return result


_LOW_UTIL_MIN_OVERVIEW_READS = 10

_TIER2_TRIGGERS = [
    trigger_source_drift,
    trigger_depth_accuracy,
    trigger_source_primacy,
    trigger_why_quality,
    trigger_concrete_examples,
    trigger_citation_quality,
    trigger_source_authority,
    trigger_provenance_completeness,
    trigger_recommendation_coverage,
]


def run_tier2_prescreening(knowledge_base_root: Path, *, _persist_history: bool = True) -> dict:
    """Run all Tier 2 deterministic triggers and return a structured queue.

    Parameters
    ----------
    knowledge_base_root:
        Root directory containing the ``docs/`` folder.
    _persist_history:
        When *True* (default), automatically persist a history snapshot.
        Set to *False* when called from ``run_combined_report`` to avoid
        duplicate entries.

    Returns
    -------
    dict
        ``{"queue": [...], "summary": {...}}``
    """
    knowledge_dir_name = read_knowledge_dir(knowledge_base_root)
    md_files = _discover_md_files(knowledge_base_root, knowledge_dir_name)

    knowledge_dir = knowledge_base_root / knowledge_dir_name
    file_list = [str(f.relative_to(knowledge_dir)) for f in md_files]

    queue: list[dict] = []
    trigger_counts: dict[str, int] = {}

    for md_file in md_files:
        for trigger_fn in _TIER2_TRIGGERS:
            for item in trigger_fn(md_file):
                queue.append(item)
                t = item["trigger"]
                trigger_counts[t] = trigger_counts.get(t, 0) + 1

    files_with_triggers = len({item["file"] for item in queue})

    result = {
        "queue": queue,
        "summary": {
            "total_files_scanned": len(md_files),
            "files_with_triggers": files_with_triggers,
            "trigger_counts": trigger_counts,
        },
    }
    if _persist_history:
        record_snapshot(knowledge_base_root, None, result["summary"], file_list=file_list)
    return result


def run_combined_report(knowledge_base_root: Path) -> dict:
    """Run both Tier 1 checks and Tier 2 pre-screening, returning a combined report.

    Parameters
    ----------
    knowledge_base_root:
        Root directory containing the ``docs/`` folder.

    Returns
    -------
    dict
        ``{"tier1": <run_health_check result>, "tier2": <run_tier2_prescreening result>}``
    """
    knowledge_dir_name = read_knowledge_dir(knowledge_base_root)
    md_files = _discover_md_files(knowledge_base_root, knowledge_dir_name)
    knowledge_dir = knowledge_base_root / knowledge_dir_name
    file_list = [str(f.relative_to(knowledge_dir)) for f in md_files]

    result = {
        "tier1": run_health_check(knowledge_base_root, _persist_history=False),
        "tier2": run_tier2_prescreening(knowledge_base_root, _persist_history=False),
    }
    record_snapshot(
        knowledge_base_root, result["tier1"]["summary"], result["tier2"]["summary"],
        file_list=file_list,
    )
    return result


def generate_recommendations(
    knowledge_base_root: Path,
    min_reads: int = 10,
    min_days: int = 7,
) -> dict:
    """Generate curation recommendations from utilization and health data.

    Cross-references utilization log (which files agents actually read)
    against the file inventory and health signals to surface actionable
    curation suggestions.

    Parameters
    ----------
    knowledge_base_root:
        Root directory containing the knowledge base.
    min_reads:
        Minimum total reads across all files before recommendations
        are generated.  Set to 0 to bypass.
    min_days:
        Minimum number of days spanned by utilization data before
        recommendations are generated.  Set to 0 to bypass.

    Returns
    -------
    dict
        ``{"recommendations": [...], "summary": {...}}``
        or ``{"recommendations": [], "skipped": str}`` if gating fails.
    """
    knowledge_dir_name = read_knowledge_dir(knowledge_base_root)
    md_files = _discover_md_files(knowledge_base_root, knowledge_dir_name)
    knowledge_dir = knowledge_base_root / knowledge_dir_name

    # Build file paths relative to knowledge_base_root (with knowledge_dir prefix)
    file_paths = {}
    for f in md_files:
        rel_to_kd = str(f.relative_to(knowledge_dir))
        rel_to_root = f"{knowledge_dir_name}/{rel_to_kd}"
        file_paths[rel_to_root] = f

    # Read utilization data
    utilization = read_utilization(knowledge_base_root)

    # --- Gating ---
    total_reads = sum(entry["count"] for entry in utilization.values())

    if not utilization or total_reads < min_reads:
        return {
            "recommendations": [],
            "skipped": (
                f"Insufficient data: {total_reads} reads"
                f" (need {min_reads} reads over {min_days} days)"
            ),
        }

    # Check day span
    all_timestamps = []
    for entry in utilization.values():
        all_timestamps.append(entry["first_referenced"])
        all_timestamps.append(entry["last_referenced"])
    if all_timestamps:
        earliest = min(all_timestamps)
        latest = max(all_timestamps)
        try:
            earliest_dt = datetime.fromisoformat(earliest)
            latest_dt = datetime.fromisoformat(latest)
            day_span = (latest_dt - earliest_dt).days
        except ValueError:
            day_span = 0
    else:
        day_span = 0

    if day_span < min_days:
        return {
            "recommendations": [],
            "skipped": (
                f"Insufficient data: {total_reads} reads over {day_span} day(s)"
                f" (need {min_reads} reads over {min_days} days)"
            ),
        }

    # --- Build per-file stats ---
    read_counts = {}
    for rel_path in file_paths:
        entry = utilization.get(rel_path)
        read_counts[rel_path] = entry["count"] if entry else 0

    # Compute median read count
    counts = sorted(read_counts.values())
    mid = len(counts) // 2
    if len(counts) % 2 == 0 and len(counts) > 0:
        median_reads = (counts[mid - 1] + counts[mid]) / 2
    elif counts:
        median_reads = counts[mid]
    else:
        median_reads = 0

    # Group by area
    areas: dict[str, dict] = {}
    for rel_path, abs_path in file_paths.items():
        # rel_path is like "docs/area/file.md"
        parts = rel_path.split("/")
        if len(parts) < 3:
            continue
        area_name = parts[1]
        filename = parts[-1]

        if area_name not in areas:
            areas[area_name] = {"overview_reads": 0, "files": {}}

        areas[area_name]["files"][rel_path] = {
            "abs_path": abs_path,
            "reads": read_counts.get(rel_path, 0),
            "is_overview": filename == "overview.md",
        }
        if filename == "overview.md":
            areas[area_name]["overview_reads"] = read_counts.get(rel_path, 0)

    # Read depth from frontmatter for each file
    depths = {}
    for rel_path, abs_path in file_paths.items():
        try:
            fm = parse_frontmatter(abs_path)
            depths[rel_path] = fm.get("depth", "")
        except Exception:
            depths[rel_path] = ""

    # Check freshness for high-read files
    stale_files: set[str] = set()
    for rel_path, abs_path in file_paths.items():
        if read_counts.get(rel_path, 0) > median_reads:
            issues = check_freshness(abs_path)
            if issues:
                stale_files.add(rel_path)

    # --- Classify files ---
    recommendations: list[dict] = []
    classified: set[str] = set()

    # Priority 1: stale_high_use
    for rel_path in sorted(file_paths):
        if rel_path in stale_files:
            area_parts = rel_path.split("/")
            area_name = area_parts[1] if len(area_parts) >= 3 else ""
            recommendations.append({
                "file": rel_path,
                "recommendation": "stale_high_use",
                "reason": (
                    f"Read {read_counts[rel_path]} times but content is stale"
                    " -- prioritize freshening"
                ),
                "data": {
                    "read_count": read_counts[rel_path],
                    "depth": depths.get(rel_path, ""),
                    "area": area_name,
                },
            })
            classified.add(rel_path)

    # Priority 2: expand_depth
    for rel_path in sorted(file_paths):
        if rel_path in classified:
            continue
        if depths.get(rel_path) != "overview":
            continue
        reads = read_counts.get(rel_path, 0)
        if median_reads > 0 and reads > 2 * median_reads:
            area_parts = rel_path.split("/")
            area_name = area_parts[1] if len(area_parts) >= 3 else ""
            recommendations.append({
                "file": rel_path,
                "recommendation": "expand_depth",
                "reason": (
                    f"Read {reads} times but only overview depth"
                    " -- consider adding working-knowledge file"
                ),
                "data": {
                    "read_count": reads,
                    "depth": "overview",
                    "area": area_name,
                },
            })
            classified.add(rel_path)

    # Priority 3: low_utilization
    for area_name, area_data in sorted(areas.items()):
        overview_reads = area_data["overview_reads"]
        if overview_reads < _LOW_UTIL_MIN_OVERVIEW_READS:
            continue
        threshold = overview_reads * 0.1
        for rel_path, info in sorted(area_data["files"].items()):
            if rel_path in classified:
                continue
            if info["is_overview"]:
                continue
            if info["reads"] < threshold:
                recommendations.append({
                    "file": rel_path,
                    "recommendation": "low_utilization",
                    "reason": (
                        f"Read {info['reads']} times vs {overview_reads}"
                        f" for {area_name} overview"
                        " -- consider demoting or merging"
                    ),
                    "data": {
                        "read_count": info["reads"],
                        "overview_reads": overview_reads,
                        "depth": depths.get(rel_path, ""),
                        "area": area_name,
                    },
                })
                classified.add(rel_path)

    # Priority 4: never_referenced
    for rel_path in sorted(file_paths):
        if rel_path in classified:
            continue
        if read_counts.get(rel_path, 0) == 0:
            area_parts = rel_path.split("/")
            area_name = area_parts[1] if len(area_parts) >= 3 else ""
            recommendations.append({
                "file": rel_path,
                "recommendation": "never_referenced",
                "reason": "No reads recorded -- review relevance or discoverability",
                "data": {
                    "read_count": 0,
                    "depth": depths.get(rel_path, ""),
                    "area": area_name,
                },
            })
            classified.add(rel_path)

    # --- Summary ---
    by_category: dict[str, int] = {}
    for rec in recommendations:
        cat = rec["recommendation"]
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "recommendations": recommendations,
        "summary": {
            "total_files": len(file_paths),
            "files_with_recommendations": len(recommendations),
            "by_category": by_category,
        },
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run knowledge base health checks.")
    parser.add_argument(
        "--knowledge-base-root",
        required=True,
        help="Knowledge-base root directory containing the docs/ folder.",
    )
    parser.add_argument(
        "--tier2",
        action="store_true",
        help="Run Tier 2 pre-screening instead of Tier 1 checks.",
    )
    parser.add_argument(
        "--both",
        action="store_true",
        help="Run both Tier 1 checks and Tier 2 pre-screening.",
    )
    parser.add_argument(
        "--recommendations",
        action="store_true",
        help="Generate utilization-driven curation recommendations.",
    )
    parser.add_argument(
        "--min-reads",
        type=int,
        default=10,
        help="Minimum total reads before generating recommendations (default: 10).",
    )
    parser.add_argument(
        "--min-days",
        type=int,
        default=7,
        help="Minimum days of utilization data before generating recommendations (default: 7).",
    )
    parser.add_argument(
        "--check-links",
        action="store_true",
        help="Check source URL accessibility (requires network).",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply conservative auto-fixes for fixable issues.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what fixes would be applied without writing.",
    )
    args = parser.parse_args()

    knowledge_base_path = Path(args.knowledge_base_root)

    if args.both and args.recommendations:
        report = run_combined_report(knowledge_base_path)
        report["recommendations"] = generate_recommendations(
            knowledge_base_path, min_reads=args.min_reads, min_days=args.min_days,
        )
    elif args.both:
        report = run_combined_report(knowledge_base_path)
    elif args.tier2 and args.recommendations:
        report = {
            "tier2": run_tier2_prescreening(knowledge_base_path),
            "recommendations": generate_recommendations(
                knowledge_base_path, min_reads=args.min_reads, min_days=args.min_days,
            ),
        }
    elif args.tier2:
        report = run_tier2_prescreening(knowledge_base_path)
    elif args.recommendations:
        report = generate_recommendations(
            knowledge_base_path, min_reads=args.min_reads, min_days=args.min_days,
        )
    else:
        report = run_health_check(knowledge_base_path, fix=args.fix, dry_run=args.dry_run, check_links=args.check_links)
    print(json.dumps(report, indent=2))
