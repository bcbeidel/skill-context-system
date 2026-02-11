# Dashboard Design Reference

Principles for creating effective, actionable context health dashboards.

## Core Principles

### 1. Scanability

**Goal:** User understands key insights in <30 seconds

**Techniques:**
- Executive summary at top
- Visual hierarchy (headings, spacing)
- Emoji indicators for quick scanning
- Tables for comparisons
- Charts for trends

**Anti-patterns:**
- Dense paragraphs
- Buried insights
- Inconsistent formatting
- No visual cues

### 2. Actionability

**Goal:** User knows exactly what to do next

**Techniques:**
- Specific commands (not vague suggestions)
- Prioritized recommendations
- Clear success criteria
- Links to relevant tools

**Good:**
```
❌ File too large
→ /dewey:split IMPLEMENTATION_PLAN.md
   Estimated time: 5 minutes
   Impact: 7,500 tokens saved
```

**Bad:**
```
Some files are large and should be split.
```

### 3. Context-Aware

**Goal:** Insights match user's situation

**Adapt messaging for:**
- **Excellent health:** Celebrate, maintain
- **Good health:** Acknowledge, minor suggestions
- **Issues present:** Specific actions, urgency
- **Critical state:** Clear priorities, step-by-step

### 4. Trend-Focused

**Goal:** Show direction, not just snapshot

**Always include:**
- Change from previous period
- Direction indicators (↑↓→)
- Trend interpretation (improving/concerning)
- Rate of change (velocity)

**Why:** Direction > Absolute values

### 5. Celebrate Wins

**Goal:** Positive reinforcement for good practices

**When to celebrate:**
- Successful optimizations
- Consistent monitoring
- Quality improvements
- Achieving goals

**How:**
- Dedicated "Wins" section
- Quantify impact
- Acknowledge effort
- Encourage continuation

## Visual Design

### Emoji Usage

**Status indicators:**
- ✅ Success, passing, improved
- ⚠️ Warning, approaching limit
- ❌ Failure, critical issue
- 🔴 Urgent priority
- 🟡 Medium priority
- 🟢 Low priority
- ➡️ Stable, no change
- 📈 Growing, increasing
- 📉 Decreasing, improving

**Content markers:**
- 📊 Data, metrics, statistics
- 💡 Insights, recommendations
- 🎯 Goals, objectives
- 🏆 Achievements, wins
- ⚡ Quick wins, easy actions
- 📅 Dates, schedules
- 📍 Locations, paths
- 🔍 Details, deep-dive

**Use consistently throughout dashboard.**

### Tables

**For comparisons:**
```markdown
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Tokens | 100K | 75K | -25% ✅ |
```

**For status:**
```markdown
| Check | Status | Details |
|-------|--------|---------|
| File sizes | ✅ Pass | All <500 lines |
| Links | ⚠️ Warn | 1 dead link |
```

### Charts (ASCII)

**Bar charts for distribution:**
```
<500 tokens      ████████████████  (70%)
500-2000 tokens  ████              (20%)
>2000 tokens     ██                (10%)
```

**Trend charts:**
```
Week 1: 125K ████████████████████
Week 2: 110K ████████████████
Week 3:  95K ████████████
Week 4:  90K ██████████── Current
```

### Sections

**Order matters:**
1. **Title & Summary** - Quick overview
2. **Key Metrics** - Numbers at a glance
3. **Highlights** - Wins or concerns
4. **Details** - Deep-dive data
5. **Recommendations** - What to do
6. **Next Steps** - Specific actions

**Visual separation:**
- Horizontal rules (`---`) between major sections
- Clear headings with emoji
- Whitespace for readability

## Content Guidelines

### Executive Summary

**Include:**
- Overall health status
- Key metric (1-2 most important)
- One-sentence story of the period
- Clear indication if action needed

**Keep brief:** 3-5 lines maximum

**Example:**
```
## 🎯 Executive Summary

**Health:** Excellent ✅
**Tokens:** 92K (↓26% this week)
**Story:** Major optimization completed, all large files eliminated.
**Action:** Maintain current practices.
```

### Metrics Section

**Show context:**
- Current value
- Previous value
- Change (absolute and %)
- Trend indicator

**Example:**
```
| Metric | Current | Last Week | Change | Trend |
|--------|---------|-----------|--------|-------|
| Tokens | 92,100 | 125,340 | -26.5% | ✅ |
```

### Trends Analysis

**Interpret, don't just report:**
- What the trend means
- Why it's happening (if known)
- What to expect if continues
- When to take action

**Example:**
```
**Token Trend:** ↓ Decreasing (excellent!)

Analysis: Successful file splitting this week reduced context by 26%.
This is a one-time improvement; expect stability next week around 90K.

Continue: Regular monitoring to maintain this level.
```

### Recommendations

**Structure:**
1. **Priority tier** (🔴 🟡 🟢)
2. **Specific action** (exact command)
3. **Estimated impact** (tokens saved, improvement)
4. **Estimated effort** (time required)

**Example:**
```
🔴 High Priority
1. Split PLAN.md
   → /dewey:split PLAN.md
   Impact: ~8K tokens saved
   Time: 5 minutes
```

### Historical Context

**If data exists:**
- Show multi-period trends
- Identify patterns
- Note milestones
- Project future

