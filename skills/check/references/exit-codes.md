# Exit Codes Reference

Understanding status codes returned by quality checks for CI/CD integration.

## Exit Code Values

### 0 - PASS ✅

**Meaning:** All quality checks passed successfully

**Criteria:**
- All files <400 lines
- Zero dead links
- Duplication <10%
- Token budget <80%
- No warnings or failures

**Next steps:**
- Continue working normally
- Commit changes safely
- Maintain current quality practices

**CI/CD behavior:**
- Allow build to proceed
- No alerts needed
- Green status

**Example scenarios:**
```
✅ Well-maintained small project
Files: 20
Max file size: 350 lines
Dead links: 0
Duplication: 5%
Token budget: 45%
```

---

### 1 - WARN ⚠️

**Meaning:** No critical failures, but warnings present

**Criteria:**
- Files 400-500 lines (approaching limit)
- OR 1-2 dead links
- OR Duplication 10-20%
- OR Token budget 80-100%
- No FAIL-level violations

**Next steps:**
- Address warnings proactively
- Plan optimization for issues
- Can proceed but issues should be fixed soon

**CI/CD behavior:**
- Allow build to proceed
- Send notification
- Yellow status
- Consider blocking if warnings accumulate

**Example scenarios:**

**Scenario 1: Growing files**
```
⚠️  Files approaching limits
api-reference.md: 420 lines (84%)
setup-guide.md: 385 lines (77%)

Action: Monitor, plan splits if continue growing
```

**Scenario 2: Moderate duplication**
```
⚠️  15% duplication detected
Repeated content in:
- guide-1.md and guide-2.md (setup section)
- spec-a.md and spec-b.md (definitions)

Action: Consider consolidating shared content
```

**Scenario 3: Token budget high**
```
⚠️  Token budget at 85%
Current: 170K tokens
Limit: 200K tokens

Action: Proactive optimization recommended
```

---

### 2 - FAIL ❌

**Meaning:** Critical quality violations that must be fixed

**Criteria:**
- Any file >500 lines
- OR 3+ dead links
- OR Duplication >20%
- OR Token budget >100%
- One or more FAIL-level violations

**Next steps:**
- Fix violations immediately
- Do not commit until fixed
- Run check again to verify

**CI/CD behavior:**
- Block build/deployment
- Send alert
- Red status
- Require manual intervention

**Example scenarios:**

**Scenario 1: Oversized files**
```
❌ Files exceed limit
IMPLEMENTATION_PLAN.md: 973 lines (FAIL)
.seed-prompt.md: 650 lines (FAIL)

Action: MUST split these files
1. /dewey:split IMPLEMENTATION_PLAN.md
2. /dewey:split .seed-prompt.md
```

**Scenario 2: Many dead links**
```
❌ 5 dead links found
README.md:45 → docs/archived.md
guide.md:120 → ../removed-file.md
api.md:67 → specs/old-spec.md
...

Action: Fix all broken links before committing
```

**Scenario 3: Excessive duplication**
```
❌ 28% duplication detected
Major duplicates:
- setup instructions copied in 4 files
- API docs duplicated in 3 locations

Action: Deduplicate and consolidate
```

**Scenario 4: Budget exceeded**
```
❌ Token budget exceeded
Current: 245K tokens
Limit: 200K tokens
Exceeded by: 45K tokens (22%)

Action: Run /dewey:analyze for optimization plan
```

---

### 3 - ERROR 🔥

**Meaning:** Script failure or system error

**Criteria:**
- Python script crashed
- File system errors
- Configuration errors
- Unexpected exceptions

**Next steps:**
- Check error message
- Verify file system permissions
- Check configuration
- Report bug if unexpected

**CI/CD behavior:**
- Block build
- Send alert
- Investigate immediately

**Example scenarios:**

**Scenario 1: Permission error**
```
🔥 ERROR: Cannot read context/private.md
Permission denied

Action: Check file permissions
```

**Scenario 2: Script crash**
```
🔥 ERROR: Validation script failed
Traceback: ...

Action: Report bug to dewey maintainers
```

**Scenario 3: Configuration error**
```
🔥 ERROR: Invalid .dewey/config.yml
YAML parse error at line 15

Action: Fix configuration file
```

---

## Exit Code Matrix

| Condition | Exit Code | Status | CI Action |
|-----------|-----------|--------|-----------|
| All checks passed | 0 | PASS ✅ | Proceed |
| Warnings only | 1 | WARN ⚠️ | Proceed (notify) |
| Critical failures | 2 | FAIL ❌ | Block |
| Script error | 3 | ERROR 🔥 | Block (alert) |

## Using Exit Codes in Scripts

### Bash

```bash
#!/bin/bash

# Run quality check
/dewey:check

# Capture exit code
exit_code=$?

# Handle based on code
case $exit_code in
  0)
    echo "✅ Quality check passed"
    exit 0
    ;;
  1)
    echo "⚠️  Quality check has warnings"
    echo "Proceeding, but please address warnings"
    exit 0  # Allow build but notify
    ;;
  2)
    echo "❌ Quality check failed"
    echo "Fix issues before committing"
    exit 1  # Block commit
    ;;
  3)
    echo "🔥 Quality check error"
    echo "Check logs for details"
    exit 1  # Block commit
    ;;
esac
```

