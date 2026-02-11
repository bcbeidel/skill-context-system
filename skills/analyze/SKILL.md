---
name: analyze
description: Analyze context usage and generate actionable optimization recommendations
---

<essential_principles>
## What This Skill Does

Analyzes context directories to identify optimization opportunities through intelligent examination of token usage, file sizes, duplication patterns, and structural issues.

## Core Workflow

1. **Python collects data** - Scans files, counts tokens/lines, categorizes by size
2. **Generates structured prompt** - Creates analysis request for Claude
3. **Claude analyzes patterns** - Identifies issues, calculates impact, prioritizes actions
4. **Reports actionable recommendations** - Specific commands with estimated savings

## Design Philosophy

- **Measure before optimizing** - Data-driven decisions
- **Prioritize by impact** - Quick wins first (high impact, low effort)
- **Specific recommendations** - Exact commands to run, not vague suggestions
- **Quantify savings** - Token estimates for each optimization
- **Integration-aware** - Recommends other `/dewey:*` skills where appropriate

## Key Variables

- `$ARGUMENTS` - Arguments passed to this skill (directory path and flags)
- `${CLAUDE_PLUGIN_ROOT}` - Root directory of the Dewey plugin
</essential_principles>

<intake>
What type of analysis do you want to run?

1. **Standard analysis** - Analyze a directory and get recommendations
2. **Detailed analysis** - Include file-by-file breakdown
3. **Baseline analysis** - Save results as baseline for future comparison
4. **Compare to baseline** - Compare current state to previous baseline

**If arguments provided** (`$ARGUMENTS` is not empty), route directly based on flags.
</intake>

<routing>
## Command-Line Routing

If `$ARGUMENTS` contains:
- `--detailed` → Route to workflows/analyze-detailed.md
- `--baseline` → Route to workflows/analyze-baseline.md
- `--compare` → Route to workflows/analyze-compare.md
- Otherwise → Route to workflows/analyze-standard.md

## Interactive Routing

| User Response | Workflow |
|---------------|----------|
| 1, "standard", "basic", "analyze" | workflows/analyze-standard.md |
| 2, "detailed", "file-by-file", "breakdown" | workflows/analyze-detailed.md |
| 3, "baseline", "save" | workflows/analyze-baseline.md |
| 4, "compare", "comparison", "diff" | workflows/analyze-compare.md |

After determining the workflow, load and follow it exactly.
</routing>

<workflows_index>
## Available Workflows

All workflows in `workflows/`:

| Workflow | Purpose |
|----------|---------|
| analyze-standard.md | Standard directory analysis with recommendations |
| analyze-detailed.md | Detailed analysis with per-file breakdown |
| analyze-baseline.md | Save analysis as baseline for tracking |
| analyze-compare.md | Compare current state to saved baseline |
</workflows_index>

<references_index>
## Domain Knowledge

All references in `references/`:

| Reference | Content |
|-----------|---------|
| context-best-practices.md | Anthropic's context organization principles |
| token-optimization.md | Token optimization strategies and patterns |
| analysis-metrics.md | Understanding metrics and their implications |
| issue-detection.md | How to identify and prioritize issues |
</references_index>

<scripts_integration>
## Python Helper Scripts

Located in `scripts/`:

**analyze_directory.py** - Main analysis script
- Scans directory for files (default: .md files)
- Counts tokens, lines, bytes
- Categorizes by size buckets
- Identifies large files (>500 lines)
- Generates structured data for Claude

**token_counter.py** - Token counting utilities
- Estimates tokens using character/word heuristics
- Scans directories recursively
- Handles multiple file extensions

**Usage in workflows:**
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/analyze_directory.py $ARGUMENTS
```

The script outputs a structured prompt for Claude to process.
</scripts_integration>

<success_criteria>
Analysis is successful when:
- All files in directory are scanned
- Issues are categorized by priority (🔴 High, 🟡 Medium, 🟢 Low)
- Recommendations are specific (exact commands to run)
- Impact is quantified (estimated token savings)
- Next steps are prioritized by impact/effort ratio
- Report is clear, actionable, and formatted with visual clarity
</success_criteria>
