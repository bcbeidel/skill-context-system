---
name: check
description: Validate context quality with pre-commit style checks for file sizes, links, duplication, and token budgets
---

<essential_principles>
## What This Skill Does

Validates context quality through automated checks, similar to a linter or pre-commit hook. Identifies issues before they become problems.

## Core Workflow

1. **Python runs validation checks** - Scans files for quality violations
2. **Generates structured report** - Lists all issues found
3. **Claude interprets and prioritizes** - Categorizes by severity
4. **Returns status code** - Pass/warn/fail for CI/CD integration

## Validation Categories

**File Size Checks:**
- Files must be <500 lines
- Warn at 400 lines
- Fail at 500+ lines

**Link Validation:**
- All internal links must resolve
- No dead links to non-existent files
- Relative paths must be correct

**Duplication Checks:**
- Detect excessive duplication (>20%)
- Identify repeated content blocks
- Flag copy-paste documentation

**Token Budget:**
- Total context within reasonable limits
- Warn if approaching limits
- Fail if budget exceeded

## Design Philosophy

- **Fast feedback** - Quick validation for rapid iteration
- **Clear failures** - Specific issues with locations
- **Actionable output** - Tell user exactly what to fix
- **CI/CD ready** - Exit codes for automation
- **Fast mode** - Quick checks for large contexts

## Key Variables

- `$ARGUMENTS` - Arguments passed to this skill (directory path and flags)
- `${CLAUDE_PLUGIN_ROOT}` - Root directory of the Dewey plugin
</essential_principles>

<intake>
Running context quality checks.

**Default behavior:** Standard validation mode
**Fast mode:** Use `--fast` flag for quick checks (skips detailed analysis)

No user input needed - skill executes based on arguments.
</intake>

<routing>
## Argument-Based Routing

Parse `$ARGUMENTS` for flags:

- Contains `--fast` → Route to workflows/check-fast.md
- Otherwise → Route to workflows/check-standard.md

**Note:** Check skill is primarily non-interactive. It runs validation and reports results.
</routing>

<workflows_index>
## Available Workflows

All workflows in `workflows/`:

| Workflow | Purpose |
|----------|---------|
| check-standard.md | Full quality validation with detailed analysis |
| check-fast.md | Quick checks optimized for speed (<2s for 200 files) |
</workflows_index>

<references_index>
## Domain Knowledge

All references in `references/`:

| Reference | Content |
|-----------|---------|
| quality-criteria.md | Standards for context quality |
| validation-rules.md | Specific rules and thresholds |
| exit-codes.md | Status codes and their meanings |
</references_index>

<scripts_integration>
## Python Helper Script

Located in `scripts/`:

**check_quality.py** - Main validation script
- Scans directory for context files
- Validates file sizes (line counts)
- Checks internal links
- Detects duplication patterns
- Calculates token totals
- Generates structured report with issues

**Usage in workflows:**
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/check/scripts/check_quality.py $ARGUMENTS
```

The script outputs:
- List of validation failures
- List of warnings
- Summary statistics
- Exit code (0=pass, 1=warn, 2=fail)
</scripts_integration>

<success_criteria>
Check is successful when:
- ✅ All validation rules executed
- ✅ Issues clearly reported with file names and line numbers
- ✅ Severity assigned to each issue (fail/warn)
- ✅ Actionable recommendations provided
- ✅ Appropriate exit code returned (0/1/2)
- ✅ Fast mode completes in <2 seconds for 200 files
</success_criteria>
