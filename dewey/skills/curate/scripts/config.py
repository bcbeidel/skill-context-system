"""Read Dewey configuration from .dewey/config.json."""

import json
from pathlib import Path


def read_knowledge_dir(knowledge_base_root: Path) -> str:
    """Return the knowledge directory name from config, defaulting to 'docs'."""
    config_path = knowledge_base_root / ".dewey" / "config.json"
    if config_path.exists():
        try:
            value = json.loads(config_path.read_text()).get("knowledge_dir", "docs")
            return value.strip("/") or "docs"
        except (json.JSONDecodeError, OSError):
            return "docs"
    return "docs"


def write_config(knowledge_base_root: Path, knowledge_dir: str = "docs") -> Path:
    """Write Dewey configuration to .dewey/config.json."""
    knowledge_dir = knowledge_dir.strip("/") or "docs"
    config_path = knowledge_base_root / ".dewey" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps({"knowledge_dir": knowledge_dir}, indent=2) + "\n")
    return config_path
