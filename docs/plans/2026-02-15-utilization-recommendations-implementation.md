# Utilization-Driven Curation Recommendations Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `--recommendations` flag to `check_kb.py` that cross-references utilization data against the file inventory to surface actionable curation recommendations (never-referenced files, expand-depth candidates, low-utilization content, stale high-use files).

**Architecture:** New `generate_recommendations()` function in `check_kb.py` reads `read_utilization()` for per-file read counts and `_discover_md_files()` for the current inventory. Files are grouped by area, classified into recommendation categories, and returned as `list[dict]`. Configurable `--min-reads` and `--min-days` thresholds gate output to avoid noisy recommendations from sparse data.

**Tech Stack:** Python 3.9+ stdlib only. unittest.TestCase. No external dependencies.

**Design doc:** `docs/plans/2026-02-15-utilization-recommendations-design.md`

---

### Task 1: Core recommendation engine — `generate_recommendations()`

**Files:**
- Create: `tests/skills/health/test_recommendations.py`
- Modify: `dewey/skills/health/scripts/check_kb.py`

**Step 1: Write the failing tests**

Create `tests/skills/health/test_recommendations.py`:

```python
"""Tests for utilization-driven curation recommendations."""

import json
import shutil
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

from check_kb import generate_recommendations


def _write(path: Path, text: str) -> Path:
    """Helper — write *text* to *path*, creating parents as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _valid_md(depth: str = "working") -> str:
    """Return a minimal valid markdown document with proper frontmatter."""
    today = date.today().isoformat()
    padding = "\n".join([f"Line {i}" for i in range(15)])
    return (
        f"---\n"
        f"sources:\n"
        f"  - https://example.com/doc\n"
        f"last_validated: {today}\n"
        f"relevance: core\n"
        f"depth: {depth}\n"
        f"---\n"
        f"\n"
        f"# Topic\n"
        f"\n"
        f"{padding}\n"
    )


def _stale_md(depth: str = "working", age_days: int = 120) -> str:
    """Return a valid markdown document with a stale last_validated date."""
    stale_date = (date.today() - timedelta(days=age_days)).isoformat()
    padding = "\n".join([f"Line {i}" for i in range(15)])
    return (
        f"---\n"
        f"sources:\n"
        f"  - https://example.com/doc\n"
        f"last_validated: {stale_date}\n"
        f"relevance: core\n"
        f"depth: {depth}\n"
        f"---\n"
        f"\n"
        f"# Topic\n"
        f"\n"
        f"{padding}\n"
    )


def _log_entry(file: str, timestamp: str, context: str = "hook") -> str:
    """Return a single JSONL utilization log entry."""
    return json.dumps({"file": file, "timestamp": timestamp, "context": context})


def _write_utilization_log(kb_root: Path, entries: list[str]) -> None:
    """Write utilization log entries to .dewey/utilization/log.jsonl."""
    log_dir = kb_root / ".dewey" / "utilization"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "log.jsonl").write_text("\n".join(entries) + "\n")


class TestGatingLogic(unittest.TestCase):
    """Tests for threshold gating before recommendations are generated."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()
        area = self.kb / "area"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_no_utilization_data_returns_skipped(self):
        """No utilization log at all returns empty with skip reason."""
        result = generate_recommendations(self.tmpdir)
        self.assertEqual(result["recommendations"], [])
        self.assertIn("skipped", result)

    def test_insufficient_reads_returns_skipped(self):
        """Fewer total reads than min_reads returns empty with skip reason."""
        now = datetime.now().isoformat(timespec="seconds")
        _write_utilization_log(self.tmpdir, [
            _log_entry("docs/area/overview.md", now),
        ])
        result = generate_recommendations(self.tmpdir, min_reads=10, min_days=0)
        self.assertEqual(result["recommendations"], [])
        self.assertIn("skipped", result)

    def test_insufficient_days_returns_skipped(self):
        """All reads on same day with min_days > 0 returns empty with skip reason."""
        now = datetime.now().isoformat(timespec="seconds")
        entries = [_log_entry("docs/area/overview.md", now) for _ in range(20)]
        _write_utilization_log(self.tmpdir, entries)
        result = generate_recommendations(self.tmpdir, min_reads=0, min_days=7)
        self.assertEqual(result["recommendations"], [])
        self.assertIn("skipped", result)

    def test_zero_thresholds_bypass_gating(self):
        """min_reads=0 and min_days=0 bypass all gating."""
        now = datetime.now().isoformat(timespec="seconds")
        _write_utilization_log(self.tmpdir, [
            _log_entry("docs/area/overview.md", now),
        ])
        result = generate_recommendations(self.tmpdir, min_reads=0, min_days=0)
        self.assertNotIn("skipped", result)


class TestNeverReferenced(unittest.TestCase):
    """Tests for never_referenced recommendation."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        area = self.kb / "area"
        area.mkdir(parents=True)
        _write(area / "overview.md", _valid_md("overview"))
        _write(area / "topic.md", _valid_md("working"))
        _write(area / "topic.ref.md", _valid_md("reference"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_unreferenced_file_flagged(self):
        """File with zero reads gets never_referenced."""
        now = datetime.now().isoformat(timespec="seconds")
        _write_utilization_log(self.tmpdir, [
            _log_entry("docs/area/overview.md", now),
        ])
        result = generate_recommendations(self.tmpdir, min_reads=0, min_days=0)
        recs = result["recommendations"]
        never_ref = [r for r in recs if r["recommendation"] == "never_referenced"]
        never_ref_files = {r["file"] for r in never_ref}
        self.assertIn("docs/area/topic.md", never_ref_files)
        self.assertIn("docs/area/topic.ref.md", never_ref_files)

    def test_referenced_file_not_flagged(self):
        """File with reads does not get never_referenced."""
        now = datetime.now().isoformat(timespec="seconds")
        _write_utilization_log(self.tmpdir, [
            _log_entry("docs/area/overview.md", now),
            _log_entry("docs/area/topic.md", now),
            _log_entry("docs/area/topic.ref.md", now),
        ])
        result = generate_recommendations(self.tmpdir, min_reads=0, min_days=0)
        recs = result["recommendations"]
        never_ref = [r for r in recs if r["recommendation"] == "never_referenced"]
        self.assertEqual(never_ref, [])


class TestExpandDepth(unittest.TestCase):
    """Tests for expand_depth recommendation."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        # Area with only an overview
        area_a = self.kb / "area-a"
        area_a.mkdir(parents=True)
        _write(area_a / "overview.md", _valid_md("overview"))
        # Area with overview + working
        area_b = self.kb / "area-b"
        area_b.mkdir(parents=True)
        _write(area_b / "overview.md", _valid_md("overview"))
        _write(area_b / "topic.md", _valid_md("working"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_high_read_overview_gets_expand(self):
        """Overview with reads > 2x median gets expand_depth."""
        now = datetime.now().isoformat(timespec="seconds")
        # area-a overview: 20 reads (high)
        # area-b overview: 2 reads, area-b topic: 1 read
        entries = (
            [_log_entry("docs/area-a/overview.md", now) for _ in range(20)]
            + [_log_entry("docs/area-b/overview.md", now) for _ in range(2)]
            + [_log_entry("docs/area-b/topic.md", now)]
        )
        _write_utilization_log(self.tmpdir, entries)
        result = generate_recommendations(self.tmpdir, min_reads=0, min_days=0)
        expand = [r for r in result["recommendations"] if r["recommendation"] == "expand_depth"]
        expand_files = {r["file"] for r in expand}
        self.assertIn("docs/area-a/overview.md", expand_files)

    def test_low_read_overview_no_expand(self):
        """Overview with average reads does not get expand_depth."""
        now = datetime.now().isoformat(timespec="seconds")
        entries = (
            [_log_entry("docs/area-a/overview.md", now) for _ in range(2)]
            + [_log_entry("docs/area-b/overview.md", now) for _ in range(2)]
            + [_log_entry("docs/area-b/topic.md", now)]
        )
        _write_utilization_log(self.tmpdir, entries)
        result = generate_recommendations(self.tmpdir, min_reads=0, min_days=0)
        expand = [r for r in result["recommendations"] if r["recommendation"] == "expand_depth"]
        self.assertEqual(expand, [])


class TestLowUtilization(unittest.TestCase):
    """Tests for low_utilization recommendation."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        area = self.kb / "area"
        area.mkdir(parents=True)
        _write(area / "overview.md", _valid_md("overview"))
        _write(area / "popular.md", _valid_md("working"))
        _write(area / "unpopular.md", _valid_md("working"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_low_read_working_file_flagged(self):
        """Working file with reads < 10% of overview gets low_utilization."""
        now = datetime.now().isoformat(timespec="seconds")
        entries = (
            [_log_entry("docs/area/overview.md", now) for _ in range(50)]
            + [_log_entry("docs/area/popular.md", now) for _ in range(30)]
            + [_log_entry("docs/area/unpopular.md", now) for _ in range(2)]
        )
        _write_utilization_log(self.tmpdir, entries)
        result = generate_recommendations(self.tmpdir, min_reads=0, min_days=0)
        low = [r for r in result["recommendations"] if r["recommendation"] == "low_utilization"]
        low_files = {r["file"] for r in low}
        self.assertIn("docs/area/unpopular.md", low_files)
        self.assertNotIn("docs/area/popular.md", low_files)

    def test_overview_never_gets_low_utilization(self):
        """Overview files are excluded from low_utilization."""
        now = datetime.now().isoformat(timespec="seconds")
        entries = (
            [_log_entry("docs/area/overview.md", now)]
            + [_log_entry("docs/area/popular.md", now) for _ in range(50)]
        )
        _write_utilization_log(self.tmpdir, entries)
        result = generate_recommendations(self.tmpdir, min_reads=0, min_days=0)
        low = [r for r in result["recommendations"] if r["recommendation"] == "low_utilization"]
        low_files = {r["file"] for r in low}
        self.assertNotIn("docs/area/overview.md", low_files)


class TestStaleHighUse(unittest.TestCase):
    """Tests for stale_high_use recommendation."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        area = self.kb / "area"
        area.mkdir(parents=True)
        _write(area / "overview.md", _valid_md("overview"))
        _write(area / "fresh.md", _valid_md("working"))
        _write(area / "stale.md", _stale_md("working", age_days=120))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_stale_high_read_file_flagged(self):
        """Stale file with above-median reads gets stale_high_use."""
        now = datetime.now().isoformat(timespec="seconds")
        entries = (
            [_log_entry("docs/area/overview.md", now) for _ in range(5)]
            + [_log_entry("docs/area/fresh.md", now) for _ in range(3)]
            + [_log_entry("docs/area/stale.md", now) for _ in range(20)]
        )
        _write_utilization_log(self.tmpdir, entries)
        result = generate_recommendations(self.tmpdir, min_reads=0, min_days=0)
        stale = [r for r in result["recommendations"] if r["recommendation"] == "stale_high_use"]
        stale_files = {r["file"] for r in stale}
        self.assertIn("docs/area/stale.md", stale_files)

    def test_stale_low_read_file_not_stale_high_use(self):
        """Stale file with below-median reads does not get stale_high_use."""
        now = datetime.now().isoformat(timespec="seconds")
        entries = (
            [_log_entry("docs/area/overview.md", now) for _ in range(20)]
            + [_log_entry("docs/area/fresh.md", now) for _ in range(20)]
            + [_log_entry("docs/area/stale.md", now)]
        )
        _write_utilization_log(self.tmpdir, entries)
        result = generate_recommendations(self.tmpdir, min_reads=0, min_days=0)
        stale = [r for r in result["recommendations"] if r["recommendation"] == "stale_high_use"]
        self.assertEqual(stale, [])

    def test_fresh_high_read_file_not_stale_high_use(self):
        """Fresh file with high reads does not get stale_high_use."""
        now = datetime.now().isoformat(timespec="seconds")
        entries = (
            [_log_entry("docs/area/overview.md", now) for _ in range(5)]
            + [_log_entry("docs/area/fresh.md", now) for _ in range(20)]
            + [_log_entry("docs/area/stale.md", now) for _ in range(2)]
        )
        _write_utilization_log(self.tmpdir, entries)
        result = generate_recommendations(self.tmpdir, min_reads=0, min_days=0)
        stale = [r for r in result["recommendations"] if r["recommendation"] == "stale_high_use"]
        stale_files = {r["file"] for r in stale}
        self.assertNotIn("docs/area/fresh.md", stale_files)


class TestPriorityOrdering(unittest.TestCase):
    """Tests that a file gets at most one recommendation, highest priority wins."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        area = self.kb / "area"
        area.mkdir(parents=True)
        _write(area / "overview.md", _valid_md("overview"))
        # Stale overview with high reads — could be expand_depth or stale_high_use
        _write(area / "stale-overview.md", _stale_md("overview", age_days=120))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_file_gets_only_one_recommendation(self):
        """Each file appears at most once in recommendations."""
        now = datetime.now().isoformat(timespec="seconds")
        entries = [_log_entry("docs/area/overview.md", now) for _ in range(5)]
        _write_utilization_log(self.tmpdir, entries)
        result = generate_recommendations(self.tmpdir, min_reads=0, min_days=0)
        files = [r["file"] for r in result["recommendations"]]
        self.assertEqual(len(files), len(set(files)))


class TestSummary(unittest.TestCase):
    """Tests for the summary section of the output."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        area = self.kb / "area"
        area.mkdir(parents=True)
        _write(area / "overview.md", _valid_md("overview"))
        _write(area / "topic.md", _valid_md("working"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_summary_has_required_fields(self):
        """Summary includes total_files, files_with_recommendations, by_category."""
        now = datetime.now().isoformat(timespec="seconds")
        _write_utilization_log(self.tmpdir, [
            _log_entry("docs/area/overview.md", now),
        ])
        result = generate_recommendations(self.tmpdir, min_reads=0, min_days=0)
        summary = result["summary"]
        self.assertIn("total_files", summary)
        self.assertIn("files_with_recommendations", summary)
        self.assertIn("by_category", summary)

    def test_by_category_counts_match_recommendations(self):
        """by_category counts should match actual recommendation counts."""
        now = datetime.now().isoformat(timespec="seconds")
        _write_utilization_log(self.tmpdir, [
            _log_entry("docs/area/overview.md", now),
        ])
        result = generate_recommendations(self.tmpdir, min_reads=0, min_days=0)
        total_from_categories = sum(result["summary"]["by_category"].values())
        self.assertEqual(total_from_categories, len(result["recommendations"]))


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/skills/health/test_recommendations.py -v`
Expected: FAIL with `ImportError: cannot import name 'generate_recommendations' from 'check_kb'`

