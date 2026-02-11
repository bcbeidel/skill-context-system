#!/usr/bin/env python3
"""Generate context health dashboard reports.

Reads baseline and historical data to generate trend-based reports.
"""

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


@dataclass
class Snapshot:
    """A point-in-time snapshot of context metrics."""
    timestamp: str
    directory: str
    total_files: int
    total_tokens: int
    total_lines: int
    total_bytes: int
    large_files: int
    duplication_percentage: Optional[float] = None


@dataclass
class TrendData:
    """Trend analysis data."""
    current: Snapshot
    previous: Optional[Snapshot]
    change_tokens: int
    change_tokens_pct: float
    change_files: int
    change_large_files: int
    period_days: int


@dataclass
class ReportData:
    """Complete report data."""
    report_type: str
    generated: str
    current_snapshot: Snapshot
    trend: Optional[TrendData]
    has_historical_data: bool


def load_baseline(baseline_path: Optional[Path] = None) -> Optional[Snapshot]:
    """Load current baseline snapshot.

    Args:
        baseline_path: Path to baseline.json (default: ~/.claude/analytics/baseline.json)

    Returns:
        Snapshot or None if doesn't exist
    """
    if baseline_path is None:
        baseline_path = Path.home() / ".claude" / "analytics" / "baseline.json"

    if not baseline_path.exists():
        return None

    try:
        with open(baseline_path) as f:
            data = json.load(f)

        return Snapshot(
            timestamp=data["timestamp"],
            directory=data["directory"],
            total_files=data["total_files"],
            total_tokens=data["total_tokens"],
            total_lines=data["total_lines"],
            total_bytes=data["total_bytes"],
            large_files=len(data.get("large_files", [])),
            duplication_percentage=None,  # Not in baseline currently
        )
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error loading baseline: {e}", file=sys.stderr)
        return None


def load_historical_snapshots(history_dir: Optional[Path] = None) -> list[Snapshot]:
    """Load historical snapshots if they exist.

    Args:
        history_dir: Directory containing historical snapshots

    Returns:
        List of snapshots, sorted by timestamp (newest first)
    """
    if history_dir is None:
        history_dir = Path.home() / ".claude" / "analytics" / "history"

    if not history_dir.exists():
        return []

    snapshots = []

    for snapshot_file in history_dir.glob("snapshot-*.json"):
        try:
            with open(snapshot_file) as f:
                data = json.load(f)

            snapshots.append(
                Snapshot(
                    timestamp=data["timestamp"],
                    directory=data["directory"],
                    total_files=data["total_files"],
                    total_tokens=data["total_tokens"],
                    total_lines=data["total_lines"],
                    total_bytes=data["total_bytes"],
                    large_files=len(data.get("large_files", [])),
                    duplication_percentage=data.get("duplication_percentage"),
                )
            )
        except (json.JSONDecodeError, KeyError):
            continue

    # Sort by timestamp (newest first)
    snapshots.sort(key=lambda s: s.timestamp, reverse=True)

    return snapshots


def find_comparison_snapshot(
    snapshots: list[Snapshot],
    current_time: datetime,
    days_back: int
) -> Optional[Snapshot]:
    """Find a snapshot approximately N days back.

    Args:
        snapshots: List of historical snapshots
        current_time: Current datetime
        days_back: How many days to look back

    Returns:
        Snapshot closest to target date or None
    """
    if not snapshots:
        return None

    target_time = current_time - timedelta(days=days_back)

    # Find closest snapshot to target
    closest = None
    min_diff = None

    for snapshot in snapshots:
        try:
            snap_time = datetime.fromisoformat(snapshot.timestamp)
            diff = abs((snap_time - target_time).total_seconds())

            if min_diff is None or diff < min_diff:
                min_diff = diff
                closest = snapshot
        except ValueError:
            continue

    return closest


def calculate_trends(current: Snapshot, previous: Optional[Snapshot]) -> Optional[TrendData]:
    """Calculate trend data between two snapshots.

    Args:
        current: Current snapshot
        previous: Previous snapshot

    Returns:
        TrendData or None if no previous snapshot
    """
    if previous is None:
        return None

    # Calculate changes
    change_tokens = current.total_tokens - previous.total_tokens
    change_tokens_pct = (
        (change_tokens / previous.total_tokens * 100)
        if previous.total_tokens > 0
        else 0
    )
    change_files = current.total_files - previous.total_files
    change_large_files = current.large_files - previous.large_files

    # Calculate period
    try:
        current_time = datetime.fromisoformat(current.timestamp)
        previous_time = datetime.fromisoformat(previous.timestamp)
        period_days = (current_time - previous_time).days
    except ValueError:
        period_days = 7  # Default assumption

    return TrendData(
        current=current,
        previous=previous,
        change_tokens=change_tokens,
        change_tokens_pct=change_tokens_pct,
        change_files=change_files,
        change_large_files=change_large_files,
        period_days=period_days,
    )


