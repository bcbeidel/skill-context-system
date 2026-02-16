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
    check_go_deeper_links,
    check_heading_hierarchy,
    check_inventory_regression,
    check_readability,
    check_ref_see_also,
    check_section_completeness,
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

    def test_hidden_dir_skipped(self):
        hidden = self.kb / ".dewey"
        hidden.mkdir()
        _write(hidden / "log.md", "# Log\n")
        issues = check_coverage(self.tmpdir)
        hidden_issues = [i for i in issues if ".dewey" in i.get("file", "")]
        self.assertEqual(hidden_issues, [])


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

    def test_structured_url_passes(self):
        """Source entries in 'url: https://...' format should be valid."""
        f = _write(
            self.tmpdir / "a.md",
            "---\nsources:\n  - url: https://example.com/doc\n---\n",
        )
        issues = check_source_urls(f)
        self.assertEqual(issues, [])


# ------------------------------------------------------------------
# check_inventory_regression
# ------------------------------------------------------------------
class TestCheckInventoryRegression(unittest.TestCase):
    """Tests for check_inventory_regression validator."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        history_dir = self.tmpdir / ".dewey" / "history"
        history_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write_snapshot(self, file_list):
        """Write a single history snapshot with the given file_list."""
        import json
        from datetime import datetime
        log_path = self.tmpdir / ".dewey" / "history" / "health-log.jsonl"
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "tier1": {"total_files": len(file_list), "fail_count": 0, "warn_count": 0, "pass_count": len(file_list)},
            "tier2": None,
            "file_list": file_list,
        }
        with log_path.open("a") as fh:
            fh.write(json.dumps(entry) + "\n")

    def test_no_history_returns_empty(self):
        """No prior snapshots means no regression to detect."""
        current = ["area/overview.md", "area/topic.md"]
        issues = check_inventory_regression(self.tmpdir, current)
        self.assertEqual(issues, [])

    def test_same_files_no_issues(self):
        """Identical file list produces no warnings."""
        files = ["area/overview.md", "area/topic.md"]
        self._write_snapshot(files)
        issues = check_inventory_regression(self.tmpdir, files)
        self.assertEqual(issues, [])

    def test_missing_file_warns(self):
        """File in last snapshot but not current produces a warning."""
        self._write_snapshot(["area/overview.md", "area/topic.md", "area/removed.md"])
        current = ["area/overview.md", "area/topic.md"]
        issues = check_inventory_regression(self.tmpdir, current)
        self.assertEqual(len(issues), 1)
        self.assertIn("removed.md", issues[0]["message"])
        self.assertEqual(issues[0]["severity"], "warn")

    def test_added_file_no_issue(self):
        """New file not in last snapshot is fine (not a regression)."""
        self._write_snapshot(["area/overview.md"])
        current = ["area/overview.md", "area/new-topic.md"]
        issues = check_inventory_regression(self.tmpdir, current)
        self.assertEqual(issues, [])

    def test_multiple_missing_files(self):
        """Multiple removals produce multiple warnings."""
        self._write_snapshot(["area/a.md", "area/b.md", "area/c.md"])
        current = ["area/a.md"]
        issues = check_inventory_regression(self.tmpdir, current)
        self.assertEqual(len(issues), 2)


# ------------------------------------------------------------------
# check_section_completeness
# ------------------------------------------------------------------
class TestCheckSectionCompleteness(unittest.TestCase):
    """Tests for check_section_completeness validator."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.today = date.today().isoformat()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _fm(self, depth: str) -> str:
        return (
            f"---\nsources:\n  - https://x.com\nlast_validated: {self.today}\n"
            f"relevance: core\ndepth: {depth}\n---\n"
        )

    def test_complete_working_passes(self):
        doc = (
            self._fm("working")
            + "\n# Topic\n\n"
            + "## Why This Matters\nText.\n\n"
            + "## In Practice\nText.\n\n"
            + "## Key Guidance\nText.\n\n"
            + "## Watch Out For\nText.\n\n"
            + "## Go Deeper\nText.\n"
        )
        f = _write(self.tmpdir / "a.md", doc)
        self.assertEqual(check_section_completeness(f), [])

    def test_missing_working_section_warns(self):
        doc = (
            self._fm("working")
            + "\n# Topic\n\n"
            + "## In Practice\nText.\n\n"
            + "## Key Guidance\nText.\n"
        )
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_section_completeness(f)
        missing_names = [i["message"] for i in issues]
        self.assertTrue(any("Why This Matters" in m for m in missing_names))
        self.assertTrue(any("Watch Out For" in m for m in missing_names))
        self.assertTrue(any("Go Deeper" in m for m in missing_names))

    def test_complete_overview_passes(self):
        doc = (
            self._fm("overview")
            + "\n# Overview\n\n"
            + "## What This Covers\nText.\n\n"
            + "## How It's Organized\nText.\n"
        )
        f = _write(self.tmpdir / "a.md", doc)
        self.assertEqual(check_section_completeness(f), [])

    def test_missing_overview_section_warns(self):
        doc = self._fm("overview") + "\n# Overview\n\n## What This Covers\nText.\n"
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_section_completeness(f)
        self.assertTrue(any("How It's Organized" in i["message"] for i in issues))

    def test_reference_with_body_passes(self):
        doc = self._fm("reference") + "\nSome reference content.\n"
        f = _write(self.tmpdir / "a.md", doc)
        self.assertEqual(check_section_completeness(f), [])

    def test_reference_empty_body_warns(self):
        doc = self._fm("reference") + "\n"
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_section_completeness(f)
        self.assertTrue(len(issues) > 0)
        self.assertTrue(any("no content" in i["message"].lower() for i in issues))

    def test_no_depth_skips(self):
        doc = "---\nsources:\n  - https://x.com\nrelevance: core\n---\n\n# Topic\n"
        f = _write(self.tmpdir / "a.md", doc)
        self.assertEqual(check_section_completeness(f), [])

    def test_severity_is_warn(self):
        doc = self._fm("working") + "\n# Topic\n"
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_section_completeness(f)
        self.assertTrue(all(i["severity"] == "warn" for i in issues))


