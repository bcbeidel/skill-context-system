"""Tier 1 deterministic validators for knowledge-base health checks.

Every validator returns a list of issue dicts::

    {"file": str, "message": str, "severity": "fail" | "warn"}

Only stdlib is used.  No network requests are made (that belongs in Tier 2).
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

# ------------------------------------------------------------------
# Shared helpers
# ------------------------------------------------------------------

_VALID_DEPTHS = {"overview", "working", "reference"}

_SIZE_BOUNDS: dict[str, tuple[int, int]] = {
    "overview": (5, 150),
    "working": (10, 400),
    "reference": (3, 150),
}


def parse_frontmatter(file_path: Path) -> dict:
    """Parse YAML-like frontmatter between ``---`` delimiters.

    Returns a dict with simple ``key: value`` pairs.  List values
    (``sources``) are collected from subsequent ``  - item`` lines.
    No third-party YAML library is required.
    """
    text = file_path.read_text()
    lines = text.split("\n")

    # Find the two --- delimiters
    delimiter_indices: list[int] = []
    for idx, line in enumerate(lines):
        if line.strip() == "---":
            delimiter_indices.append(idx)
            if len(delimiter_indices) == 2:
                break

    if len(delimiter_indices) < 2:
        return {}

    fm_lines = lines[delimiter_indices[0] + 1 : delimiter_indices[1]]

    result: dict = {}
    current_key: str | None = None

    for line in fm_lines:
        # List item: "  - value"
        list_match = re.match(r"^\s+-\s+(.+)$", line)
        if list_match and current_key is not None:
            if not isinstance(result.get(current_key), list):
                result[current_key] = []
            result[current_key].append(list_match.group(1).strip())
            continue

        # Key-value: "key: value"
        kv_match = re.match(r"^(\w[\w_]*):\s*(.*)$", line)
        if kv_match:
            key = kv_match.group(1)
            value = kv_match.group(2).strip()
            current_key = key
            if value:
                result[key] = value
            else:
                # Value may come as list items on following lines
                result[key] = None
            continue

    return result


# ------------------------------------------------------------------
# Validators
# ------------------------------------------------------------------


def check_frontmatter(file_path: Path) -> list[dict]:
    """Validate that required frontmatter fields are present and valid."""
    issues: list[dict] = []
    name = str(file_path)
    fm = parse_frontmatter(file_path)

    if not fm:
        issues.append({"file": name, "message": "Missing frontmatter", "severity": "fail"})
        return issues

    required = ["sources", "last_validated", "relevance", "depth"]
    for field in required:
        val = fm.get(field)
        if val is None or val == "":
            issues.append({
                "file": name,
                "message": f"Missing required frontmatter field: {field}",
                "severity": "fail",
            })

    # sources must be a non-empty list
    sources = fm.get("sources")
    if isinstance(sources, list) and len(sources) == 0:
        issues.append({
            "file": name,
            "message": "Missing required frontmatter field: sources",
            "severity": "fail",
        })

    # depth must be one of the valid values
    depth = fm.get("depth")
    if depth and depth not in _VALID_DEPTHS:
        issues.append({
            "file": name,
            "message": f"Invalid depth '{depth}'; must be one of {sorted(_VALID_DEPTHS)}",
            "severity": "fail",
        })

    return issues


def check_section_ordering(file_path: Path) -> list[dict]:
    """Ensure 'In Practice' appears before 'Key Guidance' in working-depth files."""
    issues: list[dict] = []
    name = str(file_path)
    fm = parse_frontmatter(file_path)

    if fm.get("depth") != "working":
        return issues

    text = file_path.read_text()
    headings = re.findall(r"^##\s+(.+)$", text, re.MULTILINE)

    in_practice_idx: int | None = None
    key_guidance_idx: int | None = None
    for idx, h in enumerate(headings):
        if "In Practice" in h and in_practice_idx is None:
            in_practice_idx = idx
        if "Key Guidance" in h and key_guidance_idx is None:
            key_guidance_idx = idx

    if in_practice_idx is not None and key_guidance_idx is not None:
        if key_guidance_idx < in_practice_idx:
            issues.append({
                "file": name,
                "message": "'In Practice' must appear before 'Key Guidance' (concrete before abstract)",
                "severity": "warn",
            })

    return issues


def check_cross_references(file_path: Path, kb_root: Path) -> list[dict]:
    """Check that internal markdown links point to existing files."""
    issues: list[dict] = []
    name = str(file_path)
    text = file_path.read_text()

    # Match [text](path) — exclude URLs (http/https), anchors (#), and mailto
    links = re.findall(r"\[([^\]]*)\]\(([^)]+)\)", text)
    for _link_text, target in links:
        target = target.strip()
        # Skip external URLs, anchors, and mailto
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        # Strip any anchor from the target
        target_path = target.split("#")[0]
        if not target_path:
            continue
        resolved = (file_path.parent / target_path).resolve()
        if not resolved.exists():
            issues.append({
                "file": name,
                "message": f"Broken internal link: {target_path}",
                "severity": "warn",
            })

    return issues


def check_size_bounds(file_path: Path) -> list[dict]:
    """Warn if file line count is outside expected range for its depth."""
    issues: list[dict] = []
    name = str(file_path)
    fm = parse_frontmatter(file_path)
    depth = fm.get("depth")

    if depth not in _SIZE_BOUNDS:
        return issues

    line_count = len(file_path.read_text().splitlines())
    lo, hi = _SIZE_BOUNDS[depth]

    if line_count < lo:
        issues.append({
            "file": name,
            "message": f"File has {line_count} lines; expected at least {lo} for depth '{depth}'",
            "severity": "warn",
        })
    elif line_count > hi:
        issues.append({
            "file": name,
            "message": f"File has {line_count} lines; expected at most {hi} for depth '{depth}'",
            "severity": "warn",
        })

    return issues


def check_coverage(kb_root: Path) -> list[dict]:
    """Check structural coverage: overview.md per area, .ref.md per topic."""
    issues: list[dict] = []
    knowledge_dir = kb_root / "docs"

    if not knowledge_dir.is_dir():
        return issues

    for child in sorted(knowledge_dir.iterdir()):
        if not child.is_dir():
            continue
        # Skip _proposals and other special directories
        if child.name.startswith("_"):
            continue

        # Every area directory must have an overview.md
        if not (child / "overview.md").exists():
            issues.append({
                "file": str(child),
                "message": f"Area '{child.name}' missing overview.md",
                "severity": "fail",
            })

        # Every .md file (not overview.md, not .ref.md) should have a .ref.md
        for md_file in sorted(child.glob("*.md")):
            if md_file.name == "overview.md":
                continue
            if md_file.name.endswith(".ref.md"):
                continue
            stem = md_file.stem  # e.g. "bidding" from "bidding.md"
            ref_file = child / f"{stem}.ref.md"
            if not ref_file.exists():
                issues.append({
                    "file": str(md_file),
                    "message": f"Topic '{md_file.name}' missing companion {stem}.ref.md",
                    "severity": "warn",
                })

    return issues


def check_freshness(file_path: Path, max_age_days: int = 90) -> list[dict]:
    """Warn if last_validated date is older than *max_age_days*."""
    issues: list[dict] = []
    name = str(file_path)
    fm = parse_frontmatter(file_path)
    last_validated = fm.get("last_validated")

    if not last_validated:
        return issues

    try:
        validated_date = date.fromisoformat(str(last_validated))
    except ValueError:
        issues.append({
            "file": name,
            "message": f"Invalid last_validated date: {last_validated}",
            "severity": "warn",
        })
        return issues

    age = (date.today() - validated_date).days
    if age > max_age_days:
        issues.append({
            "file": name,
            "message": f"Content is {age} days old (max {max_age_days}); needs re-validation",
            "severity": "warn",
        })

    return issues


def check_source_urls(file_path: Path) -> list[dict]:
    """Validate that source URLs in frontmatter are well-formed."""
    issues: list[dict] = []
    name = str(file_path)
    fm = parse_frontmatter(file_path)
    sources = fm.get("sources")

    if not isinstance(sources, list):
        return issues

    for url in sources:
        url = str(url).strip()
        # Skip placeholder comments
        if "<!--" in url:
            continue
        if not url.startswith(("http://", "https://")):
            issues.append({
                "file": name,
                "message": f"Malformed source URL: {url}",
                "severity": "fail",
            })

    return issues
