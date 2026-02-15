# Utilization Auto-Capture Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automatically log when Claude reads a knowledge base topic file, so utilization data feeds into Tier 3 health reviews without manual effort.

**Architecture:** A Claude Code `PostToolUse` hook on the `Read` tool fires a Python script that checks if the read file is under the knowledge directory. If yes, it appends to `.dewey/utilization/log.jsonl` using the existing `record_reference()` function. Zero friction for the agent — file reads work exactly as before.

**Tech Stack:** Python 3.9+ (stdlib only), Claude Code hooks (`PostToolUse`), existing `utilization.py`

**Design Doc:** `docs/plans/2026-02-15-history-utilization-design.md`

---

### Task 1: Create the log-access.py script

The hook needs a script that receives the file path, checks if it's under the knowledge directory, and logs it if so.

**Files:**
- Create: `dewey/skills/health/scripts/log_access.py`
- Create: `tests/skills/health/test_log_access.py`

**Step 1: Write the failing tests**

```python
"""Tests for skills.health.scripts.log_access — hook-driven utilization logging."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from log_access import log_if_knowledge_file


class TestLogIfKnowledgeFile(unittest.TestCase):
    """Tests for log_if_knowledge_file."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb_dir = self.tmpdir / "docs"
        self.kb_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_logs_file_under_knowledge_dir(self):
        """A file under the knowledge directory should be logged."""
        topic = self.kb_dir / "area" / "topic.md"
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
        proposal = self.kb_dir / "_proposals" / "draft.md"
        proposal.parent.mkdir(parents=True)
        proposal.write_text("content")
        logged = log_if_knowledge_file(self.tmpdir, str(proposal))
        self.assertFalse(logged)

    def test_ignores_non_md_files(self):
        """Non-markdown files should not be logged."""
        img = self.kb_dir / "area" / "diagram.png"
        img.parent.mkdir(parents=True)
        img.write_text("binary")
        logged = log_if_knowledge_file(self.tmpdir, str(img))
        self.assertFalse(logged)

    def test_context_is_hook(self):
        """Context should be 'hook' for auto-captured access."""
        topic = self.kb_dir / "area" / "topic.md"
        topic.parent.mkdir(parents=True)
        topic.write_text("content")
        log_if_knowledge_file(self.tmpdir, str(topic))
        log = self.tmpdir / ".dewey" / "utilization" / "log.jsonl"
        entry = json.loads(log.read_text().strip())
        self.assertEqual(entry["context"], "hook")

    def test_stores_relative_path(self):
        """Logged file path should be relative to kb_root, not absolute."""
        topic = self.kb_dir / "area" / "topic.md"
        topic.parent.mkdir(parents=True)
        topic.write_text("content")
        log_if_knowledge_file(self.tmpdir, str(topic))
        log = self.tmpdir / ".dewey" / "utilization" / "log.jsonl"
        entry = json.loads(log.read_text().strip())
        self.assertFalse(entry["file"].startswith("/"))

    def test_custom_knowledge_dir(self):
        """Should respect custom knowledge_dir from .dewey/config.json."""
        # Set up custom knowledge dir
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


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/skills/health/test_log_access.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

```python
"""Hook-driven utilization logging.

Called by a Claude Code PostToolUse hook on the Read tool.
Checks if the file is a .md under the knowledge directory and
logs it via ``record_reference`` if so.

Only stdlib is used (plus sibling module imports).
"""

from __future__ import annotations

import sys
from pathlib import Path

# config.py lives in init/scripts/
_init_scripts = str(Path(__file__).resolve().parent.parent.parent / "init" / "scripts")
if _init_scripts not in sys.path:
    sys.path.insert(0, _init_scripts)

from config import read_knowledge_dir
from utilization import record_reference


