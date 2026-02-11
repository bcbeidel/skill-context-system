# Weekly Dashboard Report Workflow

<objective>
Generate a weekly dashboard showing the last 7 days of context health, recent changes, and quick wins.
</objective>

<required_reading>
Before proceeding, read these references:
- `references/dashboard-design.md` - Dashboard principles
- `references/kpis-tracking.md` - Understanding KPIs
</required_reading>

<process>

## Step 1: Execute Report Script

Run the report generation script:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/report/scripts/generate_report.py --weekly
```

**What this script does:**
- Loads current baseline from `~/.claude/analytics/baseline.json`
- Looks for historical data (previous reports, analysis runs)
- Calculates 7-day trends if data exists
- Identifies changes in the last week
- Flags new issues or improvements

**Expected output:**
- Current metrics
- Week-over-week changes (if previous data exists)
- List of recent activities (splits, optimizations)
- KPI status

## Step 2: Handle Data Availability

### If Historical Data Exists

Great! You have trend data. Proceed to Step 3.

### If No Historical Data

**First-time setup scenario:**

The script will indicate no historical data exists. Generate a baseline report:

```
📊 Weekly Context Health Dashboard
==================================================

📅 Week of: [date range]
🆕 First Report - Baseline Established

📈 Current Metrics
==================================================
[Show current state from baseline.json]

💡 Getting Started
==================================================

This is your first dashboard! To track trends:

1. Run analysis regularly:
   /dewey:analyze --baseline  (updates baseline)

2. Generate weekly reports:
   /dewey:report --weekly

3. Compare progress:
   /dewey:analyze --compare

📅 Next Steps
==================================================
• Save this report as your starting point
• Run /dewey:analyze weekly
• Check back next week to see trends
```

Return early with this setup guidance.

## Step 3: Analyze Trend Data

You (Claude) will receive trend data. Analyze for:

### Positive Trends ✅

**Token reduction:**
- Tokens decreased week-over-week
- Successful optimization
- Maintained or improved quality

**File health:**
- Large files split
- Better organization
- Improved structure

**Proactive maintenance:**
- Issues addressed before critical
- Regular optimization
- Consistent monitoring

### Concerning Trends ⚠️

**Context growth:**
- Tokens increasing without optimization
- New large files added
- Accumulating technical debt

**Quality degradation:**
- More dead links
- Increasing duplication
- Files growing unchecked

**Neglect indicators:**
- No optimization activity
- Growing issue count
- Warnings becoming failures

### Stability ➡️

**Steady state:**
- Minimal week-over-week change (<5%)
- Consistent file count
- Maintained quality

## Step 4: Generate Weekly Dashboard

Format the dashboard following this structure:

```markdown
# 📊 Weekly Context Health Dashboard

**Week of:** [Start Date] - [End Date]
**Generated:** [Timestamp]

---

## 📈 Summary

| Metric | Current | Last Week | Change | Trend |
|--------|---------|-----------|--------|-------|
| Files | [count] | [count] | [+/-] | [emoji] |
| Total Tokens | [count] | [count] | [+/-%] | [emoji] |
| Avg Tokens/File | [count] | [count] | [+/-%] | [emoji] |
| Large Files (>500) | [count] | [count] | [+/-] | [emoji] |
| Token Budget | [%] | [%] | [+/-%] | [emoji] |

**Trend Legend:**
- ✅ Improved (decreased)
- ⚠️ Growing (increased)
- ➡️ Stable (< 5% change)

---

## 🎯 This Week's Highlights

[Choose one category based on data:]

### ✅ Wins This Week
[If positive changes]
- 🎉 [Major accomplishment]
- ✨ [Improvement achieved]
- 💪 [Quality enhancement]

### ⚠️ Concerns This Week
[If negative changes]
- 📈 [Growing issue]
- 🔴 [New problem]
- ⏰ [Needs attention]