**Step 3: Write the implementation**

Add to `dewey/skills/health/scripts/check_kb.py`, before the `if __name__` block:

```python
def generate_recommendations(
    kb_root: Path,
    min_reads: int = 10,
    min_days: int = 7,
) -> dict:
    """Generate curation recommendations from utilization and health data.

    Cross-references utilization log (which files agents actually read)
    against the file inventory and health signals to surface actionable
    curation suggestions.

    Parameters
    ----------
    kb_root:
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
    from datetime import datetime
    from utilization import read_utilization
    from validators import check_freshness, parse_frontmatter

    knowledge_dir_name = read_knowledge_dir(kb_root)
    md_files = _discover_md_files(kb_root, knowledge_dir_name)
    knowledge_dir = kb_root / knowledge_dir_name

    # Build file paths relative to kb_root (with knowledge_dir prefix)
    file_paths = {}
    for f in md_files:
        rel_to_kd = str(f.relative_to(knowledge_dir))
        rel_to_root = f"{knowledge_dir_name}/{rel_to_kd}"
        file_paths[rel_to_root] = f

    # Read utilization data
    utilization = read_utilization(kb_root)

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
        if overview_reads < 10:
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
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/skills/health/test_recommendations.py -v`
Expected: ALL PASS

**Step 5: Run full test suite**

