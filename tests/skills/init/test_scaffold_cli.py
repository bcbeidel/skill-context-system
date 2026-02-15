"""Tests for scaffold.py CLI interface.

These tests invoke scaffold.py as a subprocess to verify the argparse
entry point works correctly when the script is called from the command line.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "dewey"
    / "skills"
    / "init"
    / "scripts"
    / "scaffold.py"
)


class TestScaffoldCli(unittest.TestCase):
    """Tests for the ``python scaffold.py`` CLI."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_cli_creates_kb(self):
        """Running the CLI with --target and --role creates AGENTS.md."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--target",
                str(self.tmpdir),
                "--role",
                "Test Role",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue((self.tmpdir / "AGENTS.md").exists())

    def test_cli_with_areas(self):
        """Running the CLI with --areas creates domain area directories."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--target",
                str(self.tmpdir),
                "--role",
                "Test Role",
                "--areas",
                "Area One,Area Two",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(
            (self.tmpdir / "docs" / "area-one" / "overview.md").exists()
        )
        self.assertTrue(
            (self.tmpdir / "docs" / "area-two" / "overview.md").exists()
        )

    def test_cli_outputs_summary(self):
        """CLI stdout contains the word 'created'."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--target",
                str(self.tmpdir),
                "--role",
                "Test Role",
            ],
            capture_output=True,
            text=True,
        )
        self.assertIn("created", result.stdout.lower())

    def test_cli_creates_docs_index(self):
        """CLI creates docs/index.md."""
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--target",
                str(self.tmpdir),
                "--role",
                "Test Role",
            ],
            capture_output=True,
            text=True,
        )
        self.assertTrue((self.tmpdir / "docs" / "index.md").exists())

    def test_cli_creates_dewey_dirs(self):
        """CLI creates .dewey/ subdirectories."""
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--target",
                str(self.tmpdir),
                "--role",
                "Test Role",
            ],
            capture_output=True,
            text=True,
        )
        for subdir in ("health", "history", "utilization"):
            with self.subTest(subdir=subdir):
                self.assertTrue((self.tmpdir / ".dewey" / subdir).is_dir())

    def test_cli_missing_required_args(self):
        """CLI exits non-zero when required arguments are missing."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