def log_if_knowledge_file(kb_root: Path, file_path: str) -> bool:
    """Log a utilization event if *file_path* is a knowledge base topic.

    Parameters
    ----------
    kb_root:
        Root directory of the knowledge base.
    file_path:
        Absolute path to the file that was read.

    Returns
    -------
    bool
        ``True`` if the access was logged, ``False`` if skipped.
    """
    path = Path(file_path)

    if not path.suffix == ".md":
        return False

    if not path.exists():
        return False

    knowledge_dir_name = read_knowledge_dir(kb_root)
    knowledge_dir = (kb_root / knowledge_dir_name).resolve()

    try:
        rel = path.resolve().relative_to(knowledge_dir)
    except ValueError:
        return False

    # Skip _proposals and other _ directories
    if any(part.startswith("_") for part in rel.parts):
        return False

    relative_path = f"{knowledge_dir_name}/{rel}"
    record_reference(kb_root, relative_path, context="hook")
    return True
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/skills/health/test_log_access.py -v`
Expected: 8 passed

**Step 5: Run full suite**

Run: `python3 -m pytest tests/ -v -k "not test_scaffold_sandbox"`
Expected: All pass, no regressions

**Step 6: Commit**

```bash
git add dewey/skills/health/scripts/log_access.py tests/skills/health/test_log_access.py
git commit -m "Add log_access.py for hook-driven utilization capture"
```

---

### Task 2: Create the hook entry-point script

The Claude Code hook runs a shell command. We need a thin CLI wrapper that resolves the KB root and calls `log_if_knowledge_file`. This script lives at the KB project level (not inside the plugin), because hooks are configured per-project.

The hook receives tool input as JSON on stdin. For the `Read` tool, this includes `{"file_path": "..."}`.

**Files:**
- Create: `dewey/skills/health/scripts/hook_log_access.py`
- Modify: `tests/skills/health/test_log_access.py`

**Step 1: Write the failing test**

Add to `test_log_access.py`:

```python
import subprocess


class TestHookEntryPoint(unittest.TestCase):
    """Tests for hook_log_access.py CLI entry point."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb_dir = self.tmpdir / "docs"
        self.kb_dir.mkdir()
        # Create AGENTS.md so the script can find KB root
        (self.tmpdir / "AGENTS.md").write_text("# Role\n")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run_hook(self, tool_input: dict) -> subprocess.CompletedProcess:
        """Run hook_log_access.py with tool input on stdin."""
        script = Path(__file__).resolve().parent.parent.parent.parent / \
            "dewey" / "skills" / "health" / "scripts" / "hook_log_access.py"
        return subprocess.run(
            ["python3", str(script), "--kb-root", str(self.tmpdir)],
            input=json.dumps(tool_input),
            capture_output=True,
            text=True,
            timeout=5,
        )

    def test_logs_knowledge_file_via_stdin(self):
        """Hook should log a knowledge file path received via stdin."""
        topic = self.kb_dir / "area" / "topic.md"
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
            ["python3", str(script), "--kb-root", str(self.tmpdir)],
            input="not json",
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0)
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/skills/health/test_log_access.py::TestHookEntryPoint -v`
Expected: FAIL with `FileNotFoundError` (script doesn't exist)

**Step 3: Write the entry-point script**

```python
#!/usr/bin/env python3
"""Claude Code PostToolUse hook entry point for utilization tracking.

Reads tool input JSON from stdin, extracts file_path, and logs
knowledge base file access via log_if_knowledge_file.

Usage in .claude/hooks.json:
    {
        "hooks": {
            "PostToolUse": [{
                "matcher": "Read",
                "hooks": [{
                    "type": "command",
                    "command": "python3 <plugin_root>/skills/health/scripts/hook_log_access.py --kb-root <kb_root>"
                }]
            }]
        }
    }

Exit code is always 0 — hook failures should never block the agent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure sibling scripts are importable
_scripts_dir = str(Path(__file__).resolve().parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

_init_scripts = str(Path(__file__).resolve().parent.parent.parent / "init" / "scripts")
if _init_scripts not in sys.path:
    sys.path.insert(0, _init_scripts)

from log_access import log_if_knowledge_file


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--kb-root", required=True)
    args = parser.parse_args()

    try:
        tool_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return

    file_path = tool_input.get("file_path")
    if not file_path:
        return

    log_if_knowledge_file(Path(args.kb_root), file_path)


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/skills/health/test_log_access.py -v`
Expected: 12 passed (8 + 4 new)

**Step 5: Run full suite**

Run: `python3 -m pytest tests/ -v -k "not test_scaffold_sandbox"`
Expected: All pass

**Step 6: Commit**

```bash
git add dewey/skills/health/scripts/hook_log_access.py tests/skills/health/test_log_access.py
git commit -m "Add hook entry point for PostToolUse Read utilization tracking"
```

---

### Task 3: Generate hooks.json during /dewey:init

When `/dewey:init` scaffolds a KB, it should also create `.claude/hooks.json` with the PostToolUse hook configured. This way every new KB automatically gets utilization tracking.

**Files:**
- Modify: `dewey/skills/init/scripts/scaffold.py`
- Modify: `dewey/skills/init/scripts/templates.py`
- Modify: `tests/skills/init/test_scaffold.py`
- Modify: `tests/skills/init/test_templates.py`

**Step 1: Write the failing test for the template**

Add to `test_templates.py`:

```python
class TestRenderHooksJson(unittest.TestCase):
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
```

**Step 2: Run to verify failure**

Run: `python3 -m pytest tests/skills/init/test_templates.py::TestRenderHooksJson -v`
Expected: FAIL with `ImportError`

**Step 3: Implement the template**

Add to `templates.py`:

```python
def render_hooks_json(plugin_root: str, kb_root: str) -> str:
    """Render .claude/hooks.json for utilization tracking."""
    script_path = f"{plugin_root}/skills/health/scripts/hook_log_access.py"
    hooks = {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "Read",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"python3 {script_path} --kb-root {kb_root}",
                        }
                    ],
                }
            ]
        }
    }
    return json.dumps(hooks, indent=2) + "\n"
