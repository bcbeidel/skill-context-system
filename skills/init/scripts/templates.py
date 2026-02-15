"""Render markdown templates for Dewey knowledge-base files.

All functions return plain strings. Only stdlib is used.
Templates use HTML comments (<!-- -->) as placeholders for user content.
"""

from __future__ import annotations

import re
from datetime import date


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

def render_agents_md(role_name: str, domain_areas: list[dict]) -> str:
    """Render AGENTS.md (persona + manifest).

    Parameters
    ----------
    role_name:
        The role name shown in the heading (e.g. "Senior Python Developer").
    domain_areas:
        List of ``{"name": "Area Name", "topics": [{"name": ..., "description": ...}]}``.
    """
    sections: list[str] = []

    sections.append(f"# Role: {role_name}")
    sections.append("")
    sections.append("## Who You Are")
    sections.append("<!-- Describe the persona, tone, and expertise level -->")

    sections.append("")
    sections.append("## What You Have Access To")

    for area in domain_areas:
        sections.append(f"### {area['name']}")
        for topic in area.get("topics", []):
            sections.append(f"- **{topic['name']}** -- {topic['description']}")
        sections.append("")

    # Remove trailing blank if domain_areas was non-empty (we'll add one before next section)
    if domain_areas and sections[-1] == "":
        sections.pop()

    sections.append("")
    sections.append("## How To Use This Knowledge")
    sections.append("- Load topic files from `knowledge/` when the task relates to that domain area.")
    sections.append("- Cite primary sources from the `sources` frontmatter when making recommendations.")
    sections.append("- Defer to primary sources for detailed reference.")

    return "\n".join(sections) + "\n"


def render_index_md(role_name: str, domain_areas: list[dict]) -> str:
    """Render knowledge/index.md (human-readable TOC).

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

    for area in domain_areas:
        sections.append(f"- [{area['name']}]({area['dirname']}/overview.md)")

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

    for topic in topics:
        body_lines.append(f"- [{topic['name']}]({topic['filename']}) -- {topic['description']}")

    if not topics:
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
