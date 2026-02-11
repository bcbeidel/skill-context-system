#!/usr/bin/env python3
"""Skill-based intelligent file splitting.

This module provides file splitting that uses Claude Code's native skill system,
eliminating the need for separate API keys.
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Import from local module
from file_splitter import SplitResult, create_backup


@dataclass
class AnalysisRequest:
    """Request for LLM to analyze and refactor content."""

    file_path: Path
    content: str
    total_lines: int
    target_main_lines: int
    max_lines: int


@dataclass
class RefactorPlan:
    """LLM's plan for refactoring the file."""

    folder_name: str  # Semantic name for the folder (e.g., "cooking", "project-phases")
    main_content: str
    reference_sections: list[dict[str, str]]  # [{name: str, content: str}]
    summary: str
    reasoning: str


def identify_large_files(
    directory: Path, max_lines: int = 500, extensions: Optional[list[str]] = None
) -> list[dict[str, any]]:
    """Identify files that need splitting.

    Args:
        directory: Directory to scan
        max_lines: Maximum lines threshold
        extensions: File extensions to check (default: ['.md'])

    Returns:
        List of dicts with file info: {path, lines, tokens}
    """
    if extensions is None:
        extensions = [".md"]

    # Import from analyze skill
    import sys
    analyze_scripts = Path(__file__).parent.parent.parent / "analyze" / "scripts"
    sys.path.insert(0, str(analyze_scripts))
    from token_counter import scan_directory

    results = scan_directory(directory, extensions=extensions)
    return [r for r in results if r["lines"] > max_lines]


def generate_refactor_prompt(request: AnalysisRequest) -> str:
    """Generate prompt for LLM to analyze and refactor content.

    Args:
        request: Analysis request with file info

    Returns:
        Formatted prompt for the LLM
    """
    prompt = f"""I need help intelligently refactoring a large context file to follow Anthropic's best practices.

**File**: {request.file_path.name}
**Current Size**: {request.total_lines} lines
**Target Main Size**: ~{request.target_main_lines} lines
**Threshold**: {request.max_lines} lines

**Current Content**:
```markdown
{request.content}
```

**Task**: Analyze this content and refactor it into a CLEAN, hierarchical folder structure.

**CRITICAL NAMING RULES:**
1. **Folder name** - Simple, clean, semantic:
   - Think hierarchically: broad concept → specific topic
   - NO timestamps (no "2026-02", no dates)
   - NO synthesis/collection suffixes (no "synthesis", "collection")
   - Use the CORE CONCEPT only
   - Examples: "best-practices" (not "best-practices-synthesis-2026-02")
   - Examples: "cooking" (not "recipes-collection"), "api" (not "api-reference-v2")

2. **File names** - Clean topic names:
   - NO numbered prefixes (no "theme-1-", "section-2-", "part-3-")
   - NO redundant context (folder already provides it)
   - Just the topic name: "progressive-disclosure.md" (not "theme-1-progressive-disclosure.md")
   - Examples: "italian-pasta.md", "french-desserts.md", "quality-testing.md"

3. **Hierarchical thinking**:
   - The filepath should tell a story from broad → narrow
   - Example: skills/best-practices/progressive-disclosure.md
   - Reads as: "Skills area → Best practices topic → Specific practice"

**Structure to create:**

Main file (~{request.target_main_lines} lines) as `main.md`:
- Essential overview
- Navigation to supporting files
- Scannable structure

Supporting files (3-10 topically organized):
- One clear topic per file
- Clean, descriptive names (no prefixes)
- Self-contained content
- Link back to main

**Quality checks**:
- ✅ Folder name is simple and semantic (no dates, no suffixes)
- ✅ File names are clean topics (no "theme-1-", no "part-2-")
- ✅ Filepath reads as a logical hierarchy
- ✅ All information preserved
- ✅ Clear navigation with bidirectional links

**Output Format** (JSON):
```json
{{
  "folder_name": "core-concept",
  "main_content": "the refactored main.md content with overview and navigation",
  "reference_sections": [
    {{
      "name": "topic-name",
      "content": "full content for this supporting file"
    }},
    {{
      "name": "another-topic",
      "content": "full content for this supporting file"
    }}
  ],
  "summary": "brief description of organizational strategy",
  "reasoning": "explanation of folder naming and content organization"
}}
```

**Example for a best practices document:**
```json
{{
  "folder_name": "best-practices",
  "main_content": "...",
  "reference_sections": [
    {{"name": "progressive-disclosure", "content": "..."}},
    {{"name": "description-discovery", "content": "..."}},
    {{"name": "tool-definition", "content": "..."}}
  ],
  "summary": "Organized into core practices",
  "reasoning": "Folder 'best-practices' is the core concept. Files are clean topic names without prefixes."
}}
```

Please provide ONLY the JSON output, no additional commentary."""

    return prompt


