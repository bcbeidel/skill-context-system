"""Tests for skills.health.scripts.auto_fix — auto-fix for common KB issues."""

import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from auto_fix import fix_missing_cross_links, fix_missing_sections


def _write(path: Path, text: str) -> Path:
    """Helper — write *text* to *path*, creating parents as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _working_fm() -> str:
    today = date.today().isoformat()
    return (
        f"---\nsources:\n  - https://x.com\nlast_validated: {today}\n"
        f"relevance: core\ndepth: working\n---\n"
    )


def _overview_fm() -> str:
    today = date.today().isoformat()
    return (
        f"---\nsources:\n  - https://x.com\nlast_validated: {today}\n"
        f"relevance: core\ndepth: overview\n---\n"
    )


def _ref_fm() -> str:
    today = date.today().isoformat()
    return (
        f"---\nsources:\n  - https://x.com\nlast_validated: {today}\n"
        f"relevance: core\ndepth: reference\n---\n"
    )


# ------------------------------------------------------------------
# fix_missing_sections
# ------------------------------------------------------------------
class TestFixMissingSections(unittest.TestCase):
    """Tests for fix_missing_sections."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_inserts_stub_for_missing_sections(self):
        doc = (
            _working_fm()
            + "\n# Topic\n\n"
            + "## In Practice\nText.\n\n"
            + "## Key Guidance\nText.\n"
        )
        f = _write(self.tmpdir / "topic.md", doc)
        issues = [
            {"file": str(f), "message": "Missing required section: Why This Matters", "severity": "warn"},
            {"file": str(f), "message": "Missing required section: Watch Out For", "severity": "warn"},
            {"file": str(f), "message": "Missing required section: Go Deeper", "severity": "warn"},
        ]
        actions = fix_missing_sections(f, issues)
        self.assertEqual(len(actions), 3)

        text = f.read_text()
        self.assertIn("## Why This Matters", text)
        self.assertIn("## Watch Out For", text)
        self.assertIn("## Go Deeper", text)
        self.assertIn("<!-- TODO: Add content -->", text)

    def test_preserves_existing_content(self):
        doc = (
            _working_fm()
            + "\n# Topic\n\n"
            + "## In Practice\nImportant content here.\n"
        )
        f = _write(self.tmpdir / "topic.md", doc)
        issues = [
            {"file": str(f), "message": "Missing required section: Go Deeper", "severity": "warn"},
        ]
        fix_missing_sections(f, issues)
        text = f.read_text()
        self.assertIn("Important content here.", text)
        self.assertIn("## Go Deeper", text)

    def test_no_op_when_no_relevant_issues(self):
        doc = _working_fm() + "\n# Topic\n\n## In Practice\nText.\n"
        f = _write(self.tmpdir / "topic.md", doc)
        original = f.read_text()
        issues = [
            {"file": "/some/other/file.md", "message": "Missing required section: Go Deeper", "severity": "warn"},
        ]
        actions = fix_missing_sections(f, issues)
        self.assertEqual(actions, [])
        self.assertEqual(f.read_text(), original)

    def test_ignores_issues_for_other_files(self):
        doc = _working_fm() + "\n# Topic\n\n## In Practice\nText.\n"
        f = _write(self.tmpdir / "topic.md", doc)
        original = f.read_text()
        issues = [
            {"file": str(self.tmpdir / "other.md"), "message": "Missing required section: Go Deeper", "severity": "warn"},
        ]
        actions = fix_missing_sections(f, issues)
        self.assertEqual(actions, [])
        self.assertEqual(f.read_text(), original)

    def test_overview_sections(self):
        doc = _overview_fm() + "\n# Overview\n"
        f = _write(self.tmpdir / "overview.md", doc)
        issues = [
            {"file": str(f), "message": "Missing required section: What This Covers", "severity": "warn"},
            {"file": str(f), "message": "Missing required section: How It's Organized", "severity": "warn"},
        ]
        actions = fix_missing_sections(f, issues)
        self.assertEqual(len(actions), 2)
        text = f.read_text()
        self.assertIn("## What This Covers", text)
        self.assertIn("## How It's Organized", text)