### Git Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running context quality check..."
/dewey:check --fast

exit_code=$?

if [ $exit_code -eq 2 ] || [ $exit_code -eq 3 ]; then
  echo ""
  echo "❌ Context quality check failed!"
  echo "Fix issues before committing."
  echo ""
  echo "To bypass this check (not recommended):"
  echo "  git commit --no-verify"
  exit 1
fi

if [ $exit_code -eq 1 ]; then
  echo ""
  echo "⚠️  Context quality check has warnings"
  echo "Consider addressing these before committing"
  echo ""
fi

exit 0
```

### GitHub Actions

```yaml
name: Context Quality Check

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Run quality check
        run: /dewey:check
        continue-on-error: false

      - name: Check exit code
        if: failure()
        run: |
          echo "::error::Context quality check failed"
          exit 1
```

### CI/CD Strategy by Exit Code

| Exit Code | Development | Staging | Production |
|-----------|-------------|---------|------------|
| 0 (PASS) | Deploy | Deploy | Deploy |
| 1 (WARN) | Deploy + notify | Deploy + notify | Deploy + alert |
| 2 (FAIL) | Block | Block | Block |
| 3 (ERROR) | Block + alert | Block + alert | Block + alert |

## Exit Code Overrides

### Force Success

**Not recommended**, but available for emergencies:

```bash
# Run check but always exit 0
/dewey:check || true

# Or suppress exit code
/dewey:check; exit 0
```

**Use cases:**
- Initial adoption (grandfathering existing issues)
- Temporary exception during migration
- Testing/debugging

**Risks:**
- Quality can degrade unnoticed
- Issues accumulate
- Technical debt grows

### Force Failure

For stricter enforcement:

```bash
# Treat warnings as failures
/dewey:check
exit_code=$?

if [ $exit_code -ge 1 ]; then
  echo "Treating warnings as failures (strict mode)"
  exit 2
fi
```

## Interpreting Multiple Checks

### Sequential Checks

When running multiple checks in sequence:

```bash
/dewey:check context/
code1=$?

/dewey:check docs/
code2=$?

# Use worst exit code
if [ $code1 -gt $code2 ]; then
  exit $code1
else
  exit $code2
fi
```

### Parallel Checks

When checking multiple directories in parallel:

```bash
/dewey:check context/ & pid1=$!
/dewey:check docs/ & pid2=$!

wait $pid1; code1=$?
wait $pid2; code2=$?

# Return worst exit code
if [ $code1 -gt $code2 ]; then
  exit $code1
else
  exit $code2
fi
```

## Best Practices

### For Developers

1. **Run before committing**
   ```bash
   /dewey:check
   ```

2. **Fix failures immediately**
   - Don't commit with FAIL status
   - Address issues while fresh

3. **Address warnings promptly**
   - Don't let warnings accumulate
   - Prevent them from becoming failures

### For CI/CD

1. **Always check on push**
   - Catch quality issues early
   - Prevent degradation

2. **Block on failures**
   - Don't merge PRs with FAIL status
   - Maintain quality bar

3. **Alert on errors**
   - Investigate script failures
   - Fix tooling issues

### For Teams

1. **Set clear policies**
   - What exit codes block merges?
   - Who can override?
   - How to handle exceptions?

2. **Monitor trends**
   - Track exit code distribution
   - Watch for increasing warnings
   - Identify problematic areas

3. **Automate enforcement**
   - Pre-commit hooks
   - CI/CD gates
   - Status checks on PRs

## Troubleshooting Exit Codes

### Unexpected FAIL

**Issue:** Check fails but you think it should pass

**Debug:**
```bash
# Run with verbose output
/dewey:check --detailed

# Check specific violations
# Review validation-rules.md for thresholds
```

### Inconsistent Results

**Issue:** Check passes locally, fails in CI

**Causes:**
- Different working directories
- Different file states
- Configuration differences

**Solution:**
```bash
# Verify configuration
cat .dewey/config.yml

# Check from same directory
cd /path/to/context
/dewey:check
```

### Exit Code 3 Errors

**Issue:** Script errors

**Debug:**
```bash
# Run Python script directly
python ${CLAUDE_PLUGIN_ROOT}/skills/check/scripts/check_quality.py

# Check Python installation
python --version

# Check dependencies
# (should be none - stdlib only)
```

## Future Enhancements

### Planned Exit Codes

- **4**: Soft failure (informational)
- **5-9**: Reserved for future use

### Configurable Strictness

```yaml
quality_check:
  exit_code_behavior:
    warnings: 1  # Could be 0 (ignore) or 2 (fail)
    failures: 2  # Could be 1 (warn) or 2 (fail)
```

### Partial Pass

Future: More granular status
- PASS: 100% checks passed
- PARTIAL: 90-99% checks passed
- WARN: 75-90% checks passed
- FAIL: <75% checks passed
