"""Tests for cross-file consistency validators."""

import shutil
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from cross_validators import (
    check_curation_plan_sync,
    check_duplicate_content,
    check_link_graph,
    check_manifest_sync,
    check_naming_conventions,
    check_proposal_integrity,
)
from templates import MARKER_BEGIN, MARKER_END


def _write(path: Path, text: str) -> Path:
    """Helper — write *text* to *path*, creating parents as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _valid_fm(depth: str = "working") -> str:
    today = date.today().isoformat()
    return (
        f"---\nsources:\n  - https://example.com\nlast_validated: {today}\n"
        f"relevance: core\ndepth: {depth}\n---\n"
    )


def _working_body(stem: str = "topic") -> str:
    return (
        f"# Topic\n\n"
        f"## Why This Matters\nImportant.\n\n"
        f"## In Practice\nConcrete.\n\n"
        f"## Key Guidance\nGuidance.\n\n"
        f"## Watch Out For\nPitfalls.\n\n"
        f"## Go Deeper\n"
        f"- [{stem} Reference]({stem}.ref.md) -- quick-lookup\n"
        f"- [External](https://example.com)\n"
    )


def _agents_md(areas: list[dict], knowledge_dir: str = "docs") -> str:
    """Build an AGENTS.md with managed section containing area headings and topic tables."""
    lines = [
        "# Role: Test Role",
        "",
        "## Who You Are",
        "Test persona.",
        "",
        MARKER_BEGIN,
        "## What You Have Access To",
    ]
    for area in areas:
        lines.append(f"### {area['name']}")
        lines.append("")
        lines.append("| Topic | Description |")
        lines.append("|-------|-------------|")
        for topic in area.get("topics", []):
            path = topic.get("path", f"{knowledge_dir}/{area['slug']}/{topic['file']}")
            lines.append(f"| [{topic['name']}]({path}) | Description |")
        lines.append("")
    lines.append(MARKER_END)
    return "\n".join(lines) + "\n"


def _claude_md(areas: list[dict], knowledge_dir: str = "docs") -> str:
    """Build a CLAUDE.md with managed section containing Domain Areas table."""
    lines = [
        "# Project",
        "",
        MARKER_BEGIN,
        "## Knowledge Base",
        "",
        "### Domain Areas",
        "",
        "| Area | Path | Overview |",
        "|------|------|----------|",
    ]
    for area in areas:
        slug = area["slug"]
        lines.append(
            f"| {area['name']} "
            f"| `{knowledge_dir}/{slug}/` "
            f"| [overview.md]({knowledge_dir}/{slug}/overview.md) |"
        )
    lines.append(MARKER_END)
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------
# TestCheckManifestSync
# ------------------------------------------------------------------
class TestCheckManifestSync(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_synced_agents_and_claude_no_issues(self):
        """Perfectly synced AGENTS.md + CLAUDE.md -> no issues."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area One\n")
        _write(area / "topic.md", _valid_fm("working") + "\n" + _working_body())

        _write(self.tmpdir / "AGENTS.md", _agents_md([{
            "name": "Area One", "slug": "area-one",
            "topics": [{"name": "Topic", "file": "topic.md"}],
        }]))
        _write(self.tmpdir / "CLAUDE.md", _claude_md([{
            "name": "Area One", "slug": "area-one",
        }]))

        issues = check_manifest_sync(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])

    def test_area_on_disk_not_in_agents(self):
        """Area dir on disk not listed in AGENTS.md -> warn."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")

        _write(self.tmpdir / "AGENTS.md", _agents_md([]))  # empty manifest

        issues = check_manifest_sync(self.tmpdir, knowledge_dir_name="docs")
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("area-one" in m and "AGENTS.md" in m for m in msgs))

    def test_topic_on_disk_not_in_agents(self):
        """Topic file on disk not in AGENTS.md table -> warn."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")
        _write(area / "topic.md", _valid_fm("working") + "\n# Topic\n")

        _write(self.tmpdir / "AGENTS.md", _agents_md([{
            "name": "Area One", "slug": "area-one",
            "topics": [],  # no topics listed
        }]))

        issues = check_manifest_sync(self.tmpdir, knowledge_dir_name="docs")
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("topic.md" in m and "AGENTS.md" in m for m in msgs))

    def test_agents_entry_references_missing_file(self):
        """AGENTS.md entry pointing to nonexistent file -> warn."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")

        _write(self.tmpdir / "AGENTS.md", _agents_md([{
            "name": "Area One", "slug": "area-one",
            "topics": [{"name": "Ghost", "file": "ghost.md"}],
        }]))

        issues = check_manifest_sync(self.tmpdir, knowledge_dir_name="docs")
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("nonexistent" in m and "ghost.md" in m for m in msgs))

    def test_area_on_disk_not_in_claude(self):
        """Area dir on disk not listed in CLAUDE.md -> warn."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")

        _write(self.tmpdir / "CLAUDE.md", _claude_md([]))  # empty table

        issues = check_manifest_sync(self.tmpdir, knowledge_dir_name="docs")
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("area-one" in m and "CLAUDE.md" in m for m in msgs))

    def test_claude_entry_references_missing_dir(self):
        """CLAUDE.md entry referencing nonexistent directory -> warn."""
        _write(self.tmpdir / "CLAUDE.md", _claude_md([{
            "name": "Ghost Area", "slug": "ghost-area",
        }]))

        issues = check_manifest_sync(self.tmpdir, knowledge_dir_name="docs")
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("nonexistent" in m.lower() and "ghost-area" in m for m in msgs))

    def test_missing_agents_skips(self):
        """No AGENTS.md -> skip (empty list)."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")
        # No AGENTS.md, no CLAUDE.md
        issues = check_manifest_sync(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])

    def test_no_markers_in_agents_skips(self):
        """AGENTS.md without markers -> skip."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")

        _write(self.tmpdir / "AGENTS.md", "# Role\n\nNo markers here.\n")

        issues = check_manifest_sync(self.tmpdir, knowledge_dir_name="docs")
        # Should not warn about AGENTS.md sync since there are no markers
        agents_issues = [i for i in issues if "AGENTS.md" in i.get("message", "")]
        self.assertEqual(agents_issues, [])


