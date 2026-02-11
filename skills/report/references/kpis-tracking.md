# KPIs Tracking Reference

Key Performance Indicators for measuring and tracking context health over time.

## Primary KPIs

### 1. Total Token Count

**What it measures:** Overall context size

**Target ranges:**
- Excellent: <80K tokens
- Good: 80-120K tokens
- Acceptable: 120-160K tokens
- Warning: 160-200K tokens
- Critical: >200K tokens

**Track:**
- Absolute value
- Week-over-week change
- Month-over-month change
- Trend direction

**Why it matters:**
- Affects loading performance
- Impacts context window usage
- Indicates optimization need

### 2. Large File Count

**What it measures:** Files exceeding 500 lines

**Target:** 0 files >500 lines

**Track:**
- Current count
- Trend over time
- Average size of large files

**Why it matters:**
- Direct quality indicator
- Scanability measure
- Optimization target

### 3. Average Tokens Per File

**What it measures:** Mean token count across all files

**Target ranges:**
- Excellent: 500-2000 tokens/file
- Good: 2000-3000 tokens/file
- Acceptable: 3000-4000 tokens/file
- Warning: >4000 tokens/file

**Track:**
- Current average
- Distribution
- Outliers

**Why it matters:**
- Efficiency indicator
- File size consistency
- Organization quality

### 4. Quality Score

**What it measures:** Overall context health grade (A-F)

**Components:**
- File size compliance (30%)
- Token efficiency (25%)
- Link quality (25%)
- Duplication level (20%)

**Target:** Grade A or B

**Track:**
- Current grade
- Component scores
- Trend over time

**Why it matters:**
- Holistic health indicator
- Easy to communicate
- Motivational metric

### 5. Token Budget Utilization

**What it measures:** % of practical token limit used

**Target ranges:**
- Excellent: <60%
- Good: 60-80%
- Warning: 80-100%
- Critical: >100%

**Track:**
- Current percentage
- Rate of change
- Time to limit

**Why it matters:**
- Headroom indicator
- Growth sustainability
- Planning metric

## Secondary KPIs

### 6. File Count

**What it measures:** Total number of context files

**Track for:**
- Overall growth
- File creation rate
- Consolidation opportunities

**Context-dependent target**

### 7. Duplication Percentage

**What it measures:** % of content that's duplicated

**Target:**
- Excellent: <5%
- Good: 5-10%
- Acceptable: 10-20%
- Poor: >20%

**Why it matters:**
- Waste indicator
- Maintenance burden
- Optimization opportunity

### 8. Dead Link Count

**What it measures:** Number of broken internal links

**Target:** 0

**Track:**
- Current count
- Fix rate
- New dead link rate

**Why it matters:**
- Quality indicator
- Navigation health
- Maintenance quality

### 9. Optimization Frequency

**What it measures:** How often optimization actions are taken

**Track:**
- Days since last analysis
- Days since last optimization
- Actions per week/month

**Target:** Regular cadence (weekly analysis)

**Why it matters:**
- Process indicator
- Proactive vs reactive
- Sustainability measure

### 10. Response Time

**What it measures:** Time from issue identification to resolution

**Track:**
- Average days to fix
- Issue backlog
- Issue age distribution

**Target:** <7 days for warnings, <1 day for critical

**Why it matters:**
- Process effectiveness
- Technical debt accumulation
- Team responsiveness

## Composite Metrics

### Context Health Index

**Formula:**
```
Health Index = (
  (100 - TokenBudget%) * 0.30 +
  (FileSizeScore) * 0.25 +
  (LinkQuality) * 0.25 +
  (100 - Duplication%) * 0.20
)
```

**Range:** 0-100
- 90-100: Excellent
- 80-89: Good
- 70-79: Fair
- 60-69: Poor
- <60: Critical

### Optimization ROI

**Formula:**
```
ROI = TokensSaved / TimeInvested
```

**Track:**
- Per optimization action
- Weekly average
- Monthly cumulative

**Use for:**
- Prioritizing actions
- Justifying time spent
- Measuring efficiency

### Maintenance Cadence Score

**Formula:**
```
Score = (
  AnalysisFrequency * 0.40 +
  OptimizationFrequency * 0.30 +
  IssueResponseTime * 0.30
)
```

**Measures:** Process consistency

### Quality Velocity

**Formula:**
```
Velocity = (CurrentQuality - PreviousQuality) / TimePeriod
```

**Measures:** Rate of quality improvement

**Positive:** Improving
**Negative:** Degrading
**Zero:** Stable

## Dashboard KPI Display

### Summary Table Format

```markdown
| KPI | Current | Target | Status | Trend |
|-----|---------|--------|--------|-------|
| Total Tokens | 92K | <120K | ✅ Good | ↓ |
| Large Files | 0 | 0 | ✅ Excellent | → |
| Quality Score | B+ | A/B | ✅ Good | ↑ |
| Token Budget | 46% | <80% | ✅ Excellent | ↓ |
| Duplication | 8% | <10% | ✅ Good | → |
```