### ➡️ Stable Health
[If no major changes]
- ✅ Context health maintained
- 📊 Metrics within target ranges
- 🎯 Continue current practices

---

## 📊 Detailed Metrics

### File Health

**Size Distribution:**
```
<500 lines      [██████████] [count] files ([%]%)
500-1000 lines  [██]         [count] files ([%]%)
>1000 lines     [▌]          [count] files ([%]%)
```

**Changes:**
- Files added: [count] ([+tokens])
- Files removed: [count] ([-tokens])
- Files split: [count] ([-tokens saved])

### Token Efficiency

**Current Usage:**
- Total: [count] tokens
- Budget: [%]% of [limit]
- Efficiency: [tokens/file] avg

**Trend:**
- Week change: [+/-%]
- Direction: [Improving/Growing/Stable]
- Projection: [estimate for next week]

### Quality Metrics

**Issues:**
- Large files: [count]
- Dead links: [count]
- Duplication: [%]%

**Status:**
[All green / Some concerns / Action needed]

---

## 💡 Recommendations

[Priority-ordered actions based on data:]

### 🔴 High Priority
[If critical issues exist]
1. [Specific action with command]
2. [Second priority action]

### 🟡 Medium Priority
[If warnings exist]
1. [Proactive action]
2. [Optimization opportunity]

### 🟢 Maintenance
[Always include]
1. Continue regular analysis: `/dewey:analyze --baseline`
2. Address issues proactively
3. Maintain current quality practices

---

## 📅 Week-Over-Week Comparison

### Activity This Week
[List specific changes if tracked]
- [Date]: Split IMPLEMENTATION_PLAN.md (saved 7.5K tokens)
- [Date]: Archived old documentation (saved 5K tokens)
- [Date]: Fixed 3 dead links

### Impact Assessment
- **Token savings:** [total tokens saved]
- **Quality improvement:** [specific improvements]
- **Time invested:** [estimated hours]
- **ROI:** [savings per hour of effort]

---

## 🎯 Goals for Next Week

Based on current state and trends:

**If doing well:**
1. ✅ Maintain current health
2. 📊 Monitor new additions
3. 🔄 Run weekly check: `/dewey:report`

**If issues exist:**
1. 🔴 [Top priority action]
2. 🟡 [Second priority]
3. 📊 Re-assess with `/dewey:analyze --compare`

---

## 📈 Historical Trend

[If multiple weeks of data]

```
Tokens Over Time:
Week 1: [count] ████████████████████
Week 2: [count] ███████████████
Week 3: [count] ██████████████
Week 4: [count] ██████████████ ← Current
```

**Overall trend:** [Improving/Growing/Stable]
**Since start:** [total change] ([%]% change)

---

## 📝 Notes

_This dashboard shows a 7-day snapshot of context health._
_For detailed analysis, run `/dewey:analyze`._
_For quality validation, run `/dewey:check`._

**Next report:** [Date next week]

---

_Generated by Dewey Context Optimizer_
```

## Step 5: Save Dashboard

Write the dashboard to `.claude/analytics/dashboard.md`:

1. Create directory if needed: `~/.claude/analytics/`
2. Write markdown to `dashboard.md`
3. Confirm save location to user

## Step 6: Provide Next Steps

Based on dashboard content:

**If health is good:**
```
✅ Weekly dashboard generated!

Your context health is good. Keep it up!

📍 Saved to: ~/.claude/analytics/dashboard.md

📅 Next actions:
• Run weekly: /dewey:report
• Monitor growth: /dewey:analyze --compare
• Validate quality: /dewey:check
```

**If issues found:**
```
⚠️ Weekly dashboard generated!

Issues need attention this week:
1. [Top priority]
2. [Second priority]

📍 Saved to: ~/.claude/analytics/dashboard.md

