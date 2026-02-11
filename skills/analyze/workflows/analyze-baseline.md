# Baseline Analysis Workflow

<objective>
Perform standard analysis and save results as baseline for future comparison tracking.
</objective>

<required_reading>
Before proceeding, read:
- `workflows/analyze-standard.md` - Standard analysis process
</required_reading>

<process>

## Step 1: Follow Standard Analysis

Execute the complete standard analysis workflow as described in `workflows/analyze-standard.md`.

Run with baseline flag:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/analyze_directory.py $ARGUMENTS --baseline
```

**What the baseline flag does:**
- Performs normal analysis
- Saves results to `~/.claude/analytics/baseline.json`
- Creates parent directories if needed
- Overwrites previous baseline

## Step 2: Verify Baseline Saved

After analysis completes, confirm:

```
✓ Baseline saved to: ~/.claude/analytics/baseline.json
```

**Baseline data includes:**
- Timestamp of analysis
- Directory path
- Total files, tokens, lines, bytes
- Distribution across size buckets
- List of large files (>500 lines)
- Top 10 files by token count

## Step 3: Generate Standard Report

Provide the same analysis report as standard workflow, but add:

```
📊 Baseline Saved
==================================================
Location: ~/.claude/analytics/baseline.json
Timestamp: [ISO timestamp]
Purpose: Track optimization progress over time

To compare future changes:
  /dewey:analyze --compare
  /dewey:analyze path/ --compare
```

## Step 4: Explain Baseline Usage

Add to the report:

```
💡 What's Next?
==================================================

This baseline captures your current context state. Use it to:

1. **Track optimization impact**
   After making changes (splits, deduplication, etc.),
   run: /dewey:analyze --compare

2. **Monitor context growth**
   Run weekly to see if context is growing unsustainably

3. **Measure improvement**
   Compare before/after token counts to validate optimizations

**Recommended:** Set a weekly reminder to run:
  /dewey:analyze --compare

This helps catch context bloat before it becomes a problem.
```

</process>

<success_criteria>
Baseline workflow is complete when:
- ✅ Standard analysis completed successfully
- ✅ Baseline file saved to `~/.claude/analytics/baseline.json`
- ✅ Confirmation message shown
- ✅ Baseline usage instructions provided
- ✅ User understands how to use `--compare` flag
</success_criteria>

<example_output>
```
📊 Context Analysis Report
==================================================

[... standard analysis output ...]

📊 Baseline Saved
==================================================
Location: ~/.claude/analytics/baseline.json
Timestamp: 2026-02-10T14:23:45
Purpose: Track optimization progress over time

To compare future changes:
  /dewey:analyze --compare

💡 What's Next?
==================================================

This baseline captures your current context state. Use it to:

1. **Track optimization impact**
   After making changes (splits, deduplication, etc.),
   run: /dewey:analyze --compare

2. **Monitor context growth**
   Run weekly to see if context is growing unsustainably

3. **Measure improvement**
   Compare before/after token counts to validate optimizations

**Recommended:** Set a weekly reminder to run:
  /dewey:analyze --compare

This helps catch context bloat before it becomes a problem.
```
</example_output>
