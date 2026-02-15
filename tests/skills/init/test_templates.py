"""Tests for skills.init.scripts.templates — knowledge-base content template rendering."""

import datetime
import json
import unittest
from unittest.mock import patch

from templates import (
    MARKER_BEGIN,
    MARKER_END,
    _slugify,
    render_agents_md,
    render_agents_md_section,
    render_claude_md,
    render_claude_md_section,
    render_curate_plan,
    render_curation_plan_md,
    render_hooks_json,
    render_index_md,
    render_overview_md,
    render_proposal_md,
    render_topic_md,
    render_topic_ref_md,
)


class TestSlugify(unittest.TestCase):
    """Tests for the _slugify helper."""

    def test_basic_lowercase(self):
        self.assertEqual(_slugify("Hello World"), "hello-world")

    def test_already_lowercase(self):
        self.assertEqual(_slugify("foo bar"), "foo-bar")

    def test_multiple_spaces(self):
        self.assertEqual(_slugify("foo   bar"), "foo-bar")

    def test_leading_trailing_spaces(self):
        self.assertEqual(_slugify("  foo bar  "), "foo-bar")

    def test_special_characters_stripped(self):
        self.assertEqual(_slugify("C++ & Python!"), "c-python")

    def test_hyphens_preserved(self):
        self.assertEqual(_slugify("already-slugged"), "already-slugged")

    def test_mixed_case_with_numbers(self):
        self.assertEqual(_slugify("React 18 Patterns"), "react-18-patterns")

    def test_consecutive_hyphens_collapsed(self):
        self.assertEqual(_slugify("foo - bar"), "foo-bar")

    def test_empty_string(self):
        self.assertEqual(_slugify(""), "")

    def test_single_word(self):
        self.assertEqual(_slugify("Python"), "python")

    def test_dots_stripped(self):
        self.assertEqual(_slugify("Node.js Basics"), "nodejs-basics")

    def test_underscores_become_hyphens(self):
        self.assertEqual(_slugify("snake_case_name"), "snake-case-name")


FIXED_DATE = datetime.date(2026, 1, 15)


