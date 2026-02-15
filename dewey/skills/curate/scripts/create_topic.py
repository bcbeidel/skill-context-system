"""Create a new topic file (working + reference) inside a domain area.

Only stdlib is used.  Existing files are never overwritten.
"""

from __future__ import annotations

import sys
from pathlib import Path

# templates.py lives in init/scripts/ — add it to sys.path for cross-skill import.
_init_scripts = str(Path(__file__).resolve().parent.parent.parent / "init" / "scripts")
if _init_scripts not in sys.path:
    sys.path.insert(0, _init_scripts)

from templates import (
    _slugify,
    render_topic_md,
    render_topic_ref_md,
)


def create_topic(kb_root: Path, area: str, topic_name: str, relevance: str) -> str:
    """Create a working-knowledge topic and its reference companion.

    Parameters
    ----------
    kb_root:
        Root directory of the knowledge base.
    area:
        Domain area directory name (e.g. "campaign-management").
    topic_name:
        Human-readable topic name (e.g. "Bid Strategies").
    relevance:
        One of core / supporting / peripheral.

    Returns
    -------
    str
        A summary string listing what was created.

    Raises
    ------
    FileNotFoundError
        If the domain area directory does not exist.
    """
    area_dir = kb_root / "docs" / area
    if not area_dir.is_dir():
        raise FileNotFoundError(f"Domain area directory does not exist: {area_dir}")

    slug = _slugify(topic_name)
    created: list[str] = []

    # Working-knowledge topic file
    topic_path = area_dir / f"{slug}.md"
    if not topic_path.exists():
        topic_path.write_text(render_topic_md(topic_name, relevance))
        created.append(str(topic_path.relative_to(kb_root)))

    # Expert-reference companion
    ref_path = area_dir / f"{slug}.ref.md"
    if not ref_path.exists():
        ref_path.write_text(render_topic_ref_md(topic_name, relevance))
        created.append(str(ref_path.relative_to(kb_root)))

    # Summary
    if created:
        summary_lines = [f"Topic '{topic_name}' created:"]
        for item in created:
            summary_lines.append(f"  - {item}")
        return "\n".join(summary_lines)

    return f"Topic '{topic_name}' already exists — nothing created."


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create a topic in a domain area.")
    parser.add_argument("--kb-root", required=True, help="KB root directory")
    parser.add_argument("--area", required=True, help="Domain area directory name")
    parser.add_argument("--topic", required=True, help="Topic name")
    parser.add_argument("--relevance", required=True, help="core / supporting / peripheral")
    args = parser.parse_args()

    result = create_topic(Path(args.kb_root), args.area, args.topic, args.relevance)
    print(result)