# ------------------------------------------------------------------
# check_heading_hierarchy
# ------------------------------------------------------------------
class TestCheckHeadingHierarchy(unittest.TestCase):
    """Tests for check_heading_hierarchy validator."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_valid_hierarchy_passes(self):
        doc = "---\ndepth: working\n---\n\n# Title\n\n## Section\n\n### Sub\n"
        f = _write(self.tmpdir / "a.md", doc)
        self.assertEqual(check_heading_hierarchy(f), [])

    def test_multiple_h1_warns(self):
        doc = "---\ndepth: working\n---\n\n# Title One\n\n# Title Two\n"
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_heading_hierarchy(f)
        self.assertTrue(any("Multiple H1" in i["message"] for i in issues))

    def test_no_h1_warns(self):
        doc = "---\ndepth: working\n---\n\n## Just a Section\n"
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_heading_hierarchy(f)
        self.assertTrue(any("No H1" in i["message"] for i in issues))

    def test_skipped_level_warns(self):
        doc = "---\ndepth: working\n---\n\n# Title\n\n### Skipped H2\n"
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_heading_hierarchy(f)
        self.assertTrue(any("Skipped" in i["message"] for i in issues))

    def test_code_blocks_excluded(self):
        doc = (
            "---\ndepth: working\n---\n\n# Title\n\n## Section\n\n"
            "```markdown\n# This is inside a code block\n"
            "### Also inside\n```\n"
        )
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_heading_hierarchy(f)
        self.assertEqual(issues, [])

    def test_severity_is_warn(self):
        doc = "---\ndepth: working\n---\n\n# One\n\n# Two\n\n### Skip\n"
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_heading_hierarchy(f)
        self.assertTrue(all(i["severity"] == "warn" for i in issues))

    def test_no_frontmatter_still_works(self):
        doc = "# Title\n\n## Section\n"
        f = _write(self.tmpdir / "a.md", doc)
        self.assertEqual(check_heading_hierarchy(f), [])


# ------------------------------------------------------------------
# check_go_deeper_links
# ------------------------------------------------------------------
class TestCheckGoDeeperLinks(unittest.TestCase):
    """Tests for check_go_deeper_links validator."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.today = date.today().isoformat()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _working_fm(self) -> str:
        return (
            f"---\nsources:\n  - https://x.com\nlast_validated: {self.today}\n"
            f"relevance: core\ndepth: working\n---\n"
        )

    def test_valid_go_deeper_passes(self):
        doc = (
            self._working_fm()
            + "\n# Topic\n\n## Go Deeper\n"
            + "- [Ref](bidding.ref.md)\n"
            + "- [External](https://example.com/docs)\n"
        )
        f = _write(self.tmpdir / "bidding.md", doc)
        self.assertEqual(check_go_deeper_links(f), [])

    def test_missing_ref_link_warns(self):
        doc = (
            self._working_fm()
            + "\n# Topic\n\n## Go Deeper\n"
            + "- [External](https://example.com/docs)\n"
        )
        f = _write(self.tmpdir / "bidding.md", doc)
        issues = check_go_deeper_links(f)
        self.assertTrue(any("bidding.ref.md" in i["message"] for i in issues))

    def test_missing_external_link_warns(self):
        doc = (
            self._working_fm()
            + "\n# Topic\n\n## Go Deeper\n"
            + "- [Ref](bidding.ref.md)\n"
        )
        f = _write(self.tmpdir / "bidding.md", doc)
        issues = check_go_deeper_links(f)
        self.assertTrue(any("external link" in i["message"].lower() for i in issues))

    def test_both_missing_warns_twice(self):
        doc = self._working_fm() + "\n# Topic\n\n## Go Deeper\nSome text.\n"
        f = _write(self.tmpdir / "bidding.md", doc)
        issues = check_go_deeper_links(f)
        self.assertEqual(len(issues), 2)

    def test_non_working_skips(self):
        doc = (
            f"---\nsources:\n  - https://x.com\nlast_validated: {self.today}\n"
            f"relevance: core\ndepth: overview\n---\n"
            + "\n# Topic\n\n## Go Deeper\nNo links.\n"
        )
        f = _write(self.tmpdir / "overview.md", doc)
        self.assertEqual(check_go_deeper_links(f), [])

    def test_missing_section_skips(self):
        doc = self._working_fm() + "\n# Topic\n\n## In Practice\nText.\n"
        f = _write(self.tmpdir / "bidding.md", doc)
        self.assertEqual(check_go_deeper_links(f), [])

    def test_ref_file_skips(self):
        doc = self._working_fm() + "\n# Topic\n\n## Go Deeper\nNo links.\n"
        f = _write(self.tmpdir / "bidding.ref.md", doc)
        self.assertEqual(check_go_deeper_links(f), [])


