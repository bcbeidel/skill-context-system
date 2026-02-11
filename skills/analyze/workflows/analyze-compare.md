# Compare to Baseline Workflow

<objective>
Analyze current context state and compare to previously saved baseline to track changes and optimization progress.
</objective>

<required_reading>
Before proceeding, read:
- `workflows/analyze-standard.md` - Standard analysis process
- `references/analysis-metrics.md` - Understanding trend metrics
</required_reading>

<process>

## Step 1: Check for Baseline

Before running analysis, verify baseline exists:

**Expected location:** `~/.claude/analytics/baseline.json`

If baseline doesn't exist:
```
❌ No baseline found

You need to create a baseline first:
  /dewey:analyze --baseline

This will save your current state for future comparisons.
```

Stop workflow if no baseline found.

## Step 2: Run Current Analysis

Execute analysis with compare flag:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/analyze_directory.py $ARGUMENTS --compare
```

**Note:** The Python script will automatically:
- Load the baseline from `~/.claude/analytics/baseline.json`
- Perform current analysis
- Calculate delta metrics
- Include comparison data in the output

## Step 3: Analyze Changes

Compare current metrics to baseline:

### Metrics to Compare

**File Count Changes:**
- Files added (current - baseline)
- Files removed (if applicable)
- Net change

**Token Changes:**
- Current total vs baseline total
- Absolute difference
- Percentage change
- Token efficiency trend

**Large Files:**
- How many large files now vs baseline
- New large files added
- Large files that were split

### Trend Assessment

Determine if changes are:
- ✅ **Improved** - Fewer tokens, better organization
- ⚠️ **Growing** - More tokens, approaching limits
- ❌ **Regressed** - More large files, worse organization
- ➡️ **Stable** - Minimal change (<5% difference)

## Step 4: Generate Comparison Report

Structure the report with comparison focus:

```
📊 Context Analysis - Comparison Report
==================================================

📁 Directory: [path]
📅 Current Analysis: [timestamp]
📅 Baseline: [baseline timestamp]
⏱️  Time Since Baseline: [duration]

📈 Change Summary
==================================================
Metric              Baseline    Current    Change      Trend
----------------------------------------------------------
Files               XX          XX         +/- X       [emoji]
Total Tokens        XXX,XXX     XXX,XXX    +/- X%      [emoji]
Total Lines         XXX,XXX     XXX,XXX    +/- X%      [emoji]
Large Files (>500)  X           X          +/- X       [emoji]
Avg Tokens/File     X,XXX       X,XXX      +/- X%      [emoji]

Trend indicators:
  ✅ Improved (reduced)
  ⚠️ Growing (increased <20%)
  ❌ Alert (increased >20%)
  ➡️ Stable (changed <5%)

📊 Current Distribution
==================================================
[standard distribution chart]

⚡ Key Changes
==================================================

[If tokens decreased:]
✅ Optimization Success!
   • Tokens reduced by [X] ([X%])
   • [Specific changes that helped]
   • Well done!

[If tokens increased moderately:]
⚠️  Context Growing
   • Tokens increased by [X] ([X%])
   • [Files that grew or were added]
   • Consider: [optimization recommendations]

[If tokens increased significantly:]
❌ Context Bloat Detected
   • Tokens increased by [X] ([X%] - concerning!)
   • [Problematic files identified]
   • Urgent action needed:
     1. [Specific command]
     2. [Specific command]

🔍 Detailed Changes
==================================================

New Files Added: [count]
  • [filename] ([tokens])
  • [filename] ([tokens])

Files Removed: [count]
  [if any]

Files That Grew Significantly (>20% increase):
  • [filename]: [old tokens] → [new tokens] (+X%)

New Large Files (>500 lines):
  • [filename] ([lines] lines) - needs split!

💡 Recommendations Based on Changes
==================================================

[Context-specific recommendations based on what changed]

📈 Progress Tracking
==================================================
Starting Point:  [baseline tokens] ([baseline date])
Current State:   [current tokens] ([current date])
Net Change:      [difference] ([percentage]%)

[If improved:]
Keep up the good work! Your optimizations are effective.

[If growing:]
Context is trending upward. Consider these preventive measures:
1. [Recommendation]
2. [Recommendation]

[If regressed:]
Context efficiency has decreased. Priority actions:
1. [Most urgent action]
2. [Second priority]
```

## Step 5: Provide Next Steps

Based on comparison results:

**If Improved:**
- Acknowledge the optimization work
- Suggest maintaining current practices
- Recommend updating baseline: `/dewey:analyze --baseline`

**If Growing:**
- Highlight concerning trends
- Provide specific optimization commands
- Suggest more frequent monitoring

**If Regressed:**
- Urgent recommendations
- Specific files to address
- Consider reverting recent changes

</process>

<success_criteria>
Comparison workflow is complete when:
- ✅ Baseline successfully loaded
- ✅ Current analysis completed
- ✅ All metrics compared (files, tokens, lines, large files)
- ✅ Trend assessed and communicated clearly
- ✅ Specific changes identified (new files, growth, removed files)
- ✅ Recommendations tailored to actual changes observed
- ✅ Clear indication whether context is improving or degrading
</success_criteria>

<example_output>
```
📊 Context Analysis - Comparison Report
==================================================

📁 Directory: context/
📅 Current Analysis: 2026-02-10 16:30:00
📅 Baseline: 2026-02-03 09:15:00
⏱️  Time Since Baseline: 7 days

📈 Change Summary
==================================================
Metric              Baseline    Current    Change      Trend
----------------------------------------------------------
Files               47          45         -2          ✅
Total Tokens        125,340     92,100     -26.5%      ✅
Total Lines         18,450      13,200     -28.5%      ✅
Large Files (>500)  2           0          -2          ✅
Avg Tokens/File     2,667       2,047      -23.2%      ✅

⚡ Key Changes
==================================================

✅ Optimization Success!
   • Tokens reduced by 33,240 (26.5%)
   • Split IMPLEMENTATION_PLAN.md and .seed-prompt.md
   • Both large files now under 500 lines
   • Excellent progress!

🔍 Detailed Changes
==================================================

Files Removed: 2
  • IMPLEMENTATION_PLAN.md.backup (moved to backups/)
  • .seed-prompt.md.backup (moved to backups/)

Files That Were Split:
  • IMPLEMENTATION_PLAN.md: 973 lines → 187 lines
    Created 3 reference files in references/IMPLEMENTATION_PLAN/
  • .seed-prompt.md: 650 lines → 145 lines
    Created 2 reference files in references/seed-prompt/

New Large Files: 0
  All files now within optimal ranges!

💡 Recommendations
==================================================

✅ Your context is now well-optimized!

To maintain this:
1. Update your baseline to reflect current state:
   /dewey:analyze --baseline

2. Run weekly comparisons to catch growth early:
   /dewey:analyze --compare

3. Split new files proactively when they approach 400 lines

📈 Progress Tracking
==================================================
Starting Point:  125,340 tokens (2026-02-03)
Current State:   92,100 tokens (2026-02-10)
Net Change:      -33,240 tokens (-26.5%)

Excellent work! Your optimizations have significantly improved
context efficiency. This is exactly the kind of progress we want to see.
```
</example_output>
