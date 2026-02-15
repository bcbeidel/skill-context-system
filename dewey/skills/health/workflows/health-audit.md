<objective>
Run Tier 1 deterministic checks followed by Tier 2 LLM-assisted quality assessment on flagged or stale entries.
</objective>

<process>
## Step 1: Run Tier 1 checks

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/health/scripts/check_kb.py --kb-root <kb_root>
```

Capture the JSON output. Present the Tier 1 summary as in the health-check workflow.

## Step 2: Identify entries for Tier 2 assessment

Build the Tier 2 evaluation queue from two sources:

1. **Tier 1 flagged entries** -- Any file with warnings or failures from Tier 1 (especially freshness warnings)
2. **Stale entries** -- Any file where `last_validated` is older than 90 days, even if Tier 1 did not flag other issues

Deduplicate the list. Present to the user:

"**Tier 2 evaluation queue:** <N> entries to assess."

List each entry with the reason it was queued (Tier 1 flag, staleness, or both).

## Step 3: Perform Tier 2 LLM assessment

For each entry in the queue, read the file and evaluate four dimensions:

### 3a. Source drift

Extract the `sources` URLs from frontmatter. For each URL, use the **WebFetch** tool to retrieve the current content:

```
WebFetch(url=<source_url>, prompt="Summarize the key claims and recommendations in this document")
```

Compare the fetched content against the claims in the KB entry. Flag if:
- The KB entry makes claims not supported by the sources
- The sources have been updated with information not reflected in the KB entry
- Sources are no longer accessible (WebFetch returns an error)

If a source URL cannot be fetched (timeout, 404, paywall), note: "Source drift check skipped for `<url>` -- not accessible." and continue with the remaining sources.

### 3b. Depth label accuracy

Read the content and compare against depth expectations:
- **overview** -- Should orient: what is this area, why it matters, how topics connect. Should NOT contain detailed how-to guidance.
- **working** -- Should have actionable guidance: In Practice examples, Key Guidance, Watch Out For. Should NOT be terse/scannable-only.
- **reference** -- Should be terse and scannable: tables, lists, lookup patterns. Should NOT have lengthy narrative.

Flag if the content does not match its declared depth.

### 3c. "Why This Matters" quality

For working-depth files, read the "Why This Matters" section. Evaluate:
- Does it explain **why**, not just **what**?
- Does it connect to the role's goals and outcomes?
- Would someone unfamiliar with the topic understand the stakes?

Flag if the section reads as a description rather than a motivation.

### 3d. "In Practice" concreteness

For working-depth files, read the "In Practice" section. Evaluate:
- Does it contain a **concrete example** (specific scenario, numbers, names)?
- Could someone follow this guidance in a real situation?
- Is it actionable, not just theoretical?

Flag if the section is abstract or generic.

## Step 4: Present combined report

Format the combined Tier 1 + Tier 2 report:

```
## Audit Report

### Tier 1: Deterministic Checks
<summary from Step 1>

### Tier 2: LLM Assessment
<N> entries evaluated.

| File | Source Drift | Depth Accuracy | Why Quality | In Practice Quality |
|------|-------------|----------------|-------------|---------------------|
| <path> | OK / Flag | OK / Flag | OK / Flag | OK / Flag |

### Detailed Findings
<for each flagged item, provide specific reasoning and a recommendation>
```

## Step 5: Suggest next steps

- Entries with Tier 2 flags -> "Re-validate these entries against their sources and update the content."
- Entries with depth mismatches -> "Consider changing the depth label or restructuring the content."
- Entries with weak Why/In Practice -> "Strengthen these sections with causal reasoning and concrete examples."
- If many entries are flagged -> "Consider running `/dewey:health review` to surface items for human decision."
</process>

<success_criteria>
- Tier 1 checks run successfully and results are presented
- Tier 2 queue is built from Tier 1 flags and staleness
- Each Tier 2 assessment includes specific reasoning, not just pass/fail
- Combined report clearly separates Tier 1 and Tier 2 findings
- Recommendations are actionable and specific to each finding
</success_criteria>