### KPI Cards

```markdown
## 📊 Key Metrics

**Total Tokens**
└─ 92,100 (↓26.5% from last week) ✅

**Large Files**
└─ 0 files >500 lines ✅

**Quality Score**
└─ B+ (↑from B last week) ✅

**Token Budget**
└─ 46% of 200K limit ✅
```

### Trend Charts

```markdown
## 📈 Trends

**Tokens Over Time:**
Week 1: 125K ████████████████████
Week 2: 110K ████████████████
Week 3:  95K ████████████
Week 4:  92K ███████████── ✅ Current

**Quality Score:**
Week 1: C   ██████
Week 2: B-  ████████
Week 3: B   █████████
Week 4: B+  ██████████── ✅ Current
```

## KPI Targets by Project Phase

### Startup Phase

**Focus:** Establishing baseline
- Total Tokens: Any (measuring)
- Quality Score: C+ acceptable
- Large Files: <5
- Optimization: Monthly

### Growth Phase

**Focus:** Controlled expansion
- Total Tokens: Growing <15%/month
- Quality Score: B minimum
- Large Files: <3
- Optimization: Bi-weekly

### Mature Phase

**Focus:** Excellence and stability
- Total Tokens: Stable ±5%
- Quality Score: A/B target
- Large Files: 0
- Optimization: Weekly maintenance

### Maintenance Phase

**Focus:** Sustaining quality
- Total Tokens: Stable
- Quality Score: A target
- Large Files: 0
- Optimization: As needed, monitored weekly

## Tracking Tools

### Manual Tracking

**Simple spreadsheet:**
```
Date | Tokens | Files | Large | Quality | Notes
2026-02-01 | 125K | 47 | 2 | C | Baseline
2026-02-08 | 110K | 45 | 1 | B- | Split PLAN.md
2026-02-15 | 92K | 45 | 0 | B+ | Split prompt
```

### Automated Tracking

**Use baseline.json:**
- Captures metrics automatically
- Compare over time
- Generate trend data

**Store history:**
- `~/.claude/analytics/history/`
- One snapshot per analysis
- Enable trend analysis

## Reporting KPIs

### Weekly Report

**Include:**
- 5 primary KPIs
- Week-over-week changes
- Status indicators
- Brief interpretation

**Format:** Compact table

### Monthly Report

**Include:**
- All primary KPIs
- Selected secondary KPIs
- Month-over-month changes
- Trend analysis
- Composite metrics

**Format:** Detailed tables + charts

### Executive Summary

**Include:**
- Health Index
- 1-2 most critical KPIs
- Overall trend
- Key action needed

**Format:** 3-4 sentences maximum

## KPI-Driven Actions

### Trigger-Based Actions

**If Total Tokens >160K:**
```
→ Run full analysis
→ Identify optimization opportunities
→ Execute top 3 actions
→ Re-measure
```

**If Large Files >2:**
```
→ Split all files >500 lines
→ Target: 0 large files
→ Verify with quality check
```

**If Quality Score <C:**
```
→ Run diagnostic
→ Address all failures
→ Fix critical warnings
→ Improve to B minimum
```

**If Token Budget >90%:**
```
→ Emergency optimization
→ Archive old content
→ Split largest files
→ Reduce to <80%
```

## KPI Evolution

### As Context Matures

**Early:**
- Focus on measurement
- Establish baselines
- Identify patterns

**Middle:**
- Set targets
- Optimize actively
- Track improvements

**Mature:**
- Maintain excellence
- Proactive monitoring
- Continuous improvement

### Adjusting Targets

**As team improves:**
- Tighten targets
- Raise quality bar
- Reduce tolerance

**As project scales:**
- Adjust absolute limits
- Maintain relative health
- Scale processes

## Best Practices

### Regular Measurement

**Frequency:**
- Weekly: Primary KPIs
- Monthly: All KPIs
- Quarterly: Deep analysis

### Consistent Methodology

**Always measure:**
- Same way
- Same tools
- Same conditions

### Trend Over Snapshot

**Focus on:**
- Direction
- Rate of change
- Consistency

### Actionable Metrics

**Choose KPIs that:**
- You can influence
- Drive decisions
- Matter to outcomes

### Celebrate Progress

**When KPIs improve:**
- Acknowledge effort
- Quantify impact
- Share success

## Common Mistakes

### Too Many KPIs

**Problem:** Tracking everything, acting on nothing

**Solution:** Focus on 5-7 key metrics

### Vanity Metrics

**Problem:** Measuring what looks good, not what matters

**Solution:** Choose actionable, relevant KPIs

### No Targets

**Problem:** Measuring without goals

**Solution:** Set clear targets for each KPI

### Ignoring Trends

**Problem:** Reacting to single data points

**Solution:** Look at 3+ period trends

### No Action

**Problem:** Measuring but not responding

**Solution:** Define trigger-based actions
