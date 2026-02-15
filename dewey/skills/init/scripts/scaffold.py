"""Create the on-disk directory structure and template files for a Dewey KB.

Only stdlib is used.  Supports merging KB sections into existing files
using marker-based managed sections.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from templates import (
    MARKER_BEGIN,
    MARKER_END,
    _slugify,
    render_agents_md,
    render_agents_md_section,
    render_claude_md,
    render_claude_md_section,
    render_curate_plan,
    render_index_md,
    render_overview_md,
)


def merge_managed_section(
    existing_content: str | None,
    managed_section: str,
    full_template: str,
) -> str:
    """Merge a dewey-managed section into file content.

    Three cases:
    1. ``existing_content is None`` -- return ``full_template`` (new file)
    2. No markers in existing -- append markers + section
    3. Has both markers -- replace content between them (idempotent)
    """
    if existing_content is None:
        return full_template

    if MARKER_BEGIN not in existing_content:
        return (
            existing_content.rstrip("\n")
            + "\n\n"
            + MARKER_BEGIN
            + "\n"
            + managed_section
            + "\n"
            + MARKER_END
            + "\n"
        )

    # Replace content between markers
    begin_idx = existing_content.index(MARKER_BEGIN)
    end_idx = existing_content.index(MARKER_END) + len(MARKER_END)
    return (
        existing_content[:begin_idx]
        + MARKER_BEGIN
        + "\n"
        + managed_section
        + "\n"
        + MARKER_END
        + existing_content[end_idx:]
    )


def scaffold_kb(
    target_dir: Path,
    role_name: str,
    domain_areas: list[str] | None = None,
    starter_topics: dict[str, list[str]] | None = None,
) -> str:
    """Scaffold a knowledge-base directory tree under *target_dir*.

    Parameters
    ----------
    target_dir:
        Root directory for the KB.
    role_name:
        Human-readable role name (e.g. "Paid Media Analyst").
    domain_areas:
        Optional list of domain area names to pre-create
        (e.g. ["Campaign Management", "Measurement"]).
    starter_topics:
        Optional mapping of area name to list of starter topic names.
        Used to generate a curate plan in the summary.

    Returns
    -------
    str
        A summary string listing what was created.
    """
    if domain_areas is None:
        domain_areas = []

    created: list[str] = []

    # ------------------------------------------------------------------
    # 1. Core directories
    # ------------------------------------------------------------------
    knowledge_dir = target_dir / "docs"
    proposals_dir = knowledge_dir / "_proposals"
    dewey_dirs = [
        target_dir / ".dewey" / "health",
        target_dir / ".dewey" / "history",
        target_dir / ".dewey" / "utilization",
    ]

    for d in [knowledge_dir, proposals_dir, *dewey_dirs]:
        d.mkdir(parents=True, exist_ok=True)
        created.append(str(d.relative_to(target_dir)) + "/")

    # .gitkeep in empty .dewey subdirectories
    for d in dewey_dirs:
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    # ------------------------------------------------------------------
    # 2. Build domain-area metadata used by templates
    # ------------------------------------------------------------------
    area_slugs: list[dict] = []
    for name in domain_areas:
        area_slugs.append({"name": name, "dirname": _slugify(name)})

    # For AGENTS.md we need the slightly richer format (with topics list)
    agents_areas: list[dict] = []
    for name in domain_areas:
        agents_areas.append({"name": name, "topics": []})

    # ------------------------------------------------------------------
    # 3. AGENTS.md (merge-safe)
    # ------------------------------------------------------------------
    agents_path = target_dir / "AGENTS.md"
    existing_agents = agents_path.read_text() if agents_path.exists() else None
    agents_section = render_agents_md_section(role_name, agents_areas)
    agents_full = render_agents_md(role_name, agents_areas)
    agents_new = merge_managed_section(existing_agents, agents_section, agents_full)
    agents_path.write_text(agents_new)
    if existing_agents is None:
        created.append("AGENTS.md")
    else:
        created.append("AGENTS.md (merged)")

    # ------------------------------------------------------------------
    # 4. CLAUDE.md (merge-safe)
    # ------------------------------------------------------------------
    claude_path = target_dir / "CLAUDE.md"
    existing_claude = claude_path.read_text() if claude_path.exists() else None
    claude_section = render_claude_md_section(role_name, area_slugs)
    claude_full = render_claude_md(role_name, area_slugs)
    claude_new = merge_managed_section(existing_claude, claude_section, claude_full)
    claude_path.write_text(claude_new)
    if existing_claude is None:
        created.append("CLAUDE.md")
    else:
        created.append("CLAUDE.md (merged)")

    # ------------------------------------------------------------------
    # 5. docs/index.md
    # ------------------------------------------------------------------
    index_path = knowledge_dir / "index.md"
    if not index_path.exists():
        index_path.write_text(render_index_md(role_name, area_slugs))
        created.append("docs/index.md")

    # ------------------------------------------------------------------
    # 6. Domain area directories + overview.md
    # ------------------------------------------------------------------
    for name in domain_areas:
        slug = _slugify(name)
        area_dir = knowledge_dir / slug
        area_dir.mkdir(parents=True, exist_ok=True)

        overview_path = area_dir / "overview.md"
        if not overview_path.exists():
            overview_path.write_text(
                render_overview_md(name, relevance="core", topics=[])
            )
            created.append(f"docs/{slug}/overview.md")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    summary_lines = [f"Scaffold created for '{role_name}':"]
    for item in created:
        summary_lines.append(f"  - {item}")

    # Curate plan (if starter topics provided)
    if starter_topics:
        curate_areas = []
        for name in domain_areas:
            topics = starter_topics.get(name, [])
            if topics:
                curate_areas.append({
                    "name": name,
                    "slug": _slugify(name),
                    "starter_topics": topics,
                })
        plan = render_curate_plan(curate_areas)
        if plan:
            summary_lines.append("")
            summary_lines.append(plan.rstrip("\n"))

    return "\n".join(summary_lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scaffold a knowledge base.")
    parser.add_argument("--target", required=True, help="Target directory")
    parser.add_argument("--role", required=True, help="Role name")
    parser.add_argument(
        "--areas",
        default="",
        help="Comma-separated domain area names",
    )
    parser.add_argument(
        "--starter-topics",
        default="",
        help='JSON mapping of area name to starter topics, e.g. \'{"Area": ["Topic1"]}\'',
    )
    args = parser.parse_args()

    areas = (
        [a.strip() for a in args.areas.split(",") if a.strip()]
        if args.areas
        else []
    )
    topics = json.loads(args.starter_topics) if args.starter_topics else None
    result = scaffold_kb(Path(args.target), args.role, areas, topics)
    print(result)
