"""Tests for skills.init.scripts.scaffold — KB directory scaffolding."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from scaffold import merge_managed_section, scaffold_kb
from templates import MARKER_BEGIN, MARKER_END


class TestScaffoldKB(unittest.TestCase):
    """Tests for the scaffold_kb function."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_creates_agents_md(self):
        """AGENTS.md exists after scaffold."""
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        self.assertTrue((self.tmpdir / "AGENTS.md").is_file())

    def test_creates_knowledge_directory(self):
        """knowledge/ directory exists after scaffold."""
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        self.assertTrue((self.tmpdir / "docs").is_dir())

    def test_creates_claude_md(self):
        """CLAUDE.md exists after scaffold."""
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        self.assertTrue((self.tmpdir / "CLAUDE.md").is_file())

    def test_claude_md_references_agents(self):
        """CLAUDE.md references AGENTS.md."""
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        content = (self.tmpdir / "CLAUDE.md").read_text()
        self.assertIn("AGENTS.md", content)

    def test_merges_into_existing_claude_md(self):
        """Existing CLAUDE.md is preserved with KB section appended."""
        claude_path = self.tmpdir / "CLAUDE.md"
        claude_path.write_text("# Custom content\n")
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        content = claude_path.read_text()
        self.assertIn("# Custom content", content)
        self.assertIn(MARKER_BEGIN, content)
        self.assertIn(MARKER_END, content)

    def test_merges_into_existing_agents_md(self):
        """Existing AGENTS.md is preserved with KB section appended."""
        agents_path = self.tmpdir / "AGENTS.md"
        agents_path.write_text("# My Custom Role\n\nCustom persona text.\n")
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        content = agents_path.read_text()
        self.assertIn("# My Custom Role", content)
        self.assertIn("Custom persona text.", content)
        self.assertIn(MARKER_BEGIN, content)
        self.assertIn(MARKER_END, content)
        self.assertIn("## What You Have Access To", content)

    def test_creates_index_md(self):
        """knowledge/index.md exists after scaffold."""
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        self.assertTrue((self.tmpdir / "docs" / "index.md").is_file())

    def test_creates_proposals_directory(self):
        """knowledge/_proposals/ directory exists after scaffold."""
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        self.assertTrue((self.tmpdir / "docs" / "_proposals").is_dir())

    def test_creates_dewey_directories(self):
        """.dewey/health, .dewey/history, .dewey/utilization exist."""
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        for subdir in ("health", "history", "utilization"):
            with self.subTest(subdir=subdir):
                self.assertTrue(
                    (self.tmpdir / ".dewey" / subdir).is_dir(),
                    f".dewey/{subdir} should exist",
                )

    def test_agents_md_contains_role(self):
        """AGENTS.md content includes the role name."""
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        content = (self.tmpdir / "AGENTS.md").read_text()
        self.assertIn("Paid Media Analyst", content)

    def test_creates_domain_area_with_overview(self):
        """knowledge/{slug}/overview.md exists for each domain area."""
        scaffold_kb(
            self.tmpdir,
            "Paid Media Analyst",
            domain_areas=["Campaign Management", "Measurement"],
        )
        self.assertTrue(
            (self.tmpdir / "docs" / "campaign-management" / "overview.md").is_file()
        )
        self.assertTrue(
            (self.tmpdir / "docs" / "measurement" / "overview.md").is_file()
        )

    def test_agents_md_under_100_lines(self):
        """AGENTS.md stays under 100 lines."""
        scaffold_kb(
            self.tmpdir,
            "Paid Media Analyst",
            domain_areas=["Campaign Management", "Measurement"],
        )
        content = (self.tmpdir / "AGENTS.md").read_text()
        line_count = len(content.splitlines())
        self.assertLess(line_count, 100, f"AGENTS.md has {line_count} lines")

    def test_scaffold_returns_summary(self):
        """Return value contains 'created'."""
        result = scaffold_kb(self.tmpdir, "Paid Media Analyst")
        self.assertIn("created", result.lower())

    def test_index_md_contains_domain_area_links(self):
        """index.md links to domain areas."""
        scaffold_kb(
            self.tmpdir,
            "Paid Media Analyst",
            domain_areas=["Campaign Management", "Measurement"],
        )
        content = (self.tmpdir / "docs" / "index.md").read_text()
        self.assertIn("campaign-management/overview.md", content)
        self.assertIn("measurement/overview.md", content)

    def test_claude_md_contains_markers(self):
        """CLAUDE.md contains managed-section markers."""
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        content = (self.tmpdir / "CLAUDE.md").read_text()
        self.assertIn(MARKER_BEGIN, content)
        self.assertIn(MARKER_END, content)

    def test_agents_md_contains_markers(self):
        """AGENTS.md contains managed-section markers."""
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        content = (self.tmpdir / "AGENTS.md").read_text()
        self.assertIn(MARKER_BEGIN, content)
        self.assertIn(MARKER_END, content)

    def test_merge_is_idempotent(self):
        """Running scaffold twice produces the same content."""
        scaffold_kb(self.tmpdir, "Paid Media Analyst", domain_areas=["Testing"])
        claude_first = (self.tmpdir / "CLAUDE.md").read_text()
        agents_first = (self.tmpdir / "AGENTS.md").read_text()

        scaffold_kb(self.tmpdir, "Paid Media Analyst", domain_areas=["Testing"])
        claude_second = (self.tmpdir / "CLAUDE.md").read_text()
        agents_second = (self.tmpdir / "AGENTS.md").read_text()

        self.assertEqual(claude_first, claude_second)
        self.assertEqual(agents_first, agents_second)

    def test_merge_updates_managed_section(self):
        """Re-running with new areas updates the managed section."""
        scaffold_kb(self.tmpdir, "Analyst", domain_areas=["Testing"])
        scaffold_kb(self.tmpdir, "Analyst", domain_areas=["Testing", "Backend"])

        claude_content = (self.tmpdir / "CLAUDE.md").read_text()
        self.assertIn("Backend", claude_content)
        self.assertIn("Testing", claude_content)

    def test_summary_reports_merged(self):
        """Summary says 'merged' when files already existed."""
        scaffold_kb(self.tmpdir, "Analyst")
        result = scaffold_kb(self.tmpdir, "Analyst")
        self.assertIn("merged", result.lower())

    def test_starter_topics_in_summary(self):
        """Summary includes curate plan when starter_topics provided."""
        result = scaffold_kb(
            self.tmpdir,
            "Analyst",
            domain_areas=["Testing"],
            starter_topics={"Testing": ["Unit Testing", "Integration Testing"]},
        )
        self.assertIn("Next Steps", result)
        self.assertIn("/dewey:curate add Unit Testing in testing", result)


