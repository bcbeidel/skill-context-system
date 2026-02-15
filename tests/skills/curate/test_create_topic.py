"""Tests for skills.curate.scripts.create_topic — topic file creation."""

import shutil
import tempfile
import unittest
from pathlib import Path

from create_topic import create_topic


class TestCreateTopic(unittest.TestCase):
    """Tests for the create_topic function."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        # Minimal KB structure: knowledge/{area}/ and knowledge/_proposals/
        self.area = "campaign-management"
        (self.tmpdir / "docs" / self.area).mkdir(parents=True)
        (self.tmpdir / "docs" / "_proposals").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_creates_topic_file(self):
        """knowledge/{area}/{slug}.md exists after create_topic."""
        create_topic(self.tmpdir, self.area, "Bid Strategies", relevance="core")
        self.assertTrue(
            (self.tmpdir / "docs" / self.area / "bid-strategies.md").is_file()
        )

    def test_creates_reference_file(self):
        """knowledge/{area}/{slug}.ref.md exists after create_topic."""
        create_topic(self.tmpdir, self.area, "Bid Strategies", relevance="core")
        self.assertTrue(
            (self.tmpdir / "docs" / self.area / "bid-strategies.ref.md").is_file()
        )

    def test_topic_has_correct_depth(self):
        """Topic file contains 'depth: working'."""
        create_topic(self.tmpdir, self.area, "Bid Strategies", relevance="core")
        content = (
            self.tmpdir / "docs" / self.area / "bid-strategies.md"
        ).read_text()
        self.assertIn("depth: working", content)

    def test_ref_has_correct_depth(self):
        """Reference file contains 'depth: reference'."""
        create_topic(self.tmpdir, self.area, "Bid Strategies", relevance="core")
        content = (
            self.tmpdir / "docs" / self.area / "bid-strategies.ref.md"
        ).read_text()
        self.assertIn("depth: reference", content)

    def test_does_not_overwrite_existing(self):
        """Existing file is preserved and not overwritten."""
        topic_path = self.tmpdir / "docs" / self.area / "bid-strategies.md"
        topic_path.write_text("# Custom content\n")
        create_topic(self.tmpdir, self.area, "Bid Strategies", relevance="core")
        content = topic_path.read_text()
        self.assertEqual(content, "# Custom content\n")

    def test_raises_if_area_does_not_exist(self):
        """FileNotFoundError raised when domain area directory does not exist."""
        with self.assertRaises(FileNotFoundError):
            create_topic(self.tmpdir, "nonexistent-area", "Bid Strategies", relevance="core")

    def test_returns_summary(self):
        """Return value contains the filename."""
        result = create_topic(self.tmpdir, self.area, "Bid Strategies", relevance="core")
        self.assertIn("bid-strategies", result)


if __name__ == "__main__":
    unittest.main()