**Example:**
```
📈 Historical Trend

Tokens Over Time:
Month 1: 150K ████████████████████
Month 2: 125K ████████████████
Month 3:  90K ████████████ ← Current

Overall: Improving ✅
Rate: ~30K reduction per month
Projection: Stabilizing around 90K
```

## Frequency-Specific Design

### Weekly Dashboards

**Focus:**
- Recent changes
- Quick wins
- Immediate actions
- Short-term trends

**Keep concise:** 1-2 pages

**Tone:** Tactical, actionable

### Monthly Dashboards

**Focus:**
- Strategic insights
- Long-term patterns
- Cumulative impact
- Goals and ROI

**More detail:** 2-4 pages

**Tone:** Strategic, reflective

### Custom Dashboards

**Focus:**
- Specific comparison purpose
- Relevant metrics only
- Context for the comparison
- Targeted insights

**Variable length:** Match scope

**Tone:** Analytical, precise

## Common Patterns

### The "All Green" Dashboard

**Situation:** Everything is healthy

**Design:**
- Lead with celebration
- Highlight consistency
- Suggest maintenance actions
- Note any potential future issues

**Example:**
```
✅ Excellent Health!

All metrics in optimal ranges. Your consistent optimization
efforts are paying off.

Maintain:
• Weekly analysis
• Proactive splitting
• Quality checks
```

### The "Issues Found" Dashboard

**Situation:** Problems need attention

**Design:**
- Clear status (how bad?)
- Prioritized issues list
- Specific fix commands
- Time estimates
- Re-check instructions

**Example:**
```
⚠️ Issues Need Attention

3 files exceed 500 lines. Split these this week:

1. /dewey:split file1.md (5 min)
2. /dewey:split file2.md (5 min)
3. /dewey:split file3.md (5 min)

After fixing: /dewey:check
```

### The "Positive Trend" Dashboard

**Situation:** Things are improving

**Design:**
- Celebrate the trend
- Quantify improvement
- Credit good practices
- Encourage continuation

**Example:**
```
📈 Improving Trend!

Context reduced 40% over 3 weeks.

What's working:
• Regular file splitting
• Proactive optimization
• Weekly monitoring

Keep it up! 🎉
```

### The "Concerning Trend" Dashboard

**Situation:** Metrics degrading

**Design:**
- State concern clearly
- Show the trend
- Explain consequences
- Provide action plan

**Example:**
```
⚠️ Concerning Trend

Tokens growing 15% per week for 3 weeks.

If continues:
• Will exceed budget in 2 weeks
• Quality will degrade
• Performance will suffer

Action plan:
1. [Immediate action]
2. [Follow-up]
3. [Prevention]
```

## Pitfalls to Avoid

### Too Much Data

**Problem:** User overwhelmed, can't find insights

**Solution:**
- Summary first, details later
- Progressive disclosure
- Clear sections

### Too Little Context

**Problem:** Numbers without meaning

**Solution:**
- Always show comparison
- Interpret trends
- Explain significance

### Vague Recommendations

**Problem:** User unsure what to do

**Solution:**
- Specific commands
- Priority ordering
- Time estimates

### Inconsistent Formatting

**Problem:** Hard to scan, unprofessional

**Solution:**
- Use templates
- Consistent emoji usage
- Standard sections

### Missing Trends

**Problem:** Snapshot only, no direction

**Solution:**
- Always compare to previous
- Show rate of change
- Project future

### No Celebration

**Problem:** Feels like nagging, no positive reinforcement

**Solution:**
- Acknowledge improvements
- Celebrate wins
- Recognize effort

## Dashboard Quality Checklist

Before finalizing, verify:

**Structure:**
- [ ] Title and date clear
- [ ] Executive summary present
- [ ] Sections logically ordered
- [ ] Visual hierarchy clear

**Content:**
- [ ] Key metrics shown
- [ ] Trends included
- [ ] Changes from previous period
- [ ] Insights interpreted, not just data

**Actionability:**
- [ ] Recommendations specific
- [ ] Commands exact
- [ ] Priorities clear
- [ ] Time estimates provided

**Visual:**
- [ ] Emoji used consistently
- [ ] Tables formatted correctly
- [ ] Whitespace for readability
- [ ] Charts clear

**Tone:**
- [ ] Appropriate for situation
- [ ] Wins celebrated if applicable
- [ ] Issues stated clearly
- [ ] Next steps obvious

## Examples by Scenario

### Scenario: First-Time User

**Adapt for:**
- No historical data
- Setup guidance needed
- Educational tone

**Include:**
- What baseline means
- How to track trends
- When to run reports

### Scenario: Mature Project

**Adapt for:**
- Rich historical data
- Strategic insights
- ROI focus

**Include:**
- Long-term trends
- Cumulative impact
- Efficiency metrics

### Scenario: Crisis Mode

**Adapt for:**
- Critical issues
- Urgent action needed
- Clear priorities

**Include:**
- Severity assessment
- Step-by-step plan
- Expected timeline

### Scenario: Maintenance Mode

**Adapt for:**
- Stable state
- Preventive focus
- Consistency rewards

**Include:**
- Acknowledge stability
- Minor optimizations
- Continued monitoring
