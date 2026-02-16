"""Tests for skills.health.scripts.check_kb — health check runner."""

import json
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from check_kb import run_health_check, run_tier2_prescreening, run_combined_report


def _write(path: Path, text: str) -> Path:
    """Helper — write *text* to *path*, creating parents as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _valid_md(depth: str = "working", extra_body: str = "", stem: str = "topic") -> str:
    """Return a minimal valid markdown document with proper frontmatter.

    Produces depth-appropriate sections so all validators pass cleanly:
    - working: 5 required sections + ref link in Go Deeper + external link
    - overview: What This Covers + How It's Organized
    - reference: See also with companion link
    """
    today = date.today().isoformat()
    padding = "\n".join([f"Line {i}" for i in range(15)])

    if depth == "working":
        sections = (
            f"# Topic\n"
            f"\n"
            f"## Why This Matters\n"
            f"Explains why this topic is important.\n"
            f"\n"
            f"## In Practice\n"
            f"Concrete guidance here.\n"
            f"\n"
            f"## Key Guidance\n"
            f"Abstract principles here.\n"
            f"\n"
            f"## Watch Out For\n"
            f"Common pitfalls.\n"
            f"\n"
            f"## Go Deeper\n"
            f"- [{stem} Reference]({stem}.ref.md) -- quick-lookup version\n"
            f"- [External resource](https://example.com/resource)\n"
        )
    elif depth == "overview":
        sections = (
            f"# Overview\n"
            f"\n"
            f"## What This Covers\n"
            f"Scope of this area.\n"
            f"\n"
            f"## How It's Organized\n"
            f"Structure of this area.\n"
        )
    elif depth == "reference":
        sections = (
            f"# Reference\n"
            f"\n"
            f"Quick lookup content.\n"
            f"\n"
            f"**See also:** [{stem}]({stem}.md)\n"
        )
    else:
        sections = "# Topic\n\nBody content.\n"

    return (
        f"---\n"
        f"sources:\n"
        f"  - https://example.com/doc\n"
        f"last_validated: {today}\n"
        f"relevance: core\n"
        f"depth: {depth}\n"
        f"---\n"
        f"\n"
        f"{sections}\n"
        f"{padding}\n"
        f"{extra_body}\n"
    )


class TestRunHealthCheck(unittest.TestCase):
    """Tests for the run_health_check function."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    # ------------------------------------------------------------------
    # test_returns_structured_report
    # ------------------------------------------------------------------
    def test_returns_structured_report(self):
        """Result has 'issues' and 'summary' keys."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        result = run_health_check(self.tmpdir)
        self.assertIn("issues", result)
        self.assertIn("summary", result)
        self.assertIsInstance(result["issues"], list)
        self.assertIsInstance(result["summary"], dict)

    # ------------------------------------------------------------------
    # test_reports_missing_overview
    # ------------------------------------------------------------------
    def test_reports_missing_overview(self):
        """Area without overview.md produces a fail-severity issue."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "topic.md", _valid_md("working"))
        result = run_health_check(self.tmpdir)
        overview_issues = [
            i for i in result["issues"]
            if "overview.md" in i["message"]
        ]
        self.assertTrue(len(overview_issues) > 0)
        self.assertTrue(any(i["severity"] == "fail" for i in overview_issues))

    # ------------------------------------------------------------------
    # test_clean_kb_has_no_failures
    # ------------------------------------------------------------------
    def test_clean_kb_has_no_failures(self):
        """A valid KB produces zero fail-severity issues."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        _write(area / "topic.md", _valid_md("working"))
        _write(area / "topic.ref.md", _valid_md("reference"))
        result = run_health_check(self.tmpdir)
        fails = [i for i in result["issues"] if i["severity"] == "fail"]
        self.assertEqual(fails, [], f"Unexpected failures: {fails}")

    # ------------------------------------------------------------------
    # test_summary_includes_counts
    # ------------------------------------------------------------------
    def test_summary_includes_counts(self):
        """Summary contains total_files, fail_count, warn_count, pass_count."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        result = run_health_check(self.tmpdir)
        summary = result["summary"]
        for key in ("total_files", "fail_count", "warn_count", "pass_count"):
            self.assertIn(key, summary, f"Missing summary key: {key}")
            self.assertIsInstance(summary[key], int)

    # ------------------------------------------------------------------
    # test_skips_proposals
    # ------------------------------------------------------------------
    def test_skips_proposals_per_file_validators(self):
        """Per-file validators skip _proposals/ (proposal integrity is separate)."""
        proposals = self.kb / "_proposals"
        proposals.mkdir()
        _write(proposals / "draft.md", "# No frontmatter at all\n")
        result = run_health_check(self.tmpdir)
        # Per-file validators (frontmatter, sections, etc.) should not fire
        per_file_issues = [
            i for i in result["issues"]
            if "_proposals" in i.get("file", "")
            and "Missing frontmatter" in i.get("message", "")
        ]
        self.assertEqual(per_file_issues, [])
        # But proposal integrity warnings ARE expected from cross-validators
        proposal_integrity = [
            i for i in result["issues"]
            if "_proposals" in i.get("file", "")
            and "Proposal" in i.get("message", "")
        ]
        self.assertTrue(len(proposal_integrity) > 0)

    # ------------------------------------------------------------------
    # test_total_files_count
    # ------------------------------------------------------------------
    def test_total_files_count(self):
        """total_files accurately counts markdown files."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        _write(area / "topic.md", _valid_md("working"))
        result = run_health_check(self.tmpdir)
        self.assertEqual(result["summary"]["total_files"], 2)


class TestRunTier2Prescreening(unittest.TestCase):
    """Tests for the run_tier2_prescreening function."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_returns_structured_queue(self):
        """Result has 'queue' and 'summary' keys."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        result = run_tier2_prescreening(self.tmpdir)
        self.assertIn("queue", result)
        self.assertIn("summary", result)
        self.assertIsInstance(result["queue"], list)
        self.assertIsInstance(result["summary"], dict)

    def test_stale_file_produces_trigger(self):
        """A file with old last_validated should produce a source_drift trigger."""
        area = self.kb / "area-one"
        area.mkdir()
        stale_md = (
            "---\n"
            "sources:\n"
            "  - https://example.com/doc\n"
            "last_validated: 2020-01-01\n"
            "relevance: core\n"
            "depth: overview\n"
            "---\n"
            "\n"
            "# Topic\n"
            "\n"
            "Content here.\n"
        )
        _write(area / "stale.md", stale_md)
        result = run_tier2_prescreening(self.tmpdir)
        drift_items = [i for i in result["queue"] if i["trigger"] == "source_drift"]
        self.assertTrue(len(drift_items) > 0)

    def test_summary_includes_counts(self):
        """Summary contains total_files_scanned, files_with_triggers, trigger_counts."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        result = run_tier2_prescreening(self.tmpdir)
        summary = result["summary"]
        for key in ("total_files_scanned", "files_with_triggers", "trigger_counts"):
            self.assertIn(key, summary, f"Missing summary key: {key}")

    def test_clean_file_no_triggers(self):
        """A well-formed file should produce no triggers."""
        area = self.kb / "area-one"
        area.mkdir()
        # Pad with enough words to satisfy Tier 2 depth_accuracy (min 50 for overview)
        extra = "\n".join([f"Additional content line {i} with words." for i in range(10)])
        _write(area / "overview.md", _valid_md("overview", extra_body=extra))
        result = run_tier2_prescreening(self.tmpdir)
        overview_triggers = [
            i for i in result["queue"]
            if "overview.md" in i["file"]
        ]
        self.assertEqual(overview_triggers, [])


