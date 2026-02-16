"""Topic reference tracking.

Records when KB files are referenced to ``.dewey/utilization/log.jsonl``
inside the KB root.  This data feeds into utilization-aware health scoring
and curation recommendations.

Only stdlib is used.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


_LOG_DIR = Path(".dewey") / "utilization"
_LOG_FILE = "log.jsonl"


def record_reference(
    knowledge_base_root: Path,
    file_path: str,
    context: str = "user",
) -> Path:
    """Append a reference entry to the utilization log.

    Parameters
    ----------
    knowledge_base_root:
        Root directory of the knowledge base (the log is written
        inside ``knowledge_base_root/.dewey/utilization/``).
    file_path:
        Relative path (from *knowledge_base_root*) of the referenced file,
        e.g. ``"topic/foo.md"``.
    context:
        Free-form label describing *how* the file was referenced.
        Defaults to ``"user"``.

    Returns
    -------
    Path
        Absolute path to the log file.
    """
    log_dir = knowledge_base_root / _LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / _LOG_FILE

    entry = {
        "file": file_path,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "context": context,
    }

    with log_path.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")

    return log_path


def read_utilization(knowledge_base_root: Path) -> dict[str, dict]:
    """Read utilization stats per file.

    Returns mapping of file path to
    {"count": int, "first_referenced": str, "last_referenced": str}.
    """
    log_file = knowledge_base_root / ".dewey" / "utilization" / "log.jsonl"
    if not log_file.exists():
        return {}

    lines = log_file.read_text().strip().split("\n")
    if not lines or lines == [""]:
        return {}

    stats: dict[str, dict] = {}
    for line in lines:
        entry = json.loads(line)
        fp = entry["file"]
        ts = entry["timestamp"]

        if fp not in stats:
            stats[fp] = {
                "count": 0,
                "first_referenced": ts,
                "last_referenced": ts,
            }

        stats[fp]["count"] += 1
        if ts < stats[fp]["first_referenced"]:
            stats[fp]["first_referenced"] = ts
        if ts > stats[fp]["last_referenced"]:
            stats[fp]["last_referenced"] = ts

    return stats
