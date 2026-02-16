"""Tests for skills.health.scripts.log_access — hook-driven utilization logging."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from log_access import log_if_knowledge_file


class TestLogIfKnowledgeFile(unittest.TestCase):
    """Tests for log_if_knowledge_file."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.knowledge_base_dir = self.tmpdir / "docs"
        self.knowledge_base_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_logs_file_under_knowledge_dir(self):
        """A file under the knowledge directory should be logged."""
        topic = self.knowledge_base_dir / "area" / "topic.md"
        topic.parent.mkdir(parents=True)
        topic.write_text("content")
        logged = log_if_knowledge_file(self.tmpdir, str(topic))
        self.assertTrue(logged)
        log = self.tmpdir / ".dewey" / "utilization" / "log.jsonl"
        self.assertTrue(log.exists())
        entry = json.loads(log.read_text().strip())
        self.assertIn("docs/area/topic.md", entry["file"])

    def test_ignores_file_outside_knowledge_dir(self):
        """A file outside the knowledge directory should not be logged."""
        other = self.tmpdir / "README.md"
        other.write_text("content")
        logged = log_if_knowledge_file(self.tmpdir, str(other))
        self.assertFalse(logged)
        log = self.tmpdir / ".dewey" / "utilization" / "log.jsonl"
        self.assertFalse(log.exists())

    def test_ignores_proposals(self):
        """Files under _proposals/ should not be logged."""
        proposal = self.knowledge_base_dir / "_proposals" / "draft.md"
        proposal.parent.mkdir(parents=True)
        proposal.write_text("content")
        logged = log_if_knowledge_file(self.tmpdir, str(proposal))
        self.assertFalse(logged)

    def test_ignores_non_md_files(self):
        """Non-markdown files should not be logged."""
        img = self.knowledge_base_dir / "area" / "diagram.png"
        img.parent.mkdir(parents=True)
        img.write_text("binary")
        logged = log_if_knowledge_file(self.tmpdir, str(img))
        self.assertFalse(logged)

    def test_context_is_hook(self):
        """Context should be 'hook' for auto-captured access."""
        topic = self.knowledge_base_dir / "area" / "topic.md"
        topic.parent.mkdir(parents=True)
        topic.write_text("content")
        log_if_knowledge_file(self.tmpdir, str(topic))
        log = self.tmpdir / ".dewey" / "utilization" / "log.jsonl"
        entry = json.loads(log.read_text().strip())
        self.assertEqual(entry["context"], "hook")

    def test_stores_relative_path(self):
        """Logged file path should be relative to knowledge_base_root, not absolute."""
        topic = self.knowledge_base_dir / "area" / "topic.md"
        topic.parent.mkdir(parents=True)
        topic.write_text("content")
        log_if_knowledge_file(self.tmpdir, str(topic))
        log = self.tmpdir / ".dewey" / "utilization" / "log.jsonl"
        entry = json.loads(log.read_text().strip())
        self.assertFalse(entry["file"].startswith("/"))

    def test_custom_knowledge_dir(self):
        """Should respect custom knowledge_dir from .dewey/config.json."""
        config_dir = self.tmpdir / ".dewey"
        config_dir.mkdir(parents=True)
        (config_dir / "config.json").write_text('{"knowledge_dir": "knowledge"}')
        knowledge = self.tmpdir / "knowledge"
        knowledge.mkdir()
        topic = knowledge / "area" / "topic.md"
        topic.parent.mkdir(parents=True)
        topic.write_text("content")
        logged = log_if_knowledge_file(self.tmpdir, str(topic))
        self.assertTrue(logged)

    def test_nonexistent_file_no_error(self):
        """A nonexistent file path should return False without error."""
        logged = log_if_knowledge_file(self.tmpdir, "/nonexistent/path.md")
        self.assertFalse(logged)



class TestHookEntryPoint(unittest.TestCase):
    """Tests for hook_log_access.py CLI entry point."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.knowledge_base_dir = self.tmpdir / "docs"
        self.knowledge_base_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run_hook(self, tool_input: dict) -> subprocess.CompletedProcess:
        """Run hook_log_access.py with tool input on stdin."""
        script = Path(__file__).resolve().parent.parent.parent.parent / \
            "dewey" / "skills" / "health" / "scripts" / "hook_log_access.py"
        return subprocess.run(
            ["python3", str(script), "--knowledge-base-root", str(self.tmpdir)],
            input=json.dumps(tool_input),
            capture_output=True,
            text=True,
            timeout=5,
        )

    def test_logs_knowledge_file_via_stdin(self):
        """Hook should log a knowledge file path received via stdin."""
        topic = self.knowledge_base_dir / "area" / "topic.md"
        topic.parent.mkdir(parents=True)
        topic.write_text("content")
        result = self._run_hook({"file_path": str(topic)})
        self.assertEqual(result.returncode, 0)
        log = self.tmpdir / ".dewey" / "utilization" / "log.jsonl"
        self.assertTrue(log.exists())

    def test_ignores_non_knowledge_file(self):
        """Hook should silently ignore non-knowledge files."""
        result = self._run_hook({"file_path": str(self.tmpdir / "README.md")})
        self.assertEqual(result.returncode, 0)
        log = self.tmpdir / ".dewey" / "utilization" / "log.jsonl"
        self.assertFalse(log.exists())

    def test_handles_missing_file_path(self):
        """Hook should handle missing file_path in input without error."""
        result = self._run_hook({"other_key": "value"})
        self.assertEqual(result.returncode, 0)

    def test_handles_invalid_json(self):
        """Hook should handle non-JSON stdin without crashing."""
        script = Path(__file__).resolve().parent.parent.parent.parent / \
            "dewey" / "skills" / "health" / "scripts" / "hook_log_access.py"
        result = subprocess.run(
            ["python3", str(script), "--knowledge-base-root", str(self.tmpdir)],
            input="not json",
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
