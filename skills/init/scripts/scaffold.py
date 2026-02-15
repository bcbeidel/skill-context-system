"""Create the on-disk directory structure and template files for a Dewey KB.

Only stdlib is used.  The function never overwrites existing files.
"""

from __future__ import annotations

from pathlib import Path

from skills.init.scripts.templates import (
    _slugify,
    render_agents_md,
    render_index_md,
    render_overview_md,
)


def scaffold_kb(
    target_dir: Path,
    role_name: str,
    domain_areas: list[str] | None = None,
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
    knowledge_dir = target_dir / "knowledge"
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
    # 3. AGENTS.md
    # ------------------------------------------------------------------
    agents_path = target_dir / "AGENTS.md"
    if not agents_path.exists():
        agents_path.write_text(render_agents_md(role_name, agents_areas))
        created.append("AGENTS.md")

    # ------------------------------------------------------------------
    # 4. knowledge/index.md
    # ------------------------------------------------------------------
    index_path = knowledge_dir / "index.md"
    if not index_path.exists():
        index_path.write_text(render_index_md(role_name, area_slugs))
        created.append("knowledge/index.md")

    # ------------------------------------------------------------------
    # 5. Domain area directories + overview.md
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
            created.append(f"knowledge/{slug}/overview.md")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    summary_lines = [f"Scaffold created for '{role_name}':"]
    for item in created:
        summary_lines.append(f"  - {item}")
    return "\n".join(summary_lines)
