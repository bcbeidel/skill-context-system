"""Render markdown templates for Dewey knowledge-base files.

All functions return plain strings. Only stdlib is used.
Templates use HTML comments (<!-- -->) as placeholders for user content.
Managed sections are bracketed by MARKER_BEGIN / MARKER_END for safe merging.
"""

from __future__ import annotations

import re
from datetime import date


# ---------------------------------------------------------------------------
# Managed-section markers
# ---------------------------------------------------------------------------

MARKER_BEGIN = "<!-- dewey:kb:begin -->"
MARKER_END = "<!-- dewey:kb:end -->"


def _slugify(name: str) -> str:
    """Convert a human-readable name to a filename slug.

    Lowercases, replaces spaces and underscores with hyphens, strips
    non-alphanumeric characters (except hyphens), and collapses runs of
    hyphens.
    """
    slug = name.lower().strip()
    slug = slug.replace("_", "-")
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.strip("-")
    return slug


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _today() -> str:
    """ISO-formatted date string for today."""
    return date.today().isoformat()


def _frontmatter(fields: dict) -> str:
    """Render YAML frontmatter block from a dict."""
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public render functions
# ---------------------------------------------------------------------------

def render_agents_md_section(role_name: str, domain_areas: list[dict]) -> str:
    """Render the dewey-managed section of AGENTS.md (no markers).

    Contains the "What You Have Access To" manifest and
    "How To Use This Knowledge" guidance.
    """
    sections: list[str] = []

    sections.append("## What You Have Access To")

    for area in domain_areas:
        topics = area.get("topics", [])
        sections.append(f"### {area['name']}")
        if topics:
            sections.append("")
            sections.append("| Topic | Description |")
            sections.append("|-------|-------------|")
            for topic in topics:
                sections.append(f"| [{topic['name']}](docs/{_slugify(area['name'])}/{_slugify(topic['name'])}.md) | {topic['description']} |")
        sections.append("")

    # Remove trailing blank if domain_areas was non-empty
    if domain_areas and sections[-1] == "":
        sections.pop()

    sections.append("")
    sections.append("## How To Use This Knowledge")
    sections.append("- Load topic files from `docs/` when the task relates to that domain area.")
    sections.append("- Use `.ref.md` files for quick lookups; use full topic files for deep context.")
    sections.append("- Cite primary sources from the `sources` frontmatter when making recommendations.")
    sections.append("- Defer to primary sources for detailed reference.")

    return "\n".join(sections)


def render_agents_md(role_name: str, domain_areas: list[dict]) -> str:
    """Render AGENTS.md (persona + manifest).

    The role heading and "Who You Are" section are user-owned (outside markers).
    The manifest and usage sections are dewey-managed (inside markers).

    Parameters
    ----------
    role_name:
        The role name shown in the heading (e.g. "Senior Python Developer").
    domain_areas:
        List of ``{"name": "Area Name", "topics": [{"name": ..., "description": ...}]}``.
    """
    lines: list[str] = []

    # User-owned section (outside markers)
    lines.append(f"# Role: {role_name}")
    lines.append("")
    lines.append("## Who You Are")
    lines.append("<!-- Describe the persona, tone, and expertise level -->")
    lines.append("")

    # Dewey-managed section (inside markers)
    lines.append(MARKER_BEGIN)
    lines.append(render_agents_md_section(role_name, domain_areas))
    lines.append(MARKER_END)

    return "\n".join(lines) + "\n"


def render_index_md(role_name: str, domain_areas: list[dict]) -> str:
    """Render docs/index.md (human-readable TOC).

    Parameters
    ----------
    role_name:
        Included for context in the preamble.
    domain_areas:
        List of ``{"name": "Area Name", "dirname": "area-name"}``.
    """
    sections: list[str] = []

    sections.append("# Knowledge Base")
    sections.append("")
    sections.append(f"> Domain knowledge for **{role_name}**.")
    sections.append("")
    sections.append("## Domain Areas")
    sections.append("")

    if domain_areas:
        sections.append("| Area | Overview |")
        sections.append("|------|----------|")
        for area in domain_areas:
            sections.append(f"| {area['name']} | [{area['dirname']}/overview.md]({area['dirname']}/overview.md) |")
    else:
        sections.append("<!-- No domain areas yet. Use init --role to create them. -->")

    return "\n".join(sections) + "\n"


