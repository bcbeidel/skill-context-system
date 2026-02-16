"""Auto-fix for common knowledge-base issues.

Provides conservative, deterministic fixes for the two most common
fixable issues found by Tier 1 validators:

1. Missing required sections — inserts stub headings with TODO comments
2. Missing cross-links — adds companion links between working and ref files

Only stdlib is used.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Ensure validators is importable (same directory).
_scripts_dir = str(Path(__file__).resolve().parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from validators import (
    _OVERVIEW_SECTIONS,
    _WORKING_SECTIONS,
    _body_without_frontmatter,
    _extract_section,
    parse_frontmatter,
)


def fix_missing_sections(file_path: Path, issues: list[dict]) -> list[dict]:
    """Insert stub headings for missing required sections.

    Filters *issues* to "Missing required section" for *file_path*,
    then inserts ``## Name\\n\\n<!-- TODO: Add content -->\\n`` at the
    canonical position for each missing section.

    Returns a list of action dicts describing what was inserted.
    """
    name = str(file_path)
    relevant = [
        i for i in issues
        if i.get("file") == name and "Missing required section" in i.get("message", "")
    ]
    if not relevant:
        return []

    fm = parse_frontmatter(file_path)
    depth = fm.get("depth")

    if depth == "working":
        canonical_order = _WORKING_SECTIONS
    elif depth == "overview":
        canonical_order = _OVERVIEW_SECTIONS
    else:
        return []

    missing_names = set()
    for issue in relevant:
        # Extract section name from message "Missing required section: Name"
        msg = issue["message"]
        prefix = "Missing required section: "
        if prefix in msg:
            missing_names.add(msg[len(prefix):])

    if not missing_names:
        return []

    text = file_path.read_text()
    lines = text.split("\n")

    # Build a map of existing section positions (by canonical name)
    section_positions: dict[str, int] = {}
    for idx, line in enumerate(lines):
        if line.startswith("## "):
            heading_text = line[3:].strip()
            for section in canonical_order:
                if section.lower() in heading_text.lower():
                    section_positions[section] = idx
                    break

    actions: list[dict] = []
    offset = 0

    for section in canonical_order:
        if section not in missing_names:
            continue

        stub = [f"## {section}", "", f"<!-- TODO: Add content -->", ""]

        # Find insertion point: after the last existing section that comes
        # before this one in canonical order, or after H1/frontmatter.
        insert_after = None
        for prev_section in canonical_order:
            if prev_section == section:
                break
            adjusted_pos = section_positions.get(prev_section)
            if adjusted_pos is not None:
                insert_after = adjusted_pos + offset

        if insert_after is not None:
            # Find the end of the previous section (next ## or EOF)
            search_start = insert_after + 1
            insert_at = len(lines)
            for j in range(search_start, len(lines)):
                if lines[j].startswith("## "):
                    insert_at = j
                    break
        else:
            # No prior section found — insert after first blank line after H1
            insert_at = len(lines)
            for j, line in enumerate(lines):
                if line.startswith("# ") and not line.startswith("## "):
                    # Find next blank line after H1
                    for k in range(j + 1, len(lines)):
                        if lines[k].strip() == "":
                            insert_at = k + 1
                            break
                    else:
                        insert_at = j + 1
                    break

        # Insert the stub
        for s_idx, stub_line in enumerate(stub):
            lines.insert(insert_at + s_idx, stub_line)
        offset += len(stub)

        # Update positions for sections after this one
        for s_name in section_positions:
            if section_positions[s_name] >= insert_at - offset + len(stub):
                section_positions[s_name] += len(stub)
        section_positions[section] = insert_at

        actions.append({
            "file": name,
            "action": "inserted_stub_section",
            "section": section,
        })

    if actions:
        file_path.write_text("\n".join(lines))

    return actions


def fix_missing_cross_links(file_path: Path, issues: list[dict]) -> list[dict]:
    """Add missing cross-links between companion files.

    For ``.ref.md`` files: appends ``**See also:** [Name](companion.md)``
    (only if companion exists on disk).

    For working files: inserts ref link in Go Deeper section
    (only if ref file exists on disk).

    Returns a list of action dicts describing what was changed.
    """
    name = str(file_path)
    relevant = [
        i for i in issues
        if i.get("file") == name and (
            "See also" in i.get("message", "")
            or "Go Deeper" in i.get("message", "")
        )
    ]
    if not relevant:
        return []

    actions: list[dict] = []
    text = file_path.read_text()

    if file_path.name.endswith(".ref.md"):
        # Check for missing "See also" linking to companion
        see_also_issues = [
            i for i in relevant
            if "See also" in i.get("message", "") or "see also" in i.get("message", "").lower()
        ]
        if see_also_issues:
            stem = file_path.name[: -len(".ref.md")]
            companion = file_path.parent / f"{stem}.md"
            if companion.exists():
                # Determine display name from stem
                display_name = stem.replace("-", " ").title()
                link_line = f"\n**See also:** [{display_name}]({stem}.md)\n"
                text = text.rstrip() + "\n" + link_line
                file_path.write_text(text)
                actions.append({
                    "file": name,
                    "action": "appended_see_also",
                    "detail": f"Added See also link to {stem}.md",
                })
    else:
        # Working file — check for missing ref link in Go Deeper
        go_deeper_issues = [
            i for i in relevant
            if "Go Deeper" in i.get("message", "") and "ref.md" in i.get("message", "")
        ]
        if go_deeper_issues:
            stem = file_path.stem
            ref_file = file_path.parent / f"{stem}.ref.md"
            if ref_file.exists():
                display_name = stem.replace("-", " ").title()
                ref_link = f"- [{display_name} Reference]({stem}.ref.md) -- quick-lookup version"
                body = _body_without_frontmatter(text)
                section = _extract_section(body, "Go Deeper")
                if section is not None:
                    # Insert after the Go Deeper heading
                    lines = text.split("\n")
                    for idx, line in enumerate(lines):
                        if line.startswith("## ") and "go deeper" in line.lower():
                            lines.insert(idx + 1, ref_link)
                            text = "\n".join(lines)
                            file_path.write_text(text)
                            actions.append({
                                "file": name,
                                "action": "inserted_ref_link",
                                "detail": f"Added link to {stem}.ref.md in Go Deeper",
                            })
                            break

    return actions


def fix_curation_plan_checkmarks(knowledge_base_root: Path, *, knowledge_dir_name: str = "docs") -> list[dict]:
    """Check off curation plan items when matching files exist on disk.

    For each ``[ ]`` item in the curation plan, if the corresponding
    topic file exists at ``<knowledge_dir>/<area>/<slugify(name)>.md``,
    replace ``- [ ]`` with ``- [x]``.

    Returns a list of action dicts describing what was changed.
    """
    from cross_validators import _parse_curation_plan
    from templates import _slugify

    plan_path = knowledge_base_root / ".dewey" / "curation-plan.md"
    if not plan_path.exists():
        return []

    knowledge_dir = knowledge_base_root / knowledge_dir_name
    plan_text = plan_path.read_text()
    items = _parse_curation_plan(plan_text)

    if not items:
        return []

    actions: list[dict] = []
    lines = plan_text.split("\n")
    modified = False

    for item in items:
        if item["checked"]:
            continue

        area = item["area"]
        name = item["name"]
        slug = _slugify(name)
        topic_path = knowledge_dir / area / f"{slug}.md"

        if topic_path.exists():
            # Find and replace the line
            for idx, line in enumerate(lines):
                # Match "- [ ] Name" (with possible trailing -- content)
                if re.match(r"^-\s+\[ \]\s+" + re.escape(name), line):
                    lines[idx] = line.replace("- [ ]", "- [x]", 1)
                    modified = True
                    actions.append({
                        "file": str(plan_path),
                        "action": "checked_plan_item",
                        "detail": f"Checked off '{name}' — file exists: {area}/{slug}.md",
                    })
                    break

    if modified:
        plan_path.write_text("\n".join(lines))

    return actions


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Auto-fix common knowledge-base issues."
    )
    parser.add_argument("file", help="Path to the markdown file to fix.")
    parser.add_argument(
        "--issues-json",
        required=True,
        help="JSON string of issues list for this file.",
    )
    args = parser.parse_args()

    file_path = Path(args.file)
    issues = json.loads(args.issues_json)

    all_actions: list[dict] = []
    all_actions.extend(fix_missing_sections(file_path, issues))
    all_actions.extend(fix_missing_cross_links(file_path, issues))
    print(json.dumps(all_actions, indent=2))
