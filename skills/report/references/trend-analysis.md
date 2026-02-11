# Trend Analysis Reference

Guide for interpreting trends in context health metrics over time.

## Understanding Trends

### What is a Trend?

**Definition:** The general direction of change in a metric over time

**Components:**
- **Direction:** Up, down, or stable
- **Magnitude:** How much change
- **Velocity:** How fast the change
- **Consistency:** Steady or volatile

### Why Trends Matter More Than Absolutes

**Absolute value:** "You have 100K tokens"
- Tells you current state
- Doesn't indicate trajectory
- No sense of urgency

**Trend value:** "Tokens growing 15% per week"
- Tells you direction
- Indicates urgency
- Enables prediction

## Trend Categories

### Positive Trends ✅

**Decreasing waste:**
- Tokens going down
- Large files being split
- Duplication reducing
- Dead links being fixed

**Improving efficiency:**
- Better tokens/file ratio
- More consistent file sizes
- Higher quality scores
- Faster optimization cycles

**Maintaining quality:**
- Stable at good levels
- Proactive maintenance
- Issues addressed quickly

### Concerning Trends ⚠️

**Uncontrolled growth:**
- Tokens increasing >10% per period
- Large files accumulating
- Quality metrics degrading
- Technical debt growing

**Volatility:**
- Large swings period-to-period
- Inconsistent maintenance
- Reactive vs proactive
- No stable patterns

**Degradation:**
- Worsening quality scores
- Increasing issue counts
- Lengthening response times
- Growing technical debt

### Stable Trends ➡️

**Healthy stability:**
- Metrics in good ranges
- <5% variation
- Consistent practices
- Sustainable patterns

**Concerning stability:**
- Stuck at poor levels
- No improvement efforts
- Acceptance of problems
- Stagnation

## Interpreting Trend Data

### Rate of Change

**Calculate:**
```
Rate = (Current - Previous) / Previous * 100
```

**Interpret:**
- <5%: Stable
- 5-10%: Noticeable change
- 10-20%: Significant change
- >20%: Major change, investigate

### Velocity

**What it tells:**
- How fast metrics are changing
- When you'll hit limits
- Urgency of action needed

**Example:**
```
Tokens: 150K, growing 15K per week
At this rate: Will hit 200K limit in 3.3 weeks
Action needed: Within 2 weeks
```

### Consistency

**Patterns to look for:**

**Steady trend:**
```
Week 1: 100K
Week 2: 110K
Week 3: 120K
Week 4: 130K
```
→ Predictable, can plan response

**Volatile pattern:**
```
Week 1: 100K
Week 2: 140K
Week 3: 95K
Week 4: 135K
```
→ Unpredictable, investigate cause

**Stepped pattern:**
```
Week 1-3: 100K (stable)
Week 4: 150K (sudden jump)
Week 5-7: 150K (new stable)
```
→ Event-driven, normal if explained

## Multi-Metric Analysis

### Correlation Patterns

**Token growth + Stable file count:**
- Files getting larger
- Need splitting
- Quality degrading

**Token growth + Increasing file count:**
- New content being added
- Normal project growth
- Monitor rate

**Token decrease + Stable file count:**
- Successful optimization
- Better efficiency
- Good maintenance

**Token decrease + Decreasing file count:**
- Consolidation or archival
- Major cleanup
- Verify no data loss

### Leading vs Lagging Indicators

**Leading indicators** (predict future):
- Files approaching 500 lines
- Duplication increasing
- New content additions
- Slowing optimization pace

**Lagging indicators** (reflect past):
- Total token count
- Quality scores
- Large file count
- Issue resolution time

**Use leading indicators for prevention.**

## Trend Prediction

### Linear Projection

**When to use:** Steady, consistent trends

**Formula:**
```
Future Value = Current + (Rate * Periods)
```

**Example:**
```
Current: 100K tokens
Rate: +10K per week
Projection (4 weeks): 100K + (10K * 4) = 140K
```

### Threshold Alerts

**Set thresholds:**
- Warning: 80% of limit
- Critical: 100% of limit

**Calculate ETA:**
```
If growing 10K/week toward 200K limit:
Currently at 150K
Remaining: 50K
ETA to warning (160K): 1 week
ETA to critical (200K): 5 weeks
```

### Confidence Levels

**High confidence predictions:**
- Consistent trend for 3+ periods
- Low volatility
- Clear cause

**Low confidence predictions:**
- New trend (<3 periods)
- High volatility
- Unknown causes

**State confidence in reports.**

## Seasonal Patterns

### Project-Based Cycles

**Common pattern:**
```
Planning phase: Context grows (research, specs)
Development: Stable or slight growth
Pre-release: Cleanup, documentation grows
Post-release: Archival, context shrinks
```

**Recognition:**
- Recurring patterns
- Tied to project phases
- Predictable timing

**Response:**
- Plan optimization for appropriate phases
- Expect growth during research
- Schedule cleanup pre-release

### Team Cycles

**Patterns:**
- Week-long sprints: Weekly spikes
- Monthly releases: Monthly cleanup
- Quarterly planning: Quarterly growth

**Use patterns for:**
- Scheduling maintenance
- Setting expectations
- Optimizing workflow

## Anomaly Detection

### What is an Anomaly?

**Definition:** Data point significantly different from trend

**Examples:**
- Sudden 50% token increase
- Unexpected decrease
- Quality score drop

### Investigating Anomalies

**Questions to ask:**
1. **What changed?**
   - New files added?
   - Major refactor?
   - External content?

