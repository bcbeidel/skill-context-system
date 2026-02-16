"""Tier 1 deterministic validators for knowledge-base health checks.

Every validator returns a list of issue dicts::

    {"file": str, "message": str, "severity": "fail" | "warn"}

Only stdlib is used.  No network requests are made (that belongs in Tier 2).
"""

from __future__ import annotations

import hashlib
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

_WORKING_SECTIONS = [
    "Why This Matters",
    "In Practice",
    "Key Guidance",
    "Watch Out For",
    "Go Deeper",
]

_OVERVIEW_SECTIONS = [
    "What This Covers",
    "How It's Organized",
]


def _body_without_frontmatter(text: str) -> str:
    """Strip content between first two ``---`` lines."""
    lines = text.split("\n")
    delimiter_count = 0
    start = 0
    for idx, line in enumerate(lines):
        if line.strip() == "---":
            delimiter_count += 1
            if delimiter_count == 2:
                start = idx + 1
                break
    if delimiter_count < 2:
        return text
    return "\n".join(lines[start:])


def _extract_section(body: str, heading: str) -> str | None:
    """Extract text between ``## <heading>`` and next ``## `` (or EOF).

    Uses case-insensitive substring match on *heading*, matching the
    convention in ``check_section_ordering`` (e.g. ``"In Practice" in h``).
    """
    lines = body.split("\n")
    capturing = False
    section_lines: list[str] = []

    for line in lines:
        if line.startswith("## "):
            if capturing:
                break
            heading_text = line[3:].strip()
            if heading.lower() in heading_text.lower():
                capturing = True
                continue
        elif capturing:
            section_lines.append(line)

    if not section_lines and not capturing:
        return None
    return "\n".join(section_lines)


def _strip_fenced_code_blocks(text: str) -> str:
    """Replace fenced code block content with blank lines (preserves line count)."""
    lines = text.split("\n")
    result: list[str] = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            result.append("")
        elif in_fence:
            result.append("")
        else:
            result.append(line)
    return "\n".join(result)


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


def check_coverage(kb_root: Path, *, knowledge_dir_name: str = "docs") -> list[dict]:
    """Check structural coverage: overview.md per area, .ref.md per topic."""
    issues: list[dict] = []
    knowledge_dir = kb_root / knowledge_dir_name

    if not knowledge_dir.is_dir():
        return issues

    for child in sorted(knowledge_dir.iterdir()):
        if not child.is_dir():
            continue
        # Skip _proposals, hidden directories, and other special directories
        if child.name.startswith("_") or child.name.startswith("."):
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

    for entry in sources:
        url = str(entry).strip()
        # Handle structured format: "url: https://..." from YAML dicts
        if url.startswith("url:"):
            url = url[4:].strip()
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


