"""Tests for skills.health.scripts.check_kb — health check runner."""

import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from skills.health.scripts.check_kb import run_health_check


def _write(path: Path, text: str) -> Path:
    """Helper — write *text* to *path*, creating parents as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _valid_md(depth: str = "working", extra_body: str = "") -> str:
    """Return a minimal valid markdown document with proper frontmatter."""
    today = date.today().isoformat()
    # Ensure enough lines to pass size bounds for the given depth
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
        f"## In Practice\n"
        f"Concrete guidance here.\n"
        f"\n"
        f"## Key Guidance\n"
        f"Abstract principles here.\n"
        f"\n"
        f"{padding}\n"
        f"{extra_body}\n"
    )


class TestRunHealthCheck(unittest.TestCase):
    """Tests for the run_health_check function."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "knowledge"
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
    def test_skips_proposals(self):
        """Files inside _proposals/ are not validated."""
        proposals = self.kb / "_proposals"
        proposals.mkdir()
        _write(proposals / "draft.md", "# No frontmatter at all\n")
        result = run_health_check(self.tmpdir)
        proposal_issues = [
            i for i in result["issues"]
            if "_proposals" in i.get("file", "")
        ]
        self.assertEqual(proposal_issues, [])

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


if __name__ == "__main__":
    unittest.main()