# ------------------------------------------------------------------
# TestCheckCurationPlanSync
# ------------------------------------------------------------------
class TestCheckCurationPlanSync(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write_plan(self, content: str) -> Path:
        return _write(self.tmpdir / ".dewey" / "curation-plan.md", content)

    def test_synced_plan_no_issues(self):
        """Checked items with files + unchecked without files -> no issues."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")
        _write(area / "topic-a.md", _valid_fm("working") + "\n# Topic A\n")

        self._write_plan(
            "---\nlast_updated: 2026-02-15\n---\n\n"
            "# Curation Plan\n\n"
            "## area-one\n\n"
            "- [x] Topic A -- core\n"
            "- [ ] Topic B -- core\n"
        )

        issues = check_curation_plan_sync(self.tmpdir, knowledge_dir_name="docs")
        # Only topic-a is on disk, and it's checked. Topic B is unchecked and not on disk.
        # topic-a is in the plan, so no "not in plan" warning.
        self.assertEqual(issues, [])

    def test_checked_item_missing_file(self):
        """[x] item without matching file -> warn."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")

        self._write_plan(
            "---\nlast_updated: 2026-02-15\n---\n\n"
            "# Curation Plan\n\n"
            "## area-one\n\n"
            "- [x] Ghost Topic -- core\n"
        )

        issues = check_curation_plan_sync(self.tmpdir, knowledge_dir_name="docs")
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("checked" in m.lower() and "not found" in m.lower() for m in msgs))

    def test_unchecked_item_with_file(self):
        """[ ] item where matching file exists -> warn."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")
        _write(area / "existing-topic.md", _valid_fm("working") + "\n# Topic\n")

        self._write_plan(
            "---\nlast_updated: 2026-02-15\n---\n\n"
            "# Curation Plan\n\n"
            "## area-one\n\n"
            "- [ ] Existing Topic -- core\n"
        )

        issues = check_curation_plan_sync(self.tmpdir, knowledge_dir_name="docs")
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("should be checked" in m.lower() for m in msgs))

    def test_topic_not_in_plan(self):
        """Topic file on disk not mentioned in plan -> warn."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")
        _write(area / "surprise.md", _valid_fm("working") + "\n# Surprise\n")

        self._write_plan(
            "---\nlast_updated: 2026-02-15\n---\n\n"
            "# Curation Plan\n\n"
            "## area-one\n\n"
            "- [x] Other Topic -- core\n"
        )

        issues = check_curation_plan_sync(self.tmpdir, knowledge_dir_name="docs")
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("not in curation plan" in m.lower() for m in msgs))

    def test_no_plan_file_skips(self):
        """No plan file -> skip."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")

        issues = check_curation_plan_sync(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])

    def test_empty_plan_skips(self):
        """Plan file with no items -> skip."""
        self._write_plan(
            "---\nlast_updated: 2026-02-15\n---\n\n"
            "# Curation Plan\n\n"
            "No items yet.\n"
        )

        issues = check_curation_plan_sync(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])

    def test_slugify_matching(self):
        """'Bid Strategies' matches bid-strategies.md via slugify."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")
        _write(area / "bid-strategies.md", _valid_fm("working") + "\n# Bid Strategies\n")

        self._write_plan(
            "---\nlast_updated: 2026-02-15\n---\n\n"
            "# Curation Plan\n\n"
            "## area-one\n\n"
            "- [x] Bid Strategies -- core\n"
        )

        issues = check_curation_plan_sync(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])


