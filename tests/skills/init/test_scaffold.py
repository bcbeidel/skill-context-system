"""Tests for skills.init.scripts.scaffold — KB directory scaffolding."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from skills.init.scripts.scaffold import scaffold_kb


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
        self.assertTrue((self.tmpdir / "knowledge").is_dir())

    def test_creates_index_md(self):
        """knowledge/index.md exists after scaffold."""
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        self.assertTrue((self.tmpdir / "knowledge" / "index.md").is_file())

    def test_creates_proposals_directory(self):
        """knowledge/_proposals/ directory exists after scaffold."""
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        self.assertTrue((self.tmpdir / "knowledge" / "_proposals").is_dir())

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
            (self.tmpdir / "knowledge" / "campaign-management" / "overview.md").is_file()
        )
        self.assertTrue(
            (self.tmpdir / "knowledge" / "measurement" / "overview.md").is_file()
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

    def test_does_not_overwrite_existing_agents_md(self):
        """Existing AGENTS.md is preserved and not overwritten."""
        agents_path = self.tmpdir / "AGENTS.md"
        agents_path.write_text("# Custom content\n")
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        content = agents_path.read_text()
        self.assertEqual(content, "# Custom content\n")

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
        content = (self.tmpdir / "knowledge" / "index.md").read_text()
        self.assertIn("campaign-management/overview.md", content)
        self.assertIn("measurement/overview.md", content)


if __name__ == "__main__":
    unittest.main()
