"""Tests for skills.init.scripts.templates — KB content template rendering."""

import datetime
import unittest
from unittest.mock import patch

from skills.init.scripts.templates import (
    _slugify,
    render_agents_md,
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


@patch("skills.init.scripts.templates.date")
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
        self.assertIn("**API Design**", result)
        self.assertIn("RESTful API patterns", result)
        self.assertIn("**Unit Testing**", result)

    def test_contains_how_to_use_section(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Senior Python Developer", self._domain_areas())
        self.assertIn("## How To Use This Knowledge", result)
        self.assertIn("knowledge/", result)

    def test_contains_what_you_have_access_to_section(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Senior Python Developer", self._domain_areas())
        self.assertIn("## What You Have Access To", result)

    def test_empty_domain_areas(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_agents_md("Generalist", [])
        self.assertIn("# Role: Generalist", result)
        self.assertIn("## What You Have Access To", result)


@patch("skills.init.scripts.templates.date")
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

    def test_empty_domain_areas(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_index_md("Generalist", [])
        self.assertIn("# Knowledge Base", result)


@patch("skills.init.scripts.templates.date")
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

    def test_contains_area_heading(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Backend Development", "core", self._topics())
        self.assertIn("# Backend Development", result)

    def test_contains_relevance(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Backend Development", "core", self._topics())
        self.assertIn("core", result)

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

    def test_empty_topics(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_overview_md("Empty Area", "peripheral", [])
        self.assertIn("# Empty Area", result)


@patch("skills.init.scripts.templates.date")
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
        self.assertIn("relevance: core", result)

    def test_frontmatter_has_depth_working(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_md("API Design", "core")
        self.assertIn("depth: working", result)

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

    def test_contains_html_comment_placeholders(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_md("API Design", "core")
        self.assertGreater(result.count("<!--"), 0)
        self.assertGreater(result.count("-->"), 0)

    def test_uses_today_date(self, mock_date):
        mock_date.today.return_value = datetime.date(2026, 6, 30)
        result = render_topic_md("Testing", "supporting")
        self.assertIn("last_validated: 2026-06-30", result)


@patch("skills.init.scripts.templates.date")
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
        self.assertIn("relevance: core", result)

    def test_frontmatter_has_last_validated(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        result = render_topic_ref_md("API Design", "core")
        self.assertIn("last_validated: 2026-01-15", result)

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


@patch("skills.init.scripts.templates.date")
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
        self.assertIn("relevance: supporting", result)

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


class TestReturnTypes(unittest.TestCase):
    """All render functions must return strings."""

    @patch("skills.init.scripts.templates.date")
    def test_all_render_functions_return_str(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        domain_areas_agents = [
            {"name": "Area", "topics": [{"name": "T", "description": "d"}]}
        ]
        domain_areas_index = [{"name": "Area", "dirname": "area"}]
        topics_overview = [{"name": "T", "filename": "t.md", "description": "d"}]

        cases = [
            render_agents_md("R", domain_areas_agents),
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

    @patch("skills.init.scripts.templates.date")
    def test_no_trailing_whitespace(self, mock_date):
        mock_date.today.return_value = FIXED_DATE
        domain_areas_agents = [
            {"name": "Area", "topics": [{"name": "T", "description": "d"}]}
        ]
        domain_areas_index = [{"name": "Area", "dirname": "area"}]
        topics_overview = [{"name": "T", "filename": "t.md", "description": "d"}]

        results = [
            ("agents_md", render_agents_md("R", domain_areas_agents)),
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