def render_overview_md(area_name: str, relevance: str, topics: list[dict]) -> str:
    """Render overview.md for a single domain area.

    Parameters
    ----------
    area_name:
        Human-readable area name shown in the heading.
    relevance:
        One of core / supporting / peripheral.
    topics:
        List of ``{"name": ..., "filename": ..., "description": ...}``.
    """
    fm = _frontmatter({
        "sources": [
            "url: <!-- Add primary source URL -->\n    title: <!-- Add source title -->",
        ],
        "last_validated": _today(),
        "relevance": f'"{relevance}"',
        "depth": "overview",
    })

    body_lines: list[str] = []

    body_lines.append(f"# {area_name}")
    body_lines.append("")
    body_lines.append("## What This Covers")
    body_lines.append("<!-- placeholder -->")
    body_lines.append("")
    body_lines.append("## How It's Organized")

    if topics:
        body_lines.append("")
        body_lines.append("| Topic | Description |")
        body_lines.append("|-------|-------------|")
        for topic in topics:
            body_lines.append(f"| [{topic['name']}]({topic['filename']}) | {topic['description']} |")
    else:
        body_lines.append("<!-- No topics yet. Use the create-topic skill to add one. -->")

    body_lines.append("")
    body_lines.append("## Key Sources")
    body_lines.append("<!-- placeholder -->")

    return fm + "\n\n" + "\n".join(body_lines) + "\n"


def render_topic_md(topic_name: str, relevance: str) -> str:
    """Render a working-knowledge topic file (<topic>.md).

    Includes YAML frontmatter and the five required sections.
    """
    slug = _slugify(topic_name)
    fm = _frontmatter({
        "sources": [
            "url: <!-- Add primary source URL -->\n    title: <!-- Add source title -->",
        ],
        "last_validated": _today(),
        "relevance": f'"{relevance}"',
        "depth": "working",
    })

    body_lines = [
        f"# {topic_name}",
        "",
        "## Why This Matters",
        "<!-- Explain why this topic is important in your domain -->",
        "",
        "## In Practice",
        "<!-- Describe how this topic is applied day-to-day -->",
        "",
        "## Key Guidance",
        "<!-- Actionable recommendations and best practices -->",
        "",
        "## Watch Out For",
        "<!-- Common pitfalls, anti-patterns, and mistakes -->",
        "",
        "## Go Deeper",
        "",
        f"- [{topic_name} Reference]({slug}.ref.md) -- quick-lookup version",
        "- [Source Title](url) -- primary source for full treatment",
    ]

    return fm + "\n\n" + "\n".join(body_lines) + "\n"


def render_topic_ref_md(topic_name: str, relevance: str) -> str:
    """Render an expert-reference topic file (<topic>.ref.md).

    Terse and scannable. Intended for quick look-ups by experienced users.
    """
    slug = _slugify(topic_name)
    fm = _frontmatter({
        "sources": [
            "url: <!-- Add primary source URL -->\n    title: <!-- Add source title -->",
        ],
        "last_validated": _today(),
        "relevance": f'"{relevance}"',
        "depth": "reference",
    })

    body_lines = [
        f"# {topic_name}",
        "",
        "<!-- Quick-reference notes: keep terse and scannable -->",
        "",
        f"**See also:** [{topic_name}]({slug}.md)",
    ]

    return fm + "\n\n" + "\n".join(body_lines) + "\n"