def generate_report_prompt(report_data: ReportData) -> str:
    """Generate prompt for Claude to format the report.

    Args:
        report_data: Complete report data

    Returns:
        Formatted prompt string
    """
    current = report_data.current_snapshot

    prompt = f"""I need your help generating a {report_data.report_type} context health dashboard.

**Report Type:** {report_data.report_type}
**Generated:** {report_data.generated}
**Directory:** {current.directory}

"""

    # Current metrics
    prompt += f"""**Current Metrics:**
- Total Files: {current.total_files:,}
- Total Tokens: {current.total_tokens:,}
- Total Lines: {current.total_lines:,}
- Large Files (>500 lines): {current.large_files}
- Average Tokens/File: {current.total_tokens // current.total_files if current.total_files > 0 else 0:,}
"""

    # Trend data if available
    if report_data.trend:
        trend = report_data.trend
        prev = trend.previous

        prompt += f"""

**{trend.period_days}-Day Comparison:**

Previous ({prev.timestamp}):
- Files: {prev.total_files:,}
- Tokens: {prev.total_tokens:,}
- Large Files: {prev.large_files}

Changes:
- Files: {trend.change_files:+,} ({'+' if trend.change_files >= 0 else ''}{trend.change_files / prev.total_files * 100:.1f}% if prev.total_files else 0)
- Tokens: {trend.change_tokens:+,} ({trend.change_tokens_pct:+.1f}%)
- Large Files: {trend.change_large_files:+}

**Trend Analysis:**
"""

        # Interpret trend
        if trend.change_tokens_pct < -10:
            prompt += "- ✅ Significant improvement! Tokens reduced by >10%\n"
        elif trend.change_tokens_pct < -5:
            prompt += "- ✅ Good progress, tokens decreasing\n"
        elif -5 <= trend.change_tokens_pct <= 5:
            prompt += "- ➡️ Stable (< 5% change)\n"
        elif trend.change_tokens_pct <= 20:
            prompt += "- ⚠️ Growing (5-20% increase)\n"
        else:
            prompt += "- ❌ Rapid growth (>20% increase) - needs attention\n"

        if trend.change_large_files < 0:
            prompt += f"- ✅ Large files reduced (now {current.large_files})\n"
        elif trend.change_large_files > 0:
            prompt += f"- ⚠️ Large files increased (now {current.large_files})\n"

    else:
        prompt += """

**Historical Data:** None available

This is the first report or no historical data exists yet.
Focus on:
- Establishing baseline understanding
- Setting up tracking
- Initial optimization opportunities
"""

    prompt += """

**Your Task:**

Generate a comprehensive dashboard report following the format specified in:
- workflows/report-weekly.md (if weekly)
- workflows/report-monthly.md (if monthly)
- workflows/report-custom.md (if custom)

The report should include:
1. Title and summary section
2. Key metrics table with trends (if available)
3. Highlights (wins or concerns based on trends)
4. Detailed metrics breakdown
5. Recommendations prioritized by impact
6. Next steps and goals

**Important:**
- Use the exact dashboard format from the workflow
- Include emoji indicators for visual clarity
- Interpret trends, don't just report numbers
- Provide specific, actionable recommendations
- Celebrate wins if improvements detected
- Flag concerns if degradation detected

**Output:**
Generate the complete markdown dashboard that should be saved to
`.claude/analytics/dashboard.md` (or custom path if specified).
"""

    return prompt


def save_snapshot(snapshot: Snapshot, history_dir: Optional[Path] = None):
    """Save current snapshot to history for future trend analysis.

    Args:
        snapshot: Snapshot to save
        history_dir: Directory to save to (default: ~/.claude/analytics/history/)
    """
    if history_dir is None:
        history_dir = Path.home() / ".claude" / "analytics" / "history"

    history_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename from timestamp
    timestamp = snapshot.timestamp.replace(":", "-").replace(".", "-")
    filename = f"snapshot-{timestamp}.json"
    filepath = history_dir / filename

    with open(filepath, "w") as f:
        json.dump(asdict(snapshot), f, indent=2)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate context health report")
    parser.add_argument(
        "--weekly",
        action="store_true",
        help="Generate weekly report (last 7 days)",
    )
    parser.add_argument(
        "--monthly",
        action="store_true",
        help="Generate monthly report (last 30 days)",
    )
    parser.add_argument(
        "--custom",
        action="store_true",
        help="Generate custom report",
    )
    parser.add_argument(
        "--from",
        dest="from_date",
        type=str,
        help="Start date for custom report (ISO format)",
    )
    parser.add_argument(
        "--to",
        dest="to_date",
        type=str,
        help="End date for custom report (ISO format)",
    )
    parser.add_argument(
        "--save-snapshot",
        action="store_true",
        help="Save current baseline as historical snapshot",
    )

    args = parser.parse_args()

    # Determine report type
    if args.monthly:
        report_type = "Monthly"
        days_back = 30
    elif args.custom:
        report_type = "Custom"
        days_back = None  # Handled separately
    else:
        report_type = "Weekly"
        days_back = 7

    # Load current baseline
    current = load_baseline()

    if current is None:
        print("""
❌ No baseline found

You need to create a baseline first:
  /dewey:analyze --baseline

This will save your current state for tracking and reporting.
""", file=sys.stderr)
        sys.exit(1)

    # Load historical data
    historical = load_historical_snapshots()

    # Find comparison snapshot
    if days_back:
        current_time = datetime.fromisoformat(current.timestamp)
        previous = find_comparison_snapshot(historical, current_time, days_back)
    else:
        previous = None  # Custom report, handle differently

    # Calculate trends
    trend = calculate_trends(current, previous)

    # Build report data
    report_data = ReportData(
        report_type=report_type,
        generated=datetime.now().isoformat(),
        current_snapshot=current,
        trend=trend,
        has_historical_data=len(historical) > 0,
    )

    # Save current as snapshot if requested
    if args.save_snapshot:
        save_snapshot(current)
        print(f"✓ Snapshot saved to history", file=sys.stderr)

    # Generate prompt
    prompt = generate_report_prompt(report_data)
    print(prompt)


if __name__ == "__main__":
    main()