# ------------------------------------------------------------------
# check_ref_see_also
# ------------------------------------------------------------------
class TestCheckRefSeeAlso(unittest.TestCase):
    """Tests for check_ref_see_also validator."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.today = date.today().isoformat()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _ref_fm(self) -> str:
        return (
            f"---\nsources:\n  - https://x.com\nlast_validated: {self.today}\n"
            f"relevance: core\ndepth: reference\n---\n"
        )

    def test_valid_see_also_passes(self):
        doc = self._ref_fm() + "\n# Reference\n\nContent.\n\n**See also:** [Bidding](bidding.md)\n"
        f = _write(self.tmpdir / "bidding.ref.md", doc)
        self.assertEqual(check_ref_see_also(f), [])

    def test_missing_see_also_warns(self):
        doc = self._ref_fm() + "\n# Reference\n\nContent only, no see also.\n"
        f = _write(self.tmpdir / "bidding.ref.md", doc)
        issues = check_ref_see_also(f)
        self.assertTrue(any("See also" in i["message"] for i in issues))

    def test_wrong_companion_warns(self):
        doc = self._ref_fm() + "\n# Reference\n\n**See also:** [Other](other.md)\n"
        f = _write(self.tmpdir / "bidding.ref.md", doc)
        issues = check_ref_see_also(f)
        self.assertTrue(any("bidding.md" in i["message"] for i in issues))

    def test_case_insensitive_see_also(self):
        doc = self._ref_fm() + "\n# Reference\n\n**SEE ALSO:** [Bidding](bidding.md)\n"
        f = _write(self.tmpdir / "bidding.ref.md", doc)
        self.assertEqual(check_ref_see_also(f), [])

    def test_non_ref_file_skips(self):
        doc = self._ref_fm() + "\n# Topic\n\nNo see also.\n"
        f = _write(self.tmpdir / "bidding.md", doc)
        self.assertEqual(check_ref_see_also(f), [])

    def test_hyphenated_filename(self):
        doc = self._ref_fm() + "\n# Reference\n\n**See also:** [Ad Serving](ad-serving.md)\n"
        f = _write(self.tmpdir / "ad-serving.ref.md", doc)
        self.assertEqual(check_ref_see_also(f), [])


# ------------------------------------------------------------------
# check_readability
# ------------------------------------------------------------------
class TestCheckReadability(unittest.TestCase):
    """Tests for check_readability validator."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.today = date.today().isoformat()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _fm(self, depth: str) -> str:
        return (
            f"---\nsources:\n  - https://x.com\nlast_validated: {self.today}\n"
            f"relevance: core\ndepth: {depth}\n---\n"
        )

    def _prose(self, grade_target: str = "normal") -> str:
        """Generate prose at roughly the target readability level."""
        if grade_target == "simple":
            # Very short, simple sentences — should score below grade 8
            return (
                "The cat sat on a mat. The dog ran in the sun. "
                "It was a big day. The boy ate his food. "
                "She ran to the door. He sat on the bed. "
                "They went to the park. We had a good time. "
                "The sun was up high. The bird sang a song. "
            )
        elif grade_target == "complex":
            # Long sentences with multisyllabic words
            return (
                "The implementation of sophisticated interdisciplinary methodologies "
                "necessitates comprehensive understanding of organizational infrastructure. "
                "Psychopharmacological interventions demonstrate considerable efficacy "
                "in ameliorating neuropsychiatric symptomatology. "
                "The conceptualization of multidimensional representational frameworks "
                "requires extraordinary phenomenological investigation. "
                "Telecommunications infrastructure modernization presupposes "
                "substantial capital expenditure authorization. "
            )
        else:
            # Mid-range prose — should land in the 10-14 range
            return (
                "Understanding how systems work requires careful observation and analysis. "
                "The primary challenge in modern software development is managing complexity. "
                "Teams that communicate effectively tend to produce better outcomes over time. "
                "Documentation serves as a bridge between current knowledge and future reference. "
                "Clear writing reflects clear thinking and benefits everyone involved. "
            )

    def test_working_normal_prose_no_issues(self):
        doc = self._fm("working") + "\n# Topic\n\n" + self._prose("normal")
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_readability(f)
        self.assertEqual(issues, [])

    def test_overview_normal_prose_no_issues(self):
        # Overview bounds are 8-14; balance sentence length (~15 words) and
        # moderate vocabulary to target FK grade ~10
        prose = (
            "The system processes incoming requests and routes them to the nearest available worker node. "
            "Each worker keeps a local cache that stores the most frequently accessed data on disk. "
            "When a request fails on the first attempt, the system retries it with a different worker. "
            "Health checks run every thirty seconds so that problems are detected before users notice them. "
        )
        doc = self._fm("overview") + "\n# Overview\n\n" + prose
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_readability(f)
        self.assertEqual(issues, [])

    def test_reference_skipped(self):
        doc = self._fm("reference") + "\n# Reference\n\n" + self._prose("complex")
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_readability(f)
        self.assertEqual(issues, [])

    def test_complex_prose_warns(self):
        doc = self._fm("working") + "\n# Topic\n\n" + self._prose("complex")
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_readability(f)
        self.assertTrue(len(issues) > 0)
        self.assertTrue(any("complex" in i["message"].lower() for i in issues))

    def test_simple_prose_warns_for_overview(self):
        doc = self._fm("overview") + "\n# Overview\n\n" + self._prose("simple")
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_readability(f)
        self.assertTrue(len(issues) > 0)
        self.assertTrue(any("simplistic" in i["message"].lower() for i in issues))

    def test_too_few_sentences_skipped(self):
        doc = self._fm("working") + "\n# Topic\n\nJust one sentence here.\n"
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_readability(f)
        self.assertEqual(issues, [])

    def test_code_blocks_excluded(self):
        code_block = "```python\nfor i in range(100):\n    print(i)\n```\n"
        doc = self._fm("working") + "\n# Topic\n\n" + code_block + self._prose("normal")
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_readability(f)
        self.assertEqual(issues, [])

    def test_markdown_formatting_stripped(self):
        formatted = (
            "Understanding **how systems** work requires [careful](https://x.com) observation. "
            "The *primary* challenge in `modern` software development is managing complexity. "
            "Teams that communicate effectively tend to produce better outcomes over time. "
            "Documentation serves as a bridge between current knowledge and future reference. "
            "Clear writing reflects clear thinking and benefits everyone involved. "
        )
        doc = self._fm("working") + "\n# Topic\n\n" + formatted
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_readability(f)
        self.assertEqual(issues, [])

    def test_severity_is_warn(self):
        doc = self._fm("working") + "\n# Topic\n\n" + self._prose("complex")
        f = _write(self.tmpdir / "a.md", doc)
        issues = check_readability(f)
        self.assertTrue(all(i["severity"] == "warn" for i in issues))


if __name__ == "__main__":
    unittest.main()