```

**Step 4: Write the failing scaffold test**

Add to `test_scaffold.py`:

```python
def test_creates_hooks_json(self):
    """.claude/hooks.json is created with utilization hook."""
    # Run scaffold, then check .claude/hooks.json exists
    hooks_path = self.target / ".claude" / "hooks.json"
    self.assertTrue(hooks_path.exists())
    parsed = json.loads(hooks_path.read_text())
    self.assertIn("PostToolUse", parsed["hooks"])
```

**Step 5: Integrate into scaffold.py**

Add a call to `render_hooks_json` in the scaffold function, writing to `target_dir / ".claude" / "hooks.json"`. Only write if the file doesn't already exist (don't overwrite user customizations).

**Step 6: Run all tests**

Run: `python3 -m pytest tests/ -v -k "not test_scaffold_sandbox"`
Expected: All pass

**Step 7: Commit**

```bash
git add dewey/skills/init/scripts/scaffold.py dewey/skills/init/scripts/templates.py \
    tests/skills/init/test_scaffold.py tests/skills/init/test_templates.py
git commit -m "Generate .claude/hooks.json with utilization tracking during init"
```

---

### Task 4: Update documentation

**Files:**
- Modify: `dewey/skills/health/SKILL.md`
- Modify: `CLAUDE.md`

**Step 1: Update SKILL.md scripts_integration**

Add entry for `log_access.py` and `hook_log_access.py`:

```markdown
**log_access.py** -- Hook-driven utilization logging
- `log_if_knowledge_file(kb_root, file_path)` -- Logs access if file is a .md under the knowledge directory
- Filters out _proposals, non-.md files, and files outside the knowledge directory
- Called by `hook_log_access.py` (Claude Code PostToolUse hook entry point)

**hook_log_access.py** -- CLI entry point for Claude Code PostToolUse hook
- Reads tool input JSON from stdin, extracts file_path
- Calls `log_if_knowledge_file` to conditionally log the access
- Exit code always 0 (hook failures never block the agent)
```

**Step 2: Update CLAUDE.md**

Add a note about the hook under the Architecture section or Current Status.

**Step 3: Commit**

```bash
git add dewey/skills/health/SKILL.md CLAUDE.md
git commit -m "Document utilization auto-capture hook in SKILL.md and CLAUDE.md"
```

---

### Task 5: End-to-end validation

**Step 1: Run full test suite**

Run: `python3 -m pytest tests/ -v -k "not test_scaffold_sandbox"`
Expected: All pass

**Step 2: Manual validation**

Simulate the hook by piping Read tool input to the script:

```bash
echo '{"file_path": "/path/to/sandbox/docs/code-quality/naming-conventions.md"}' | \
    python3 dewey/skills/health/scripts/hook_log_access.py --kb-root sandbox
cat sandbox/.dewey/utilization/log.jsonl
```

Verify the access was logged with `context: "hook"`.

**Step 3: Verify read_utilization picks it up**

```bash
python3 -c "
import sys
sys.path.insert(0, 'dewey/skills/health/scripts')
sys.path.insert(0, 'dewey/skills/init/scripts')
from utilization import read_utilization
from pathlib import Path
print(read_utilization(Path('sandbox')))
"
```

**Step 4: Review commits**

```bash
git log --oneline -8
```