def parse_llm_response(response: str) -> RefactorPlan:
    """Parse LLM's JSON response into a RefactorPlan.

    Args:
        response: LLM's response text

    Returns:
        Parsed RefactorPlan

    Raises:
        ValueError: If response cannot be parsed
    """
    # Extract JSON from response (handle markdown code blocks)
    json_str = response.strip()

    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0].strip()
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0].strip()

    try:
        data = json.loads(json_str)

        return RefactorPlan(
            folder_name=data["folder_name"],
            main_content=data["main_content"],
            reference_sections=data["reference_sections"],
            summary=data["summary"],
            reasoning=data["reasoning"],
        )
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Failed to parse LLM response: {e}\n\nResponse: {response[:500]}")


def skill_based_split(
    file_path: Path,
    max_lines: int = 500,
    target_main_lines: int = 150,
    backup: bool = True,
    dry_run: bool = False,
) -> tuple[AnalysisRequest, str]:
    """Split file using Claude Code skill system (no separate API key needed).

    This function prepares the analysis request and returns the prompt.
    The actual LLM call happens in the user's Claude Code session.

    Args:
        file_path: Path to file to split
        max_lines: Maximum lines before splitting
        target_main_lines: Target lines for main file
        backup: Whether to create backup
        dry_run: If True, only analyze without writing

    Returns:
        Tuple of (AnalysisRequest, prompt_string)

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is too small to split
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read file
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    total_lines = len(lines)

    if total_lines <= max_lines:
        raise ValueError(
            f"File has {total_lines} lines, under the {max_lines} threshold"
        )

    # Create analysis request
    request = AnalysisRequest(
        file_path=file_path,
        content=content,
        total_lines=total_lines,
        target_main_lines=target_main_lines,
        max_lines=max_lines,
    )

    # This returns the prompt that should be sent to Claude
    # The actual LLM interaction happens via the skill
    prompt = generate_refactor_prompt(request)

    # Return the request for the skill to handle
    return request, prompt


def implement_refactor_plan(
    file_path: Path,
    plan: RefactorPlan,
    backup: bool = True,
) -> SplitResult:
    """Implement the refactoring plan by writing files.

    Args:
        file_path: Original file path
        plan: RefactorPlan from LLM with semantic folder name
        backup: Whether to create backup

    Returns:
        SplitResult with operation details
    """
    # Read original for line count
    with open(file_path, encoding="utf-8") as f:
        original_content = f.read()
    total_lines = len(original_content.split("\n"))

    # Create backup
    backup_path = None
    if backup:
        backup_path = create_backup(file_path)

    # Create semantic folder at same level as original file
    semantic_dir = file_path.parent / plan.folder_name
    semantic_dir.mkdir(parents=True, exist_ok=True)

    # Write main.md in the semantic folder
    main_file = semantic_dir / "main.md"
    with open(main_file, "w", encoding="utf-8") as f:
        f.write(plan.main_content)

    # Write supporting files in the same folder
    reference_files = []
    for ref in plan.reference_sections:
        ref_file = semantic_dir / f"{ref['name']}.md"
        with open(ref_file, "w", encoding="utf-8") as f:
            f.write(ref["content"])
        reference_files.append(ref_file)

    # Remove original file (it's already backed up)
    file_path.unlink()

    # Calculate line counts
    main_lines = len(plan.main_content.split("\n"))
    ref_lines = sum(len(ref["content"].split("\n")) for ref in plan.reference_sections)

    result = SplitResult(
        original_file=file_path,
        main_file=main_file,
        reference_files=reference_files,
        backup_file=backup_path,
        lines_in_main=main_lines,
        lines_in_references=ref_lines,
        total_lines=total_lines,
        wikilinks_updated=0,
    )

    return result