# ------------------------------------------------------------------
# fix_missing_cross_links
# ------------------------------------------------------------------
class TestFixMissingCrossLinks(unittest.TestCase):
    """Tests for fix_missing_cross_links."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_appends_see_also_to_ref(self):
        doc = _ref_fm() + "\n# Reference\n\nContent.\n"
        ref = _write(self.tmpdir / "bidding.ref.md", doc)
        # Create companion working file
        _write(self.tmpdir / "bidding.md", "# Bidding\n")
        issues = [
            {"file": str(ref), "message": "Reference file missing 'See also' section", "severity": "warn"},
        ]
        actions = fix_missing_cross_links(ref, issues)
        self.assertEqual(len(actions), 1)
        self.assertIn("See also", ref.read_text())
        self.assertIn("bidding.md", ref.read_text())

    def test_skips_when_companion_missing(self):
        doc = _ref_fm() + "\n# Reference\n\nContent.\n"
        ref = _write(self.tmpdir / "bidding.ref.md", doc)
        # No companion file
        issues = [
            {"file": str(ref), "message": "Reference file missing 'See also' section", "severity": "warn"},
        ]
        original = ref.read_text()
        actions = fix_missing_cross_links(ref, issues)
        self.assertEqual(actions, [])
        self.assertEqual(ref.read_text(), original)

    def test_inserts_ref_link_in_go_deeper(self):
        doc = (
            _working_fm()
            + "\n# Topic\n\n## Go Deeper\n"
            + "- [External](https://example.com)\n"
        )
        f = _write(self.tmpdir / "bidding.md", doc)
        # Create companion ref file
        _write(self.tmpdir / "bidding.ref.md", "# Ref\n")
        issues = [
            {"file": str(f), "message": "Go Deeper section missing link to companion bidding.ref.md", "severity": "warn"},
        ]
        actions = fix_missing_cross_links(f, issues)
        self.assertEqual(len(actions), 1)
        text = f.read_text()
        self.assertIn("bidding.ref.md", text)

    def test_no_op_when_no_issues(self):
        doc = _working_fm() + "\n# Topic\n\n## Go Deeper\nLinks.\n"
        f = _write(self.tmpdir / "topic.md", doc)
        original = f.read_text()
        actions = fix_missing_cross_links(f, [])
        self.assertEqual(actions, [])
        self.assertEqual(f.read_text(), original)


# ------------------------------------------------------------------
# fix_curation_plan_checkmarks
# ------------------------------------------------------------------
class TestFixCurationPlanCheckmarks(unittest.TestCase):
    """Tests for fix_curation_plan_checkmarks."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.knowledge_base = self.tmpdir / "docs"
        self.knowledge_base.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write_plan(self, content: str) -> Path:
        plan_path = self.tmpdir / ".dewey" / "curation-plan.md"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(content)
        return plan_path

    def test_checks_off_existing_topics(self):
        """Unchecked item with file on disk -> checked off."""
        from auto_fix import fix_curation_plan_checkmarks

        area = self.knowledge_base / "area-one"
        area.mkdir()
        _write(area / "topic-a.md", "# Topic A\n")

        plan = self._write_plan(
            "---\nlast_updated: 2026-02-15\n---\n\n"
            "# Curation Plan\n\n"
            "## area-one\n\n"
            "- [ ] Topic A -- core\n"
        )

        actions = fix_curation_plan_checkmarks(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action"], "checked_plan_item")
        self.assertIn("[x]", plan.read_text())

    def test_preserves_already_checked(self):
        """Already checked item stays checked."""
        from auto_fix import fix_curation_plan_checkmarks

        area = self.knowledge_base / "area-one"
        area.mkdir()
        _write(area / "topic-a.md", "# Topic A\n")

        plan = self._write_plan(
            "---\nlast_updated: 2026-02-15\n---\n\n"
            "# Curation Plan\n\n"
            "## area-one\n\n"
            "- [x] Topic A -- core\n"
        )
        original = plan.read_text()

        actions = fix_curation_plan_checkmarks(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(actions, [])
        self.assertEqual(plan.read_text(), original)

    def test_preserves_unchecked_without_file(self):
        """Unchecked item without file stays unchecked."""
        from auto_fix import fix_curation_plan_checkmarks

        plan = self._write_plan(
            "---\nlast_updated: 2026-02-15\n---\n\n"
            "# Curation Plan\n\n"
            "## area-one\n\n"
            "- [ ] Missing Topic -- core\n"
        )
        original = plan.read_text()

        actions = fix_curation_plan_checkmarks(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(actions, [])
        self.assertEqual(plan.read_text(), original)

    def test_no_plan_file_returns_empty(self):
        """No plan file -> empty list."""
        from auto_fix import fix_curation_plan_checkmarks

        actions = fix_curation_plan_checkmarks(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(actions, [])


if __name__ == "__main__":
    unittest.main()
