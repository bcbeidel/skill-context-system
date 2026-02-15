"""Tests for skills.init.scripts.scaffold — knowledge-base directory scaffolding."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from scaffold import _parse_agents_topics, merge_managed_section, scaffold_kb
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
        """Existing CLAUDE.md is preserved with knowledge base section appended."""
        claude_path = self.tmpdir / "CLAUDE.md"
        claude_path.write_text("# Custom content\n")
        scaffold_kb(self.tmpdir, "Paid Media Analyst")
        content = claude_path.read_text()
        self.assertIn("# Custom content", content)
        self.assertIn(MARKER_BEGIN, content)
        self.assertIn(MARKER_END, content)

    def test_merges_into_existing_agents_md(self):
        """Existing AGENTS.md is preserved with knowledge base section appended."""
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

    def test_creates_curation_plan_with_starter_topics(self):
        """scaffold creates .dewey/curation-plan.md when starter_topics provided."""
        scaffold_kb(
            self.tmpdir,
            "Analyst",
            domain_areas=["Testing"],
            starter_topics={"Testing": ["Unit Testing", "Integration Testing"]},
        )
        plan_path = self.tmpdir / ".dewey" / "curation-plan.md"
        self.assertTrue(plan_path.is_file())
        content = plan_path.read_text()
        self.assertIn("# Curation Plan", content)
        self.assertIn("## testing", content)
        self.assertIn("- [ ] Unit Testing -- core", content)
        self.assertIn("- [ ] Integration Testing -- core", content)

    def test_no_curation_plan_without_starter_topics(self):
        """scaffold does not create curation plan when no starter_topics."""
        scaffold_kb(self.tmpdir, "Analyst", domain_areas=["Testing"])
        plan_path = self.tmpdir / ".dewey" / "curation-plan.md"
        self.assertFalse(plan_path.exists())

    def test_curation_plan_in_summary(self):
        """Summary lists .dewey/curation-plan.md as created."""
        result = scaffold_kb(
            self.tmpdir,
            "Analyst",
            domain_areas=["Testing"],
            starter_topics={"Testing": ["Unit Testing"]},
        )
        self.assertIn(".dewey/curation-plan.md", result)

    def test_creates_config_json(self):
        """scaffold creates .dewey/config.json with default knowledge_dir."""
        scaffold_kb(self.tmpdir, "Analyst")
        config_path = self.tmpdir / ".dewey" / "config.json"
        self.assertTrue(config_path.is_file())
        import json
        data = json.loads(config_path.read_text())
        self.assertEqual(data["knowledge_dir"], "docs")

    def test_custom_knowledge_dir(self):
        """scaffold with custom knowledge_dir creates the named directory."""
        scaffold_kb(self.tmpdir, "Analyst", knowledge_dir="knowledge")
        self.assertTrue((self.tmpdir / "knowledge").is_dir())
        self.assertTrue((self.tmpdir / "knowledge" / "_proposals").is_dir())
        self.assertTrue((self.tmpdir / "knowledge" / "index.md").is_file())
        self.assertFalse((self.tmpdir / "docs").exists())
        import json
        data = json.loads((self.tmpdir / ".dewey" / "config.json").read_text())
        self.assertEqual(data["knowledge_dir"], "knowledge")

    def test_custom_knowledge_dir_in_summary(self):
        """Summary uses the actual knowledge dir name, not hardcoded 'docs'."""
        result = scaffold_kb(
            self.tmpdir,
            "Analyst",
            domain_areas=["Testing"],
            knowledge_dir="knowledge",
        )
        self.assertIn("knowledge/", result)
        self.assertNotIn("docs/", result)

    def test_custom_knowledge_dir_in_claude_md(self):
        """CLAUDE.md references the custom knowledge directory."""
        scaffold_kb(self.tmpdir, "Analyst", knowledge_dir="kb")
        content = (self.tmpdir / "CLAUDE.md").read_text()
        self.assertIn("kb/", content)

    def test_custom_knowledge_dir_in_agents_md(self):
        """AGENTS.md references the custom knowledge directory."""
        scaffold_kb(self.tmpdir, "Analyst", knowledge_dir="kb")
        content = (self.tmpdir / "AGENTS.md").read_text()
        self.assertIn("`kb/`", content)

    def test_reinit_preserves_topic_entries(self):
        """Re-running scaffold preserves topic entries in AGENTS.md."""
        scaffold_kb(self.tmpdir, "Analyst", domain_areas=["Testing"])
        # Simulate curate-promote adding a topic
        agents = self.tmpdir / "AGENTS.md"
        content = agents.read_text()
        content = content.replace(
            "### Testing\n",
            "### Testing\n\n| Topic | Description |\n|-------|-------------|\n"
            "| [Unit Tests](docs/testing/unit-tests.md) | How to write unit tests |\n",
        )
        agents.write_text(content)
        # Re-scaffold
        scaffold_kb(self.tmpdir, "Analyst", domain_areas=["Testing"])
        new_content = agents.read_text()
        self.assertIn("Unit Tests", new_content)
        self.assertIn("How to write unit tests", new_content)

    def test_reinit_preserves_topics_when_adding_areas(self):
        """Adding new areas preserves existing topic entries."""
        scaffold_kb(self.tmpdir, "Analyst", domain_areas=["Testing"])
        agents = self.tmpdir / "AGENTS.md"
        content = agents.read_text()
        content = content.replace(
            "### Testing\n",
            "### Testing\n\n| Topic | Description |\n|-------|-------------|\n"
            "| [Unit Tests](docs/testing/unit-tests.md) | How to write unit tests |\n",
        )
        agents.write_text(content)
        scaffold_kb(self.tmpdir, "Analyst", domain_areas=["Testing", "Backend"])
        new_content = agents.read_text()
        self.assertIn("Unit Tests", new_content)
        self.assertIn("### Backend", new_content)

    def test_index_md_updated_on_reinit(self):
        """index.md includes new areas after re-scaffold."""
        scaffold_kb(self.tmpdir, "Analyst", domain_areas=["Testing"])
        scaffold_kb(self.tmpdir, "Analyst", domain_areas=["Testing", "Backend"])
        content = (self.tmpdir / "docs" / "index.md").read_text()
        self.assertIn("backend/overview.md", content)
        self.assertIn("testing/overview.md", content)

    def test_curation_plan_preserves_progress_on_reinit(self):
        """Re-scaffold preserves [x] checkmarks in curation plan."""
        scaffold_kb(
            self.tmpdir, "Analyst",
            domain_areas=["Testing"],
            starter_topics={"Testing": ["Unit Testing"]},
        )
        plan = self.tmpdir / ".dewey" / "curation-plan.md"
        plan.write_text(plan.read_text().replace("- [ ] Unit Testing", "- [x] Unit Testing"))
        scaffold_kb(
            self.tmpdir, "Analyst",
            domain_areas=["Testing", "Backend"],
            starter_topics={"Testing": ["Unit Testing"], "Backend": ["APIs"]},
        )
        content = plan.read_text()
        self.assertIn("- [x] Unit Testing", content)
        self.assertIn("- [ ] APIs", content)

    def test_curation_plan_no_duplicate_areas(self):
        """Re-scaffold doesn't duplicate existing plan areas."""
        scaffold_kb(
            self.tmpdir, "Analyst",
            domain_areas=["Testing"],
            starter_topics={"Testing": ["Unit Testing"]},
        )
        scaffold_kb(
            self.tmpdir, "Analyst",
            domain_areas=["Testing"],
            starter_topics={"Testing": ["Unit Testing"]},
        )
        content = (self.tmpdir / ".dewey" / "curation-plan.md").read_text()
        self.assertEqual(content.count("## testing"), 1)


class TestParseAgentsTopics(unittest.TestCase):
    """Tests for the _parse_agents_topics helper."""

    def test_extracts_entries(self):
        """_parse_agents_topics extracts topic rows from managed section."""
        content = (
            "# Role\n\n"
            + MARKER_BEGIN + "\n"
            "## What You Have Access To\n"
            "### Testing\n\n"
            "| Topic | Description |\n"
            "|-------|-------------|\n"
            "| [Unit Tests](docs/testing/unit-tests.md) | How to test |\n\n"
            "### Backend\n"
            + MARKER_END
        )
        result = _parse_agents_topics(content)
        self.assertEqual(len(result["Testing"]), 1)
        self.assertEqual(result["Testing"][0]["name"], "Unit Tests")
        self.assertEqual(result["Testing"][0]["path"], "docs/testing/unit-tests.md")
        self.assertEqual(result["Testing"][0]["description"], "How to test")
        self.assertEqual(result["Backend"], [])

    def test_no_markers_returns_empty(self):
        """_parse_agents_topics returns empty dict when no markers present."""
        result = _parse_agents_topics("# Just a file\nNo markers here.")
        self.assertEqual(result, {})


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
