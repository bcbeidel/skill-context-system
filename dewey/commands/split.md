---
description: Intelligently split large files using LLM analysis to maintain semantic coherence
---

# Split Large Files

Intelligently split large context files (>500 lines) into a scannable main file and topically organized reference files, following Anthropic's best practices for context organization.

## How to Use

```
/dewey:split file.md
/dewey:split file.md --dry-run
```

## What It Does

This command uses the current Claude Code session to:

1. **Analyze** the file content semantically
2. **Identify** essential vs detailed information
3. **Organize** content into topics
4. **Create** a main file (~150 lines) with overview and navigation
5. **Generate** reference files in `references/[filename]/` directory
6. **Maintain** all information with clear bidirectional links
7. **Backup** the original file to `.dewey/backups/`

## Arguments

The command accepts a file path and optional flags:

- `file.md` - Path to the file to split
- `--dry-run` - Preview what would be created without writing files
- `--max-lines N` - Custom threshold (default: 500)
- `--target-lines N` - Target main file size (default: 150)

**Note**: `$ARGUMENTS` in this command will be the file path and any flags provided.

## What You Get

### Before
```
File: IMPLEMENTATION_PLAN.md
Lines: 973
Structure: Single monolithic file
```

### After
```
Main: IMPLEMENTATION_PLAN.md (~200 lines)
  - Project overview
  - Key principles
  - Phase 0 summary
  - Clear navigation to phases

References (3 files):
  - references/IMPLEMENTATION_PLAN/phase-1-measurement.md
  - references/IMPLEMENTATION_PLAN/phase-2-3-optimization.md
  - references/IMPLEMENTATION_PLAN/testing-completion.md

Backup: .dewey/backups/IMPLEMENTATION_PLAN_20260210.md
```

## Implementation

Use the Python helper functions to implement this command:

```python
from pathlib import Path
from dewey.core.compaction.skill_splitter import (
    analyze_directory,
    generate_refactor_prompt,
    implement_refactor_plan
)

# Parse arguments
file_path = Path("$ARGUMENTS".split()[0])
dry_run = "--dry-run" in "$ARGUMENTS"

# Generate analysis prompt
request, prompt = skill_based_split(file_path, dry_run=dry_run)

# Display the prompt and ask Claude (me!) to analyze
# Claude will provide refactoring plan in JSON format
# Then implement the plan:
# result = implement_refactor_plan(file_path, plan)
```

## Analysis Task

When invoked, analyze the file content and provide a refactoring plan in this JSON format:

```json
{
  "main_content": "Refactored main file with overview and navigation",
  "reference_sections": [
    {
      "name": "descriptive-kebab-case-name",
      "content": "Full content for this reference file"
    }
  ],
  "summary": "Brief description of organizational strategy",
  "reasoning": "Explanation of why content was grouped this way"
}
```

## Best Practices Applied

- **Scannable main files**: Overview + key concepts + navigation
- **Topical organization**: Related content grouped logically
- **Semantic coherence**: No mid-section cuts
- **Information preservation**: All content retained
- **Clear navigation**: Bidirectional links between files

## Integration

Works seamlessly with:
- `/dewey:analyze` - Identifies files that need splitting
- `/dewey:check` - Validates file sizes after splitting
- `/dewey:optimize` - Part of full optimization suite

---

**Process the arguments**: $ARGUMENTS
