"""Create the on-disk directory structure and template files for a Dewey knowledge base.

Only stdlib is used.  Supports merging knowledge base sections into existing files
using marker-based managed sections.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from config import read_knowledge_dir, write_config
from templates import (
    MARKER_BEGIN,
    MARKER_END,
    _slugify,
    _today,
    render_agents_md,
    render_agents_md_section,
    render_claude_md,
    render_claude_md_section,
    render_curate_plan,
    render_curation_plan_md,
    render_hooks_json,
    render_index_md,
    render_overview_md,
)


def _read_topic_metadata(file_path: Path) -> dict:
    """Read a single .md file's depth from frontmatter and title from the first H1.

    Returns ``{"name": str, "depth": str}`` or empty dict if the file
    cannot be read.
    """
    try:
        text = file_path.read_text()
    except OSError:
        return {}

    # Extract depth from YAML frontmatter (between --- fences)
    depth = ""
    fm_match = re.match(r"^---\n(.*?\n)---\n", text, re.DOTALL)
    if fm_match:
        depth_match = re.search(r"^depth:\s*(.+)$", fm_match.group(1), re.MULTILINE)
        if depth_match:
            depth = depth_match.group(1).strip()

    # Extract first H1 heading
    name = ""
    heading_match = re.search(r"^# (.+)$", text, re.MULTILINE)
    if heading_match:
        name = heading_match.group(1).strip()

    return {"name": name, "depth": depth}


def _discover_index_data(kb_root: Path, knowledge_dir_name: str = "docs") -> list[dict]:
    """Scan the knowledge directory for all area subdirectories and their topics.

    Returns a list of::

        {"name": str, "dirname": str, "topics": [{"name": str, "filename": str, "depth": str}]}

    Key behaviours:
    - Excludes ``overview.md`` and ``.ref.md`` files from topics
    - Excludes directories starting with ``_`` (e.g. ``_proposals``)
    - Reads area name from ``overview.md``'s H1 heading (falls back to dirname)
    - Reads topic name from each file's H1 heading (falls back to filename stem)
    - Reads depth from frontmatter
    - Areas sorted alphabetically by dirname
    - Topics sorted alphabetically by filename
    """
    knowledge_path = kb_root / knowledge_dir_name
    if not knowledge_path.is_dir():
        return []

    areas: list[dict] = []
    for entry in sorted(knowledge_path.iterdir()):
        if not entry.is_dir():
            continue
        # Skip underscore-prefixed directories like _proposals
        if entry.name.startswith("_"):
            continue

        dirname = entry.name

        # Read area name from overview.md (fall back to dirname)
        overview_path = entry / "overview.md"
        area_name = dirname
        if overview_path.is_file():
            meta = _read_topic_metadata(overview_path)
            if meta.get("name"):
                area_name = meta["name"]

        # Discover topics
        topics: list[dict] = []
        for md_file in sorted(entry.glob("*.md")):
            fname = md_file.name
            # Exclude overview.md and .ref.md files
            if fname == "overview.md":
                continue
            if fname.endswith(".ref.md"):
                continue

            meta = _read_topic_metadata(md_file)
            topic_name = meta.get("name", "") if meta else ""
            if not topic_name:
                # Fall back to filename stem (without .md)
                topic_name = fname[:-3]  # strip .md
            topic_depth = meta.get("depth", "") if meta else ""

            topics.append({
                "name": topic_name,
                "filename": fname,
                "depth": topic_depth,
            })

        areas.append({
            "name": area_name,
            "dirname": dirname,
            "topics": topics,
        })

    return areas


def _parse_agents_topics(agents_content: str) -> dict[str, list[dict]]:
    """Extract topic table entries from existing AGENTS.md managed section.

    Returns mapping of area name -> list of {"name", "path", "description"}.
    """
    if MARKER_BEGIN not in agents_content or MARKER_END not in agents_content:
        return {}
    begin = agents_content.index(MARKER_BEGIN)
    end = agents_content.index(MARKER_END)
    managed = agents_content[begin:end]

    topics_by_area: dict[str, list[dict]] = {}
    current_area: str | None = None
    for line in managed.split("\n"):
        heading_match = re.match(r"^### (.+)$", line)
        if heading_match:
            current_area = heading_match.group(1)
            topics_by_area[current_area] = []
            continue
        if current_area is not None:
            row_match = re.match(r"^\| \[(.+?)\]\((.+?)\) \| (.+?) \|$", line)
            if row_match:
                topics_by_area[current_area].append({
                    "name": row_match.group(1),
                    "path": row_match.group(2),
                    "description": row_match.group(3),
                })
    return topics_by_area


def _merge_curation_plan(existing_content: str, new_areas: list[dict]) -> str:
    """Merge new area sections into existing curation plan, preserving progress."""
    existing_slugs: set[str] = set()
    for line in existing_content.split("\n"):
        if line.startswith("## "):
            existing_slugs.add(line[3:].strip())

    new_sections: list[str] = []
    for area in new_areas:
        slug = area.get("slug") or _slugify(area["name"])
        if slug in existing_slugs:
            continue
        topics = area.get("starter_topics", [])
        if not topics:
            continue
        lines = [f"## {slug}"]
        for topic in topics:
            if isinstance(topic, str):
                name, relevance, rationale = topic, "core", ""
            else:
                name = topic["name"]
                relevance = topic.get("relevance", "core")
                rationale = topic.get("rationale", "")
            entry = f"- [ ] {name} -- {relevance}"
            if rationale:
                entry += f" -- {rationale}"
            lines.append(entry)
        new_sections.append("\n".join(lines))

    if not new_sections:
        return existing_content

    # Update last_updated in frontmatter
    updated = re.sub(
        r"last_updated: \d{4}-\d{2}-\d{2}",
        f"last_updated: {_today()}",
        existing_content,
    )
    return updated.rstrip("\n") + "\n\n" + "\n\n".join(new_sections) + "\n"


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
    knowledge_dir: str = "docs",
) -> str:
    """Scaffold a knowledge-base directory tree under *target_dir*.

    Parameters
    ----------
    target_dir:
        Root directory for the knowledge base.
    role_name:
        Human-readable role name (e.g. "Paid Media Analyst").
    domain_areas:
        Optional list of domain area names to pre-create
        (e.g. ["Campaign Management", "Measurement"]).
    starter_topics:
        Optional mapping of area name to list of starter topic names.
        Used to generate a curate plan in the summary.
    knowledge_dir:
        Name of the knowledge directory (default: "docs").

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
    knowledge_path = target_dir / knowledge_dir
    proposals_dir = knowledge_path / "_proposals"
    dewey_dirs = [
        target_dir / ".dewey" / "health",
        target_dir / ".dewey" / "history",
        target_dir / ".dewey" / "utilization",
    ]

    for d in [knowledge_path, proposals_dir, *dewey_dirs]:
        d.mkdir(parents=True, exist_ok=True)
        created.append(str(d.relative_to(target_dir)) + "/")

    # .gitkeep in empty .dewey subdirectories
    for d in dewey_dirs:
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    # Write config
    write_config(target_dir, knowledge_dir)
    created.append(".dewey/config.json")

    # ------------------------------------------------------------------
    # 2. Build domain-area metadata used by templates
    # ------------------------------------------------------------------
    area_slugs: list[dict] = []
    for name in domain_areas:
        area_slugs.append({"name": name, "dirname": _slugify(name)})

    # For AGENTS.md we need the slightly richer format (with topics list)
    # Discover existing topics from current AGENTS.md to preserve on re-init
    existing_topics: dict[str, list[dict]] = {}
    agents_path = target_dir / "AGENTS.md"
    if agents_path.exists():
        existing_topics = _parse_agents_topics(agents_path.read_text())

    agents_areas: list[dict] = []
    for name in domain_areas:
        preserved = existing_topics.get(name, [])
        agents_areas.append({"name": name, "topics": preserved})

    # ------------------------------------------------------------------
    # 3. AGENTS.md (merge-safe)
    # ------------------------------------------------------------------
    existing_agents = agents_path.read_text() if agents_path.exists() else None
    agents_section = render_agents_md_section(role_name, agents_areas, knowledge_dir=knowledge_dir)
    agents_full = render_agents_md(role_name, agents_areas, knowledge_dir=knowledge_dir)
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
    claude_section = render_claude_md_section(role_name, area_slugs, knowledge_dir=knowledge_dir)
    claude_full = render_claude_md(role_name, area_slugs, knowledge_dir=knowledge_dir)
    claude_new = merge_managed_section(existing_claude, claude_section, claude_full)
    claude_path.write_text(claude_new)
    if existing_claude is None:
        created.append("CLAUDE.md")
    else:
        created.append("CLAUDE.md (merged)")

    # ------------------------------------------------------------------
    # 5. Domain area directories + overview.md
    # ------------------------------------------------------------------
    for name in domain_areas:
        slug = _slugify(name)
        area_dir = knowledge_path / slug
        area_dir.mkdir(parents=True, exist_ok=True)

        overview_path = area_dir / "overview.md"
        if not overview_path.exists():
            overview_path.write_text(
                render_overview_md(name, relevance="core", topics=[])
            )
            created.append(f"{knowledge_dir}/{slug}/overview.md")

    # ------------------------------------------------------------------
    # 6. index.md inside the knowledge directory (filesystem-driven)
    # ------------------------------------------------------------------
    index_path = knowledge_path / "index.md"
    index_existed = index_path.exists()
    index_data = _discover_index_data(target_dir, knowledge_dir)
    # Fall back to area_slugs if no files on disk yet (fresh scaffold)
    if not index_data:
        index_data = area_slugs
    index_path.write_text(render_index_md(role_name, index_data))
    created.append(f"{knowledge_dir}/index.md" + (" (updated)" if index_existed else ""))

    # ------------------------------------------------------------------
    # 7. .claude/hooks.json (utilization tracking hook)
    # ------------------------------------------------------------------
    hooks_path = target_dir / ".claude" / "hooks.json"
    if not hooks_path.exists():
        hooks_path.parent.mkdir(parents=True, exist_ok=True)
        plugin_root = str(Path(__file__).resolve().parent.parent.parent.parent)
        hooks_path.write_text(render_hooks_json(plugin_root, str(target_dir)))
        created.append(".claude/hooks.json")

    # ------------------------------------------------------------------
    # 8. Curation plan (.dewey/curation-plan.md)
    # ------------------------------------------------------------------
    if starter_topics:
        plan_areas = []
        for name in domain_areas:
            topics = starter_topics.get(name, [])
            if topics:
                plan_areas.append({
                    "name": name,
                    "slug": _slugify(name),
                    "starter_topics": topics,
                })
        if plan_areas:
            plan_path = target_dir / ".dewey" / "curation-plan.md"
            if plan_path.exists():
                existing_plan = plan_path.read_text()
                plan_path.write_text(_merge_curation_plan(existing_plan, plan_areas))
                created.append(".dewey/curation-plan.md (updated)")
            else:
                plan_path.write_text(render_curation_plan_md(plan_areas))
                created.append(".dewey/curation-plan.md")

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


