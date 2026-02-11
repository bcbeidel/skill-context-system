# Standard Analysis Workflow

<objective>
Analyze a directory's context files and provide actionable optimization recommendations.
</objective>

<required_reading>
Before proceeding, read these references for context:
- `references/analysis-metrics.md` - Understanding what metrics mean
- `references/issue-detection.md` - How to identify and prioritize issues
</required_reading>

<process>

## Step 1: Parse Arguments

Extract directory path from `$ARGUMENTS`:
- If directory provided: use it
- If empty or just flags: use current directory (`.`)

Default directory: Current working directory

## Step 2: Execute Analysis Script

Run the Python analysis helper:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/analyze_directory.py $ARGUMENTS
```

**What this script does:**
- Scans all `.md` files in the directory
- Counts tokens using character-based estimation
- Counts lines and bytes
- Categorizes files into size buckets (<500, 500-2000, 2000-5000, >5000 tokens)
- Identifies large files (>500 lines)
- Generates a structured prompt with all metrics

**Expected output:** A formatted prompt with directory statistics and file breakdown.

## Step 3: Analyze the Data

You (Claude) will receive structured data about:
- Total files, tokens, lines, bytes
- Distribution across size buckets
- List of large files (>500 lines)
- Top files by token count (up to 20 files shown)

Examine this data for:

### Issue Detection

Categorize issues by priority using references/issue-detection.md guidance:

**🔴 High Priority** (immediate action needed):
- Large files (>500 lines) that should be split
- Critical duplicates causing significant waste
- Dead links breaking navigation
- Files over 1000 lines (urgent split needed)

**🟡 Medium Priority** (should address soon):
- Unused files (loaded but never cited)
- Inefficient organization (many small files that could be consolidated)
- Verbose documentation that could be compressed
- Files 300-500 lines (consider splitting)

**🟢 Low Priority** (optional improvements):
- Minor optimizations (small file consolidation)
- Style improvements (formatting consistency)
- Potential future issues (files approaching thresholds)

### Pattern Recognition

Look for:
- Multiple files with similar names (potential duplicates)
- Uneven distribution (many large files, few small ones)
- Outliers (one file with 10x more tokens than others)
- Structural issues (no clear organization)

## Step 4: Calculate Optimization Potential

For each identified issue, estimate:
- **Current tokens** for affected files
- **Estimated tokens after optimization**
- **Savings** (difference)
- **Percentage reduction**

Be realistic with estimates:
- Splitting: 10-15% overhead for navigation/links
- Deduplication: Actual duplicate % (don't overestimate)
- Compression: 20-40% reduction (depends on verbosity)

## Step 5: Generate Recommendations

For each issue, provide:

1. **Specific command** to run (exact file names)
   ```
   /dewey:split IMPLEMENTATION_PLAN.md
   ```

2. **Estimated impact**
   ```
   Impact: ~7,500 tokens saved
   ```

3. **Time estimate**
   ```
   Time: 5 minutes
   ```

4. **Priority** (based on impact/effort ratio)

Sort recommendations by priority:
- Quick wins first (high impact, low effort)
- Medium effort tasks next
- Long-term improvements last

## Step 6: Format Report

Structure your report following this template:

```
📊 Context Analysis Report
==================================================

📁 Directory: [path]
📅 Analyzed: [timestamp]

📈 Summary Statistics
==================================================
Total Files:        [count]
Total Tokens:       [count with commas]
Total Lines:        [count with commas]
Average File:       [avg tokens/file]
Largest File:       [tokens] ([filename])

📊 Distribution
==================================================
<500 tokens        [count] files  ([%])  [bar chart]
500-2000 tokens    [count] files  ([%])  [bar chart]
2000-5000 tokens   [count] files  ([%])  [bar chart]
>5000 tokens       [count] files  ([%])  [bar chart]

⚠️  Issues Detected
==================================================

🔴 High Priority ([count] issues)
  1. [Issue description]
     → [Specific command to fix]
     Impact: [estimated tokens saved]

🟡 Medium Priority ([count] issues)
  [if any issues found]

🟢 Low Priority ([count] issues)
  [if any issues found]

💡 Recommendations
==================================================

Quick Wins:
  1. [Action] ([time estimate], [token impact])
  2. [Action] ([time estimate], [token impact])

Medium Effort:
  1. [Action] ([time estimate], [token impact])

📈 Potential Impact
==================================================
Current:    [total tokens with commas]
Optimized:  ~[estimated tokens after optimization]
Savings:    [difference] ([percentage]% reduction)

💾 Next Steps
==================================================
1. [Most important action]
2. [Second most important]
3. [Third most important]
```

**Visual Clarity:**
- Use emojis for section headers (📊 📁 📅 📈 ⚠️ 💡 📈 💾)
- Use priority emojis (🔴 🟡 🟢)
- Use arrows (→) for commands
- Use bars (█) for distribution visualization
- Format numbers with commas for readability

</process>

<success_criteria>
The workflow is complete when:
- ✅ Script executed successfully
- ✅ All metrics analyzed
- ✅ Issues categorized by priority
- ✅ Recommendations are specific with exact commands
- ✅ Impact is quantified (token estimates)
- ✅ Report is formatted clearly with emojis and structure
- ✅ Next steps are prioritized and actionable
</success_criteria>

<example_output>
```
📊 Context Analysis Report
==================================================

📁 Directory: context/
📅 Analyzed: 2026-02-10 14:23:45

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
  2. Split .seed-prompt.md (5 min, 7,500 tokens)

📈 Potential Impact
==================================================
Current:    125,340 tokens
Optimized:  ~87,000 tokens
Savings:    38,340 tokens (30% reduction)

💾 Next Steps
==================================================
1. /dewey:split IMPLEMENTATION_PLAN.md
2. /dewey:split .seed-prompt.md
3. Review for duplicate content manually
```
</example_output>
