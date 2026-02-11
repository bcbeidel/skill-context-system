---
description: Analyze context usage and generate actionable optimization recommendations
allowed-tools: Bash(python3 *)
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

- Directory path (default: `context` directory)
- `--detailed` - Include file-by-file breakdown
- `--baseline` - Save analysis as baseline for future comparison
- `--threshold N` - Custom "large file" threshold (default: 500 lines)

**Arguments string**: $ARGUMENTS

## Implementation Steps

### Step 1: Run the Python Analysis Script

The Python script collects deterministic metrics (file sizes, line counts, token counts).

**Important**: Use the full absolute path to ensure it works:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/analyze_directory.py" ${ARGUMENTS:-context}
```

The script outputs:
- Total files, tokens, lines, bytes
- Token distribution by size buckets
- Largest files by token count
- Files exceeding threshold (>500 lines)

### Step 2: Review the Python Output

The Python script provides structured metrics. Read this data carefully - it's the foundation for your recommendations.

### Step 3: Generate Your Analysis Report

**As Claude**, interpret the metrics and provide actionable recommendations:

Provide a comprehensive analysis report with:

#### Issues Detection (Prioritized)
- 🔴 **High Priority**: Immediate action needed
  - Large files (>500 lines) → `/dewey:split file.md`
  - Dead links → Manual fixes needed
  - Critical duplicates

- 🟡 **Medium Priority**: Should address soon
  - Unused files
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

🔴 High Priority (2 issues)
  1. Large files detected (2 files >500 lines)
     → /dewey:split IMPLEMENTATION_PLAN.md
     → /dewey:split .seed-prompt.md
     Impact: ~15,000 tokens saved

  2. Duplicate content found (~15% duplication)
     → Manual review recommended
     Impact: ~18,000 tokens saved

💡 Recommendations
==================================================

Quick Wins:
  1. Split IMPLEMENTATION_PLAN.md (5 min, 7,500 tokens)
  2. Review duplicate files (10 min)

📈 Potential Impact
==================================================
Current:    125,340 tokens
Optimized:  ~87,000 tokens
Savings:    38,000 tokens (30% reduction)

💾 Next Steps
==================================================
1. /dewey:split IMPLEMENTATION_PLAN.md
2. /dewey:split .seed-prompt.md
3. Review duplicate files manually
```

## Save Results

If `--baseline` flag is present, the script automatically saves baseline data to `~/.claude/analytics/baseline.json`.

## Integration

Works with:
- `/dewey:split` - Acts on identified large files
- Other optimization commands (to be implemented)

---

**Process directory**: $ARGUMENTS
