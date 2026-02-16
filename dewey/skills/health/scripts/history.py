"""Health score history tracking.

Persists timestamped snapshots of Tier 1 (and optionally Tier 2) health
summaries to ``.dewey/history/health-log.jsonl`` inside the KB root.

Only stdlib is used.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


_LOG_DIR = Path(".dewey") / "history"
_LOG_FILE = "health-log.jsonl"


def record_snapshot(
    knowledge_base_root: Path,
    tier1_summary: dict,
    tier2_summary: Optional[dict] = None,
    file_list: Optional[list] = None,
) -> Path:
    """Append a timestamped health snapshot to the log file.

    Parameters
    ----------
    knowledge_base_root:
        Root directory of the knowledge base (the log is written
        inside ``knowledge_base_root/.dewey/history/``).
    tier1_summary:
        Summary dict from ``run_health_check``.
    tier2_summary:
        Optional summary dict from ``run_tier2_prescreening``.
    file_list:
        Optional list of knowledge-base file paths (relative to knowledge_base_root)
        discovered during this check run.

    Returns
    -------
    Path
        Absolute path to the log file.
    """
    log_dir = knowledge_base_root / _LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / _LOG_FILE

    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "tier1": tier1_summary,
        "tier2": tier2_summary,
        "file_list": file_list or [],
    }

    with log_path.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")

    return log_path


def read_history(knowledge_base_root: Path, limit: int = 10) -> list[dict]:
    """Read the last *limit* health check snapshots.

    Returns snapshots in chronological order (oldest first).
    """
    log_file = knowledge_base_root / ".dewey" / "history" / "health-log.jsonl"
    if not log_file.exists():
        return []

    lines = log_file.read_text().strip().split("\n")
    if not lines or lines == [""]:
        return []

    entries = [json.loads(line) for line in lines]
    return entries[-limit:]
