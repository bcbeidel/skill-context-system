# Standard Quality Check Workflow

<objective>
Perform comprehensive validation of context quality, identifying all issues that violate best practices.
</objective>

<required_reading>
Before proceeding, read these references:
- `references/quality-criteria.md` - Quality standards
- `references/validation-rules.md` - Specific rules and thresholds
- `references/exit-codes.md` - Understanding status codes
</required_reading>

<process>

## Step 1: Parse Arguments

Extract directory and flags from `$ARGUMENTS`:
- Directory path (default: current directory)
- Validation options (if any custom thresholds provided)

## Step 2: Execute Validation Script

Run the quality check script:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/check/scripts/check_quality.py $ARGUMENTS
```

**What this script does:**
- Scans all `.md` files in directory
- Runs all validation checks:
  - File size validation
  - Link validation
  - Duplication detection
  - Token budget check
- Collects all violations
- Generates structured report

**Expected output:** Structured data with:
- List of failures (critical issues)
- List of warnings (approaching limits)
- Summary statistics
- Exit code recommendation

## Step 3: Analyze Validation Results

You (Claude) will receive structured validation data. Categorize issues:

### ❌ Failures (Critical)

These prevent passing validation:

1. **Files >500 lines**
   - List each file with exact line count
   - Recommend: `/dewey:split filename.md`

2. **Dead links**
   - List each broken link with source file
   - Recommend: Fix link or remove

3. **Excessive duplication (>20%)**
   - Identify duplicated content blocks
   - Recommend: Consolidate or deduplicate

4. **Token budget exceeded**
   - Report total tokens vs limit
   - Recommend: Run `/dewey:analyze` for optimization plan

### ⚠️ Warnings (Approaching Limits)

These should be addressed soon:

1. **Files 400-500 lines**
   - List files approaching threshold
   - Recommend: Monitor and plan split

2. **Moderate duplication (10-20%)**
   - Note duplication level
   - Recommend: Consider deduplication

3. **Token budget at 80-100%**
   - Report current usage
   - Recommend: Proactive optimization

## Step 4: Calculate Overall Status

Determine exit code based on issues found:

**FAIL (exit code 2):**
- Any file >500 lines
- Any dead links
- Duplication >20%
- Token budget exceeded

**WARN (exit code 1):**
- Files 400-500 lines
- Duplication 10-20%
- Token budget 80-100%
- No critical failures

**PASS (exit code 0):**
- All files <400 lines
- No dead links
- Duplication <10%
- Token budget <80%

## Step 5: Generate Validation Report

Format the report clearly:

```
🔍 Context Quality Check
==================================================

📁 Directory: [path]
📅 Checked: [timestamp]
🎯 Status: [PASS ✅ | WARN ⚠️ | FAIL ❌]

📊 Summary
==================================================
Files Checked:       [count]
Total Tokens:        [count]
Token Budget:        [percentage]% of [limit]
Duplication Level:   [percentage]%

[If FAIL or WARN:]
❌ Failures: [count]
⚠️  Warnings: [count]

[If PASS:]
✅ All checks passed!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[If failures found:]
❌ FAILURES (Must Fix)
==================================================

📄 File Size Violations ([count] files)
  1. [filename] ([lines] lines) - EXCEEDS LIMIT
     → /dewey:split [filename]

  2. [filename] ([lines] lines) - EXCEEDS LIMIT
     → /dewey:split [filename]

🔗 Dead Links ([count] links)
  1. [source-file]:[line] → [broken-link]
     Fix: [suggestion]

  2. [source-file]:[line] → [broken-link]
     Fix: [suggestion]

📋 Excessive Duplication
  • [percentage]% duplication detected
  • Duplicated blocks found in:
    - [file1] and [file2]
    - [file3] and [file4]
  → Run manual deduplication review

💾 Token Budget Exceeded
  • Current: [tokens] tokens
  • Limit: [limit] tokens
  • Exceeded by: [difference] tokens ([percentage]%)
  → /dewey:analyze for optimization plan

