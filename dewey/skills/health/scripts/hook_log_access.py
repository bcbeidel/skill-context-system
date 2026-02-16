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
                    "command": "python3 <plugin_root>/skills/health/scripts/hook_log_access.py --knowledge-base-root <knowledge_base_root>"
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

_curate_scripts = str(Path(__file__).resolve().parent.parent.parent / "curate" / "scripts")
if _curate_scripts not in sys.path:
    sys.path.insert(0, _curate_scripts)

from log_access import log_if_knowledge_file


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--knowledge-base-root", required=True)
    args = parser.parse_args()

    try:
        tool_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return

    file_path = tool_input.get("file_path")
    if not file_path:
        return

    log_if_knowledge_file(Path(args.knowledge_base_root), file_path)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