# ------------------------------------------------------------------
# TestCheckProposalIntegrity
# ------------------------------------------------------------------
class TestCheckProposalIntegrity(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _proposal_fm(self, **overrides) -> str:
        today = date.today().isoformat()
        fields = {
            "sources": ["https://example.com"],
            "last_validated": today,
            "relevance": "core",
            "depth": "working",
            "status": "proposal",
            "proposed_by": "claude",
            "rationale": "Fills a gap in coverage",
        }
        fields.update(overrides)
        lines = ["---"]
        for k, v in fields.items():
            if isinstance(v, list):
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{k}: {v}")
        lines.append("---")
        return "\n".join(lines) + "\n"

    def _proposal_body(self) -> str:
        return (
            "\n# Proposal\n\n"
            "## Why This Matters\nImportant.\n\n"
            "## In Practice\nConcrete.\n\n"
            "## Key Guidance\nGuidance.\n\n"
            "## Watch Out For\nPitfalls.\n\n"
            "## Go Deeper\nLinks.\n"
        )

    def test_valid_proposal_no_issues(self):
        """Well-formed proposal -> no issues."""
        _write(
            self.kb / "_proposals" / "new-topic.md",
            self._proposal_fm() + self._proposal_body(),
        )
        issues = check_proposal_integrity(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])

    def test_missing_status(self):
        """Proposal without status: proposal -> warn."""
        fm = self._proposal_fm()
        fm = fm.replace("status: proposal\n", "")
        _write(self.kb / "_proposals" / "draft.md", fm + self._proposal_body())
        issues = check_proposal_integrity(self.tmpdir, knowledge_dir_name="docs")
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("status" in m.lower() for m in msgs))

    def test_missing_proposed_by(self):
        """Proposal without proposed_by -> warn."""
        fm = self._proposal_fm()
        fm = fm.replace("proposed_by: claude\n", "")
        _write(self.kb / "_proposals" / "draft.md", fm + self._proposal_body())
        issues = check_proposal_integrity(self.tmpdir, knowledge_dir_name="docs")
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("proposed_by" in m for m in msgs))

    def test_missing_rationale(self):
        """Proposal without rationale -> warn."""
        fm = self._proposal_fm()
        fm = fm.replace("rationale: Fills a gap in coverage\n", "")
        _write(self.kb / "_proposals" / "draft.md", fm + self._proposal_body())
        issues = check_proposal_integrity(self.tmpdir, knowledge_dir_name="docs")
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("rationale" in m for m in msgs))

    def test_stale_proposal(self):
        """Proposal with old last_validated -> warn."""
        old_date = (date.today() - timedelta(days=90)).isoformat()
        _write(
            self.kb / "_proposals" / "old.md",
            self._proposal_fm(last_validated=old_date) + self._proposal_body(),
        )
        issues = check_proposal_integrity(self.tmpdir, knowledge_dir_name="docs")
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("stale" in m.lower() for m in msgs))

    def test_no_proposals_dir_skips(self):
        """No _proposals/ directory -> skip."""
        issues = check_proposal_integrity(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])

    def test_missing_working_sections(self):
        """Proposal missing working sections -> warn."""
        _write(
            self.kb / "_proposals" / "bare.md",
            self._proposal_fm() + "\n# Proposal\n\nJust a title.\n",
        )
        issues = check_proposal_integrity(self.tmpdir, knowledge_dir_name="docs")
        section_issues = [i for i in issues if "missing required section" in i["message"].lower()]
        # Should warn for all 5 working sections
        self.assertEqual(len(section_issues), 5)