class TestMergeManagedSection(unittest.TestCase):
    """Tests for the merge_managed_section helper."""

    def test_none_returns_full_template(self):
        result = merge_managed_section(None, "section content", "full template")
        self.assertEqual(result, "full template")

    def test_no_markers_appends_section(self):
        existing = "# My File\n\nSome content."
        result = merge_managed_section(existing, "managed stuff", "unused")
        self.assertIn("# My File", result)
        self.assertIn("Some content.", result)
        self.assertIn(MARKER_BEGIN, result)
        self.assertIn("managed stuff", result)
        self.assertIn(MARKER_END, result)

    def test_with_markers_replaces_section(self):
        existing = (
            "# Header\n\n"
            + MARKER_BEGIN + "\nold content\n" + MARKER_END + "\n\n"
            "# Footer\n"
        )
        result = merge_managed_section(existing, "new content", "unused")
        self.assertIn("# Header", result)
        self.assertIn("new content", result)
        self.assertNotIn("old content", result)
        self.assertIn("# Footer", result)

    def test_idempotent(self):
        """Merging the same section twice gives the same result."""
        existing = "# Header\n"
        first = merge_managed_section(existing, "section", "unused")
        second = merge_managed_section(first, "section", "unused")
        self.assertEqual(first, second)

    def test_preserves_content_before_markers(self):
        existing = "Line 1\nLine 2\n"
        result = merge_managed_section(existing, "managed", "unused")
        self.assertTrue(result.startswith("Line 1\nLine 2"))

    def test_preserves_content_after_markers(self):
        existing = (
            "Before\n"
            + MARKER_BEGIN + "\nold\n" + MARKER_END
            + "\nAfter\n"
        )
        result = merge_managed_section(existing, "new", "unused")
        self.assertIn("Before", result)
        self.assertIn("After", result)
        self.assertIn("new", result)


if __name__ == "__main__":
    unittest.main()
