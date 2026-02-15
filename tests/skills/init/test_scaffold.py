"""Tests for skills.init.scripts.scaffold — knowledge-base directory scaffolding."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from scaffold import (
    _discover_index_data,
    _parse_agents_topics,
    _read_topic_metadata,
    merge_managed_section,
    rebuild_index,
    scaffold_kb,
)
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

    def test_creates_hooks_json(self):
        """.claude/hooks.json is created with utilization hook."""
        scaffold_kb(self.tmpdir, "Analyst")
        hooks_path = self.tmpdir / ".claude" / "hooks.json"
        self.assertTrue(hooks_path.exists())
        parsed = json.loads(hooks_path.read_text())
        self.assertIn("PostToolUse", parsed["hooks"])

    def test_hooks_json_not_overwritten(self):
        """.claude/hooks.json is not overwritten if it already exists."""
        hooks_dir = self.tmpdir / ".claude"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hooks_path = hooks_dir / "hooks.json"
        hooks_path.write_text('{"custom": true}\n')
        scaffold_kb(self.tmpdir, "Analyst")
        content = hooks_path.read_text()
        self.assertEqual(content, '{"custom": true}\n')

    def test_hooks_json_in_summary(self):
        """Summary lists .claude/hooks.json as created."""
        result = scaffold_kb(self.tmpdir, "Analyst")
        self.assertIn(".claude/hooks.json", result)


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


class TestDiscoverIndexData(unittest.TestCase):
    """Tests for _discover_index_data filesystem scanner."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()
        (self.tmpdir / ".dewey").mkdir()
        (self.tmpdir / ".dewey" / "config.json").write_text('{"knowledge_dir": "docs"}')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def _valid_topic(self, name, depth="working"):
        return (
            f"---\nsources:\n  - url: https://example.com\n    title: Ex\n"
            f"last_validated: 2026-01-15\nrelevance: core\ndepth: {depth}\n"
            f"---\n# {name}\n"
        )

    def _valid_overview(self, name):
        return (
            f"---\nsources:\n  - url: https://example.com\n    title: Ex\n"
            f"last_validated: 2026-01-15\nrelevance: core\ndepth: overview\n"
            f"---\n# {name}\n"
        )

    def test_discovers_area_with_topics(self):
        """Discovers area with topics, excludes overview.md and .ref.md."""
        area = self.kb / "testing"
        self._write(area / "overview.md", self._valid_overview("Testing"))
        self._write(area / "unit-tests.md", self._valid_topic("Unit Tests"))
        self._write(area / "unit-tests.ref.md", "reference content")

        result = _discover_index_data(self.tmpdir, "docs")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Testing")
        self.assertEqual(result[0]["dirname"], "testing")
        topic_filenames = [t["filename"] for t in result[0]["topics"]]
        self.assertIn("unit-tests.md", topic_filenames)
        self.assertNotIn("overview.md", topic_filenames)
        self.assertNotIn("unit-tests.ref.md", topic_filenames)

    def test_reads_depth_from_frontmatter(self):
        """Verifies topic depth is read correctly from frontmatter."""
        area = self.kb / "testing"
        self._write(area / "overview.md", self._valid_overview("Testing"))
        self._write(area / "deep-dive.md", self._valid_topic("Deep Dive", depth="comprehensive"))

        result = _discover_index_data(self.tmpdir, "docs")

        topic = result[0]["topics"][0]
        self.assertEqual(topic["depth"], "comprehensive")

    def test_extracts_heading_as_name(self):
        """Verifies H1 heading is used as topic name."""
        area = self.kb / "testing"
        self._write(area / "overview.md", self._valid_overview("Testing"))
        self._write(area / "my-topic.md", self._valid_topic("My Fancy Topic Name"))

        result = _discover_index_data(self.tmpdir, "docs")

        topic = result[0]["topics"][0]
        self.assertEqual(topic["name"], "My Fancy Topic Name")

    def test_skips_proposals_directory(self):
        """Directories starting with _ are excluded."""
        self._write(self.kb / "_proposals" / "idea.md", self._valid_topic("Idea"))
        self._write(self.kb / "testing" / "overview.md", self._valid_overview("Testing"))
        self._write(self.kb / "testing" / "topic.md", self._valid_topic("Topic"))

        result = _discover_index_data(self.tmpdir, "docs")

        area_names = [a["dirname"] for a in result]
        self.assertNotIn("_proposals", area_names)
        self.assertIn("testing", area_names)

    def test_empty_knowledge_dir(self):
        """No subdirectories returns empty list."""
        result = _discover_index_data(self.tmpdir, "docs")
        self.assertEqual(result, [])

    def test_areas_sorted_alphabetically(self):
        """Areas are sorted by dirname."""
        for name in ["zebra", "alpha", "middle"]:
            area = self.kb / name
            self._write(area / "overview.md", self._valid_overview(name.title()))
            self._write(area / "topic.md", self._valid_topic("Topic"))

        result = _discover_index_data(self.tmpdir, "docs")

        dirnames = [a["dirname"] for a in result]
        self.assertEqual(dirnames, ["alpha", "middle", "zebra"])

    def test_topics_sorted_alphabetically(self):
        """Topics are sorted by filename."""
        area = self.kb / "testing"
        self._write(area / "overview.md", self._valid_overview("Testing"))
        self._write(area / "z-topic.md", self._valid_topic("Z Topic"))
        self._write(area / "a-topic.md", self._valid_topic("A Topic"))
        self._write(area / "m-topic.md", self._valid_topic("M Topic"))

        result = _discover_index_data(self.tmpdir, "docs")

        filenames = [t["filename"] for t in result[0]["topics"]]
        self.assertEqual(filenames, ["a-topic.md", "m-topic.md", "z-topic.md"])

    def test_area_name_falls_back_to_dirname(self):
        """When overview.md has no H1, area name falls back to directory name."""
        area = self.kb / "my-area"
        self._write(area / "overview.md", "---\ndepth: overview\n---\nNo heading here.\n")
        self._write(area / "topic.md", self._valid_topic("Topic"))

        result = _discover_index_data(self.tmpdir, "docs")

        self.assertEqual(result[0]["name"], "my-area")

    def test_topic_name_falls_back_to_filename(self):
        """When topic has no H1, name falls back to slugified filename."""
        area = self.kb / "testing"
        self._write(area / "overview.md", self._valid_overview("Testing"))
        self._write(area / "some-topic.md", "---\ndepth: working\n---\nNo heading.\n")

        result = _discover_index_data(self.tmpdir, "docs")

        topic = result[0]["topics"][0]
        self.assertEqual(topic["name"], "some-topic")


