---
name: health
description: Validate knowledge base quality, check freshness, analyze coverage gaps, and generate health reports
---

<essential_principles>
## What This Skill Does

Validates knowledge base quality across three tiers and three quality dimensions. Runs deterministic checks, LLM-assisted assessments, and surfaces items requiring human judgment. Produces actionable health reports with severity-ranked issues.

## Three-Tier Validation

1. **Tier 1 -- Deterministic (Python)** -- Fast, automated checks run by `check_kb.py`. Validates frontmatter, section ordering, cross-references, size bounds, source URLs, freshness dates, and structural coverage. No LLM required. CI-friendly.
2. **Tier 2 -- LLM-Assisted (Claude)** -- Claude evaluates items flagged by Tier 1 or entries with stale `last_validated` dates. Assesses source drift, depth label accuracy, "Why This Matters" quality, and "In Practice" concreteness.
3. **Tier 3 -- Human Judgment** -- Surfaces decisions that require human input: relevance questions, scope decisions, pending proposals, and conflict resolution between KB claims and updated sources.

## Three Quality Dimensions

1. **Relevance** -- Is this content needed by the role? Does the relevance statement accurately describe who benefits and when?
2. **Accuracy / Freshness** -- Are claims current and traceable to sources? Has the content been validated recently?
3. **Structural Fitness** -- Does the content follow the KB spec? Correct depth, proper sections, valid frontmatter, companion files present?

## Design Philosophy

- **Fast feedback first** -- Tier 1 runs in seconds, catches structural issues immediately
- **LLM where it matters** -- Tier 2 only evaluates what Tier 1 flags or what's overdue
- **Humans decide scope** -- Tier 3 never auto-resolves relevance or pruning decisions
- **Severity-ranked output** -- Every issue carries a severity (fail, warn) so users can prioritize

## Key Variables

- `$ARGUMENTS` -- Arguments passed to this skill (workflow name and parameters)
- `${CLAUDE_PLUGIN_ROOT}` -- Root directory of the Dewey plugin
</essential_principles>

<intake>
Validating knowledge base quality.

**Default behavior:** Run Tier 1 deterministic checks only (fast, CI-friendly).

**Available actions:**
- `check` -- Tier 1 deterministic validation (default)
- `audit` -- Tier 1 + Tier 2 LLM-assisted assessment
- `review` -- Tier 1 + Tier 2 + surface Tier 3 decision queue
- `coverage` -- Gap analysis against AGENTS.md responsibilities
- `freshness` -- Staleness report sorted by urgency

Parse the action from `$ARGUMENTS`. If no arguments provided, run `check` (Tier 1 only).
</intake>

<routing>
## Argument-Based Routing

Parse `$ARGUMENTS`:

- Starts with `check` or no arguments provided -> Route to `workflows/health-check.md`
- Starts with `audit` -> Route to `workflows/health-audit.md`
- Starts with `review` -> Route to `workflows/health-review.md`
- Starts with `coverage` -> Route to `workflows/health-coverage.md`
- Starts with `freshness` -> Route to `workflows/health-freshness.md`
</routing>

<workflows_index>
## Available Workflows

All workflows in `workflows/`:

| Workflow | Purpose |
|----------|---------|
| health-check.md | Tier 1 deterministic validation -- fast, CI-friendly |
| health-audit.md | Tier 1 + Tier 2 LLM-assisted quality assessment |
| health-review.md | Full assessment + Tier 3 human decision queue |
| health-coverage.md | Gap analysis comparing AGENTS.md responsibilities to KB contents |
| health-freshness.md | Staleness report grouped by urgency |
</workflows_index>

<references_index>
## Domain Knowledge

All references in `references/`:

| Reference | Content |
|-----------|---------|
| validation-rules.md | Complete list of Tier 1 checks with fields, thresholds, and severities |
| quality-dimensions.md | Three quality dimensions: what each means, how measured, which checks apply |
</references_index>

<scripts_integration>
## Python Helper Scripts

Located in `scripts/`:

**check_kb.py** -- Health check runner
- Discovers all .md files under docs/ (excluding _proposals/)
- Runs all Tier 1 deterministic validators on each file
- Returns structured JSON report with issues and summary
- Summary includes total_files, fail_count, warn_count, pass_count

**Usage:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/health/scripts/check_kb.py --kb-root <kb_root>
```

**validators.py** -- Tier 1 deterministic validators
- `check_frontmatter` -- Required fields: sources, last_validated, relevance, depth
- `check_section_ordering` -- "In Practice" before "Key Guidance" in working-depth files
- `check_cross_references` -- Internal markdown links resolve to existing files
- `check_size_bounds` -- Line counts within range for each depth level
- `check_source_urls` -- Source URLs are well-formed (http/https)
- `check_freshness` -- last_validated within threshold (default 90 days)
- `check_coverage` -- Every area has overview.md; every topic has .ref.md companion

Every validator returns a list of issue dicts: `{"file": str, "message": str, "severity": "fail" | "warn"}`
</scripts_integration>

<success_criteria>
Health assessment is successful when:

- Every issue is reported with a severity level (fail or warn)
- Issues include the affected file path and a clear message
- Summary statistics are provided (total files, fails, warnings, passes)
- Recommendations are actionable (fix this specific field, re-validate this entry)
- Tier 2 assessments include reasoning, not just pass/fail
- Tier 3 items are framed as questions for human decision, not directives
</success_criteria>
