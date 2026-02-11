# Monthly Dashboard Report Workflow

<objective>
Generate a monthly dashboard showing 30-day trends, cumulative impact, and strategic insights.
</objective>

<required_reading>
Before proceeding, read:
- `references/dashboard-design.md` - Dashboard principles
- `references/trend-analysis.md` - Long-term trend interpretation
</required_reading>

<process>

## Step 1: Execute Monthly Report Script

Run with monthly flag:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/report/scripts/generate_report.py --monthly
```

**What this provides:**
- Current state metrics
- 30-day trend data (if available)
- Month-over-month comparison
- Cumulative changes
- Long-term patterns

## Step 2: Analyze Monthly Trends

Look for patterns over the longer timeframe:

### Strategic Patterns

**Sustained improvement:**
- Consistent token reduction
- Decreasing large file count
- Improving quality metrics
- Effective optimization routine

**Growth under control:**
- Context growing but optimized regularly
- New content balanced with cleanup
- Quality maintained despite growth

**Optimization cycles:**
- Periodic cleanup efforts
- Burst optimizations followed by stability
- Project-based context changes

**Concerning patterns:**
- Unchecked growth
- Accumulating technical debt
- Degrading quality metrics
- Lack of maintenance

## Step 3: Generate Monthly Dashboard

Use extended format with strategic focus:

```markdown
# 📊 Monthly Context Health Dashboard

**Month:** [Month Year]
**Period:** [Start Date] - [End Date]
**Generated:** [Timestamp]

---

## 🎯 Executive Summary

**Overall Health:** [Excellent/Good/Fair/Needs Attention]

**Key Metrics:**
- Total Tokens: [current] ([+/-]% vs last month)
- Files: [count] ([+/-] vs last month)
- Quality Score: [A-F grade]
- Optimization Activity: [High/Medium/Low]