class TestTier2OutputSchema(unittest.TestCase):
    """Validate the output schema of run_tier2_prescreening for workflow consumption."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

        # Create test data that triggers multiple trigger types.
        area = self.kb / "area-one"
        area.mkdir()

        # A stale overview file — triggers source_drift (old last_validated)
        stale_md = (
            "---\n"
            "sources:\n"
            "  - https://example.com/doc\n"
            "last_validated: 2020-01-01\n"
            "relevance: core\n"
            "depth: overview\n"
            "---\n"
            "\n"
            "# Topic\n"
            "\n"
            "Content here.\n"
        )
        _write(area / "overview.md", stale_md)

        # A thin working-depth file — triggers depth_accuracy (too few words),
        # why_quality (missing section), concrete_examples (no concrete elements),
        # and source_primacy (no inline sources).
        thin_working_md = (
            "---\n"
            "sources:\n"
            "  - https://example.com/doc\n"
            "last_validated: 2020-01-01\n"
            "relevance: core\n"
            "depth: working\n"
            "---\n"
            "\n"
            "# Topic\n"
            "\n"
            "## Key Guidance\n"
            "- Do the thing\n"
            "- Do the other thing\n"
            "- And another thing\n"
            "\n"
            "## In Practice\n"
            "Just some text without concrete elements.\n"
        )
        _write(area / "topic.md", thin_working_md)

        self.result = run_tier2_prescreening(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    # ------------------------------------------------------------------
    # test_queue_item_schema
    # ------------------------------------------------------------------
    def test_queue_item_schema(self):
        """Every queue item must have file, trigger, reason, context keys;
        context must be a dict."""
        queue = self.result["queue"]
        self.assertTrue(len(queue) > 0, "Expected at least one queue item")

        required_keys = {"file", "trigger", "reason", "context"}
        for item in queue:
            for key in required_keys:
                self.assertIn(key, item, f"Missing key '{key}' in queue item: {item}")
            self.assertIsInstance(
                item["context"], dict,
                f"context should be a dict, got {type(item['context']).__name__}",
            )

    # ------------------------------------------------------------------
    # test_trigger_counts_match_queue
    # ------------------------------------------------------------------
    def test_trigger_counts_match_queue(self):
        """Summary trigger_counts must match actual counts from the queue."""
        queue = self.result["queue"]
        summary_counts = self.result["summary"]["trigger_counts"]

        # Count triggers from the queue directly
        actual_counts: dict[str, int] = {}
        for item in queue:
            t = item["trigger"]
            actual_counts[t] = actual_counts.get(t, 0) + 1

        self.assertEqual(
            summary_counts, actual_counts,
            f"trigger_counts mismatch: summary={summary_counts}, actual={actual_counts}",
        )

    # ------------------------------------------------------------------
    # test_valid_trigger_names
    # ------------------------------------------------------------------
    def test_valid_trigger_names(self):
        """Every trigger name must be one of the 6 known triggers."""
        known_triggers = {
            "source_drift",
            "depth_accuracy",
            "source_primacy",
            "why_quality",
            "concrete_examples",
            "citation_quality",
        }
        queue = self.result["queue"]
        self.assertTrue(len(queue) > 0, "Expected at least one queue item")

        for item in queue:
            self.assertIn(
                item["trigger"], known_triggers,
                f"Unknown trigger '{item['trigger']}' in queue item: {item}",
            )


class TestRunCombinedReport(unittest.TestCase):
    """Tests for the run_combined_report function."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        _write(area / "topic.md", _valid_md("working"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    # ------------------------------------------------------------------
    # test_returns_both_sections
    # ------------------------------------------------------------------
    def test_returns_both_sections(self):
        """Combined report includes 'tier1' and 'tier2' keys."""
        result = run_combined_report(self.tmpdir)
        self.assertIn("tier1", result)
        self.assertIn("tier2", result)

    # ------------------------------------------------------------------
    # test_tier1_has_issues_and_summary
    # ------------------------------------------------------------------
    def test_tier1_has_issues_and_summary(self):
        """Tier 1 section has 'issues' and 'summary'."""
        result = run_combined_report(self.tmpdir)
        tier1 = result["tier1"]
        self.assertIn("issues", tier1)
        self.assertIn("summary", tier1)

    # ------------------------------------------------------------------
    # test_tier2_has_queue_and_summary
    # ------------------------------------------------------------------
    def test_tier2_has_queue_and_summary(self):
        """Tier 2 section has 'queue' and 'summary'."""
        result = run_combined_report(self.tmpdir)
        tier2 = result["tier2"]
        self.assertIn("queue", tier2)
        self.assertIn("summary", tier2)