def rebuild_index(target_dir: Path) -> str:
    """Regenerate index.md from the current filesystem contents.

    Parameters
    ----------
    target_dir:
        Root directory containing the knowledge base.

    Returns
    -------
    str
        Path to the written index.md relative to target_dir.
    """
    knowledge_dir_name = read_knowledge_dir(target_dir)
    knowledge_path = target_dir / knowledge_dir_name

    # Read role name from AGENTS.md heading
    agents_path = target_dir / "AGENTS.md"
    role_name = "Knowledge Base"
    if agents_path.exists():
        heading_match = re.search(
            r"^# Role:\s*(.+)$", agents_path.read_text(), re.MULTILINE
        )
        if heading_match:
            role_name = heading_match.group(1).strip()

    index_data = _discover_index_data(target_dir, knowledge_dir_name)
    index_path = knowledge_path / "index.md"
    index_path.write_text(render_index_md(role_name, index_data))
    return f"{knowledge_dir_name}/index.md"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scaffold a knowledge base.")
    parser.add_argument("--target", required=True, help="Target directory")
    parser.add_argument("--role", default="", help="Role name")
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
    parser.add_argument(
        "--knowledge-dir",
        default="docs",
        help="Name of the knowledge directory (default: docs)",
    )
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Regenerate index.md from filesystem contents and exit.",
    )
    args = parser.parse_args()

    if args.rebuild_index:
        result = rebuild_index(Path(args.target))
        print(f"Rebuilt {result}")
    else:
        areas = (
            [a.strip() for a in args.areas.split(",") if a.strip()]
            if args.areas
            else []
        )
        topics = json.loads(args.starter_topics) if args.starter_topics else None
        result = scaffold_kb(Path(args.target), args.role, areas, topics, knowledge_dir=args.knowledge_dir)
        print(result)