Run: `python3 -m pytest tests/ -v -k "not test_scaffold_sandbox"`
Expected: All pass, no regressions

**Step 6: Commit**

```bash
git add dewey/skills/health/scripts/check_kb.py tests/skills/health/test_recommendations.py
git commit -m "Add generate_recommendations for utilization-driven curation suggestions"
```

---

### Task 2: CLI integration — `--recommendations` flag

**Files:**
- Modify: `dewey/skills/health/scripts/check_kb.py:220-248` (the `if __name__` block)

**Step 1: Write the failing test**

Add to `tests/skills/health/test_recommendations.py`:

```python
import subprocess


class TestCLI(unittest.TestCase):
    """Tests for --recommendations CLI flag."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        area = self.kb / "area"
        area.mkdir(parents=True)
        _write(area / "overview.md", _valid_md("overview"))
        _write(area / "topic.md", _valid_md("working"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run(self, *extra_args) -> subprocess.CompletedProcess:
        script = Path(__file__).resolve().parent.parent.parent.parent / \
            "dewey" / "skills" / "health" / "scripts" / "check_kb.py"
        cmd = ["python3", str(script), "--kb-root", str(self.tmpdir)]
        cmd.extend(extra_args)
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10)

    def test_recommendations_flag_returns_json(self):
        """--recommendations produces valid JSON output."""
        now = datetime.now().isoformat(timespec="seconds")
        _write_utilization_log(self.tmpdir, [
            _log_entry("docs/area/overview.md", now),
        ])
        result = self._run("--recommendations", "--min-reads", "0", "--min-days", "0")
        self.assertEqual(result.returncode, 0)
        parsed = json.loads(result.stdout)
        self.assertIn("recommendations", parsed)

    def test_recommendations_with_both(self):
        """--both --recommendations includes all three sections."""
        now = datetime.now().isoformat(timespec="seconds")
        _write_utilization_log(self.tmpdir, [
            _log_entry("docs/area/overview.md", now),
        ])
        result = self._run("--both", "--recommendations", "--min-reads", "0", "--min-days", "0")
        self.assertEqual(result.returncode, 0)
        parsed = json.loads(result.stdout)
        self.assertIn("tier1", parsed)
        self.assertIn("tier2", parsed)
        self.assertIn("recommendations", parsed)

    def test_recommendations_standalone(self):
        """--recommendations alone (no --both, no --tier2) returns only recommendations."""
        now = datetime.now().isoformat(timespec="seconds")
        _write_utilization_log(self.tmpdir, [
            _log_entry("docs/area/overview.md", now),
        ])
        result = self._run("--recommendations", "--min-reads", "0", "--min-days", "0")
        self.assertEqual(result.returncode, 0)
        parsed = json.loads(result.stdout)
        self.assertIn("recommendations", parsed)
        self.assertNotIn("tier1", parsed)

    def test_min_reads_flag(self):
        """--min-reads flag is respected."""
        now = datetime.now().isoformat(timespec="seconds")
        _write_utilization_log(self.tmpdir, [
            _log_entry("docs/area/overview.md", now),
        ])
        result = self._run("--recommendations", "--min-reads", "999", "--min-days", "0")
        parsed = json.loads(result.stdout)
        self.assertIn("skipped", parsed)

    def test_min_days_flag(self):
        """--min-days flag is respected."""
        now = datetime.now().isoformat(timespec="seconds")
        _write_utilization_log(self.tmpdir, [
            _log_entry("docs/area/overview.md", now),
        ])
        result = self._run("--recommendations", "--min-reads", "0", "--min-days", "999")
        parsed = json.loads(result.stdout)
        self.assertIn("skipped", parsed)
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/skills/health/test_recommendations.py::TestCLI -v`
Expected: FAIL — `--recommendations` flag not recognized