class TestHistoryIntegration(unittest.TestCase):
    """Tests for automatic history snapshot persistence."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_tier1_persists_snapshot(self):
        """run_health_check should persist a history snapshot."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        run_health_check(self.tmpdir)
        log = self.tmpdir / ".dewey" / "history" / "health-log.jsonl"
        self.assertTrue(log.exists())
        entry = json.loads(log.read_text().strip())
        self.assertIn("tier1", entry)
        self.assertIsNone(entry["tier2"])

    def test_combined_persists_snapshot(self):
        """run_combined_report should persist a snapshot with both tiers."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        run_combined_report(self.tmpdir)
        log = self.tmpdir / ".dewey" / "history" / "health-log.jsonl"
        self.assertTrue(log.exists())
        entry = json.loads(log.read_text().strip())
        self.assertIn("tier1", entry)
        self.assertIsNotNone(entry["tier2"])

    def test_tier2_persists_snapshot(self):
        """run_tier2_prescreening should persist a snapshot."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        run_tier2_prescreening(self.tmpdir)
        log = self.tmpdir / ".dewey" / "history" / "health-log.jsonl"
        self.assertTrue(log.exists())
        entry = json.loads(log.read_text().strip())
        self.assertIsNone(entry["tier1"])
        self.assertIn("tier2", entry)