class TestReadTopicMetadata(unittest.TestCase):
    """Tests for _read_topic_metadata helper."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_reads_depth_and_name(self):
        """Reads depth from frontmatter and name from H1."""
        path = self.tmpdir / "topic.md"
        path.write_text(
            "---\nsources:\n  - url: https://example.com\n    title: Ex\n"
            "last_validated: 2026-01-15\nrelevance: core\ndepth: working\n"
            "---\n# My Topic\n\nContent here.\n"
        )
        result = _read_topic_metadata(path)
        self.assertEqual(result["name"], "My Topic")
        self.assertEqual(result["depth"], "working")

    def test_returns_empty_for_nonexistent_file(self):
        """Returns empty dict for nonexistent file."""
        result = _read_topic_metadata(self.tmpdir / "nonexistent.md")
        self.assertEqual(result, {})

    def test_missing_depth_returns_empty_string(self):
        """Returns empty string for depth when frontmatter lacks depth field."""
        path = self.tmpdir / "topic.md"
        path.write_text("---\nrelevance: core\n---\n# Topic\n")
        result = _read_topic_metadata(path)
        self.assertEqual(result["depth"], "")
        self.assertEqual(result["name"], "Topic")

    def test_missing_heading_returns_empty_name(self):
        """Returns empty string for name when no H1 heading found."""
        path = self.tmpdir / "topic.md"
        path.write_text("---\ndepth: working\n---\nNo heading here.\n")
        result = _read_topic_metadata(path)
        self.assertEqual(result["name"], "")
        self.assertEqual(result["depth"], "working")


class TestScaffoldIndexIncludesTopics(unittest.TestCase):
    """scaffold_kb regenerates index.md with discovered topics."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_index_md_includes_topics_on_reinit(self):
        """After adding topic files, re-scaffold picks them up in index.md."""
        scaffold_kb(self.tmpdir, "Dev", domain_areas=["Testing"])
        # Manually create a topic file (simulating curate workflow)
        topic = self.tmpdir / "docs" / "testing" / "unit-testing.md"
        topic.write_text("---\nsources:\n  - url: https://example.com\n    title: Ex\nlast_validated: 2026-01-15\nrelevance: core\ndepth: working\n---\n# Unit Testing\n")
        # Re-scaffold
        scaffold_kb(self.tmpdir, "Dev", domain_areas=["Testing"])
        index = (self.tmpdir / "docs" / "index.md").read_text()
        self.assertIn("Unit Testing", index)
        self.assertIn("unit-testing.md", index)

    def test_index_md_has_no_frontmatter(self):
        scaffold_kb(self.tmpdir, "Dev", domain_areas=["Testing"])
        index = (self.tmpdir / "docs" / "index.md").read_text()
        self.assertFalse(index.startswith("---"))


class TestRebuildIndex(unittest.TestCase):
    """Tests for the rebuild_index standalone function."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        scaffold_kb(self.tmpdir, "Dev", domain_areas=["Testing"])

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_rebuild_index_updates_from_disk(self):
        # Add a topic file
        topic = self.tmpdir / "docs" / "testing" / "api.md"
        topic.write_text("---\nsources:\n  - url: https://example.com\n    title: Ex\nlast_validated: 2026-01-15\nrelevance: core\ndepth: working\n---\n# API Patterns\n")
        rebuild_index(self.tmpdir)
        index = (self.tmpdir / "docs" / "index.md").read_text()
        self.assertIn("API Patterns", index)

    def test_rebuild_index_reads_role_from_agents_md(self):
        rebuild_index(self.tmpdir)
        index = (self.tmpdir / "docs" / "index.md").read_text()
        self.assertIn("Dev", index)

    def test_rebuild_index_respects_knowledge_dir_config(self):
        result = rebuild_index(self.tmpdir)
        self.assertEqual(result, "docs/index.md")
        self.assertTrue((self.tmpdir / "docs" / "index.md").exists())


if __name__ == "__main__":
    unittest.main()
