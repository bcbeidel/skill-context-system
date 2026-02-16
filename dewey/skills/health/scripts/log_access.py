"""Hook-driven utilization logging.

Called by a Claude Code PostToolUse hook on the Read tool.
Checks if the file is a .md under the knowledge directory and
logs it via ``record_reference`` if so.

Only stdlib is used (plus sibling module imports).
"""

from __future__ import annotations

import sys
from pathlib import Path

# config.py lives in curate/scripts/ — add it to sys.path for cross-skill import.
_curate_scripts = str(Path(__file__).resolve().parent.parent.parent / "curate" / "scripts")
if _curate_scripts not in sys.path:
    sys.path.insert(0, _curate_scripts)

from config import read_knowledge_dir
from utilization import record_reference


def log_if_knowledge_file(knowledge_base_root: Path, file_path: str) -> bool:
    """Log a utilization event if *file_path* is a knowledge base topic.

    Parameters
    ----------
    knowledge_base_root:
        Root directory of the knowledge base.
    file_path:
        Absolute path to the file that was read.

    Returns
    -------
    bool
        ``True`` if the access was logged, ``False`` if skipped.
    """
    path = Path(file_path)

    if path.suffix != ".md":
        return False

    if not path.exists():
        return False

    knowledge_dir_name = read_knowledge_dir(knowledge_base_root)
    knowledge_dir = (knowledge_base_root / knowledge_dir_name).resolve()

    try:
        rel = path.resolve().relative_to(knowledge_dir)
    except ValueError:
        return False

    # Skip _proposals and other _ directories
    if any(part.startswith("_") for part in rel.parts):
        return False

    relative_path = f"{knowledge_dir_name}/{rel}"
    record_reference(knowledge_base_root, relative_path, context="hook")
    return True
