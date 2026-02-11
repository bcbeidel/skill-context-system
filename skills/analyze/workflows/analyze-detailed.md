# Detailed Analysis Workflow

<objective>
Perform comprehensive analysis with file-by-file breakdown and detailed metrics.
</objective>

<required_reading>
Before proceeding, read these references:
- `references/analysis-metrics.md` - Understanding detailed metrics
- `references/issue-detection.md` - Issue identification patterns
</required_reading>

<process>

## Step 1: Execute Detailed Analysis

Run the analysis script with detailed flag:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/analyze_directory.py $ARGUMENTS --detailed
```

**What this includes:**
- All standard analysis metrics
- Complete file-by-file breakdown
- Per-file recommendations
- Detailed distribution patterns

## Step 2: Analyze Per-File Data

For each file in the results, examine:

**Metrics:**
- Line count (flag if >300 lines)
- Token count (flag if >2000 tokens)
- Tokens-per-line ratio (flag if >20, indicates verbosity)
- File size in bytes

**Patterns:**
- Files with similar names (potential duplicates)
- Files with unusual token density
- Outliers in any dimension

## Step 3: File-by-File Assessment

Create a detailed breakdown table:

```
File-by-File Breakdown
==================================================
Rank | File                    | Lines | Tokens | T/L | Status
-----|-------------------------|-------|--------|-----|--------
1    | IMPLEMENTATION_PLAN.md  |   973 | 9,375  | 9.6 | 🔴 Split
2    | .seed-prompt.md         |   650 | 7,200  | 11  | 🔴 Split
3    | README.md               |   245 | 2,100  | 8.6 | ✅ OK
...
```

**Status indicators:**
- 🔴 Split needed (>500 lines)
- 🟡 Watch (300-500 lines)
- ⚠️ Verbose (>15 tokens/line)
- ✅ OK (within limits)
- 💡 Consider consolidation (<50 lines, many similar files)

## Step 4: Category Analysis

Group files by size category and analyze each:

**Large files (>5000 tokens):**
- List each file
- Assess split urgency
- Estimate post-split token count

**Medium files (2000-5000 tokens):**
- Identify files approaching threshold
- Proactive split recommendations

**Small files (<500 tokens):**
- Look for consolidation opportunities
- Identify orphaned files

## Step 5: Generate Detailed Report

Follow the standard analysis report structure, but add:

### File-by-File Section
Detailed table with all files sorted by tokens (descending)

### Category Deep-Dives
Analysis of each size category with specific recommendations

### Efficiency Metrics
- Average tokens per line (target: 8-12)
- File size variance (consistency indicator)
- Distribution balance score

### Advanced Recommendations
- File consolidation strategies
- Directory reorganization suggestions
- Naming convention improvements

## Step 6: Prioritized Action Plan

Create a numbered action plan with:
1. **Immediate actions** (urgent issues)
2. **Short-term actions** (within a week)
3. **Medium-term actions** (within a month)
4. **Long-term improvements** (ongoing)

Each action includes:
- Specific file(s) affected
- Exact command to run
- Estimated time and token impact
- Rationale

</process>

<success_criteria>
Detailed analysis is complete when:
- ✅ Every file is listed and assessed
- ✅ File-by-file table is generated
- ✅ Category-specific recommendations provided
- ✅ Efficiency metrics calculated
- ✅ Time-phased action plan created
- ✅ All recommendations are specific and actionable
</success_criteria>

<example_output>
```
📊 Detailed Context Analysis Report
==================================================

📁 Directory: context/
📅 Analyzed: 2026-02-10 14:23:45

📈 Summary Statistics
==================================================
Total Files:        47
Total Tokens:       125,340
Total Lines:        18,450
Average File:       2,667 tokens/file
Avg Tokens/Line:    6.8 (✅ within optimal range)

📋 File-by-File Breakdown
==================================================
Rank | File                         | Lines | Tokens | T/L  | Status
-----|------------------------------|-------|--------|------|--------
1    | IMPLEMENTATION_PLAN.md       |   973 | 9,375  |  9.6 | 🔴 Split
2    | .seed-prompt.md              |   650 | 7,200  | 11.1 | 🔴 Split
3    | api-reference.md             |   420 | 4,100  |  9.8 | 🟡 Watch
4    | README.md                    |   245 | 2,100  |  8.6 | ✅ OK
...
[all 47 files listed]

📊 Category Analysis
==================================================

🔴 Large Files (>5000 tokens) - 2 files
  • IMPLEMENTATION_PLAN.md (9,375 tokens)
    → Split into: main (~1,500) + 3 references (~7,875)
    → Priority: URGENT

  • .seed-prompt.md (7,200 tokens)
    → Split into: main (~1,200) + 2 references (~6,000)
    → Priority: HIGH

🟡 Medium Files (2000-5000 tokens) - 3 files
  • api-reference.md approaching threshold
    → Monitor, consider split if grows beyond 500 lines

✅ Good Size (<2000 tokens) - 42 files
  • 10 files under 100 tokens - consider consolidation
  • 32 files in optimal range (500-2000 tokens)

⚙️ Efficiency Metrics
==================================================
Average Tokens/Line:       6.8 ✅ (target: 8-12)
File Size Variance:        High ⚠️ (std dev: 1,850 tokens)
Distribution Balance:      Unbalanced (68% in one category)

💡 Detailed Recommendations
==================================================

IMMEDIATE (Today):
1. /dewey:split IMPLEMENTATION_PLAN.md
   → 7,500 tokens saved, 10 min
   → Rationale: 973 lines is difficult to navigate

2. /dewey:split .seed-prompt.md
   → 6,000 tokens saved, 8 min
   → Rationale: Monolithic structure, hard to reference sections

SHORT-TERM (This Week):
3. Review small files for consolidation
   → Files: notes-*.md (10 files, total 800 tokens)
   → Could consolidate into notes-collection.md
   → 300 tokens saved (overhead reduction)

MEDIUM-TERM (This Month):
4. Reorganize directory structure
   → Create subdirectories: specs/, guides/, references/
   → Improves navigation and context loading

📈 Potential Impact
==================================================
Immediate Actions:    13,500 tokens saved
Short-term Actions:      300 tokens saved
Medium-term Actions:   1,000 tokens saved (organizational efficiency)
------------------------
Total Savings:        14,800 tokens (11.8% reduction)

After optimization:
Current:    125,340 tokens
Optimized:  110,540 tokens

💾 Action Plan
==================================================
1. [URGENT] /dewey:split IMPLEMENTATION_PLAN.md
2. [URGENT] /dewey:split .seed-prompt.md
3. [HIGH] Consolidate notes-*.md files
4. [MEDIUM] Review api-reference.md (approaching threshold)
5. [LOW] Reorganize directory structure
```
</example_output>
