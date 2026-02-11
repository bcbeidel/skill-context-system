# Analysis Metrics Reference

This reference explains what each metric means and how to interpret it.

## Core Metrics

### Total Files
**What it is:** Count of all files analyzed in the directory

**What it indicates:**
- Overall context size
- Organization complexity
- Management overhead

**Optimal range:**
- Small projects: 10-30 files
- Medium projects: 30-100 files
- Large projects: 100-300 files
- Beyond 300: Consider subdirectories

**Red flags:**
- Too many (>300): Hard to navigate, high overhead
- Too few (<5 with high tokens): Likely monolithic files

### Total Tokens
**What it is:** Estimated token count across all files

**What it indicates:**
- Context window usage
- API cost implications
- Loading performance

**Optimal range:**
- Depends on use case and model
- Claude Code context: <100K tokens for responsiveness
- Larger projects: Consider selective loading

**Red flags:**
- Sudden spikes (>20% increase)
- Sustained growth without optimization
- Exceeding your practical limits

### Total Lines
**What it is:** Sum of all lines across files

**What it indicates:**
- Overall content volume
- Reading complexity
- Navigation difficulty

**Correlation with tokens:**
- Typically 6-12 tokens per line
- Higher ratio (>15): Verbose content
- Lower ratio (<5): Code or structured data

### Average Tokens/File
**What it is:** Mean token count per file

**What it indicates:**
- File size consistency
- Organization granularity
- Reading load per file

**Optimal range:**
- 500-2000 tokens per file (sweet spot)
- Scannable in ~30 seconds
- Focused topic coverage

**Red flags:**
- Very high (>5000): Files too large, split needed
- Very low (<100): Too granular, consolidate

## Distribution Metrics

### Size Buckets

**<500 tokens:**
- Quick reference files
- Should be majority of files (60-80%)
- Easy to scan and load

**500-2000 tokens:**
- Detailed documentation
- Good size for focused topics
- Optimal range (20-30% of files)

**2000-5000 tokens:**
- Comprehensive guides
- Approaching upper limit
- Should be <10% of files

**>5000 tokens:**
- Too large for effective use
- Should be split
- Goal: 0-2% of files

### Distribution Balance

**Healthy distribution:**
```
<500 tokens      ████████████████  (70%)
500-2000 tokens  ██████            (25%)
2000-5000 tokens █                 (4%)
>5000 tokens     ▌                 (1%)
```

**Unhealthy distribution (top-heavy):**
```
<500 tokens      ██                (10%)
500-2000 tokens  ████              (20%)
2000-5000 tokens ████████          (40%)
>5000 tokens     ██████            (30%)
```
This indicates lack of organization and splitting.

## Efficiency Metrics

### Tokens Per Line (T/L)

**What it is:** Average tokens per line of text

**Interpretation:**
- 5-8: Concise, code-like
- 8-12: Optimal (clear prose)
- 12-15: Slightly verbose
- >15: Very verbose, compression opportunity

**Context matters:**
- Code files: Lower T/L (5-8) is normal
- Documentation: 8-12 is optimal
- Verbose explanations: >12 suggests compression opportunity

### Large File Count

**What it is:** Files exceeding 500 lines

**Why 500 lines:**
- Difficult to scan quickly
- Hard to navigate
- Challenges selective citation
- Often contains multiple topics

**Targets:**
- Mature projects: 0 large files
- Active projects: <5% of files
- New projects: Acceptable initially, but plan to split

### Variance/Std Deviation

**What it is:** Consistency of file sizes

**Interpretation:**
- Low variance: Consistent sizing (good)
- High variance: Mix of tiny and huge files (needs organization)

**Why it matters:**
- Consistency helps navigation
- Predictable load times
- Easier to maintain

## Trend Metrics (Comparison Mode)

### Token Change Percentage

**Interpretation:**
- < -10%: Significant optimization (excellent!)
- -10% to -5%: Good optimization
- -5% to +5%: Stable (acceptable)
- +5% to +20%: Growing (monitor)
- > +20%: Alert! Investigate immediately

### File Count Change

**Growing file count (positive):**
- May indicate: New features, documentation expansion
- Monitor: Is token/file ratio staying reasonable?

**Shrinking file count (negative):**
- May indicate: Consolidation, cleanup
- Verify: Is information being lost or properly archived?

### Large File Trend

**Goal:** Decreasing over time

**Interpretation:**
- Decreased: Splitting efforts working
- Increased: New content being added without organization
- Stable at 0: Excellent maintenance

## Actionable Thresholds

Use these thresholds for decision-making:

| Metric | Warning | Urgent |
|--------|---------|--------|
| File lines | 400 | 600 |
| File tokens | 3000 | 5000 |
| Total tokens | 80K | 120K |
| Large files | 3 | 5 |
| Tokens/line | 15 | 20 |

**Warning:** Plan optimization
**Urgent:** Take action immediately
