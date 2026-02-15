"""Tests for skills.curate.scripts.propose — proposal file creation."""

import shutil
import tempfile
import unittest
from pathlib import Path

from propose import create_proposal


class TestCreateProposal(unittest.TestCase):
    """Tests for the create_proposal function."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "docs" / "_proposals").mkdir(parents=True)
        (self.tmpdir / "docs" / "campaign-management").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_creates_proposal_file(self):
        """_proposals/{slug}.md exists after create_proposal."""
        create_proposal(
            self.tmpdir, "Bid Strategies", relevance="core",
            proposed_by="alice", rationale="Needed for optimization",
        )
        self.assertTrue(
            (self.tmpdir / "docs" / "_proposals" / "bid-strategies.md").is_file()
        )

    def test_proposal_has_status(self):
        """Proposal contains 'status: proposal' and 'proposed_by: alice'."""
        create_proposal(
            self.tmpdir, "Bid Strategies", relevance="core",
            proposed_by="alice", rationale="Needed for optimization",
        )
        content = (
            self.tmpdir / "docs" / "_proposals" / "bid-strategies.md"
        ).read_text()
        self.assertIn("status: proposal", content)
        self.assertIn("proposed_by: alice", content)


if __name__ == "__main__":
    unittest.main()
