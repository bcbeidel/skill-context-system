---
description: Analyze context usage and generate actionable optimization recommendations
---

# Analyze Context

Perform comprehensive analysis of context files to identify optimization opportunities. Examines token usage, file sizes, duplication patterns, and provides prioritized recommendations.

## How to Use

```
/dewey:analyze
/dewey:analyze context/
/dewey:analyze . --detailed
/dewey:analyze context/ --baseline
```

## What It Analyzes

- **Token usage**: Total tokens and distribution across files
- **File sizes**: Line counts and identification of large files
- **Efficiency**: Token-per-file ratios and waste
- **Patterns**: Potential duplicates and structure issues
- **Best practices**: Compliance with context organization principles

## Arguments

- Directory path (default: current directory)
- `--detailed` - Include file-by-file breakdown
- `--baseline` - Save analysis as baseline for future comparison
- `--threshold N` - Custom "large file" threshold (default: 500 lines)

**Arguments string**: $ARGUMENTS

## Implementation Steps

### 1. Scan Directory

Use Python helper to collect data:

```python
from pathlib import Path
from dewey.skills.analyze_skill import analyze_directory, generate_analysis_prompt

# Parse arguments
args = "$ARGUMENTS".split()
directory = Path(args[0]) if args else Path.cwd()
detailed = "--detailed" in "$ARGUMENTS"
baseline = "--baseline" in "$ARGUMENTS"

# Scan and analyze
data = analyze_directory(directory)

# Generate prompt for Claude
prompt = generate_analysis_prompt(data, detailed=detailed)
```

### 2. Analyze Data

As Claude, you will receive structured data about:
- Total files, tokens, lines, bytes
- Distribution across size buckets
- List of large files (>500 lines)
- Top files by token count

### 3. Generate Report

Provide a comprehensive analysis report with:

#### Issues Detection (Prioritized)
- 🔴 **High Priority**: Immediate action needed
  - Large files (>500 lines) → `/dewey:split file.md`
  - Dead links → `/dewey:check --fix-links`
  - Critical duplicates → `/dewey:dedupe`

- 🟡 **Medium Priority**: Should address soon
  - Unused files → `/dewey:archive --unused`
  - Inefficient organization
  - Verbose documentation

- 🟢 **Low Priority**: Optional improvements
  - Minor optimizations
  - Style improvements

#### Specific Recommendations
For each issue, provide:
- Exact command to run (e.g., `/dewey:split IMPLEMENTATION_PLAN.md`)
- Estimated token savings
- Time estimate
- Priority ranking

#### Optimization Potential
- Current total tokens
- Estimated tokens after optimization
- Percentage reduction possible
- Efficiency gains

#### Next Steps
Prioritized action list:
1. Quick wins (high impact, low effort)
2. Medium effort tasks
3. Long-term improvements

## Example Output

```
📊 Context Analysis Report
==================================================

📁 Directory: context/
📅 Analyzed: 2026-02-10

📈 Summary Statistics
==================================================
Total Files:        47
Total Tokens:       125,340
Total Lines:        18,450
Average File:       2,667 tokens/file
Largest File:       9,375 tokens (IMPLEMENTATION_PLAN.md)

📊 Distribution
==================================================
<500 tokens        32 files  (68%)  ████████████████
500-2000 tokens    10 files  (21%)  ████
2000-5000 tokens    3 files   (6%)  █
>5000 tokens        2 files   (4%)  █

⚠️  Issues Detected
==================================================

🔴 High Priority (3 issues)
  1. Large files detected (2 files >500 lines)
     → /dewey:split IMPLEMENTATION_PLAN.md
     → /dewey:split .seed-prompt.md
     Impact: ~15,000 tokens saved

  2. Duplicate content found (~15% duplication)
     → /dewey:dedupe context/
     Impact: ~18,000 tokens saved

  3. Dead links detected (5 broken wikilinks)
     → /dewey:check --fix-links
     Impact: Improved navigation

💡 Recommendations
==================================================

Quick Wins:
  1. Split IMPLEMENTATION_PLAN.md (5 min, 7,500 tokens)
  2. Fix dead links (2 min)

📈 Potential Impact
==================================================
Current:    125,340 tokens
Optimized:  ~87,000 tokens
Savings:    38,000 tokens (30% reduction)

💾 Next Steps
==================================================
1. /dewey:split IMPLEMENTATION_PLAN.md
2. /dewey:split .seed-prompt.md
3. /dewey:dedupe context/
```

## Save Results

If `--baseline` flag is present:

```python
from dewey.skills.analyze_skill import save_baseline

baseline_path = save_baseline(data)
print(f"\n✓ Baseline saved to: {baseline_path}")
```

## Integration

Works with:
- `/dewey:split` - Acts on identified large files
- `/dewey:report` - Uses data for trend analysis
- `/dewey:optimize` - Comprehensive optimization
- `/dewey:check` - Quality validation

---

**Process directory**: $ARGUMENTS
