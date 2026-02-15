"""Tests for skills.health.scripts.validators — Tier 1 deterministic validators."""

import shutil
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from validators import (
    check_coverage,
    check_cross_references,
    check_freshness,
    check_frontmatter,
    check_section_ordering,
    check_size_bounds,
    check_source_urls,
    parse_frontmatter,
)


def _write(path: Path, text: str) -> Path:
    """Helper — write *text* to *path*, creating parents as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


VALID_FRONTMATTER = """\
---
sources:
  - https://example.com/doc
last_validated: {today}
relevance: core
depth: working
---
"""

VALID_WORKING_DOC = """\
---
sources:
  - https://example.com/doc
last_validated: {today}
relevance: core
depth: working
---

# Topic

## In Practice
Concrete guidance here.

## Key Guidance
Abstract principles here.
"""


class TestParseFrontmatter(unittest.TestCase):
    """Tests for the parse_frontmatter helper."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_parses_simple_kv(self):
        f = _write(
            self.tmpdir / "a.md",
            "---\nrelevance: core\ndepth: working\n---\nBody.\n",
        )
        fm = parse_frontmatter(f)
        self.assertEqual(fm.get("relevance"), "core")
        self.assertEqual(fm.get("depth"), "working")

    def test_parses_date(self):
        f = _write(
            self.tmpdir / "a.md",
            "---\nlast_validated: 2026-02-14\n---\n",
        )
        fm = parse_frontmatter(f)
        self.assertEqual(fm.get("last_validated"), "2026-02-14")

    def test_parses_sources_list(self):
        f = _write(
            self.tmpdir / "a.md",
            "---\nsources:\n  - https://a.com\n  - https://b.com\n---\n",
        )
        fm = parse_frontmatter(f)
        self.assertIsInstance(fm.get("sources"), list)
        self.assertEqual(len(fm["sources"]), 2)

    def test_returns_empty_when_no_frontmatter(self):
        f = _write(self.tmpdir / "a.md", "# Just a heading\nNo frontmatter.\n")
        fm = parse_frontmatter(f)
        self.assertEqual(fm, {})


# ------------------------------------------------------------------
# check_frontmatter
# ------------------------------------------------------------------
class TestCheckFrontmatter(unittest.TestCase):
    """Tests for check_frontmatter validator."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.today = date.today().isoformat()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_valid_frontmatter_passes(self):
        f = _write(
            self.tmpdir / "a.md",
            VALID_FRONTMATTER.format(today=self.today),
        )
        issues = check_frontmatter(f)
        self.assertEqual(issues, [])

    def test_missing_sources_fails(self):
        f = _write(
            self.tmpdir / "a.md",
            "---\nlast_validated: 2026-02-14\nrelevance: core\ndepth: working\n---\n",
        )
        issues = check_frontmatter(f)
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("sources" in m for m in msgs))
        self.assertTrue(any(i["severity"] == "fail" for i in issues))

    def test_invalid_depth_fails(self):
        f = _write(
            self.tmpdir / "a.md",
            "---\nsources:\n  - https://x.com\nlast_validated: 2026-02-14\n"
            "relevance: core\ndepth: bogus\n---\n",
        )
        issues = check_frontmatter(f)
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("depth" in m.lower() for m in msgs))

    def test_missing_last_validated_fails(self):
        f = _write(
            self.tmpdir / "a.md",
            "---\nsources:\n  - https://x.com\nrelevance: core\ndepth: working\n---\n",
        )
        issues = check_frontmatter(f)
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("last_validated" in m for m in msgs))


# ------------------------------------------------------------------
# check_section_ordering
# ------------------------------------------------------------------
class TestCheckSectionOrdering(unittest.TestCase):
    """Tests for check_section_ordering validator."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.today = date.today().isoformat()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_correct_order_passes(self):
        f = _write(
            self.tmpdir / "a.md",
            VALID_WORKING_DOC.format(today=self.today),
        )
        issues = check_section_ordering(f)
        self.assertEqual(issues, [])

    def test_wrong_order_fails(self):
        doc = (
            f"---\nsources:\n  - https://x.com\nlast_validated: {self.today}\n"
            "relevance: core\ndepth: working\n---\n\n"
            "## Key Guidance\nAbstract.\n\n## In Practice\nConcrete.\n"
        )
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_section_ordering(f)
        self.assertTrue(len(issues) > 0)
        self.assertTrue(any("order" in i["message"].lower() or "before" in i["message"].lower() for i in issues))

    def test_only_checks_working_depth(self):
        doc = (
            f"---\nsources:\n  - https://x.com\nlast_validated: {self.today}\n"
            "relevance: core\ndepth: overview\n---\n\n"
            "## Key Guidance\nAbstract.\n\n## In Practice\nConcrete.\n"
        )
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_section_ordering(f)
        self.assertEqual(issues, [])