# ------------------------------------------------------------------
# TestCheckLinkGraph
# ------------------------------------------------------------------
class TestCheckLinkGraph(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_fully_linked_kb_no_issues(self):
        """All files linked from overview -> no orphans, no missing from overview."""
        area = self.kb / "area-one"
        area.mkdir()
        overview = (
            _valid_fm("overview")
            + "\n# Area\n\n"
            + "## What This Covers\nScope.\n\n"
            + "## How It's Organized\n\n"
            + "| Topic | Description |\n"
            + "|-------|-------------|\n"
            + "| [Topic](topic.md) | A topic |\n"
        )
        _write(area / "overview.md", overview)
        topic = (
            _valid_fm("working")
            + "\n# Topic\n\n"
            + "## Go Deeper\n- [Ref](topic.ref.md)\n"
        )
        _write(area / "topic.md", topic)
        ref = _valid_fm("reference") + "\n# Ref\n\n**See also:** [Topic](topic.md)\n"
        _write(area / "topic.ref.md", ref)

        issues = check_link_graph(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])

    def test_orphaned_file(self):
        """File not linked from any other file -> warn."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n\n## How It's Organized\nNothing.\n")
        _write(area / "orphan.md", _valid_fm("working") + "\n# Orphan\n")

        issues = check_link_graph(self.tmpdir, knowledge_dir_name="docs")
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("orphan" in m.lower() for m in msgs))

    def test_overview_not_flagged_as_orphan(self):
        """overview.md is an entry point — should not be flagged as orphan."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")

        issues = check_link_graph(self.tmpdir, knowledge_dir_name="docs")
        orphan_issues = [i for i in issues if "orphan" in i["message"].lower()]
        overview_orphans = [i for i in orphan_issues if "overview.md" in i["file"]]
        self.assertEqual(overview_orphans, [])

    def test_index_not_flagged_as_orphan(self):
        """index.md is excluded from discovery — not validated at all."""
        _write(self.kb / "index.md", "# Index\n")
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")

        issues = check_link_graph(self.tmpdir, knowledge_dir_name="docs")
        index_issues = [i for i in issues if "index.md" in i.get("file", "")]
        self.assertEqual(index_issues, [])

    def test_topic_not_in_overview(self):
        """Topic file not listed in overview's How It's Organized -> warn."""
        area = self.kb / "area-one"
        area.mkdir()
        overview = (
            _valid_fm("overview")
            + "\n# Area\n\n"
            + "## What This Covers\nScope.\n\n"
            + "## How It's Organized\n\n"
            + "| Topic | Description |\n"
            + "|-------|-------------|\n"
            + "| [Topic A](topic-a.md) | First |\n"
        )
        _write(area / "overview.md", overview)
        _write(area / "topic-a.md", _valid_fm("working") + "\n# A\n")
        _write(area / "topic-b.md", _valid_fm("working") + "\n# B\n")

        issues = check_link_graph(self.tmpdir, knowledge_dir_name="docs")
        msgs = [i["message"] for i in issues]
        self.assertTrue(any("topic-b.md" in m and "How It" in m for m in msgs))

    def test_empty_kb_no_issues(self):
        """Empty knowledge directory -> no issues."""
        issues = check_link_graph(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])