def check_index_sync(kb_root: Path, *, knowledge_dir_name: str = "docs") -> list[dict]:
    """Check that index.md lists all topic files that exist on disk.

    Warns when:
    - index.md is missing entirely
    - A topic file exists on disk but is not referenced in index.md
    """
    issues: list[dict] = []
    knowledge_dir = kb_root / knowledge_dir_name
    index_path = knowledge_dir / "index.md"

    if not index_path.exists():
        issues.append({
            "file": str(index_path),
            "message": "Missing index.md — run scaffold --rebuild-index to generate",
            "severity": "warn",
        })
        return issues

    index_text = index_path.read_text()

    # Collect all topic .md files on disk (excluding overview, ref, proposals, index)
    for child in sorted(knowledge_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_"):
            continue
        for md_file in sorted(child.glob("*.md")):
            if md_file.name == "overview.md":
                continue
            if md_file.name.endswith(".ref.md"):
                continue
            # Check if this file is referenced in index.md
            relative_ref = f"{child.name}/{md_file.name}"
            if relative_ref not in index_text:
                issues.append({
                    "file": str(md_file),
                    "message": f"Topic not in index.md: {relative_ref} — run scaffold --rebuild-index",
                    "severity": "warn",
                })

    return issues


def check_inventory_regression(kb_root: Path, current_files: list[str]) -> list[dict]:
    """Warn when files from the last health snapshot are missing.

    Compares *current_files* (relative paths like ``area/topic.md``)
    against the ``file_list`` recorded in the most recent history
    snapshot.  Returns a warning for each file that was present
    previously but is absent now.
    """
    from history import read_history

    issues: list[dict] = []
    history = read_history(kb_root, limit=1)
    if not history:
        return issues

    last_snapshot = history[-1]
    last_files = set(last_snapshot.get("file_list", []))
    current_set = set(current_files)

    for missing in sorted(last_files - current_set):
        issues.append({
            "file": missing,
            "message": f"File was present in last health check but is now missing: {missing}",
            "severity": "warn",
        })

    return issues


# ------------------------------------------------------------------
# Content quality validators
# ------------------------------------------------------------------


def check_section_completeness(file_path: Path) -> list[dict]:
    """Check that depth-appropriate sections are present."""
    issues: list[dict] = []
    name = str(file_path)
    fm = parse_frontmatter(file_path)
    depth = fm.get("depth")

    if depth == "working":
        expected = _WORKING_SECTIONS
    elif depth == "overview":
        expected = _OVERVIEW_SECTIONS
    elif depth == "reference":
        # Reference files just need a non-empty body
        text = file_path.read_text()
        body = _body_without_frontmatter(text).strip()
        if not body:
            issues.append({
                "file": name,
                "message": "Reference file has no content after frontmatter",
                "severity": "warn",
            })
        return issues
    else:
        return issues

    text = file_path.read_text()
    headings = re.findall(r"^##\s+(.+)$", text, re.MULTILINE)
    heading_lower = [h.lower() for h in headings]

    for section in expected:
        if not any(section.lower() in h for h in heading_lower):
            issues.append({
                "file": name,
                "message": f"Missing required section: {section}",
                "severity": "warn",
            })

    return issues


def check_heading_hierarchy(file_path: Path) -> list[dict]:
    """Check heading structure: exactly one H1, no skipped levels."""
    issues: list[dict] = []
    name = str(file_path)
    text = file_path.read_text()
    body = _body_without_frontmatter(text)
    body = _strip_fenced_code_blocks(body)

    # Extract heading levels from lines starting with #
    levels: list[int] = []
    for line in body.split("\n"):
        match = re.match(r"^(#{1,6})\s+", line)
        if match:
            levels.append(len(match.group(1)))

    h1_count = levels.count(1)
    if h1_count == 0:
        issues.append({
            "file": name,
            "message": "No H1 heading found",
            "severity": "warn",
        })
    elif h1_count > 1:
        issues.append({
            "file": name,
            "message": f"Multiple H1 headings found ({h1_count}); expected exactly 1",
            "severity": "warn",
        })

    # Check for skipped levels (e.g. H1 -> H3 without H2)
    for i in range(1, len(levels)):
        if levels[i] > levels[i - 1] + 1:
            issues.append({
                "file": name,
                "message": f"Skipped heading level: H{levels[i - 1]} to H{levels[i]}",
                "severity": "warn",
            })

    return issues


def check_go_deeper_links(file_path: Path) -> list[dict]:
    """Check that Go Deeper section links to companion ref and external sources."""
    issues: list[dict] = []
    name = str(file_path)

    # Only check working-depth files that are not reference files
    if file_path.name.endswith(".ref.md"):
        return issues

    fm = parse_frontmatter(file_path)
    if fm.get("depth") != "working":
        return issues

    text = file_path.read_text()
    body = _body_without_frontmatter(text)
    section = _extract_section(body, "Go Deeper")

    # Skip silently if section missing (covered by check_section_completeness)
    if section is None:
        return issues

    # Check for companion .ref.md link
    stem = file_path.stem  # e.g. "bidding" from "bidding.md"
    ref_name = f"{stem}.ref.md"
    if ref_name not in section:
        issues.append({
            "file": name,
            "message": f"Go Deeper section missing link to companion {ref_name}",
            "severity": "warn",
        })

    # Check for external link
    if not re.search(r"https?://", section):
        issues.append({
            "file": name,
            "message": "Go Deeper section missing external link",
            "severity": "warn",
        })

    return issues


def check_ref_see_also(file_path: Path) -> list[dict]:
    """Check that .ref.md files have a See Also linking to companion."""
    issues: list[dict] = []
    name = str(file_path)

    if not file_path.name.endswith(".ref.md"):
        return issues

    text = file_path.read_text()
    body = _body_without_frontmatter(text)

    # Check for "see also" text (case-insensitive)
    see_also_match = re.search(r"see\s+also", body, re.IGNORECASE)
    if not see_also_match:
        issues.append({
            "file": name,
            "message": "Reference file missing 'See also' section",
            "severity": "warn",
        })
        return issues

    # Check that see-also references the companion working file
    # e.g. "bidding.ref.md" should link to "bidding.md"
    stem = file_path.name[: -len(".ref.md")]  # "bidding" from "bidding.ref.md"
    companion = f"{stem}.md"
    if companion not in body:
        issues.append({
            "file": name,
            "message": f"See also section missing link to companion {companion}",
            "severity": "warn",
        })

    return issues


# ------------------------------------------------------------------
# Readability validator
# ------------------------------------------------------------------

_FK_GRADE_BOUNDS: dict[str, tuple[int, int]] = {
    "overview": (8, 14),
    "working": (10, 16),
}


def _count_syllables(word: str) -> int:
    """Count syllables via vowel-group heuristic.

    Strip trailing 'e', count contiguous vowel sequences ``[aeiouy]+``,
    minimum 1 syllable per word.
    """
    w = word.lower().strip()
    if not w:
        return 1
    # Strip trailing 'e' (silent e)
    if len(w) > 2 and w.endswith("e"):
        w = w[:-1]
    count = len(re.findall(r"[aeiouy]+", w))
    return max(count, 1)


def _strip_markdown_formatting(text: str) -> str:
    """Remove markdown inline formatting, keeping plain text.

    Handles images, links, bold, italic, and inline code.
    """
    # Images: ![alt](url) -> ''
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    # Links: [text](url) -> text
    text = re.sub(r"\[([^\]]*)\]\([^)]+\)", r"\1", text)
    # Bold: **text** or __text__ -> text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    # Italic: *text* or _text_ -> text
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", text)
    # Inline code: `code` -> code
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text


def _flesch_kincaid_grade(text: str) -> float | None:
    """Compute Flesch-Kincaid grade level.

    Returns None if fewer than 3 sentences (too little text to score).
    """
    # Split into sentences on . ! ?
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) < 3:
        return None

    words: list[str] = []
    for sentence in sentences:
        words.extend(re.findall(r"[a-zA-Z]+", sentence))

    if not words:
        return None

    total_syllables = sum(_count_syllables(w) for w in words)
    num_words = len(words)
    num_sentences = len(sentences)

    grade = 0.39 * (num_words / num_sentences) + 11.8 * (total_syllables / num_words) - 15.59
    return grade


def check_readability(file_path: Path) -> list[dict]:
    """Check Flesch-Kincaid grade level is within bounds for the content depth."""
    issues: list[dict] = []
    name = str(file_path)
    fm = parse_frontmatter(file_path)
    depth = fm.get("depth")

    # Skip reference files (terse by design)
    if depth not in _FK_GRADE_BOUNDS:
        return issues

    text = file_path.read_text()
    body = _body_without_frontmatter(text)
    body = _strip_fenced_code_blocks(body)
    body = _strip_markdown_formatting(body)

    grade = _flesch_kincaid_grade(body)
    if grade is None:
        return issues

    lo, hi = _FK_GRADE_BOUNDS[depth]
    if grade < lo:
        issues.append({
            "file": name,
            "message": f"Readability grade {grade:.1f} below {lo} for depth '{depth}' — may be too simplistic",
            "severity": "warn",
        })
    elif grade > hi:
        issues.append({
            "file": name,
            "message": f"Readability grade {grade:.1f} above {hi} for depth '{depth}' — may be too complex",
            "severity": "warn",
        })

    return issues
