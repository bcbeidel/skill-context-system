# Fast Quality Check Workflow

<objective>
Perform quick validation optimized for speed, checking only critical issues. Target: <2 seconds for 200 files.
</objective>

<required_reading>
- `references/validation-rules.md` - Understanding which checks run in fast mode
</required_reading>

<process>

## Step 1: Execute Fast Validation

Run check script with fast mode flag:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/check/scripts/check_quality.py $ARGUMENTS --fast
```

**What fast mode does:**
- ✅ File size checks (very fast - just line counts)
- ✅ Token budget check (fast - sum of estimates)
- ❌ Skips link validation (slower - requires parsing)
- ❌ Skips detailed duplication analysis (slower - requires hashing)

**Performance targets:**
- <2 seconds for 200 files
- <5 seconds for 500 files
- Linear scaling with file count

## Step 2: Analyze Fast Results

Process only the checks that were run:

### Critical Checks (Fast Mode)

**File sizes:**
- Any files >500 lines = FAIL
- Files 400-500 lines = WARN

**Token budget:**
- Total >limit = FAIL
- Total 80-100% = WARN

**Skipped checks:**
- Note that link validation was skipped
- Note that detailed duplication was skipped
- Recommend full check if needed

## Step 3: Generate Fast Report

Streamlined report format:

```
🔍 Context Quality Check (Fast Mode)
==================================================

📁 Directory: [path]
🎯 Status: [PASS ✅ | WARN ⚠️ | FAIL ❌]
⚡ Time: [seconds]s

📊 Quick Summary
==================================================
Files Checked:   [count]
Total Tokens:    [count]
Token Budget:    [percentage]% of [limit]

[If issues found:]
❌ Failures: [count]
⚠️  Warnings: [count]

[If PASS:]
✅ Quick checks passed!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[If failures:]
❌ FAILURES
==================================================

📄 Files >500 lines: [count]
  • [filename] ([lines] lines)
  • [filename] ([lines] lines)

💾 Token budget exceeded
  • [tokens] / [limit] ([percentage]%)

[If warnings:]
⚠️  WARNINGS
==================================================

📄 Files approaching limit: [count]
  • [filename] ([lines] lines)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ️  Fast Mode Limitations
==================================================

The following checks were skipped for speed:
  • Link validation
  • Detailed duplication analysis

For comprehensive validation, run:
  /dewey:check

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Exit Code: [0|1|2]
```

## Step 4: Recommend Follow-Up

Based on results:

**If FAIL in fast mode:**
- Critical issues found even without deep analysis
- Fix these first
- Then run full check: `/dewey:check`

**If WARN in fast mode:**
- Minor issues found
- Consider running full check to catch other issues
- May have dead links or duplication not detected

**If PASS in fast mode:**
- Fast checks passed
- Consider periodic full checks to catch:
  - Dead links
  - Duplication patterns
  - Other deeper issues

</process>

<success_criteria>
Fast check is complete when:
- ✅ Completed in <2 seconds for 200 files
- ✅ File size violations identified
- ✅ Token budget status determined
- ✅ Exit code returned
- ✅ User informed of skipped checks
- ✅ Clear when to run full check
</success_criteria>

<performance_notes>
## Why Fast Mode is Fast

**File size checks:**
- Just count lines (no parsing)
- Simple comparison against thresholds
- O(n) with file count

**Token estimation:**
- Character-based heuristic (no tokenizer)
- ~4 chars = 1 token
- Very fast calculation

**Skipped checks:**
- Link validation requires parsing all markdown
- Following links to verify they exist
- Can be slow with many files

- Duplication detection requires hashing
- Comparing blocks across files
- O(n²) complexity

**Result:** Fast mode is ~10-20x faster than full check on large contexts.
</performance_notes>

<example_output>

```
🔍 Context Quality Check (Fast Mode)
==================================================

📁 Directory: context/
🎯 Status: FAIL ❌
⚡ Time: 0.8s

📊 Quick Summary
==================================================
Files Checked:   47
Total Tokens:    125,340
Token Budget:    62.7% of 200,000

❌ Failures: 2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ FAILURES
==================================================

📄 Files >500 lines: 2
  • IMPLEMENTATION_PLAN.md (973 lines)
  • .seed-prompt.md (650 lines)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Recommended Actions
==================================================

Critical file size violations found:
1. /dewey:split IMPLEMENTATION_PLAN.md
2. /dewey:split .seed-prompt.md

After fixing, run full check:
  /dewey:check

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ️  Fast Mode Limitations
==================================================

The following checks were skipped for speed:
  • Link validation
  • Detailed duplication analysis

For comprehensive validation, run:
  /dewey:check

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Exit Code: 2 (FAIL ❌)
```

</example_output>
