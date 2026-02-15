"""Tests for skills.curate.scripts.promote — proposal promotion."""

import shutil
import tempfile
import unittest
from pathlib import Path

from promote import promote_proposal


class TestPromoteProposal(unittest.TestCase):
    """Tests for the promote_proposal function."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "docs" / "_proposals").mkdir(parents=True)
        (self.tmpdir / "docs" / "campaign-management").mkdir(parents=True)

        # Create a sample proposal file with proposal-specific frontmatter
        self.proposal_content = (
            "---\n"
            "sources:\n"
            "  - url: https://example.com\n"
            "    title: Example\n"
            "last_validated: 2026-02-14\n"
            'relevance: "core"\n'
            "depth: working\n"
            "status: proposal\n"
            "proposed_by: alice\n"
            "rationale: Needed for optimization\n"
            "---\n"
            "\n"
            "# Bid Strategies\n"
            "\n"
            "## Why This Matters\n"
            "Content here.\n"
        )
        (self.tmpdir / "docs" / "_proposals" / "bid-strategies.md").write_text(
            self.proposal_content
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_moves_proposal_to_area(self):
        """File exists in target area after promotion."""
        promote_proposal(self.tmpdir, "bid-strategies", "campaign-management")
        self.assertTrue(
            (self.tmpdir / "docs" / "campaign-management" / "bid-strategies.md").is_file()
        )

    def test_removes_proposal_status_from_frontmatter(self):
        """Promoted file has no status, proposed_by, or rationale fields."""
        promote_proposal(self.tmpdir, "bid-strategies", "campaign-management")
        content = (
            self.tmpdir / "docs" / "campaign-management" / "bid-strategies.md"
        ).read_text()
        self.assertNotIn("status:", content)
        self.assertNotIn("proposed_by:", content)
        self.assertNotIn("rationale:", content)

    def test_removes_original_proposal(self):
        """Original proposal file is deleted after promotion."""
        promote_proposal(self.tmpdir, "bid-strategies", "campaign-management")
        self.assertFalse(
            (self.tmpdir / "docs" / "_proposals" / "bid-strategies.md").exists()
        )

    def test_raises_if_proposal_not_found(self):
        """FileNotFoundError raised when proposal does not exist."""
        with self.assertRaises(FileNotFoundError):
            promote_proposal(self.tmpdir, "nonexistent", "campaign-management")

    def test_raises_if_target_area_not_found(self):
        """FileNotFoundError raised when target area does not exist."""
        with self.assertRaises(FileNotFoundError):
            promote_proposal(self.tmpdir, "bid-strategies", "nonexistent-area")


if __name__ == "__main__":
    unittest.main()