**This Month:**
[1-2 sentence summary of the month's story]

---

## 📈 30-Day Trends

### Token Evolution

```
[Graph showing token count over month]
Week 1: [count] ████████████████████
Week 2: [count] ██████████████████
Week 3: [count] ███████████████
Week 4: [count] ████████████████ ← Current
```

**Analysis:**
- Starting point: [tokens]
- Current: [tokens]
- Net change: [difference] ([%]%)
- Average weekly change: [tokens/week]
- Trend: [Improving/Growing/Stable/Volatile]

### File Health Evolution

**Large Files Over Time:**
```
Week 1: [count] files >500 lines
Week 2: [count] files >500 lines
Week 3: [count] files >500 lines
Week 4: [count] files >500 lines ← Current
```

**Quality Metrics:**
```
Metric          Start   End    Change
─────────────────────────────────────
Files >500      [n]     [n]    [+/-]
Dead Links      [n]     [n]    [+/-]
Duplication     [%]     [%]    [+/-%]
Token Budget    [%]     [%]    [+/-%]
```

---

## 🏆 Monthly Achievements

[Highlight significant accomplishments]

### Major Wins 🎉
1. [Most impactful optimization]
   - Impact: [tokens saved or quality improvement]
   - Effort: [time invested]

2. [Second major win]
   - Impact: [metrics]
   - Effort: [time]

3. [Third achievement]
   - Impact: [metrics]

### Consistency Awards ⭐
- Ran [N] analyses this month
- Completed [N] optimizations
- Maintained quality score of [grade]
- Zero critical issues for [N] days

---

## ⚠️ Areas for Improvement

[Identify persistent or emerging issues]

### Recurring Issues
[Issues that appeared multiple times]

1. [Pattern identified]
   - Frequency: [how often]
   - Impact: [severity]
   - Root cause: [analysis]
   - Recommendation: [solution]

### Emerging Concerns
[New trends that may become problems]

1. [Trend observed]
   - First noticed: [date]
   - Current state: [metrics]
   - Projection: [if continues]
   - Preventive action: [recommendation]

---

## 📊 Monthly Statistics

### Activity Summary

**Optimization Actions:**
- Files split: [count]
- Files archived: [count]
- Dead links fixed: [count]
- Deduplication efforts: [count]

**Token Impact:**
- Added: [tokens from new content]
- Removed: [tokens from optimization]
- Net change: [total]

**Time Investment:**
- Analysis runs: [count] × ~[minutes] = [total time]
- Optimization work: ~[total time]
- Total: ~[time] invested

### ROI Analysis

**Value Generated:**
- Token reduction: [tokens]
- Quality improvements: [specific improvements]
- Faster loading: [estimated time saved]

**Time Invested:** [hours]
**ROI:** [value per hour]

---

## 🎯 Strategic Insights

[High-level analysis and recommendations]

### What's Working

[Patterns and practices that are effective]

1. [Effective practice]
   - Evidence: [data supporting this]
   - Continue: [how to maintain]

2. [Another success pattern]
   - Evidence: [metrics]
   - Expand: [how to leverage]

### What Needs Attention

[Strategic issues requiring focus]

1. [Strategic concern]
   - Evidence: [trend data]
   - Impact if unaddressed: [projection]
   - Recommended approach: [strategy]

### Optimization Opportunities

[Potential improvements not yet addressed]

1. [Opportunity]
   - Potential impact: [estimated benefit]
   - Effort required: [estimate]
   - Priority: [High/Medium/Low]

---

## 📅 Month-Over-Month Comparison

[If previous month data exists]

### Key Changes

| Metric | Last Month | This Month | Change | Status |
|--------|------------|------------|--------|--------|
| Total Tokens | [n] | [n] | [+/-%] | [emoji] |
| Files | [n] | [n] | [+/-] | [emoji] |
| Large Files | [n] | [n] | [+/-] | [emoji] |
| Quality Grade | [grade] | [grade] | [+/-] | [emoji] |

### Trend Analysis

**Positive trends continuing:**
- [Trend 1]
- [Trend 2]

**Improvements this month:**
- [What got better]
- [What improved]

**New concerns:**
- [What emerged]
- [What needs watching]

---

## 🎯 Goals for Next Month

Based on monthly analysis and trends:

### Primary Goals
1. [Most important goal]
   - Target: [specific metric]
   - Action: [what to do]

2. [Second goal]
   - Target: [metric]
   - Action: [approach]

3. [Third goal]
   - Target: [metric]
   - Action: [strategy]

### Maintenance Goals
- Run weekly analysis: `/dewey:analyze --baseline`
- Generate weekly reports: `/dewey:report`
- Validate quality: `/dewey:check` before commits

### Stretch Goals
[Optional improvements]
- [Ambitious goal]
- [Future optimization]

---

## 📈 Long-Term Trajectory

[If multiple months of data]

### Multi-Month Trend

```
Context Size Over Time:
[Month-3]: [tokens] ████████████████████
[Month-2]: [tokens] ███████████████████
[Month-1]: [tokens] ██████████████
[Current]: [tokens] ███████████████ ← Now
```

**Overall direction:** [Improving/Growing/Stable]
**Velocity:** [rate of change]
**Projection:** [estimated state in 3 months]

### Seasonal Patterns

[If enough history exists]
- [Pattern observed over time]
- [Cyclical changes noted]
- [Project-based fluctuations]

---

## 💡 Recommended Actions

### Immediate (This Week)
1. [Most urgent action]
2. [Second priority]

### Short-Term (This Month)
1. [Important action]
2. [Strategic task]
3. [Quality improvement]

### Long-Term (Next 3 Months)
1. [Strategic goal]
2. [Major optimization project]
3. [Process improvement]

---

## 📝 Notes & Observations

[Qualitative insights not captured in metrics]

**Context changes:**
- [Major project events affecting context]
- [Team changes]
- [Process changes]

**External factors:**
- [Product releases]
- [Documentation efforts]
- [Other relevant events]

**Lessons learned:**
- [Key insights from this month]
- [What worked well]
- [What to adjust]

---

## 📚 Resources

**For detailed analysis:**
- Run: `/dewey:analyze --compare`
- Review: Previous weekly reports

**For quality validation:**
- Run: `/dewey:check`
- Review: Quality criteria documentation

**For optimization:**
- Run: `/dewey:split [file]` for large files
- Consider: Archiving old content

---

**Next monthly report:** [Date next month]
**Weekly reports:** Generate with `/dewey:report --weekly`

---

_Generated by Dewey Context Optimizer_
```

</process>

<success_criteria>
Monthly report is complete when:
- ✅ 30-day trends analyzed
- ✅ Strategic insights provided
- ✅ Achievements celebrated
- ✅ Concerns identified with root causes
- ✅ Goals set for next month
- ✅ ROI calculated
- ✅ Dashboard saved to file
- ✅ Long-term trajectory assessed
</success_criteria>