2. **When exactly?**
   - Pinpoint the time
   - Correlate with events
   - Check commit history

3. **Is it permanent?**
   - One-time event?
   - New baseline?
   - Temporary spike?

4. **Should we respond?**
   - Positive anomaly: Celebrate
   - Negative anomaly: Investigate
   - Neutral: Monitor

## Trend Communication

### For Positive Trends

**Structure:**
```
✅ [Metric] Improving

Current: [value] (↓[%] from last period)

What's working:
• [Practice 1]
• [Practice 2]

Continue:
[How to maintain]
```

### For Concerning Trends

**Structure:**
```
⚠️ [Metric] Growing

Current: [value] (↑[%] from last period)

If continues:
• [Consequence 1]
• [Consequence 2]

Action needed:
1. [Specific action]
2. [Follow-up]
```

### For Stable Trends

**Structure:**
```
➡️ [Metric] Stable

Current: [value] (±[%] from last period)

Status: [Good stability / Needs improvement]

[Appropriate recommendation]
```

## Multi-Period Trends

### Weekly vs Monthly vs Quarterly

**Weekly trends:**
- Tactical insights
- Immediate actions
- Short-term fluctuations

**Monthly trends:**
- Strategic patterns
- Medium-term direction
- Filter out noise

**Quarterly trends:**
- Strategic direction
- Long-term health
- Major patterns only

**Use appropriate timeframe for decisions.**

### Trend Strength

**Strong trend:**
- Consistent across periods
- Clear direction
- High confidence

**Weak trend:**
- Inconsistent
- Small changes
- Low confidence

**Report strength:**
```
Tokens decreasing (strong trend, 3 weeks consistent)
vs
Tokens decreasing (weak trend, volatile, just 1 week)
```

## Actionable Insights

### From Positive Trends

**Identify what's working:**
- Practices to continue
- Patterns to maintain
- Successes to replicate

**Example:**
```
Tokens reduced 30% over 3 weeks.

Working well:
• Weekly file splitting
• Proactive monitoring
• Quick issue resolution

Continue these practices!
```

### From Concerning Trends

**Identify interventions:**
- What needs to change
- When to act
- How to respond

**Example:**
```
Tokens growing 15% per week for 3 weeks.

Intervention needed:
• Stop adding unoptimized content
• Split 5 large files this week
• Run daily checks until stabilized

Target: Return to <10% weekly growth
```

### From Stable Trends

**Assess the stability:**
- Is this a good stable state?
- Or stuck at a problem level?

**For good stability:**
```
✅ Maintaining excellent health

Tokens stable at 90K (well below 200K limit)
All quality metrics in green
No issues accumulating

Continue current practices.
```

**For problematic stability:**
```
⚠️ Stable but sub-optimal

Tokens stable at 180K (90% of limit)
5 large files remain (not changing)
Quality stuck at C grade

Intervention needed to improve baseline.
```

## Trend Visualization

### Text-Based Charts

**Trend line:**
```
Tokens Over Time:
Week 1: 150K ████████████████████
Week 2: 135K █████████████████
Week 3: 120K ██████████████
Week 4: 100K ████████████ ← Current

Trend: ↓ Improving
Rate: -17K per week
```

**Direction indicators:**
```
↑ Growing (concerning)
↓ Decreasing (good for tokens)
→ Stable
↗ Slowly growing
↘ Slowly decreasing
```

### Trend Arrows in Tables

```
| Metric | Value | Trend | Status |
|--------|-------|-------|--------|
| Tokens | 100K | ↓ -10% | ✅ |
| Files | 45 | → +2% | ✅ |
| Large Files | 2 | ↓ -1 | ✅ |
```

## Best Practices

### Always Include Comparison

**Bad:**
```
Total tokens: 100,000
```

**Good:**
```
Total tokens: 100,000 (↓10,000 from last week, -9.1%)
```

### Interpret, Don't Just Report

**Bad:**
```
Tokens changed from 110K to 100K.
```

**Good:**
```
Tokens decreased 9.1% this week - excellent progress!
This is due to splitting 2 large files. If this trend continues,
we'll reach our 80K target in 2 weeks.
```

### Provide Context

**Bad:**
```
Growing 15% per week.
```

**Good:**
```
Growing 15% per week for 3 consecutive weeks.
This rate will exceed our 200K budget in 4 weeks.
Intervention needed now to avoid quality degradation.
```

### Set Expectations

**For predictions:**
```
If current trend continues:
• Best case: Stabilize at 85K in 2 weeks
• Likely case: Reach 80K in 3 weeks
• Confidence: High (consistent 3-week trend)
```

### Celebrate Improvements

**When trends are positive:**
```
🎉 Excellent trend!

Tokens reduced 25% over 2 weeks through:
• Consistent file splitting
• Regular monitoring
• Proactive optimization

Your efforts are paying off! Keep it up!
```

## Common Pitfalls

### Overreacting to Noise

**Problem:** Treating normal variation as a trend

**Solution:**
- Wait for 2-3 periods confirmation
- Consider volatility
- Look for causes

### Ignoring Early Signals

**Problem:** Waiting too long to act

**Solution:**
- Monitor leading indicators
- Set threshold alerts
- Act proactively

### Missing Context

**Problem:** Trend without explanation

**Solution:**
- Investigate causes
- Correlate with events
- Provide context

### Linear Assumptions

**Problem:** Assuming trends continue forever

**Solution:**
- Recognize limits
- Note external factors
- Adjust predictions