@patch("templates.date")
class TestRenderAgentsMd(unittest.TestCase):
    """Tests for render_agents_md."""

    def _domain_areas(self):
        return [
            {
                "name": "Backend Development",
                "topics": [
                    {"name": "API Design", "description": "RESTful API patterns"},
                    {"name": "Error Handling", "description": "Robust error strategies"},
                ],
            },
            {
                "name": "Testing",
                "topics": [
                    {"name": "Unit Testing", "description": "Isolated test practices"},
                ],
            },
        ]

    def test_contains_role_heading(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Senior Python Developer", self._domain_areas())
        self.assertIn("# Role: Senior Python Developer", result)

    def test_contains_persona_placeholder(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Senior Python Developer", self._domain_areas())
        self.assertIn("## Who You Are", result)
        self.assertIn("<!--", result)

    def test_contains_domain_area_headings(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Senior Python Developer", self._domain_areas())
        self.assertIn("### Backend Development", result)
        self.assertIn("### Testing", result)

    def test_contains_topic_entries(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Senior Python Developer", self._domain_areas())
        self.assertIn("API Design", result)
        self.assertIn("RESTful API patterns", result)
        self.assertIn("Unit Testing", result)

    def test_topics_use_table_format(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Senior Python Developer", self._domain_areas())
        self.assertIn("| Topic | Description |", result)
        self.assertIn("|-------|-------------|", result)

    def test_contains_how_to_use_section(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Senior Python Developer", self._domain_areas())
        self.assertIn("## How To Use This Knowledge", result)
        self.assertIn("docs/", result)

    def test_contains_what_you_have_access_to_section(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Senior Python Developer", self._domain_areas())
        self.assertIn("## What You Have Access To", result)

    def test_empty_domain_areas(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Generalist", [])
        self.assertIn("# Role: Generalist", result)
        self.assertIn("## What You Have Access To", result)

    def test_contains_markers(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Senior Python Developer", self._domain_areas())
        self.assertIn(MARKER_BEGIN, result)
        self.assertIn(MARKER_END, result)

    def test_user_section_outside_markers(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Senior Python Developer", self._domain_areas())
        begin_pos = result.index(MARKER_BEGIN)
        self.assertIn("# Role:", result[:begin_pos])
        self.assertIn("## Who You Are", result[:begin_pos])

    def test_managed_section_inside_markers(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Senior Python Developer", self._domain_areas())
        begin_pos = result.index(MARKER_BEGIN)
        end_pos = result.index(MARKER_END)
        managed = result[begin_pos:end_pos]
        self.assertIn("## What You Have Access To", managed)
        self.assertIn("## How To Use This Knowledge", managed)

    def test_mentions_ref_md(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Senior Python Developer", self._domain_areas())
        self.assertIn(".ref.md", result)

    def test_custom_knowledge_dir(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Dev", self._domain_areas(), knowledge_dir="knowledge")
        self.assertIn("`knowledge/`", result)
        self.assertNotIn("`docs/`", result)


@patch("templates.date")
class TestRenderAgentsMdSection(unittest.TestCase):
    """Tests for render_agents_md_section (managed content without markers)."""

    def _domain_areas(self):
        return [
            {
                "name": "Backend Development",
                "topics": [
                    {"name": "API Design", "description": "RESTful API patterns"},
                ],
            },
        ]

    def test_no_markers(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md_section("Dev", self._domain_areas())
        self.assertNotIn(MARKER_BEGIN, result)
        self.assertNotIn(MARKER_END, result)

    def test_contains_access_section(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md_section("Dev", self._domain_areas())
        self.assertIn("## What You Have Access To", result)

    def test_contains_usage_section(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md_section("Dev", self._domain_areas())
        self.assertIn("## How To Use This Knowledge", result)

    def test_contains_domain_areas(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md_section("Dev", self._domain_areas())
        self.assertIn("### Backend Development", result)
        self.assertIn("API Design", result)

    def test_mentions_ref_md(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md_section("Dev", self._domain_areas())
        self.assertIn(".ref.md", result)

    def test_references_curation_plan(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md_section("Dev", self._domain_areas())
        self.assertIn("curation-plan.md", result)


@patch("templates.date")
class TestRenderIndexMd(unittest.TestCase):
    """Tests for render_index_md."""

    def _domain_areas(self):
        return [
            {"name": "Backend Development", "dirname": "backend-development"},
            {"name": "Testing", "dirname": "testing"},
        ]

    def test_contains_heading(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_index_md("Senior Python Developer", self._domain_areas())
        self.assertIn("# Knowledge Base", result)

    def test_contains_role_reference(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_index_md("Senior Python Developer", self._domain_areas())
        self.assertIn("Senior Python Developer", result)

    def test_contains_links_to_domain_areas(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_index_md("Senior Python Developer", self._domain_areas())
        self.assertIn("backend-development", result)
        self.assertIn("Backend Development", result)
        self.assertIn("testing", result)

    def test_links_point_to_overview(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_index_md("Senior Python Developer", self._domain_areas())
        self.assertIn("backend-development/overview.md", result)

    def test_uses_table_format(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_index_md("Senior Python Developer", self._domain_areas())
        # Table format with overview links per area
        self.assertIn("| [Overview]", result)

    def test_empty_domain_areas(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_index_md("Generalist", [])
        self.assertIn("# Knowledge Base", result)

    def test_includes_topics_when_provided(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        areas = [
            {
                "name": "Backend Development",
                "dirname": "backend-development",
                "topics": [
                    {"name": "API Design", "filename": "api-design.md", "depth": "working"},
                    {"name": "Error Handling", "filename": "error-handling.md", "depth": "working"},
                ],
            },
        ]
        result = render_index_md("Dev", areas)
        self.assertIn("API Design", result)
        self.assertIn("api-design.md", result)
        self.assertIn("Error Handling", result)

    def test_topics_show_depth(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        areas = [
            {
                "name": "Testing",
                "dirname": "testing",
                "topics": [
                    {"name": "Unit Testing", "filename": "unit-testing.md", "depth": "working"},
                ],
            },
        ]
        result = render_index_md("Dev", areas)
        self.assertIn("working", result)

    def test_no_topics_key_shows_overview_only(self, mock_date):
        """Backward compat: areas without 'topics' key still render overview link."""
        mock_date.today.return_value = FIXED_DATE
        areas = [{"name": "Testing", "dirname": "testing"}]
        result = render_index_md("Dev", areas)
        self.assertIn("testing/overview.md", result)
        self.assertIn("Testing", result)

    def test_no_frontmatter_in_output(self, mock_date):
        """index.md is structural — no YAML frontmatter."""
        mock_date.today.return_value = FIXED_DATE
        areas = [{"name": "Testing", "dirname": "testing"}]
        result = render_index_md("Dev", areas)
        self.assertFalse(result.startswith("---"))

    def test_ref_md_files_excluded_from_topics(self, mock_date):
        """Reference companions should not appear as separate topic rows."""
        mock_date.today.return_value = FIXED_DATE
        areas = [
            {
                "name": "Testing",
                "dirname": "testing",
                "topics": [
                    {"name": "Unit Testing", "filename": "unit-testing.md", "depth": "working"},
                ],
            },
        ]
        result = render_index_md("Dev", areas)
        self.assertNotIn(".ref.md", result)


@patch("templates.date")
class TestRenderOverviewMd(unittest.TestCase):
    """Tests for render_overview_md."""

    def _topics(self):
        return [
            {
                "name": "API Design",
                "filename": "api-design.md",
                "description": "RESTful API patterns",
            },
            {
                "name": "Error Handling",
                "filename": "error-handling.md",
                "description": "Robust error strategies",
            },
        ]

    def test_contains_yaml_frontmatter(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Backend Development", "core", self._topics())
        self.assertTrue(result.startswith("---\n"))
        self.assertIn("---", result[3:])

    def test_frontmatter_has_depth_overview(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Backend Development", "core", self._topics())
        self.assertIn("depth: overview", result)

    def test_frontmatter_has_sources(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Backend Development", "core", self._topics())
        self.assertIn("sources:", result)

    def test_frontmatter_has_last_validated(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Backend Development", "core", self._topics())
        self.assertIn("last_validated: 2026-01-15", result)

    def test_frontmatter_has_relevance(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Backend Development", "core", self._topics())
        self.assertIn("relevance:", result)
        self.assertIn("core", result)

    def test_contains_area_heading(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Backend Development", "core", self._topics())
        self.assertIn("# Backend Development", result)

    def test_contains_what_this_covers_section(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Backend Development", "core", self._topics())
        self.assertIn("## What This Covers", result)

    def test_contains_how_its_organized_section(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Backend Development", "core", self._topics())
        self.assertIn("## How It's Organized", result)

    def test_contains_key_sources_section(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Backend Development", "core", self._topics())
        self.assertIn("## Key Sources", result)

    def test_contains_all_three_required_sections(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Backend Development", "core", self._topics())
        for section in [
            "## What This Covers",
            "## How It's Organized",
            "## Key Sources",
        ]:
            with self.subTest(section=section):
                self.assertIn(section, result)

    def test_contains_topic_links(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Backend Development", "core", self._topics())
        self.assertIn("api-design.md", result)
        self.assertIn("API Design", result)
        self.assertIn("error-handling.md", result)

    def test_contains_topic_descriptions(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Backend Development", "core", self._topics())
        self.assertIn("RESTful API patterns", result)

    def test_topics_use_table_format(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Backend Development", "core", self._topics())
        self.assertIn("| Topic | Description |", result)
        self.assertIn("|-------|-------------|", result)

    def test_empty_topics(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Empty Area", "peripheral", [])
        self.assertIn("# Empty Area", result)
        self.assertIn("depth: overview", result)


@patch("templates.date")
class TestRenderTopicMd(unittest.TestCase):
    """Tests for render_topic_md (working knowledge)."""

    def test_contains_yaml_frontmatter(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_md("API Design", "core")
        self.assertTrue(result.startswith("---\n"))
        self.assertIn("---", result[3:])

    def test_frontmatter_has_sources(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_md("API Design", "core")
        self.assertIn("sources:", result)

    def test_frontmatter_has_last_validated(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_md("API Design", "core")
        self.assertIn("last_validated: 2026-01-15", result)

    def test_frontmatter_has_relevance(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_md("API Design", "core")
        self.assertIn('relevance: "core"', result)

    def test_frontmatter_has_depth_working(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_md("API Design", "core")
        self.assertIn("depth: working", result)

    def test_frontmatter_has_source_placeholder(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_md("API Design", "core")
        self.assertIn("<!-- Add primary source URL -->", result)
        self.assertIn("<!-- Add source title -->", result)

    def test_contains_topic_heading(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_md("API Design", "core")
        self.assertIn("# API Design", result)

    def test_contains_required_sections(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_md("API Design", "core")
        for section in [
            "## Why This Matters",
            "## In Practice",
            "## Key Guidance",
            "## Watch Out For",
            "## Go Deeper",
        ]:
            with self.subTest(section=section):
                self.assertIn(section, result)

    def test_go_deeper_links_to_reference(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_md("API Design", "core")
        self.assertIn("[API Design Reference](api-design.ref.md)", result)
        self.assertIn("[Source Title](url)", result)

    def test_contains_html_comment_placeholders(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_md("API Design", "core")
        self.assertGreater(result.count("<!--"), 0)
        self.assertGreater(result.count("-->"), 0)

    def test_uses_today_date(self, mock_date):
        mock_date.today.return_value = datetime.date(2026, 6, 30)
        result = render_topic_md("Testing", "supporting")
        self.assertIn("last_validated: 2026-06-30", result)


@patch("templates.date")
class TestRenderTopicRefMd(unittest.TestCase):
    """Tests for render_topic_ref_md (expert reference)."""

    def test_contains_yaml_frontmatter(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_ref_md("API Design", "core")
        self.assertTrue(result.startswith("---\n"))

    def test_frontmatter_has_depth_reference(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_ref_md("API Design", "core")
        self.assertIn("depth: reference", result)

    def test_frontmatter_has_relevance(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_ref_md("API Design", "core")
        self.assertIn('relevance: "core"', result)

    def test_frontmatter_has_last_validated(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_ref_md("API Design", "core")
        self.assertIn("last_validated: 2026-01-15", result)

    def test_frontmatter_has_source_placeholder(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_ref_md("API Design", "core")
        self.assertIn("<!-- Add primary source URL -->", result)
        self.assertIn("<!-- Add source title -->", result)

    def test_contains_see_also_link(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_ref_md("API Design", "core")
        self.assertIn("**See also:**", result)

    def test_is_terse(self, mock_date):
        """Reference docs should be shorter than working docs."""
        mock_date.today.return_value = FIXED_DATE
        working = render_topic_md("API Design", "core")
        ref = render_topic_ref_md("API Design", "core")
        self.assertLess(len(ref), len(working))

    def test_contains_topic_heading(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_ref_md("API Design", "core")
        self.assertIn("# API Design", result)


@patch("templates.date")
class TestRenderProposalMd(unittest.TestCase):
    """Tests for render_proposal_md."""

    def test_contains_yaml_frontmatter(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_proposal_md("New Topic", "supporting", "alice", "Needed for X")
        self.assertTrue(result.startswith("---\n"))

    def test_frontmatter_has_status_proposal(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_proposal_md("New Topic", "supporting", "alice", "Needed for X")
        self.assertIn("status: proposal", result)

    def test_frontmatter_has_proposed_by(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_proposal_md("New Topic", "supporting", "alice", "Needed for X")
        self.assertIn("proposed_by: alice", result)

    def test_frontmatter_has_rationale(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_proposal_md("New Topic", "supporting", "alice", "Needed for X")
        self.assertIn("rationale: Needed for X", result)

    def test_frontmatter_has_relevance(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_proposal_md("New Topic", "supporting", "alice", "Needed for X")
        self.assertIn('relevance: "supporting"', result)

    def test_frontmatter_has_source_placeholder(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_proposal_md("New Topic", "supporting", "alice", "Needed for X")
        self.assertIn("<!-- Add primary source URL -->", result)
        self.assertIn("<!-- Add source title -->", result)

    def test_frontmatter_has_last_validated(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_proposal_md("New Topic", "supporting", "alice", "Needed for X")
        self.assertIn("last_validated: 2026-01-15", result)

    def test_contains_topic_heading(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_proposal_md("New Topic", "supporting", "alice", "Needed for X")
        self.assertIn("# New Topic", result)

    def test_contains_required_working_sections(self, mock_date):
        """Proposals should contain the same sections as working docs."""
        mock_date.today.return_value = FIXED_DATE
        result = render_proposal_md("New Topic", "supporting", "alice", "Needed for X")
        for section in [
            "## Why This Matters",
            "## In Practice",
            "## Key Guidance",
            "## Watch Out For",
            "## Go Deeper",
        ]:
            with self.subTest(section=section):
                self.assertIn(section, result)


@patch("templates.date")
class TestRenderClaudeMd(unittest.TestCase):
    """Tests for render_claude_md."""

    def _domain_areas(self):
        return [
            {"name": "Backend Development", "dirname": "backend-development"},
            {"name": "Testing", "dirname": "testing"},
        ]

    def test_contains_kb_heading(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md("Senior Python Developer", self._domain_areas())
        self.assertIn("## Knowledge Base", result)

    def test_references_agents_md(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md("Senior Python Developer", self._domain_areas())
        self.assertIn("AGENTS.md", result)

    def test_references_docs_directory(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md("Senior Python Developer", self._domain_areas())
        self.assertIn("docs/", result)

    def test_contains_domain_area_table(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md("Senior Python Developer", self._domain_areas())
        self.assertIn("| Area | Path | Overview |", result)
        self.assertIn("backend-development", result)
        self.assertIn("testing", result)

    def test_empty_domain_areas(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md("Generalist", [])
        self.assertIn("## Knowledge Base", result)
        self.assertNotIn("| Area |", result)

    def test_contains_markers(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md("Senior Python Developer", self._domain_areas())
        self.assertIn(MARKER_BEGIN, result)
        self.assertIn(MARKER_END, result)

    def test_contains_how_to_use_section(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md("Senior Python Developer", self._domain_areas())
        self.assertIn("### How to Use This Knowledge Base", result)

    def test_contains_directory_structure(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md("Senior Python Developer", self._domain_areas())
        self.assertIn("### Directory Structure", result)
        self.assertIn("AGENTS.md", result)
        self.assertIn("_proposals/", result)

    def test_contains_frontmatter_reference(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md("Senior Python Developer", self._domain_areas())
        self.assertIn("### Frontmatter Reference", result)
        self.assertIn("`sources`", result)
        self.assertIn("`last_validated`", result)
        self.assertIn("`relevance`", result)
        self.assertIn("`depth`", result)

    def test_mentions_ref_md(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md("Senior Python Developer", self._domain_areas())
        self.assertIn(".ref.md", result)

    def test_custom_knowledge_dir(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md("Dev", self._domain_areas(), knowledge_dir="kb")
        self.assertIn("kb/", result)
        self.assertIn("`kb/backend-development/`", result)


@patch("templates.date")
class TestRenderClaudeMdSection(unittest.TestCase):
    """Tests for render_claude_md_section (managed content without markers)."""

    def _domain_areas(self):
        return [
            {"name": "Backend Development", "dirname": "backend-development"},
            {"name": "Testing", "dirname": "testing"},
        ]

    def test_no_markers(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md_section("Dev", self._domain_areas())
        self.assertNotIn(MARKER_BEGIN, result)
        self.assertNotIn(MARKER_END, result)

    def test_contains_domain_areas(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md_section("Dev", self._domain_areas())
        self.assertIn("Backend Development", result)
        self.assertIn("Testing", result)

    def test_contains_frontmatter_reference(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md_section("Dev", self._domain_areas())
        self.assertIn("### Frontmatter Reference", result)

    def test_contains_directory_structure(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md_section("Dev", self._domain_areas())
        self.assertIn("### Directory Structure", result)

    def test_contains_how_to_use(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md_section("Dev", self._domain_areas())
        self.assertIn("### How to Use This Knowledge Base", result)

    def test_contains_overview_links(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md_section("Dev", self._domain_areas())
        self.assertIn("overview.md", result)

    def test_references_curation_plan(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_claude_md_section("Dev", self._domain_areas())
        self.assertIn("curation-plan.md", result)


@patch("templates.date")
class TestRenderCurationPlanMd(unittest.TestCase):
    """Tests for render_curation_plan_md (persistent plan file)."""

    def test_contains_frontmatter(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        areas = [{"name": "Testing", "slug": "testing", "starter_topics": ["Unit Testing"]}]
        result = render_curation_plan_md(areas)
        self.assertTrue(result.startswith("---\n"))
        self.assertIn("last_updated: 2026-01-15", result)

    def test_contains_heading(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        areas = [{"name": "Testing", "slug": "testing", "starter_topics": ["Unit Testing"]}]
        result = render_curation_plan_md(areas)
        self.assertIn("# Curation Plan", result)

    def test_contains_description(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        areas = [{"name": "Testing", "slug": "testing", "starter_topics": ["Unit Testing"]}]
        result = render_curation_plan_md(areas)
        self.assertIn("/dewey:curate plan", result)

    def test_area_heading_uses_slug(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        areas = [{"name": "Backend Development", "slug": "backend-development", "starter_topics": ["API Design"]}]
        result = render_curation_plan_md(areas)
        self.assertIn("## backend-development", result)

    def test_topics_as_strings(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        areas = [{"name": "Testing", "slug": "testing", "starter_topics": ["Unit Testing", "Integration Testing"]}]
        result = render_curation_plan_md(areas)
        self.assertIn("- [ ] Unit Testing -- core", result)
        self.assertIn("- [ ] Integration Testing -- core", result)

    def test_topics_as_dicts(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        areas = [{
            "name": "Testing",
            "slug": "testing",
            "starter_topics": [
                {"name": "Unit Testing", "relevance": "core", "rationale": "isolated test practices"},
                {"name": "E2E Testing", "relevance": "supporting"},
            ],
        }]
        result = render_curation_plan_md(areas)
        self.assertIn("- [ ] Unit Testing -- core -- isolated test practices", result)
        self.assertIn("- [ ] E2E Testing -- supporting", result)

    def test_empty_areas(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_curation_plan_md([])
        self.assertIn("# Curation Plan", result)
        self.assertNotIn("## ", result.split("# Curation Plan")[1])

    def test_areas_without_topics_skipped(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        areas = [{"name": "Empty", "slug": "empty", "starter_topics": []}]
        result = render_curation_plan_md(areas)
        self.assertNotIn("## empty", result)

    def test_slugifies_name_when_no_slug(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        areas = [{"name": "Backend Development", "starter_topics": ["API Design"]}]
        result = render_curation_plan_md(areas)
        self.assertIn("## backend-development", result)

    def test_multiple_areas(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        areas = [
            {"name": "Testing", "slug": "testing", "starter_topics": ["Unit Testing"]},
            {"name": "Backend", "slug": "backend", "starter_topics": ["API Design"]},
        ]
        result = render_curation_plan_md(areas)
        self.assertIn("## testing", result)
        self.assertIn("## backend", result)
        self.assertIn("- [ ] Unit Testing -- core", result)
        self.assertIn("- [ ] API Design -- core", result)


class TestRenderCuratePlan(unittest.TestCase):
    """Tests for render_curate_plan."""

    def test_heading(self):
        areas = [{"name": "Testing", "slug": "testing", "starter_topics": ["Unit Testing"]}]
        result = render_curate_plan(areas)
        self.assertIn("## Next Steps: Populate Your Knowledge Base", result)

    def test_numbered_commands(self):
        areas = [
            {"name": "Testing", "slug": "testing", "starter_topics": ["Unit Testing", "Integration Testing"]},
        ]
        result = render_curate_plan(areas)
        self.assertIn("1. `/dewey:curate add Unit Testing in testing`", result)
        self.assertIn("2. `/dewey:curate add Integration Testing in testing`", result)

    def test_area_headings(self):
        areas = [
            {"name": "Testing", "slug": "testing", "starter_topics": ["Unit Testing"]},
            {"name": "Backend", "slug": "backend", "starter_topics": ["API Design"]},
        ]
        result = render_curate_plan(areas)
        self.assertIn("### Testing", result)
        self.assertIn("### Backend", result)

    def test_cross_area_numbering(self):
        areas = [
            {"name": "Testing", "slug": "testing", "starter_topics": ["Unit Testing"]},
            {"name": "Backend", "slug": "backend", "starter_topics": ["API Design"]},
        ]
        result = render_curate_plan(areas)
        self.assertIn("1. `/dewey:curate add Unit Testing in testing`", result)
        self.assertIn("2. `/dewey:curate add API Design in backend`", result)

    def test_empty_areas(self):
        result = render_curate_plan([])
        self.assertEqual(result, "")

    def test_areas_without_starter_topics(self):
        areas = [{"name": "Testing", "slug": "testing", "starter_topics": []}]
        result = render_curate_plan(areas)
        self.assertEqual(result, "")

    def test_slugifies_name_when_no_slug(self):
        areas = [{"name": "Backend Development", "starter_topics": ["API Design"]}]
        result = render_curate_plan(areas)
        self.assertIn("in backend-development", result)


class TestRenderHooksJson(unittest.TestCase):
    """Tests for render_hooks_json."""

    def test_returns_valid_json(self):
        result = render_hooks_json(plugin_root="/path/to/plugin", kb_root="/path/to/kb")
        parsed = json.loads(result)
        self.assertIn("hooks", parsed)

    def test_contains_post_tool_use(self):
        result = render_hooks_json(plugin_root="/path/to/plugin", kb_root="/path/to/kb")
        parsed = json.loads(result)
        self.assertIn("PostToolUse", parsed["hooks"])

    def test_matcher_is_read(self):
        result = render_hooks_json(plugin_root="/path/to/plugin", kb_root="/path/to/kb")
        parsed = json.loads(result)
        hook_group = parsed["hooks"]["PostToolUse"][0]
        self.assertEqual(hook_group["matcher"], "Read")

    def test_command_references_script(self):
        result = render_hooks_json(plugin_root="/path/to/plugin", kb_root="/path/to/kb")
        parsed = json.loads(result)
        command = parsed["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
        self.assertIn("hook_log_access.py", command)
        self.assertIn("/path/to/kb", command)


class TestReturnTypes(unittest.TestCase):
    """All render functions must return strings."""

    @patch("templates.date")
    def test_all_render_functions_return_str(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        domain_areas_agents = [
            {"name": "Area", "topics": [{"name": "T", "description": "d"}]}
        ]
        domain_areas_index = [{"name": "Area", "dirname": "area"}]
        topics_overview = [{"name": "T", "filename": "t.md", "description": "d"}]
        curate_areas = [{"name": "Area", "slug": "area", "starter_topics": ["T"]}]

        cases = [
            render_agents_md("R", domain_areas_agents),
            render_agents_md_section("R", domain_areas_agents),
            render_claude_md("R", domain_areas_index),
            render_claude_md_section("R", domain_areas_index),
            render_curate_plan(curate_areas),
            render_curation_plan_md(curate_areas),
            render_hooks_json("/plugin", "/kb"),
            render_index_md("R", domain_areas_index),
            render_overview_md("A", "core", topics_overview),
            render_topic_md("T", "core"),
            render_topic_ref_md("T", "core"),
            render_proposal_md("T", "core", "alice", "reason"),
        ]
        for i, result in enumerate(cases):
            with self.subTest(i=i):
                self.assertIsInstance(result, str)


class TestNoTrailingWhitespace(unittest.TestCase):
    """Rendered templates should not have trailing whitespace on lines."""

    @patch("templates.date")
    def test_no_trailing_whitespace(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        domain_areas_agents = [
            {"name": "Area", "topics": [{"name": "T", "description": "d"}]}
        ]
        domain_areas_index = [{"name": "Area", "dirname": "area"}]
        topics_overview = [{"name": "T", "filename": "t.md", "description": "d"}]
        curate_areas = [{"name": "Area", "slug": "area", "starter_topics": ["T"]}]

        results = [
            ("agents_md", render_agents_md("R", domain_areas_agents)),
            ("agents_md_section", render_agents_md_section("R", domain_areas_agents)),
            ("claude_md", render_claude_md("R", domain_areas_index)),
            ("claude_md_section", render_claude_md_section("R", domain_areas_index)),
            ("curate_plan", render_curate_plan(curate_areas)),
            ("curation_plan_md", render_curation_plan_md(curate_areas)),
            ("hooks_json", render_hooks_json("/plugin", "/kb")),
            ("index_md", render_index_md("R", domain_areas_index)),
            ("overview_md", render_overview_md("A", "core", topics_overview)),
            ("topic_md", render_topic_md("T", "core")),
            ("topic_ref_md", render_topic_ref_md("T", "core")),
            ("proposal_md", render_proposal_md("T", "core", "alice", "reason")),
        ]
        for name, result in results:
            for lineno, line in enumerate(result.split("\n"), 1):
                with self.subTest(template=name, line=lineno):
                    self.assertEqual(line, line.rstrip(), f"Trailing whitespace in {name} line {lineno}: {line!r}")


if __name__ == "__main__":
    unittest.main()