# ------------------------------------------------------------------
# check_cross_references
# ------------------------------------------------------------------
class TestCheckCrossReferences(unittest.TestCase):
    """Tests for check_cross_references validator."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_valid_link_passes(self):
        area = self.kb / "area"
        area.mkdir()
        _write(area / "target.md", "# Target\n")
        f = _write(area / "source.md", "See [target](target.md) for details.\n")
        issues = check_cross_references(f, self.tmpdir)
        self.assertEqual(issues, [])

    def test_broken_link_fails(self):
        area = self.kb / "area"
        area.mkdir()
        f = _write(area / "source.md", "See [missing](no-such-file.md) for details.\n")
        issues = check_cross_references(f, self.tmpdir)
        self.assertTrue(len(issues) > 0)
        self.assertTrue(any("no-such-file.md" in i["message"] for i in issues))

    def test_external_url_ignored(self):
        area = self.kb / "area"
        area.mkdir()
        f = _write(area / "source.md", "See [Google](https://google.com) for details.\n")
        issues = check_cross_references(f, self.tmpdir)
        self.assertEqual(issues, [])


# ------------------------------------------------------------------
# check_size_bounds
# ------------------------------------------------------------------
class TestCheckSizeBounds(unittest.TestCase):
    """Tests for check_size_bounds validator."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.today = date.today().isoformat()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_working_within_bounds_passes(self):
        lines = "\n".join([f"Line {i}" for i in range(50)])
        doc = (
            f"---\nsources:\n  - https://x.com\nlast_validated: {self.today}\n"
            f"relevance: core\ndepth: working\n---\n{lines}\n"
        )
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_size_bounds(f)
        self.assertEqual(issues, [])

    def test_overview_too_large_warns(self):
        lines = "\n".join([f"Line {i}" for i in range(200)])
        doc = (
            f"---\nsources:\n  - https://x.com\nlast_validated: {self.today}\n"
            f"relevance: core\ndepth: overview\n---\n{lines}\n"
        )
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_size_bounds(f)
        self.assertTrue(len(issues) > 0)
        self.assertTrue(any(i["severity"] == "warn" for i in issues))

    def test_working_too_small_warns(self):
        # A working-depth file needs at least 10 lines; this one has only 8.
        doc = (
            f"---\nsources:\n  - https://x.com\nlast_validated: {self.today}\n"
            "relevance: core\ndepth: working\n---\nShort.\n"
        )
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_size_bounds(f)
        self.assertTrue(len(issues) > 0)


# ------------------------------------------------------------------
# check_coverage
# ------------------------------------------------------------------
class TestCheckCoverage(unittest.TestCase):
    """Tests for check_coverage validator."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_area_without_overview_fails(self):
        area = self.kb / "some-area"
        area.mkdir()
        _write(area / "topic.md", "# Topic\n")
        issues = check_coverage(self.tmpdir)
        self.assertTrue(len(issues) > 0)
        self.assertTrue(any("overview.md" in i["message"] for i in issues))
        self.assertTrue(any(i["severity"] == "fail" for i in issues))

    def test_area_with_overview_passes(self):
        area = self.kb / "some-area"
        area.mkdir()
        _write(area / "overview.md", "# Overview\n")
        issues = check_coverage(self.tmpdir)
        overview_issues = [i for i in issues if "overview.md" in i["message"]]
        self.assertEqual(overview_issues, [])

    def test_topic_without_ref_warns(self):
        area = self.kb / "area"
        area.mkdir()
        _write(area / "overview.md", "# Overview\n")
        _write(area / "bidding.md", "# Bidding\n")
        issues = check_coverage(self.tmpdir)
        ref_issues = [i for i in issues if ".ref.md" in i["message"]]
        self.assertTrue(len(ref_issues) > 0)
        self.assertTrue(any(i["severity"] == "warn" for i in ref_issues))

    def test_proposals_dir_skipped(self):
        proposals = self.kb / "_proposals"
        proposals.mkdir()
        _write(proposals / "draft.md", "# Draft\n")
        issues = check_coverage(self.tmpdir)
        proposal_issues = [i for i in issues if "_proposals" in i.get("file", "")]
        self.assertEqual(proposal_issues, [])


# ------------------------------------------------------------------
# check_freshness
# ------------------------------------------------------------------
class TestCheckFreshness(unittest.TestCase):
    """Tests for check_freshness validator."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_recent_date_passes(self):
        today = date.today().isoformat()
        f = _write(
            self.tmpdir / "a.md",
            f"---\nlast_validated: {today}\n---\nBody.\n",
        )
        issues = check_freshness(f)
        self.assertEqual(issues, [])

    def test_old_date_warns(self):
        old = (date.today() - timedelta(days=120)).isoformat()
        f = _write(
            self.tmpdir / "a.md",
            f"---\nlast_validated: {old}\n---\nBody.\n",
        )
        issues = check_freshness(f)
        self.assertTrue(len(issues) > 0)
        self.assertTrue(any(i["severity"] == "warn" for i in issues))

    def test_custom_max_age(self):
        old = (date.today() - timedelta(days=10)).isoformat()
        f = _write(
            self.tmpdir / "a.md",
            f"---\nlast_validated: {old}\n---\nBody.\n",
        )
        issues = check_freshness(f, max_age_days=5)
        self.assertTrue(len(issues) > 0)


# ------------------------------------------------------------------
# check_source_urls
# ------------------------------------------------------------------
class TestCheckSourceUrls(unittest.TestCase):
    """Tests for check_source_urls validator."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_valid_url_passes(self):
        f = _write(
            self.tmpdir / "a.md",
            "---\nsources:\n  - https://example.com/doc\n---\n",
        )
        issues = check_source_urls(f)
        self.assertEqual(issues, [])

    def test_malformed_url_fails(self):
        f = _write(
            self.tmpdir / "a.md",
            "---\nsources:\n  - not-a-url\n---\n",
        )
        issues = check_source_urls(f)
        self.assertTrue(len(issues) > 0)
        self.assertTrue(any(i["severity"] == "fail" for i in issues))

    def test_placeholder_url_skipped(self):
        f = _write(
            self.tmpdir / "a.md",
            "---\nsources:\n  - <!-- add primary source URL -->\n---\n",
        )
        issues = check_source_urls(f)
        self.assertEqual(issues, [])

    def test_http_url_passes(self):
        f = _write(
            self.tmpdir / "a.md",
            "---\nsources:\n  - http://legacy.example.com/doc\n---\n",
        )
        issues = check_source_urls(f)
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
