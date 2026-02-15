<objective>
Run Tier 1 deterministic health checks on the knowledge base and format the results into a readable report.
</objective>

<process>
## Step 1: Locate the knowledge base root

Determine the KB root directory. If provided in `$ARGUMENTS` (e.g., `check /path/to/kb`), use that path. Otherwise, use the current working directory.

Verify that `docs/` exists under the KB root. If not, report: "No docs/ directory found at `<path>`. Is this a knowledge base? Use `/dewey:init` to create one."

## Step 2: Run Tier 1 validators

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/health/scripts/check_kb.py --kb-root <kb_root>
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