# ------------------------------------------------------------------
# TestCheckDuplicateContent
# ------------------------------------------------------------------
class TestCheckDuplicateContent(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_no_duplicates_no_issues(self):
        """Unique content across files -> no issues."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n\n"
               + "This is a unique paragraph about the overview topic with enough words to count.\n")
        _write(area / "topic.md", _valid_fm("working") + "\n# Topic\n\n"
               + "This is a completely different paragraph about a separate working topic here.\n")
        issues = check_duplicate_content(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])

    def test_exact_duplicate_paragraph_warns(self):
        """Same paragraph in two files -> warn."""
        area = self.kb / "area-one"
        area.mkdir()
        shared_para = "This is a substantial paragraph that appears in both files and should be detected as a duplicate by the validator."
        _write(area / "overview.md", _valid_fm("overview") + f"\n# Area\n\n{shared_para}\n")
        _write(area / "topic.md", _valid_fm("working") + f"\n# Topic\n\n{shared_para}\n")
        issues = check_duplicate_content(self.tmpdir, knowledge_dir_name="docs")
        dup_issues = [i for i in issues if "duplicate paragraph" in i["message"].lower()]
        self.assertTrue(len(dup_issues) > 0)

    def test_companion_pair_no_similarity_warning(self):
        """Working/ref companion pair -> skip similarity check."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n\nUnique overview content here with enough words.\n")
        shared = (
            "This topic covers important aspects of the domain area including "
            "detailed guidance on implementation patterns and best practices "
            "for working with the system effectively in production."
        )
        _write(area / "topic.md", _valid_fm("working") + f"\n# Topic\n\n{shared}\n")
        _write(area / "topic.ref.md", _valid_fm("reference") + f"\n# Ref\n\n{shared}\n")
        issues = check_duplicate_content(self.tmpdir, knowledge_dir_name="docs")
        sim_issues = [i for i in issues if "similarity" in i["message"].lower()
                      and "topic.md" in i["message"] and "topic.ref.md" in i["message"]]
        self.assertEqual(sim_issues, [])

    def test_high_similarity_non_companion_warns(self):
        """High Jaccard similarity between non-companion files -> warn."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n\nOverview content standalone.\n")
        # Two very similar non-companion files
        content = (
            "The comprehensive implementation methodology requires understanding "
            "of fundamental architectural principles and systematic application "
            "of established engineering practices across the development lifecycle. "
            "Performance optimization strategies involve careful analysis of "
            "bottlenecks and systematic improvement of critical code paths."
        )
        _write(area / "topic-a.md", _valid_fm("working") + f"\n# Topic A\n\n{content}\n")
        _write(area / "topic-b.md", _valid_fm("working") + f"\n# Topic B\n\n{content}\n")
        issues = check_duplicate_content(self.tmpdir, knowledge_dir_name="docs")
        sim_issues = [i for i in issues if "similarity" in i["message"].lower()]
        self.assertTrue(len(sim_issues) > 0)

    def test_short_paragraphs_ignored(self):
        """Paragraphs under 40 chars are not checked for duplicates."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n\nShort.\n")
        _write(area / "topic.md", _valid_fm("working") + "\n# Topic\n\nShort.\n")
        issues = check_duplicate_content(self.tmpdir, knowledge_dir_name="docs")
        dup_issues = [i for i in issues if "duplicate paragraph" in i["message"].lower()]
        self.assertEqual(dup_issues, [])

    def test_code_blocks_excluded(self):
        """Code blocks should be stripped before comparison."""
        area = self.kb / "area-one"
        area.mkdir()
        code = "```python\nfor i in range(100):\n    print(i)\n```\n"
        overview_text = (
            "The architecture overview covers system design principles and high-level "
            "component interaction patterns used in production deployment environments. "
            "This section explains monitoring strategies and alert configuration rules."
        )
        topic_text = (
            "Database migration workflows require careful version control and staged "
            "rollout procedures to prevent data loss during schema transformation. "
            "Backup verification steps must be completed before any production change."
        )
        _write(area / "overview.md", _valid_fm("overview") + f"\n# Area\n\n{code}\n{overview_text}\n")
        _write(area / "topic.md", _valid_fm("working") + f"\n# Topic\n\n{code}\n{topic_text}\n")
        issues = check_duplicate_content(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])

    def test_empty_kb_no_issues(self):
        """Empty knowledge directory -> no issues."""
        issues = check_duplicate_content(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])


# ------------------------------------------------------------------
# TestCheckNamingConventions
# ------------------------------------------------------------------
class TestCheckNamingConventions(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_well_named_files_no_issues(self):
        """Properly slugified names -> no issues."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")
        _write(area / "my-topic.md", _valid_fm("working") + "\n# Topic\n")
        _write(area / "my-topic.ref.md", _valid_fm("reference") + "\n# Ref\n")
        issues = check_naming_conventions(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])

    def test_uppercase_directory_warns(self):
        """Uppercase directory name -> warn."""
        area = self.kb / "Area-One"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")
        issues = check_naming_conventions(self.tmpdir, knowledge_dir_name="docs")
        dir_issues = [i for i in issues if "directory" in i["message"].lower()]
        self.assertTrue(len(dir_issues) > 0)

    def test_underscore_in_filename_warns(self):
        """Underscore in filename -> warn."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")
        _write(area / "my_topic.md", _valid_fm("working") + "\n# Topic\n")
        issues = check_naming_conventions(self.tmpdir, knowledge_dir_name="docs")
        file_issues = [i for i in issues if "my_topic" in i["message"]]
        self.assertTrue(len(file_issues) > 0)

    def test_overview_and_index_exempt(self):
        """overview.md and index.md are exempt from slug check."""
        area = self.kb / "area-one"
        area.mkdir()
        _write(area / "overview.md", _valid_fm("overview") + "\n# Area\n")
        _write(area / "index.md", "# Index\n")
        issues = check_naming_conventions(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])

    def test_no_knowledge_dir_no_issues(self):
        """Missing knowledge directory -> no issues."""
        empty = Path(tempfile.mkdtemp())
        try:
            issues = check_naming_conventions(empty, knowledge_dir_name="docs")
            self.assertEqual(issues, [])
        finally:
            shutil.rmtree(empty)


if __name__ == "__main__":
    unittest.main()