**Step 3: Update the CLI block**

Replace the `if __name__ == "__main__"` block in `dewey/skills/health/scripts/check_kb.py`:

```python
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run knowledge base health checks.")
    parser.add_argument(
        "--kb-root",
        required=True,
        help="Root directory containing the docs/ folder.",
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
    args = parser.parse_args()

    kb_path = Path(args.kb_root)

    if args.both and args.recommendations:
        report = run_combined_report(kb_path)
        report["recommendations"] = generate_recommendations(
            kb_path, min_reads=args.min_reads, min_days=args.min_days,
        )
    elif args.both:
        report = run_combined_report(kb_path)
    elif args.tier2:
        report = run_tier2_prescreening(kb_path)
    elif args.recommendations:
        report = generate_recommendations(
            kb_path, min_reads=args.min_reads, min_days=args.min_days,
        )
    else:
        report = run_health_check(kb_path)
    print(json.dumps(report, indent=2))
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/skills/health/test_recommendations.py -v`
Expected: ALL PASS

**Step 5: Run full test suite**

Run: `python3 -m pytest tests/ -v -k "not test_scaffold_sandbox"`
Expected: All pass, no regressions

**Step 6: Commit**

```bash
git add dewey/skills/health/scripts/check_kb.py tests/skills/health/test_recommendations.py
git commit -m "Add --recommendations CLI flag with --min-reads and --min-days thresholds"
```

---

### Task 3: End-to-end validation against sandbox

**Step 1: Run full test suite**

Run: `python3 -m pytest tests/ -v -k "not test_scaffold_sandbox"`
Expected: ALL PASS

**Step 2: Test against sandbox with zero thresholds**

Run: `python3 dewey/skills/health/scripts/check_kb.py --kb-root sandbox --recommendations --min-reads 0 --min-days 0`
Expected: JSON with recommendations (likely many `never_referenced` since utilization data is sparse). Verify output has `recommendations` list and `summary` with `by_category`.

**Step 3: Test combined output**

Run: `python3 dewey/skills/health/scripts/check_kb.py --kb-root sandbox --both --recommendations --min-reads 0 --min-days 0`
Expected: JSON with `tier1`, `tier2`, and `recommendations` keys.

**Step 4: Test default thresholds gate correctly**

Run: `python3 dewey/skills/health/scripts/check_kb.py --kb-root sandbox --recommendations`
Expected: JSON with `skipped` key (sandbox only has 3 reads over 0 days, well below defaults).

**Step 5: Commit if any adjustments needed**

```bash
git add -A
git commit -m "Final adjustments from end-to-end validation"
```
