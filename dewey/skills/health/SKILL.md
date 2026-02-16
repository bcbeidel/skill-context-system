---
name: health
description: Validate knowledge base quality, check freshness, analyze coverage gaps, and generate health reports
---

<essential_principles>
## What This Skill Does

Validates knowledge base quality across three tiers and three quality dimensions. Runs deterministic checks, LLM-assisted assessments, and surfaces items requiring human judgment. Produces actionable health reports with severity-ranked issues.

## Three-Tier Validation

1. **Tier 1 -- Deterministic (Python)** -- Fast, automated checks run by `check_kb.py`. 18 per-file validators (frontmatter, sections, size bounds, readability, sources, freshness, and more) plus 6 cross-file validators (manifest sync, curation plan sync, proposal integrity, link graph, duplicate detection, naming conventions). Auto-fix available for common issues. No LLM required. CI-friendly.
2. **Tier 2 -- LLM-Assisted (Claude)** -- Claude evaluates items flagged by Tier 1 or entries with stale `last_validated` dates. Assesses source drift, depth label accuracy, "Why This Matters" quality, and "In Practice" concreteness.
3. **Tier 3 -- Human Judgment** -- Surfaces decisions that require human input: relevance questions, scope decisions, pending proposals, and conflict resolution between knowledge base claims and updated sources.

## Three Quality Dimensions

1. **Relevance** -- Is this content needed by the role? Does the relevance statement accurately describe who benefits and when?
2. **Accuracy / Freshness** -- Are claims current and traceable to sources? Has the content been validated recently?
3. **Structural Fitness** -- Does the content follow the knowledge base spec? Correct depth, proper sections, valid frontmatter, companion files present?

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

**Before routing, check if a curation plan exists:**

1. **No knowledge base initialized** (no AGENTS.md or knowledge base directory) -- Suggest `/dewey:curate` first. Do not proceed.
2. **Knowledge base exists but no `.dewey/curation-plan.md`** -- Pause and build a plan:
   - Read AGENTS.md to understand the role and domain areas
   - Read the knowledge base directory structure to see what topics already exist
   - Propose 2-4 starter topics per domain area based on context
   - Ask the user to confirm or adjust
   - Write `.dewey/curation-plan.md` with the confirmed topics (use the format from the curate-plan workflow)
   - Then resume the original command
3. **Plan exists** -- Proceed to routing normally

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
| health-coverage.md | Gap analysis comparing AGENTS.md responsibilities to knowledge base contents |
| health-freshness.md | Staleness report grouped by urgency |
</workflows_index>

<references_index>
## Domain Knowledge

All references in `references/`:

| Reference | Content |
|-----------|---------|
| validation-rules.md | Complete list of Tier 1 checks with fields, thresholds, and severities |
| quality-dimensions.md | Three quality dimensions: what each means, how measured, which checks apply |
| design-principles.md | Twelve design principles grounded in agent context research and cognitive science |
</references_index>

<scripts_integration>
## Python Helper Scripts

Located in `scripts/`:

**check_kb.py** -- Health check runner
- Discovers all .md files under the knowledge base directory (excluding _proposals/ and index.md)
- Runs all Tier 1 deterministic validators on each file
- Returns structured JSON report with issues and summary
- Summary includes total_files, fail_count, warn_count, pass_count

**Usage:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/health/scripts/check_kb.py --knowledge-base-root <knowledge_base_root>
```

**validators.py** -- Tier 1 deterministic validators

Structural checks:
- `check_frontmatter` -- Required fields: sources, last_validated, relevance, depth
- `check_section_ordering` -- "In Practice" before "Key Guidance" in working-depth files
- `check_section_completeness` -- Required sections present for each depth level
- `check_heading_hierarchy` -- No skipped heading levels (e.g., h1 to h3)
- `check_cross_references` -- Internal markdown links resolve to existing files
- `check_size_bounds` -- Line counts within range for each depth level
- `check_readability` -- Flesch-Kincaid grade level within bounds per depth (overview 8-14, working 10-16)

Coverage and sync checks:
- `check_coverage` -- Every area has overview.md; every topic has .ref.md companion
- `check_index_sync` -- index.md references all topic files on disk; warns on stale index
- `check_inventory_regression` -- Detects topics that disappeared between runs

Source and link checks:
- `check_source_urls` -- Source URLs are well-formed (http/https)
- `check_freshness` -- last_validated within threshold (default 90 days)
- `check_go_deeper_links` -- Working files link to their reference companions
- `check_ref_see_also` -- Reference files include a "See Also" section linking back
- `check_placeholder_comments` -- Flags TODO/FIXME/placeholder markers left in content
- `check_source_diversity` -- Warns when all sources come from a single domain
- `check_citation_grounding` -- Working files have inline citations near key claims
- `check_source_accessibility` -- Source URLs return HTTP 200 (opt-in via `--check-links`)

Every validator returns a list of issue dicts: `{"file": str, "message": str, "severity": "fail" | "warn"}`

**Tier 2 pre-screening only:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/health/scripts/check_kb.py --knowledge-base-root <knowledge_base_root> --tier2
```