class TestIndexMdExclusion(unittest.TestCase):
    """index.md is structural, not a knowledge topic — skip per-file validators."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        kb = self.tmpdir / "docs" / "area"
        kb.mkdir(parents=True)
        # A valid overview file
        _write(kb / "overview.md", _valid_md("overview"))
        # index.md with NO frontmatter (should not cause failures)
        (self.tmpdir / "docs" / "index.md").write_text(
            "# Knowledge Base\n\n## Domain Areas\n"
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_index_md_without_frontmatter_no_failures(self):
        result = run_health_check(self.tmpdir)
        fail_messages = [i["message"] for i in result["issues"] if i["severity"] == "fail"]
        self.assertEqual(fail_messages, [], f"index.md should not trigger failures: {fail_messages}")

    def test_discover_md_files_excludes_index(self):
        from check_kb import _discover_md_files
        files = _discover_md_files(self.tmpdir, "docs")
        filenames = [f.name for f in files]
        self.assertNotIn("index.md", filenames)


class TestCheckIndexSync(unittest.TestCase):
    """Tier 1 validator: detect when index.md is out of sync with disk."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        kb = self.tmpdir / "docs" / "area"
        kb.mkdir(parents=True)
        _write(kb / "overview.md", _valid_md("overview"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_missing_index_md_warns(self):
        from validators import check_index_sync
        issues = check_index_sync(self.tmpdir, knowledge_dir_name="docs")
        self.assertTrue(any("index.md" in i["message"] and i["severity"] == "warn" for i in issues))

    def test_synced_index_no_issues(self):
        from validators import check_index_sync
        # Create index.md that references the area overview
        (self.tmpdir / "docs" / "index.md").write_text("# Knowledge Base\n\n## Area\n\n| [Overview](area/overview.md) |\n")
        issues = check_index_sync(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])

    def test_topic_on_disk_not_in_index_warns(self):
        from validators import check_index_sync
        # Create a topic file not listed in index
        _write(
            self.tmpdir / "docs" / "area" / "new-topic.md",
            _valid_md("working"),
        )
        (self.tmpdir / "docs" / "index.md").write_text("# Knowledge Base\n\n## Area\n\n| [Overview](area/overview.md) |\n")
        issues = check_index_sync(self.tmpdir, knowledge_dir_name="docs")
        self.assertTrue(any("new-topic.md" in i["message"] for i in issues))

    def test_check_index_sync_in_health_check(self):
        """check_index_sync is included in the Tier 1 health check."""
        (self.tmpdir / "docs" / "index.md").write_text("# Knowledge Base\n")
        _write(
            self.tmpdir / "docs" / "area" / "unlisted.md",
            _valid_md("working"),
        )
        result = run_health_check(self.tmpdir)
        index_issues = [i for i in result["issues"] if "index.md" in i["message"]]
        self.assertGreater(len(index_issues), 0)


class TestInventoryIntegration(unittest.TestCase):
    """Tests for inventory regression detection in the health check runner."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_file_list_recorded_in_snapshot(self):
        """run_health_check records discovered files in history snapshot."""
        area = self.kb / "area"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        _write(area / "topic.md", _valid_md("working"))
        _write(area / "topic.ref.md", _valid_md("reference"))
        run_health_check(self.tmpdir)

        log = self.tmpdir / ".dewey" / "history" / "health-log.jsonl"
        entry = json.loads(log.read_text().strip())
        self.assertIn("file_list", entry)
        self.assertEqual(len(entry["file_list"]), 3)
        self.assertTrue(all("area/" in f for f in entry["file_list"]))

    def test_missing_file_detected_on_second_run(self):
        """Second health check detects file removed since first run."""
        area = self.kb / "area"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        topic = _write(area / "topic.md", _valid_md("working"))
        _write(area / "topic.ref.md", _valid_md("reference"))

        # First run records all 3 files
        run_health_check(self.tmpdir)

        # Remove a file
        topic.unlink()

        # Second run should detect the regression
        result = run_health_check(self.tmpdir)
        regression_issues = [
            i for i in result["issues"] if "missing" in i["message"].lower()
            and "topic.md" in i["message"]
        ]
        self.assertTrue(len(regression_issues) > 0)

    def test_combined_report_records_file_list(self):
        """run_combined_report also records file_list in snapshot."""
        area = self.kb / "area"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        run_combined_report(self.tmpdir)

        log = self.tmpdir / ".dewey" / "history" / "health-log.jsonl"
        entry = json.loads(log.read_text().strip())
        self.assertIn("file_list", entry)


class TestCitationQualityIntegration(unittest.TestCase):
    """Tests for citation quality trigger in the prescreening runner."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_duplicate_citations_appear_in_queue(self):
        """File with repeated inline citations produces a citation_quality trigger."""
        area = self.kb / "area"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        # Build a working doc with duplicate citations inside Key Guidance
        today = date.today().isoformat()
        dup_working = (
            f"---\nsources:\n  - https://example.com/doc\n"
            f"last_validated: {today}\nrelevance: core\ndepth: working\n---\n\n"
            f"# Topic\n\n"
            f"## Why This Matters\nImportant topic.\n\n"
            f"## In Practice\nConcrete guidance here.\n\n"
            f"## Key Guidance\n"
            f"- A [s](https://example.com/dup)\n"
            f"- B [s](https://example.com/dup)\n"
            f"- C [s](https://example.com/dup)\n\n"
            f"## Watch Out For\nPitfalls.\n\n"
            f"## Go Deeper\n"
            f"- [topic Reference](topic.ref.md) -- quick-lookup version\n"
            f"- [External](https://example.com/resource)\n"
        )
        _write(area / "topic.md", dup_working)
        _write(area / "topic.ref.md", _valid_md("reference"))

        result = run_tier2_prescreening(self.tmpdir)
        citation_items = [i for i in result["queue"] if i["trigger"] == "citation_quality"]
        self.assertTrue(len(citation_items) > 0)


class TestNewValidatorsIntegration(unittest.TestCase):
    """Verify new validators fire through run_health_check pipeline."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_section_completeness_fires(self):
        """Working file missing sections produces warnings through pipeline."""
        area = self.kb / "area"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        today = date.today().isoformat()
        # Working file with only In Practice + Key Guidance (missing 3 sections)
        bare_working = (
            f"---\nsources:\n  - https://example.com/doc\n"
            f"last_validated: {today}\nrelevance: core\ndepth: working\n---\n\n"
            f"# Topic\n\n## In Practice\nText.\n\n## Key Guidance\nText.\n"
            + "\n".join([f"Line {i}" for i in range(15)]) + "\n"
        )
        _write(area / "topic.md", bare_working)
        _write(area / "topic.ref.md", _valid_md("reference"))
        result = run_health_check(self.tmpdir)
        section_issues = [
            i for i in result["issues"]
            if "Missing required section" in i.get("message", "")
        ]
        self.assertTrue(len(section_issues) >= 3)

    def test_heading_hierarchy_fires(self):
        """File with heading issues produces warnings through pipeline."""
        area = self.kb / "area"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        today = date.today().isoformat()
        bad_headings = (
            f"---\nsources:\n  - https://example.com/doc\n"
            f"last_validated: {today}\nrelevance: core\ndepth: working\n---\n\n"
            f"# Title\n\n# Second Title\n\n### Skipped\n"
            + "\n".join([f"Line {i}" for i in range(15)]) + "\n"
        )
        _write(area / "topic.md", bad_headings)
        _write(area / "topic.ref.md", _valid_md("reference"))
        result = run_health_check(self.tmpdir)
        heading_issues = [
            i for i in result["issues"]
            if "H1" in i.get("message", "") or "Skipped" in i.get("message", "")
        ]
        self.assertTrue(len(heading_issues) >= 2)


class TestAutoFixIntegration(unittest.TestCase):
    """Verify --fix and --dry-run work through run_health_check pipeline."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _make_incomplete_kb(self):
        """Create a KB with a working file missing sections."""
        area = self.kb / "area"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        today = date.today().isoformat()
        bare_working = (
            f"---\nsources:\n  - https://example.com/doc\n"
            f"last_validated: {today}\nrelevance: core\ndepth: working\n---\n\n"
            f"# Topic\n\n## In Practice\nText.\n\n## Key Guidance\nText.\n"
            + "\n".join([f"Line {i}" for i in range(15)]) + "\n"
        )
        _write(area / "topic.md", bare_working)
        _write(area / "topic.ref.md", _valid_md("reference"))
        return area / "topic.md"

    def test_dry_run_does_not_modify(self):
        """dry_run reports fixes but doesn't write to disk."""
        topic = self._make_incomplete_kb()
        original = topic.read_text()
        result = run_health_check(self.tmpdir, dry_run=True)
        self.assertIn("fixes", result)
        self.assertTrue(len(result["fixes"]) > 0)
        # Verify all actions are prefixed with "would_"
        for fix in result["fixes"]:
            self.assertTrue(fix["action"].startswith("would_"))
        # File should be unchanged
        self.assertEqual(topic.read_text(), original)

    def test_fix_modifies_file(self):
        """fix=True applies changes and reports them."""
        topic = self._make_incomplete_kb()
        original = topic.read_text()
        result = run_health_check(self.tmpdir, fix=True)
        self.assertIn("fixes", result)
        self.assertTrue(len(result["fixes"]) > 0)
        # File should be modified
        self.assertNotEqual(topic.read_text(), original)
        # Stubs should be present
        self.assertIn("## Why This Matters", topic.read_text())

    def test_no_fix_flag_no_fixes_key(self):
        """Without fix/dry_run, result has no 'fixes' key."""
        self._make_incomplete_kb()
        result = run_health_check(self.tmpdir)
        self.assertNotIn("fixes", result)


class TestManifestSyncIntegration(unittest.TestCase):
    """Verify manifest sync fires through run_health_check pipeline."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_manifest_sync_fires_in_pipeline(self):
        """AGENTS.md referencing nonexistent file -> warn through pipeline."""
        from templates import MARKER_BEGIN, MARKER_END

        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))

        agents_text = (
            "# Role\n\n"
            f"{MARKER_BEGIN}\n"
            "## What You Have Access To\n"
            "### Area One\n\n"
            "| Topic | Description |\n"
            "|-------|-------------|\n"
            "| [Ghost](docs/area-one/ghost.md) | Missing |\n\n"
            f"{MARKER_END}\n"
        )
        _write(self.tmpdir / "AGENTS.md", agents_text)

        result = run_health_check(self.tmpdir)
        manifest_issues = [
            i for i in result["issues"]
            if "AGENTS.md" in i.get("message", "") and "nonexistent" in i.get("message", "")
        ]
        self.assertTrue(len(manifest_issues) > 0)


class TestPlanFixIntegration(unittest.TestCase):
    """Verify curation plan fix works through run_health_check pipeline."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_plan_fix_with_fix_flag(self):
        """fix=True checks off plan items with existing files."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        _write(area / "topic-a.md", _valid_md("working", stem="topic-a"))
        _write(area / "topic-a.ref.md", _valid_md("reference", stem="topic-a"))

        plan_path = self.tmpdir / ".dewey" / "curation-plan.md"
        _write(plan_path, (
            "---\nlast_updated: 2026-02-15\n---\n\n"
            "# Curation Plan\n\n"
            "## area-one\n\n"
            "- [ ] Topic A -- core\n"
        ))

        result = run_health_check(self.tmpdir, fix=True)
        self.assertIn("fixes", result)
        plan_fixes = [f for f in result["fixes"] if f.get("action") == "checked_plan_item"]
        self.assertTrue(len(plan_fixes) > 0)
        self.assertIn("[x]", plan_path.read_text())


class TestCrossValidatorSkip(unittest.TestCase):
    """Cross validators skip gracefully when manifests absent."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_clean_kb_still_passes_without_manifests(self):
        """Clean KB with no AGENTS.md/CLAUDE.md/plan still has zero fails."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        _write(area / "topic.md", _valid_md("working"))
        _write(area / "topic.ref.md", _valid_md("reference"))
        result = run_health_check(self.tmpdir)
        fails = [i for i in result["issues"] if i["severity"] == "fail"]
        self.assertEqual(fails, [], f"Unexpected failures: {fails}")


class TestReadabilityIntegration(unittest.TestCase):
    """Verify readability fires through run_health_check pipeline."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_readability_fires_in_pipeline(self):
        """Very complex prose in a working file -> readability warn through pipeline."""
        area = self.kb / "area"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        today = date.today().isoformat()
        complex_prose = (
            "The implementation of sophisticated interdisciplinary methodologies "
            "necessitates comprehensive understanding of organizational infrastructure. "
            "Psychopharmacological interventions demonstrate considerable efficacy "
            "in ameliorating neuropsychiatric symptomatology. "
            "The conceptualization of multidimensional representational frameworks "
            "requires extraordinary phenomenological investigation. "
            "Telecommunications infrastructure modernization presupposes "
            "substantial capital expenditure authorization. "
        )
        doc = (
            f"---\nsources:\n  - https://example.com/doc\n"
            f"last_validated: {today}\nrelevance: core\ndepth: working\n---\n\n"
            f"# Topic\n\n"
            f"## Why This Matters\n{complex_prose}\n\n"
            f"## In Practice\n{complex_prose}\n\n"
            f"## Key Guidance\n{complex_prose}\n\n"
            f"## Watch Out For\nPitfalls.\n\n"
            f"## Go Deeper\n"
            f"- [topic Reference](topic.ref.md) -- quick-lookup\n"
            f"- [External](https://example.com/resource)\n"
        )
        _write(area / "topic.md", doc)
        _write(area / "topic.ref.md", _valid_md("reference"))
        result = run_health_check(self.tmpdir)
        readability_issues = [
            i for i in result["issues"]
            if "readability" in i.get("message", "").lower()
        ]
        self.assertTrue(len(readability_issues) > 0)


class TestNamingConventionsIntegration(unittest.TestCase):
    """Verify naming conventions fires through run_health_check pipeline."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_naming_conventions_fires_in_pipeline(self):
        """Uppercase directory name -> naming warn through pipeline."""
        area = self.kb / "Bad_Name"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        result = run_health_check(self.tmpdir)
        naming_issues = [
            i for i in result["issues"]
            if "naming conventions" in i.get("message", "").lower()
        ]
        self.assertTrue(len(naming_issues) > 0)


class TestCleanKbStillPasses(unittest.TestCase):
    """Ensure new validators don't break clean KB."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_clean_kb_no_fails_with_new_validators(self):
        """A valid KB produces zero fail-severity issues with all new validators active."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        _write(area / "topic.md", _valid_md("working"))
        _write(area / "topic.ref.md", _valid_md("reference"))
        result = run_health_check(self.tmpdir)
        fails = [i for i in result["issues"] if i["severity"] == "fail"]
        self.assertEqual(fails, [], f"Unexpected failures: {fails}")


if __name__ == "__main__":
    unittest.main()