[If warnings found:]
⚠️  WARNINGS (Should Address Soon)
==================================================

📄 Files Approaching Limit ([count] files)
  • [filename] ([lines] lines) - 80% of limit
  • [filename] ([lines] lines) - 85% of limit

📋 Moderate Duplication
  • [percentage]% duplication detected
  • Consider reviewing for consolidation opportunities

💾 Token Budget High
  • Current: [tokens] tokens
  • Limit: [limit] tokens
  • Usage: [percentage]%
  • Recommend proactive optimization

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Recommended Actions
==================================================

[If FAIL:]
Critical issues must be resolved before committing:

1. [Most critical action]
2. [Second most critical]
3. [Third most critical]

Fix these issues and run /dewey:check again.

[If WARN:]
No critical issues, but address these soon:

1. [Warning to address]
2. [Second warning]

[If PASS:]
✅ Context quality is good!

Maintain this by:
- Running /dewey:check before commits
- Keeping files <400 lines
- Monitoring token usage

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Exit Code: [0|1|2]
  0 = PASS ✅
  1 = WARN ⚠️
  2 = FAIL ❌
```

## Step 6: Provide Next Steps

Based on validation status:

**If FAIL:**
- List specific commands to fix each issue
- Block further progress until resolved
- Suggest running `/dewey:analyze` for comprehensive plan

**If WARN:**
- Suggest preventive actions
- Recommend monitoring
- OK to proceed but issues should be addressed

**If PASS:**
- Acknowledge good context health
- Suggest periodic checks
- Encourage maintaining current practices

</process>

<success_criteria>
Standard check workflow is complete when:
- ✅ All validation checks executed
- ✅ Issues categorized by severity (fail/warn)
- ✅ Specific file names and line numbers provided
- ✅ Actionable recommendations given
- ✅ Exit code determined and reported
- ✅ Clear next steps provided based on status
</success_criteria>

<example_output>

## Example: FAIL Status

```
🔍 Context Quality Check
==================================================

📁 Directory: context/
📅 Checked: 2026-02-10 16:45:00
🎯 Status: FAIL ❌

📊 Summary
==================================================
Files Checked:       47
Total Tokens:        125,340
Token Budget:        62.7% of 200,000
Duplication Level:   15%

❌ Failures: 3
⚠️  Warnings: 2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ FAILURES (Must Fix)
==================================================

📄 File Size Violations (2 files)
  1. IMPLEMENTATION_PLAN.md (973 lines) - EXCEEDS LIMIT
     → /dewey:split IMPLEMENTATION_PLAN.md

  2. .seed-prompt.md (650 lines) - EXCEEDS LIMIT
     → /dewey:split .seed-prompt.md

🔗 Dead Links (1 link)
  1. README.md:45 → docs/archived-guide.md
     Fix: Update link to archive/2025/archived-guide.md

⚠️  WARNINGS (Should Address Soon)
==================================================

📄 Files Approaching Limit (2 files)
  • api-reference.md (420 lines) - 84% of limit
  • setup-guide.md (385 lines) - 77% of limit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Recommended Actions
==================================================

Critical issues must be resolved before committing:

1. /dewey:split IMPLEMENTATION_PLAN.md
2. /dewey:split .seed-prompt.md
3. Fix dead link in README.md:45

Fix these issues and run /dewey:check again.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Exit Code: 2 (FAIL ❌)
```

## Example: PASS Status

```
🔍 Context Quality Check
==================================================

📁 Directory: context/
📅 Checked: 2026-02-10 16:45:00
🎯 Status: PASS ✅

📊 Summary
==================================================
Files Checked:       45
Total Tokens:        87,200
Token Budget:        43.6% of 200,000
Duplication Level:   5%

✅ All checks passed!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Recommended Actions
==================================================

✅ Context quality is excellent!

Maintain this by:
- Running /dewey:check before commits
- Keeping files <400 lines
- Monitoring token usage with /dewey:analyze

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Exit Code: 0 (PASS ✅)
```

</example_output>