**Combined Tier 1 + Tier 2:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/health/scripts/check_kb.py --knowledge-base-root <knowledge_base_root> --both
```

Returns `{"tier1": {...}, "tier2": {...}}` with both Tier 1 issues/summary and Tier 2 queue/summary.

**tier2_triggers.py** -- Tier 2 deterministic pre-screener

Content quality triggers:
- `trigger_source_drift` -- Flags files with stale or missing last_validated
- `trigger_depth_accuracy` -- Flags files where word count or prose ratio mismatches depth
- `trigger_source_primacy` -- Flags working files with low inline citation density
- `trigger_why_quality` -- Flags working files with missing or thin "Why This Matters"
- `trigger_concrete_examples` -- Flags working files with missing or abstract "In Practice"
- `trigger_citation_quality` -- Flags files with weak or missing inline citations

Source quality triggers:
- `trigger_source_authority` -- Flags files whose sources lack authoritative domains
- `trigger_provenance_completeness` -- Flags files with incomplete provenance metadata
- `trigger_recommendation_coverage` -- Flags files lacking actionable recommendations

Every trigger returns: `{"file": str, "trigger": str, "reason": str, "context": dict}`

**history.py** -- Health score history tracking
- `record_snapshot(knowledge_base_root, tier1_summary, tier2_summary)` -- Appends timestamped snapshot to `.dewey/history/health-log.jsonl`
- `read_history(knowledge_base_root, limit=10)` -- Returns the last N snapshots in chronological order
- Auto-called by `check_kb.py` after each run

**utilization.py** -- Topic reference tracking
- `record_reference(knowledge_base_root, file_path, context="user")` -- Appends to `.dewey/utilization/log.jsonl`
- `read_utilization(knowledge_base_root)` -- Returns per-file stats: `{file: {count, first_referenced, last_referenced}}`

**log_access.py** -- Hook-driven utilization logging
- `log_if_knowledge_file(knowledge_base_root, file_path)` -- Logs access if file is a .md under the knowledge directory
- Filters out _proposals, non-.md files, and files outside the knowledge directory
- Called by `hook_log_access.py` (Claude Code PostToolUse hook entry point)

**hook_log_access.py** -- CLI entry point for Claude Code PostToolUse hook
- Reads tool input JSON from stdin, extracts file_path
- Calls `log_if_knowledge_file` to conditionally log the access
- Exit code always 0 (hook failures never block the agent)

**cross_validators.py** -- Cross-file consistency validators
- `check_manifest_sync` -- AGENTS.md topic list matches files on disk
- `check_curation_plan_sync` -- Curation plan checkmarks match actual file presence
- `check_proposal_integrity` -- Proposals have required frontmatter and valid target areas
- `check_link_graph` -- Internal links between knowledge files all resolve
- `check_duplicate_content` -- Detects duplicate paragraphs and high Jaccard similarity across files (skips companion pairs)
- `check_naming_conventions` -- Validates directory and file names against slug conventions

Every cross-validator returns: `{"file": str, "message": str, "severity": "fail" | "warn"}`

**auto_fix.py** -- Automated fixes for common issues
- `fix_missing_sections` -- Adds missing required sections with placeholder content
- `fix_missing_cross_links` -- Adds "Go Deeper" / "See Also" links between companion files
- `fix_curation_plan_checkmarks` -- Updates curation plan checkmarks to match files on disk
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
