"""Create a proposal file for a new or revised topic.

Only stdlib is used.  Existing files are never overwritten.
"""

from __future__ import annotations

from pathlib import Path

from config import read_knowledge_dir
from templates import (
    _slugify,
    render_proposal_md,
)


def create_proposal(
    knowledge_base_root: Path,
    topic_name: str,
    relevance: str,
    proposed_by: str,
    rationale: str,
) -> str:
    """Create a proposal file in docs/_proposals/.

    Parameters
    ----------
    knowledge_base_root:
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
    knowledge_dir = read_knowledge_dir(knowledge_base_root)
    proposals_dir = knowledge_base_root / knowledge_dir / "_proposals"
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
        return f"Proposal created: {knowledge_dir}/_proposals/{slug}.md"

    return f"Proposal '{topic_name}' already exists — nothing created."


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create a topic proposal.")
    parser.add_argument("--knowledge-base-root", required=True, help="Knowledge-base root directory")
    parser.add_argument("--topic", required=True, help="Topic name")
    parser.add_argument("--relevance", required=True, help="core / supporting / peripheral")
    parser.add_argument("--proposed-by", required=True, help="Who proposed the topic")
    parser.add_argument("--rationale", required=True, help="Why this topic should be added")
    args = parser.parse_args()

    result = create_proposal(
        Path(args.knowledge_base_root), args.topic, args.relevance, args.proposed_by, args.rationale
    )
    print(result)
