"""Cross-file consistency validators for knowledge-base health checks.

Operates on the KB as a whole rather than individual files.  Checks
manifest sync (AGENTS.md / CLAUDE.md), curation plan sync, proposal
integrity, and the internal link graph.

Every validator returns ``list[dict]`` with
``{"file": str, "message": str, "severity": "warn"}``.

Only stdlib is used.
"""

from __future__ import annotations

import hashlib
import re
import sys
from datetime import date
from pathlib import Path

# ------------------------------------------------------------------
# Cross-skill imports (templates.py lives in curate/scripts/)
# ------------------------------------------------------------------
_curate_scripts = str(Path(__file__).resolve().parent.parent.parent / "curate" / "scripts")
if _curate_scripts not in sys.path:
    sys.path.insert(0, _curate_scripts)

from templates import MARKER_BEGIN, MARKER_END, _slugify

# Same-dir imports
_scripts_dir = str(Path(__file__).resolve().parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from validators import (
    _WORKING_SECTIONS,
    _body_without_frontmatter,
    _strip_fenced_code_blocks,
    parse_frontmatter,
)


# ------------------------------------------------------------------
# Shared private helpers
# ------------------------------------------------------------------

def _discover_areas_and_topics(kb_root: Path, knowledge_dir_name: str = "docs") -> dict[str, list[Path]]:
    """Scan filesystem for area dirs -> topic files.

    Returns ``{"area-slug": [Path, ...]}`` where each path is a ``.md``
    file inside that area dir (excluding ``overview.md``, ``.ref.md``,
    and ``index.md``).
    """
    knowledge_dir = kb_root / knowledge_dir_name
    if not knowledge_dir.is_dir():
        return {}

    areas: dict[str, list[Path]] = {}
    for child in sorted(knowledge_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_") or child.name.startswith("."):
            continue
        topics: list[Path] = []
        for md_file in sorted(child.glob("*.md")):
            if md_file.name == "overview.md":
                continue
            if md_file.name.endswith(".ref.md"):
                continue
            if md_file.name == "index.md":
                continue
            topics.append(md_file)
        areas[child.name] = topics
    return areas


def _managed_section(text: str) -> str | None:
    """Extract text between MARKER_BEGIN and MARKER_END, or None."""
    begin = text.find(MARKER_BEGIN)
    end = text.find(MARKER_END)
    if begin == -1 or end == -1 or end <= begin:
        return None
    return text[begin + len(MARKER_BEGIN):end]


# ------------------------------------------------------------------
# AGENTS.md parser
# ------------------------------------------------------------------

def _parse_agents_managed(text: str) -> dict[str, list[dict]]:
    """Extract area headings and topic table rows from AGENTS.md managed section.

    Returns ``{"Area Name": [{"name": str, "path": str}, ...]}``
    """
    section = _managed_section(text)
    if section is None:
        return {}

    areas: dict[str, list[dict]] = {}
    current_area: str | None = None

    for line in section.split("\n"):
        # ### Area Name
        heading_match = re.match(r"^###\s+(.+)$", line)
        if heading_match:
            current_area = heading_match.group(1).strip()
            areas[current_area] = []
            continue

        # | [Topic Name](path) | description |
        if current_area is not None and line.startswith("|"):
            link_match = re.search(r"\[([^\]]+)\]\(([^)]+)\)", line)
            if link_match:
                areas[current_area].append({
                    "name": link_match.group(1),
                    "path": link_match.group(2),
                })

    return areas


# ------------------------------------------------------------------
# CLAUDE.md parser
# ------------------------------------------------------------------

def _parse_claude_managed(text: str) -> list[dict]:
    """Extract Domain Areas table entries from CLAUDE.md managed section.

    Returns ``[{"name": str, "path": str, "overview": str}, ...]``
    """
    section = _managed_section(text)
    if section is None:
        return []

    entries: list[dict] = []
    in_domain_table = False

    for line in section.split("\n"):
        # Detect "### Domain Areas" heading
        if re.match(r"^###\s+Domain Areas", line):
            in_domain_table = True
            continue

        # Stop at next heading
        if in_domain_table and re.match(r"^#{1,3}\s+", line) and "Domain Areas" not in line:
            break

        if not in_domain_table:
            continue

        if not line.startswith("|"):
            continue
        if "---" in line:
            continue

        # | Area Name | `docs/area-slug/` | [overview.md](docs/area-slug/overview.md) |
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]  # remove empty from leading/trailing |
        if len(cells) < 3:
            continue
        # Skip the header row "| Area | Path | Overview |"
        if cells[0] == "Area":
            continue

        name = cells[0]
        path = cells[1].strip("`")
        overview_match = re.search(r"\[([^\]]*)\]\(([^)]+)\)", cells[2])
        overview = overview_match.group(2) if overview_match else ""
        entries.append({"name": name, "path": path, "overview": overview})

    return entries


# ------------------------------------------------------------------
# Curation plan parser
# ------------------------------------------------------------------

def _parse_curation_plan(text: str) -> list[dict]:
    """Parse curation plan checkboxes.

    Returns ``[{"area": str, "name": str, "checked": bool}, ...]``
    """
    items: list[dict] = []
    current_area: str | None = None

    for line in text.split("\n"):
        # ## area-slug
        heading_match = re.match(r"^##\s+(.+)$", line)
        if heading_match:
            current_area = heading_match.group(1).strip()
            continue

        if current_area is None:
            continue

        # - [x] Topic Name -- relevance -- rationale
        # - [ ] Topic Name -- relevance
        check_match = re.match(r"^-\s+\[([ xX])\]\s+(.+?)(?:\s+--\s+.*)?$", line)
        if check_match:
            checked = check_match.group(1).lower() == "x"
            name = check_match.group(2).strip()
            items.append({
                "area": current_area,
                "name": name,
                "checked": checked,
            })

    return items


# ------------------------------------------------------------------
# Validators
# ------------------------------------------------------------------

def check_manifest_sync(kb_root: Path, *, knowledge_dir_name: str = "docs") -> list[dict]:
    """Check AGENTS.md and CLAUDE.md are in sync with files on disk."""
    issues: list[dict] = []
    areas_on_disk = _discover_areas_and_topics(kb_root, knowledge_dir_name)

    # --- AGENTS.md ---
    agents_path = kb_root / "AGENTS.md"
    if agents_path.exists():
        agents_text = agents_path.read_text()
        has_managed = _managed_section(agents_text) is not None
        agents_areas = _parse_agents_managed(agents_text)

        if has_managed:  # has markers — check sync
            # Areas on disk not in AGENTS.md
            agents_area_names_lower = {n.lower(): n for n in agents_areas}
            for area_slug in sorted(areas_on_disk):
                # Match by slug or name
                found = False
                for agents_name in agents_areas:
                    if _slugify(agents_name) == area_slug or agents_name.lower() == area_slug:
                        found = True
                        break
                if not found:
                    issues.append({
                        "file": str(agents_path),
                        "message": f"Area '{area_slug}' on disk not listed in AGENTS.md",
                        "severity": "warn",
                    })

            # Topics on disk not in AGENTS.md
            for area_slug, topic_files in sorted(areas_on_disk.items()):
                # Find matching agents area
                matched_area = None
                for agents_name in agents_areas:
                    if _slugify(agents_name) == area_slug or agents_name.lower() == area_slug:
                        matched_area = agents_name
                        break
                if matched_area is None:
                    continue  # already warned about missing area

                agents_topic_paths = {e["path"] for e in agents_areas[matched_area]}
                for topic_file in topic_files:
                    rel_path = f"{knowledge_dir_name}/{area_slug}/{topic_file.name}"
                    if rel_path not in agents_topic_paths:
                        issues.append({
                            "file": str(topic_file),
                            "message": f"Topic not listed in AGENTS.md: {rel_path}",
                            "severity": "warn",
                        })

            # AGENTS.md entries referencing nonexistent files
            for area_name, entries in agents_areas.items():
                for entry in entries:
                    ref_path = kb_root / entry["path"]
                    if not ref_path.exists():
                        issues.append({
                            "file": str(agents_path),
                            "message": f"AGENTS.md references nonexistent file: {entry['path']}",
                            "severity": "warn",
                        })

    # --- CLAUDE.md ---
    claude_path = kb_root / "CLAUDE.md"
    if claude_path.exists():
        claude_text = claude_path.read_text()
        has_claude_managed = _managed_section(claude_text) is not None
        claude_entries = _parse_claude_managed(claude_text)

        if has_claude_managed:  # has markers — check sync
            claude_dir_slugs = set()
            for entry in claude_entries:
                # path is like "docs/area-slug/" — extract slug
                parts = entry["path"].strip("/").split("/")
                if len(parts) >= 2:
                    claude_dir_slugs.add(parts[1])

            # Areas on disk not in CLAUDE.md
            for area_slug in sorted(areas_on_disk):
                if area_slug not in claude_dir_slugs:
                    issues.append({
                        "file": str(claude_path),
                        "message": f"Area '{area_slug}' on disk not listed in CLAUDE.md",
                        "severity": "warn",
                    })

            # CLAUDE.md entries referencing nonexistent dirs/overviews
            for entry in claude_entries:
                dir_path = kb_root / entry["path"].strip("/")
                if not dir_path.is_dir():
                    issues.append({
                        "file": str(claude_path),
                        "message": f"CLAUDE.md references nonexistent directory: {entry['path']}",
                        "severity": "warn",
                    })
                if entry.get("overview"):
                    overview_path = kb_root / entry["overview"]
                    if not overview_path.exists():
                        issues.append({
                            "file": str(claude_path),
                            "message": f"CLAUDE.md references nonexistent overview: {entry['overview']}",
                            "severity": "warn",
                        })

    return issues


def check_curation_plan_sync(kb_root: Path, *, knowledge_dir_name: str = "docs") -> list[dict]:
    """Check curation plan checkboxes match files on disk."""
    issues: list[dict] = []
    plan_path = kb_root / ".dewey" / "curation-plan.md"

    if not plan_path.exists():
        return issues

    plan_text = plan_path.read_text()
    items = _parse_curation_plan(plan_text)

    if not items:
        return issues

    knowledge_dir = kb_root / knowledge_dir_name

    # Build set of topic files on disk (area/slug.md)
    areas_on_disk = _discover_areas_and_topics(kb_root, knowledge_dir_name)
    disk_files: set[str] = set()
    for area_slug, topic_files in areas_on_disk.items():
        for tf in topic_files:
            disk_files.add(f"{area_slug}/{tf.name}")

    plan_topics: set[str] = set()

    for item in items:
        area = item["area"]
        name = item["name"]
        slug = _slugify(name)
        rel = f"{area}/{slug}.md"
        plan_topics.add(rel)

        file_exists = (knowledge_dir / area / f"{slug}.md").exists()

        if item["checked"] and not file_exists:
            issues.append({
                "file": str(plan_path),
                "message": f"Plan item '{name}' is checked but file not found: {rel}",
                "severity": "warn",
            })
        elif not item["checked"] and file_exists:
            issues.append({
                "file": str(plan_path),
                "message": f"Plan item '{name}' should be checked off — file exists: {rel}",
                "severity": "warn",
            })

    # Topics on disk not in plan
    for area_slug, topic_files in sorted(areas_on_disk.items()):
        for tf in topic_files:
            rel = f"{area_slug}/{tf.name}"
            if rel not in plan_topics:
                issues.append({
                    "file": str(tf),
                    "message": f"Topic on disk not in curation plan: {rel}",
                    "severity": "warn",
                })

    return issues


def check_proposal_integrity(
    kb_root: Path,
    *,
    knowledge_dir_name: str = "docs",
    max_age_days: int = 60,
) -> list[dict]:
    """Validate proposal files in _proposals/ directory."""
    issues: list[dict] = []
    proposals_dir = kb_root / knowledge_dir_name / "_proposals"

    if not proposals_dir.is_dir():
        return issues

    proposal_files = sorted(proposals_dir.glob("*.md"))
    if not proposal_files:
        return issues

    for pf in proposal_files:
        name = str(pf)
        fm = parse_frontmatter(pf)

        if fm.get("status") != "proposal":
            issues.append({
                "file": name,
                "message": "Proposal missing 'status: proposal' in frontmatter",
                "severity": "warn",
            })

        if not fm.get("proposed_by"):
            issues.append({
                "file": name,
                "message": "Proposal missing 'proposed_by' field",
                "severity": "warn",
            })

        if not fm.get("rationale"):
            issues.append({
                "file": name,
                "message": "Proposal missing 'rationale' field",
                "severity": "warn",
            })

        # Freshness check
        last_validated = fm.get("last_validated")
        if last_validated:
            try:
                validated_date = date.fromisoformat(str(last_validated))
                age = (date.today() - validated_date).days
                if age > max_age_days:
                    issues.append({
                        "file": name,
                        "message": f"Stale proposal: {age} days old (max {max_age_days})",
                        "severity": "warn",
                    })
            except ValueError:
                pass

        # Check for required working sections
        text = pf.read_text()
        body = _body_without_frontmatter(text)
        headings = re.findall(r"^##\s+(.+)$", body, re.MULTILINE)
        heading_lower = [h.lower() for h in headings]

        for section in _WORKING_SECTIONS:
            if not any(section.lower() in h for h in heading_lower):
                issues.append({
                    "file": name,
                    "message": f"Proposal missing required section: {section}",
                    "severity": "warn",
                })

    return issues


def check_link_graph(kb_root: Path, *, knowledge_dir_name: str = "docs") -> list[dict]:
    """Check for orphaned files and overview completeness."""
    issues: list[dict] = []
    knowledge_dir = kb_root / knowledge_dir_name

    if not knowledge_dir.is_dir():
        return issues

    # Collect all .md files (excluding _proposals, index.md)
    all_files: list[Path] = []
    for md_file in sorted(knowledge_dir.rglob("*.md")):
        parts = md_file.relative_to(knowledge_dir).parts
        if any(part.startswith("_") for part in parts):
            continue
        if md_file.name == "index.md":
            continue
        all_files.append(md_file)

    if not all_files:
        return issues

    # Entry points — never orphans
    entry_names = {"overview.md", "index.md"}

    # Build directed link graph: file -> set of files it links to
    linked_from: dict[str, set[str]] = {}  # target -> set of sources
    for md_file in all_files:
        text = md_file.read_text()
        links = re.findall(r"\[([^\]]*)\]\(([^)]+)\)", text)
        for _link_text, target in links:
            target = target.strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target_path = target.split("#")[0]
            if not target_path:
                continue
            resolved = (md_file.parent / target_path).resolve()
            if resolved.exists():
                resolved_key = str(resolved)
                if resolved_key not in linked_from:
                    linked_from[resolved_key] = set()
                linked_from[resolved_key].add(str(md_file))

    # Orphan detection
    for md_file in all_files:
        if md_file.name in entry_names:
            continue
        file_key = str(md_file.resolve())
        if file_key not in linked_from:
            rel = str(md_file.relative_to(knowledge_dir))
            issues.append({
                "file": str(md_file),
                "message": f"Orphaned file — not linked from any other file: {rel}",
                "severity": "warn",
            })

    # Overview completeness: each overview.md's "How It's Organized" should
    # link to all topic files in that area directory
    for area_dir in sorted(knowledge_dir.iterdir()):
        if not area_dir.is_dir():
            continue
        if area_dir.name.startswith("_") or area_dir.name.startswith("."):
            continue

        overview = area_dir / "overview.md"
        if not overview.exists():
            continue

        # Get topic files in this area (not overview, not .ref.md)
        topic_files = set()
        for md_file in sorted(area_dir.glob("*.md")):
            if md_file.name == "overview.md":
                continue
            if md_file.name.endswith(".ref.md"):
                continue
            if md_file.name == "index.md":
                continue
            topic_files.add(md_file.name)

        if not topic_files:
            continue

        # Parse overview's "How It's Organized" section
        text = overview.read_text()
        body = _body_without_frontmatter(text)

        # Find "How It's Organized" section
        lines = body.split("\n")
        capturing = False
        section_text = ""
        for line in lines:
            if line.startswith("## "):
                if capturing:
                    break
                if "how it" in line.lower() and "organized" in line.lower():
                    capturing = True
                    continue
            elif capturing:
                section_text += line + "\n"

        if not section_text:
            continue

        # Extract linked filenames from the section
        linked_files = set()
        for _text, target in re.findall(r"\[([^\]]*)\]\(([^)]+)\)", section_text):
            target = target.strip().split("#")[0]
            if target and not target.startswith(("http://", "https://")):
                linked_files.add(target)

        # Check each topic file is linked
        for topic_name in sorted(topic_files):
            if topic_name not in linked_files:
                issues.append({
                    "file": str(overview),
                    "message": f"Topic '{topic_name}' not listed in overview's How It's Organized section",
                    "severity": "warn",
                })

    return issues


# ------------------------------------------------------------------
# Duplicate content detection
# ------------------------------------------------------------------

def _extract_paragraphs(text: str) -> list[str]:
    """Split on double newlines, strip whitespace, filter to 40+ chars."""
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if len(p.strip()) >= 40]