📅 Next actions:
1. Address issues above
2. Re-run: /dewey:analyze --compare
3. Next report: /dewey:report (in 7 days)
```

</process>

<success_criteria>
Weekly report is complete when:
- ✅ Current metrics displayed
- ✅ Week-over-week trends shown (if data exists)
- ✅ Highlights identified (wins or concerns)
- ✅ Recommendations prioritized
- ✅ Dashboard saved to file
- ✅ Clear next steps provided
- ✅ User knows when to run next report
</success_criteria>

<example_output>

```markdown
# 📊 Weekly Context Health Dashboard

**Week of:** Feb 3 - Feb 10, 2026
**Generated:** 2026-02-10 16:30:00

---

## 📈 Summary

| Metric | Current | Last Week | Change | Trend |
|--------|---------|-----------|--------|-------|
| Files | 45 | 47 | -2 | ✅ |
| Total Tokens | 92,100 | 125,340 | -26.5% | ✅ |
| Avg Tokens/File | 2,047 | 2,667 | -23.2% | ✅ |
| Large Files (>500) | 0 | 2 | -2 | ✅ |
| Token Budget | 46% | 63% | -17% | ✅ |

**Trend Legend:**
- ✅ Improved (decreased)
- ⚠️ Growing (increased)
- ➡️ Stable (< 5% change)

---

## 🎯 This Week's Highlights

### ✅ Wins This Week

- 🎉 **Major optimization completed!** Reduced context by 26.5%
- ✨ **Eliminated all large files** - Split 2 files >500 lines
- 💪 **Improved efficiency** - Better tokens/file ratio

**Impact:** 33,240 tokens saved = faster loading & better focus

---

## 📊 Detailed Metrics

### File Health

**Size Distribution:**
```
<500 lines      [██████████████████] 45 files (100%)
500-1000 lines  []                    0 files (0%)
>1000 lines     []                    0 files (0%)
```

**Changes:**
- Files split: 2 (IMPLEMENTATION_PLAN.md, .seed-prompt.md)
- Reference files created: 5 (in references/ subdirs)
- Net change: -2 files (consolidation)

### Token Efficiency

**Current Usage:**
- Total: 92,100 tokens
- Budget: 46% of 200,000
- Efficiency: 2,047 tokens/file avg

**Trend:**
- Week change: -26.5% 📉 (excellent!)
- Direction: Improving ✅
- Projection: Stable at ~90K if no major additions

### Quality Metrics

**Issues:**
- Large files: 0 ✅
- Dead links: 0 ✅
- Duplication: 8% ✅

**Status:** All green! 🎉

---

## 💡 Recommendations

### 🟢 Maintenance

1. Continue regular analysis: `/dewey:analyze --baseline`
2. Keep files under 400 lines proactively
3. Run quality checks before commits: `/dewey:check`

**Optional:**
- Update baseline to reflect current state
- Consider consolidating small reference files (<50 lines)

---

## 📅 Week-Over-Week Comparison

### Activity This Week

- **Feb 5**: Split IMPLEMENTATION_PLAN.md → saved 7,500 tokens
- **Feb 5**: Split .seed-prompt.md → saved 6,000 tokens
- **Feb 7**: Archived backup files → saved 1,000 tokens

### Impact Assessment

- **Token savings:** 33,240 tokens (26.5% reduction)
- **Quality improvement:** Zero large files, improved navigation
- **Time invested:** ~30 minutes
- **ROI:** 1,108 tokens saved per minute

---

## 🎯 Goals for Next Week

Based on current excellent health:

1. ✅ Maintain current health
2. 📊 Monitor new additions (keep files <400 lines)
3. 🔄 Run weekly check: `/dewey:report`

---

## 📝 Notes

_This dashboard shows a 7-day snapshot of context health._
_For detailed analysis, run `/dewey:analyze`._
_For quality validation, run `/dewey:check`._

**Next report:** February 17, 2026

---

_Generated by Dewey Context Optimizer_
```

</example_output>
