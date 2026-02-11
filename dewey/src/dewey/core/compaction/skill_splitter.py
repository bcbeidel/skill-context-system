"""Skill-based intelligent file splitting.

This module provides file splitting that uses Claude Code's native skill system,
eliminating the need for separate API keys.
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dewey.core.compaction.file_splitter import SplitResult, create_backup


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

    from dewey.core.measurement.token_counter import scan_directory

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

**Task**: Analyze this content and refactor it into:

1. **Main file** (~{request.target_main_lines} lines):
   - Essential overview/introduction
   - Key high-level concepts
   - Clear navigation to detailed sections
   - Scannable structure

2. **Reference files** (1-3 topically organized):
   - Group related content together
   - Self-contained sections
   - Descriptive names (e.g., "phase-1-tasks", "testing-guide")
   - Link back to main file

**Best Practices**:
- Maintain semantic coherence (don't break mid-section)
- Preserve ALL information (no content loss)
- Create clear navigation (bidirectional links)
- Use descriptive headers
- Group by topic/theme, not arbitrary lines

**Output Format** (JSON):
```json
{{
  "main_content": "the refactored main file content with navigation",
  "reference_sections": [
    {{
      "name": "descriptive-kebab-case-name",
      "content": "full content for this reference file"
    }}
  ],
  "summary": "brief description of organizational strategy",
  "reasoning": "explanation of why content was grouped this way"
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
) -> tuple[SplitResult, RefactorPlan]:
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
        Tuple of (SplitResult, RefactorPlan)

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
        plan: RefactorPlan from LLM
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

    # Create references directory
    references_dir = file_path.parent / "references" / file_path.stem
    references_dir.mkdir(parents=True, exist_ok=True)

    # Write main file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(plan.main_content)

    # Write reference files
    reference_files = []
    for ref in plan.reference_sections:
        ref_file = references_dir / f"{ref['name']}.md"
        with open(ref_file, "w", encoding="utf-8") as f:
            f.write(ref["content"])
        reference_files.append(ref_file)

    # Calculate line counts
    main_lines = len(plan.main_content.split("\n"))
    ref_lines = sum(len(ref["content"].split("\n")) for ref in plan.reference_sections)

    result = SplitResult(
        original_file=file_path,
        main_file=file_path,
        reference_files=reference_files,
        backup_file=backup_path,
        lines_in_main=main_lines,
        lines_in_references=ref_lines,
        total_lines=total_lines,
        wikilinks_updated=0,
    )

    return result