def render_claude_md_section(role_name: str, domain_areas: list[dict]) -> str:
    """Render the dewey-managed section of CLAUDE.md (no markers).

    Contains the KB heading, usage guide, directory structure,
    frontmatter reference, and domain areas table.

    Parameters
    ----------
    role_name:
        Human-readable role name.
    domain_areas:
        List of ``{"name": "Area Name", "dirname": "area-name"}``.
    """
    lines: list[str] = []

    lines.append(f"## {role_name} Knowledge Base")
    lines.append("")
    lines.append("This project contains a curated knowledge base with progressive disclosure:")
    lines.append("overviews for orientation, working-knowledge files for daily use, and")
    lines.append("`.ref.md` reference companions for quick lookups.")
    lines.append("")

    # How to Use This KB
    lines.append("### How to Use This KB")
    lines.append("")
    lines.append("1. Read `AGENTS.md` for the full role definition and topic manifest")
    lines.append("2. Load topic files from `docs/` when the task relates to a domain area")
    lines.append("3. Cite primary sources from the `sources` frontmatter when making recommendations")
    lines.append("4. Use `.ref.md` files for quick lookups without loading full topic context")
    lines.append("")

    # Directory Structure
    lines.append("### Directory Structure")
    lines.append("")
    lines.append("```")
    lines.append("AGENTS.md              # Role persona and topic manifest")
    lines.append("docs/")
    lines.append("  index.md             # Table of contents")
    for area in domain_areas:
        lines.append(f"  {area['dirname']}/")
        lines.append(f"    overview.md        # {area['name']} overview")
    lines.append("  _proposals/            # Pending topic proposals")
    lines.append("```")
    lines.append("")

    # Frontmatter Reference
    lines.append("### Frontmatter Reference")
    lines.append("")
    lines.append("Every topic file includes YAML frontmatter with these fields:")
    lines.append("")
    lines.append("| Field | Purpose |")
    lines.append("|-------|---------|")
    lines.append("| `sources` | Primary source URLs and titles for citation |")
    lines.append("| `last_validated` | Date the content was last verified against sources |")
    lines.append("| `relevance` | `core` / `supporting` / `peripheral` -- importance to the role |")
    lines.append("| `depth` | `overview` / `working` / `reference` -- level of detail |")
    lines.append("")

    # Domain Areas
    if domain_areas:
        lines.append("### Domain Areas")
        lines.append("")
        lines.append("| Area | Path | Overview |")
        lines.append("|------|------|----------|")
        for area in domain_areas:
            lines.append(
                f"| {area['name']} "
                f"| `docs/{area['dirname']}/` "
                f"| [overview.md](docs/{area['dirname']}/overview.md) |"
            )

    return "\n".join(lines)


def render_claude_md(role_name: str, domain_areas: list[dict]) -> str:
    """Render CLAUDE.md for Claude Code discovery.

    The entire KB section is wrapped in managed-section markers so it can
    be safely merged into an existing CLAUDE.md.

    Parameters
    ----------
    role_name:
        Human-readable role name.
    domain_areas:
        List of ``{"name": "Area Name", "dirname": "area-name"}``.
    """
    lines: list[str] = []

    lines.append(MARKER_BEGIN)
    lines.append(render_claude_md_section(role_name, domain_areas))
    lines.append(MARKER_END)

    return "\n".join(lines) + "\n"


def render_proposal_md(
    topic_name: str,
    relevance: str,
    proposed_by: str,
    rationale: str,
) -> str:
    """Render a proposal file for a new or revised topic.

    Extends the working-knowledge template with proposal-specific frontmatter.
    """
    fm = _frontmatter({
        "sources": [
            "url: <!-- Add primary source URL -->\n    title: <!-- Add source title -->",
        ],
        "last_validated": _today(),
        "relevance": f'"{relevance}"',
        "depth": "working",
        "status": "proposal",
        "proposed_by": proposed_by,
        "rationale": rationale,
    })

    body_lines = [
        f"# {topic_name}",
        "",
        "## Why This Matters",
        "<!-- Explain why this topic is important in your domain -->",
        "",
        "## In Practice",
        "<!-- Describe how this topic is applied day-to-day -->",
        "",
        "## Key Guidance",
        "<!-- Actionable recommendations and best practices -->",
        "",
        "## Watch Out For",
        "<!-- Common pitfalls, anti-patterns, and mistakes -->",
        "",
        "## Go Deeper",
        "<!-- Links to primary sources, books, talks, and further reading -->",
    ]

    return fm + "\n\n" + "\n".join(body_lines) + "\n"


def render_curate_plan(domain_areas: list[dict]) -> str:
    """Render an actionable curate plan with starter topic commands.

    Parameters
    ----------
    domain_areas:
        List of ``{"name": "Area Name", "slug": "area-slug",
        "starter_topics": ["Topic One", "Topic Two"]}``.
        If ``starter_topics`` is empty or missing for an area, it is skipped.

    Returns an empty string if no areas have starter topics.
    """
    lines: list[str] = []
    counter = 0

    for area in domain_areas:
        topics = area.get("starter_topics", [])
        if not topics:
            continue
        slug = area.get("slug") or _slugify(area["name"])
        lines.append(f"### {area['name']}")
        for topic in topics:
            counter += 1
            lines.append(f"{counter}. `/dewey:curate add {topic} in {slug}`")
        lines.append("")

    if not lines:
        return ""

    header = ["## Next Steps: Populate Your Knowledge Base", ""]
    return "\n".join(header + lines).rstrip("\n") + "\n"
