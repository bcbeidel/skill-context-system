"""Promote a proposal file from _proposals/ to a domain area.

Strips proposal-specific frontmatter (status, proposed_by, rationale)
before writing to the target area.  Only stdlib is used.
"""

from __future__ import annotations

import re
from pathlib import Path


def _strip_proposal_fields(content: str) -> str:
    """Remove proposal-specific frontmatter fields from file content.

    Parses lines and, when inside the ``---`` frontmatter block, skips
    lines whose field name is ``status``, ``proposed_by``, or ``rationale``.
    """
    lines = content.splitlines(keepends=True)
    result: list[str] = []
    in_frontmatter = False
    fence_count = 0

    for line in lines:
        stripped = line.strip()

        if stripped == "---":
            fence_count += 1
            in_frontmatter = fence_count == 1
            result.append(line)
            continue

        if in_frontmatter:
            match = re.match(r"^(\w+):", line)
            if match and match.group(1) in ("status", "proposed_by", "rationale"):
                continue

        result.append(line)

    return "".join(result)


def promote_proposal(kb_root: Path, proposal_name: str, target_area: str) -> str:
    """Move a proposal into a domain area directory.

    Parameters
    ----------
    kb_root:
        Root directory of the knowledge base.
    proposal_name:
        Slug name of the proposal (without .md extension).
    target_area:
        Domain area directory name (e.g. "campaign-management").

    Returns
    -------
    str
        A summary string describing what was done.

    Raises
    ------
    FileNotFoundError
        If the proposal file or target area directory does not exist.
    """
    proposal_path = kb_root / "docs" / "_proposals" / f"{proposal_name}.md"
    if not proposal_path.is_file():
        raise FileNotFoundError(f"Proposal not found: {proposal_path}")

    target_dir = kb_root / "docs" / target_area
    if not target_dir.is_dir():
        raise FileNotFoundError(
            f"Target area directory does not exist: {target_dir}"
        )

    # Read, strip proposal fields, write to target
    content = proposal_path.read_text()
    cleaned = _strip_proposal_fields(content)
    target_path = target_dir / f"{proposal_name}.md"
    target_path.write_text(cleaned)

    # Delete original proposal
    proposal_path.unlink()

    return (
        f"Promoted '{proposal_name}' from _proposals/ to {target_area}/: "
        f"docs/{target_area}/{proposal_name}.md"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Promote a proposal to a domain area.")
    parser.add_argument("--kb-root", required=True, help="KB root directory")
    parser.add_argument("--proposal", required=True, help="Proposal slug name (without .md)")
    parser.add_argument("--target-area", required=True, help="Target domain area directory")
    args = parser.parse_args()

    result = promote_proposal(Path(args.kb_root), args.proposal, args.target_area)
    print(result)