def _word_shingles(text: str, n: int = 5) -> set[tuple]:
    """Create n-gram tuples as sliding window over words."""
    words = re.findall(r"[a-z]+", text.lower())
    if len(words) < n:
        return set()
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def _jaccard(a: set, b: set) -> float:
    """Jaccard similarity: |a & b| / |a | b|."""
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _is_companion_pair(path_a: Path, path_b: Path) -> bool:
    """Check if two paths are a working/ref companion pair in the same dir."""
    if path_a.parent != path_b.parent:
        return False
    a_name, b_name = path_a.name, path_b.name
    # Check <stem>.md vs <stem>.ref.md
    if a_name.endswith(".ref.md"):
        return b_name == a_name[: -len(".ref.md")] + ".md"
    if b_name.endswith(".ref.md"):
        return a_name == b_name[: -len(".ref.md")] + ".md"
    return False


def check_duplicate_content(
    kb_root: Path,
    *,
    knowledge_dir_name: str = "docs",
    similarity_threshold: float = 0.4,
) -> list[dict]:
    """Detect duplicate paragraphs and high similarity between files."""
    issues: list[dict] = []
    knowledge_dir = kb_root / knowledge_dir_name

    if not knowledge_dir.is_dir():
        return issues

    # Collect all .md files (areas + overviews)
    all_files: list[Path] = []
    for child in sorted(knowledge_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_") or child.name.startswith("."):
            continue
        for md_file in sorted(child.glob("*.md")):
            if md_file.name == "index.md":
                continue
            all_files.append(md_file)

    if len(all_files) < 2:
        return issues

    # Read and process each file
    file_data: dict[Path, dict] = {}
    for f in all_files:
        text = f.read_text()
        body = _body_without_frontmatter(text)
        body = _strip_fenced_code_blocks(body)
        paragraphs = _extract_paragraphs(body)
        shingles = _word_shingles(body)
        file_data[f] = {
            "paragraphs": paragraphs,
            "shingles": shingles,
        }

    # Pass 1 — exact paragraph duplicates
    para_hash_map: dict[str, list[Path]] = {}
    for f, data in file_data.items():
        for para in data["paragraphs"]:
            h = hashlib.md5(para.encode()).hexdigest()
            if h not in para_hash_map:
                para_hash_map[h] = []
            para_hash_map[h].append(f)

    reported_para_pairs: set[tuple] = set()
    for h, files in para_hash_map.items():
        unique_files = sorted(set(files), key=lambda p: str(p))
        if len(unique_files) < 2:
            continue
        for i in range(len(unique_files)):
            for j in range(i + 1, len(unique_files)):
                pair = (str(unique_files[i]), str(unique_files[j]))
                if pair not in reported_para_pairs:
                    reported_para_pairs.add(pair)
                    rel_a = str(unique_files[i].relative_to(knowledge_dir))
                    rel_b = str(unique_files[j].relative_to(knowledge_dir))
                    issues.append({
                        "file": str(unique_files[i]),
                        "message": f"Exact duplicate paragraph found in {rel_a} and {rel_b}",
                        "severity": "warn",
                    })

    # Pass 2 — cross-file Jaccard similarity
    for i in range(len(all_files)):
        for j in range(i + 1, len(all_files)):
            a, b = all_files[i], all_files[j]
            if _is_companion_pair(a, b):
                continue
            shingles_a = file_data[a]["shingles"]
            shingles_b = file_data[b]["shingles"]
            if not shingles_a or not shingles_b:
                continue
            sim = _jaccard(shingles_a, shingles_b)
            if sim > similarity_threshold:
                rel_a = str(a.relative_to(knowledge_dir))
                rel_b = str(b.relative_to(knowledge_dir))
                issues.append({
                    "file": str(a),
                    "message": (
                        f"High similarity ({sim:.0%}) between {rel_a} and {rel_b}"
                        " — consider deduplicating"
                    ),
                    "severity": "warn",
                })

    return issues


# ------------------------------------------------------------------
# Naming conventions
# ------------------------------------------------------------------

def check_naming_conventions(
    kb_root: Path,
    *,
    knowledge_dir_name: str = "docs",
) -> list[dict]:
    """Check that file and directory names follow slug conventions."""
    issues: list[dict] = []
    knowledge_dir = kb_root / knowledge_dir_name

    if not knowledge_dir.is_dir():
        return issues

    exempt_filenames = {"overview.md", "index.md"}

    for child in sorted(knowledge_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_") or child.name.startswith("."):
            continue

        # Check area directory name
        if child.name != _slugify(child.name):
            issues.append({
                "file": str(child),
                "message": f"Area directory '{child.name}' doesn't follow naming conventions — expected '{_slugify(child.name)}'",
                "severity": "warn",
            })

        # Check files within area
        for md_file in sorted(child.glob("*.md")):
            if md_file.name in exempt_filenames:
                continue

            # For .ref.md files, check the stem before .ref.md
            if md_file.name.endswith(".ref.md"):
                stem = md_file.name[: -len(".ref.md")]
            else:
                stem = md_file.stem

            if stem != _slugify(stem):
                issues.append({
                    "file": str(md_file),
                    "message": f"Filename '{md_file.name}' doesn't follow naming conventions — expected '{_slugify(stem)}'",
                    "severity": "warn",
                })

    return issues
