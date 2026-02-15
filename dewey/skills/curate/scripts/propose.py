"""Create a proposal file for a new or revised topic.

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
    render_proposal_md,
)


def create_proposal(
    kb_root: Path,
    topic_name: str,
    relevance: str,
    proposed_by: str,
    rationale: str,
) -> str:
    """Create a proposal file in docs/_proposals/.

    Parameters
    ----------
    kb_root:
        Root directory of the knowledge base.
    topic_name:
        Human-readable topic name (e.g. "Bid Strategies").
    relevance:
        One of core / supporting / peripheral.
    proposed_by:
        Who proposed the topic.
    rationale:
        Why this topic should be added.

    Returns
    -------
    str
        A summary string listing what was created.

    Raises
    ------
    FileNotFoundError
        If the _proposals/ directory does not exist.
    """
    proposals_dir = kb_root / "docs" / "_proposals"
    if not proposals_dir.is_dir():
        raise FileNotFoundError(
            f"Proposals directory does not exist: {proposals_dir}"
        )

    slug = _slugify(topic_name)
    proposal_path = proposals_dir / f"{slug}.md"

    if not proposal_path.exists():
        proposal_path.write_text(
            render_proposal_md(topic_name, relevance, proposed_by, rationale)
        )
        return f"Proposal created: docs/_proposals/{slug}.md"

    return f"Proposal '{topic_name}' already exists — nothing created."


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create a topic proposal.")
    parser.add_argument("--kb-root", required=True, help="KB root directory")
    parser.add_argument("--topic", required=True, help="Topic name")
    parser.add_argument("--relevance", required=True, help="core / supporting / peripheral")
    parser.add_argument("--proposed-by", required=True, help="Who proposed the topic")
    parser.add_argument("--rationale", required=True, help="Why this topic should be added")
    args = parser.parse_args()

    result = create_proposal(
        Path(args.kb_root), args.topic, args.relevance, args.proposed_by, args.rationale
    )
    print(result)
