"""Tests for utilization-driven curation recommendations."""

import json
import shutil
import subprocess
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


def _write_utilization_log(knowledge_base_root: Path, entries: list[str]) -> None:
    """Write utilization log entries to .dewey/utilization/log.jsonl."""
    log_dir = knowledge_base_root / ".dewey" / "utilization"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "log.jsonl").write_text("\n".join(entries) + "\n")


class TestGatingLogic(unittest.TestCase):
    """Tests for threshold gating before recommendations are generated."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.knowledge_base = self.tmpdir / "docs"
        self.knowledge_base.mkdir()
        area = self.knowledge_base / "area"
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
        self.knowledge_base = self.tmpdir / "docs"
        area = self.knowledge_base / "area"
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
        self.knowledge_base = self.tmpdir / "docs"
        # Area with only an overview
        area_a = self.knowledge_base / "area-a"
        area_a.mkdir(parents=True)
        _write(area_a / "overview.md", _valid_md("overview"))
        # Area with overview + working
        area_b = self.knowledge_base / "area-b"
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
        self.knowledge_base = self.tmpdir / "docs"
        area = self.knowledge_base / "area"
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
        self.knowledge_base = self.tmpdir / "docs"
        area = self.knowledge_base / "area"
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
        self.knowledge_base = self.tmpdir / "docs"
        area = self.knowledge_base / "area"
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
        self.knowledge_base = self.tmpdir / "docs"
        area = self.knowledge_base / "area"
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


class TestCLI(unittest.TestCase):
    """Tests for --recommendations CLI flag."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.knowledge_base = self.tmpdir / "docs"
        area = self.knowledge_base / "area"
        area.mkdir(parents=True)
        _write(area / "overview.md", _valid_md("overview"))
        _write(area / "topic.md", _valid_md("working"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run(self, *extra_args) -> subprocess.CompletedProcess:
        script = Path(__file__).resolve().parent.parent.parent.parent / \
            "dewey" / "skills" / "health" / "scripts" / "check_kb.py"
        cmd = ["python3", str(script), "--knowledge-base-root", str(self.tmpdir)]
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
        self.assertEqual(result.returncode, 0)
        parsed = json.loads(result.stdout)
        self.assertIn("skipped", parsed)

    def test_min_days_flag(self):
        """--min-days flag is respected."""
        now = datetime.now().isoformat(timespec="seconds")
        _write_utilization_log(self.tmpdir, [
            _log_entry("docs/area/overview.md", now),
        ])
        result = self._run("--recommendations", "--min-reads", "0", "--min-days", "999")
        self.assertEqual(result.returncode, 0)
        parsed = json.loads(result.stdout)
        self.assertIn("skipped", parsed)

    def test_recommendations_with_tier2(self):
        """--tier2 --recommendations includes both sections."""
        now = datetime.now().isoformat(timespec="seconds")
        _write_utilization_log(self.tmpdir, [
            _log_entry("docs/area/overview.md", now),
        ])
        result = self._run("--tier2", "--recommendations", "--min-reads", "0", "--min-days", "0")
        self.assertEqual(result.returncode, 0)
        parsed = json.loads(result.stdout)
        self.assertIn("tier2", parsed)
        self.assertIn("recommendations", parsed)
        self.assertNotIn("tier1", parsed)


if __name__ == "__main__":
    unittest.main()
