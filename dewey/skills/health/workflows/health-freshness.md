<objective>
Generate a staleness report for all knowledge base entries, grouped by urgency.
</objective>

<process>
## Step 1: Extract freshness data

Use a two-step approach:

### Step 1a: Run check_kb.py for initial scan

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/health/scripts/check_kb.py --knowledge-base-root <knowledge_base_root>
```

This runs `check_freshness` as part of Tier 1 validation and will flag files that are overdue (>90 days) or missing `last_validated`. Use the JSON output to identify which files have freshness issues.

### Step 1b: Read frontmatter directly for detailed report

For the full freshness report, read each .md file under `docs/` (excluding `_proposals/` and other `_` prefixed directories) and extract:

- File path (relative to KB root)
- `last_validated` date from frontmatter
- `depth` from frontmatter
- Domain area (parent directory name)

This direct read is needed because check_kb.py only flags failures/warnings -- the freshness report also needs data from **passing** files to show the full picture.

If a file has no `last_validated` field, flag it as "never validated."

## Step 2: Calculate staleness

For each entry, compute the age in days: `today - last_validated`.

Classify into urgency groups:

| Group | Criteria | Action |
|-------|----------|--------|
| **Overdue** | > 90 days old or never validated | Must re-validate |
| **Due soon** | 60-90 days old | Schedule re-validation |
| **Fresh** | < 60 days old | No action needed |

## Step 3: Present the freshness report

```
## Freshness Report

### Summary
- Total entries: <N>
- Fresh (< 60 days): <N>
- Due soon (60-90 days): <N>
- Overdue (> 90 days): <N>
- Never validated: <N>

### Overdue (must re-validate)

| File | Last Validated | Age (days) | Area |
|------|---------------|------------|------|
| <path> | <date> | <days> | <area> |

### Due Soon (schedule re-validation)

| File | Last Validated | Age (days) | Area |
|------|---------------|------------|------|
| <path> | <date> | <days> | <area> |

### Fresh (no action needed)

| File | Last Validated | Age (days) | Area |
|------|---------------|------------|------|
| <path> | <date> | <days> | <area> |
```

Sort entries within each group by age (most stale first).

## Step 4: Area-level summary

Group the staleness data by domain area to identify which areas need the most attention:

```
### Staleness by Area

| Area | Total | Overdue | Due Soon | Fresh |
|------|-------|---------|----------|-------|
| <area> | <N> | <N> | <N> | <N> |
```

## Step 5: Suggest next steps

- For overdue entries -> "Re-validate against sources and update `last_validated`. Use `/dewey:health audit` for LLM-assisted assessment."
- For never-validated entries -> "These entries have never been validated. Add `last_validated: <today>` after verifying content."
- For areas with many overdue entries -> "Consider a focused audit of `<area>` using `/dewey:health audit`."
- If everything is fresh -> "All entries are current. Next freshness review recommended in <N> days."
</process>

<success_criteria>
- All knowledge files are scanned for last_validated dates
- Entries are correctly classified by urgency (overdue, due soon, fresh, never validated)
- Report is sorted by staleness within each group
- Area-level summary highlights which domains need attention
- Recommendations point to specific actions and Dewey skills
</success_criteria>
