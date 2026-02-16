<objective>
Run Tier 1 deterministic health checks on the knowledge base and format the results into a readable report.
</objective>

<process>
## Step 1: Locate the knowledge base root

Determine the knowledge base root directory using this resolution order:

1. If a path is provided in `$ARGUMENTS` (e.g., `check /path/to/kb`), use that path
2. Otherwise, check the current working directory for the knowledge base directory (configured in `.dewey/config.json`, defaults to `docs/`)
3. If not found in CWD, walk up parent directories (up to 3 levels) looking for a directory that contains both the knowledge base directory and `AGENTS.md`

Verify the resolved knowledge base root:
- The knowledge base directory must exist
- `AGENTS.md` should exist (warn if missing but continue -- health checks can still run on the knowledge base directory)

If no knowledge base root can be found, report: "No knowledge base found. Looked for the knowledge base directory (configured in `.dewey/config.json`, defaults to `docs/`) in the current directory and up to 3 parent directories. Use `/dewey:curate` to create one."

## Step 2: Run Tier 1 validators

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/health/scripts/check_kb.py --knowledge-base-root <knowledge_base_root>
```

This runs all deterministic validators:
- Frontmatter completeness (required fields: sources, last_validated, relevance, depth)
- Section ordering (In Practice before Key Guidance)
- Cross-reference integrity (internal links resolve)
- Size bounds (line counts within range for depth)
- Source URL format (well-formed http/https)
- Freshness (last_validated within 90 days)
- Structural coverage (overview.md per area, .ref.md per topic)

Capture the JSON output.

## Step 3: Format the report

Parse the JSON output and present a readable report:

**Summary section:**
```
## Health Check Summary

- Total files scanned: <N>
- Passing: <N>
- Failures: <N>
- Warnings: <N>
```

**Failures section** (if any):
```
## Failures (must fix)

| File | Issue |
|------|-------|
| <relative path> | <message> |
```

**Warnings section** (if any):
```
## Warnings (should fix)

| File | Issue |
|------|-------|
| <relative path> | <message> |
```

If there are no issues, report: "All files pass Tier 1 validation."

## Step 4: Provide recommendations

For each category of failure, provide a brief actionable recommendation:

- Missing frontmatter -> "Add the required frontmatter fields. See the topic template for the expected format."
- Broken links -> "Update or remove the broken internal link."
- Stale content -> "Re-validate this content against its sources and update `last_validated`."
- Missing overview.md -> "Create an overview.md for this domain area using `/dewey:curate add`."
- Missing .ref.md -> "Create a companion reference file for this topic."

## Step 5: Exit code guidance

If running in CI, note the summary counts:
- **0 failures** -> Health check passed
- **1+ failures** -> Health check failed; fix failures before merging
</process>

<success_criteria>
- check_kb.py runs without errors
- JSON output is parsed and formatted into a readable report
- Issues are grouped by severity (failures first, then warnings)
- Each issue shows the affected file and a clear message
- Actionable recommendations are provided for each failure category
</success_criteria>
