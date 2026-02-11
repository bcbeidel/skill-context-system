# Validation Rules Reference

Specific rules, thresholds, and checks performed by the quality validation system.

## Validation Categories

### 1. File Size Validation

**Rule:** All context files must be ≤500 lines

**Check process:**
1. Count lines in each `.md` file
2. Compare against thresholds
3. Categorize violations

**Thresholds:**
- **PASS**: <400 lines
- **WARN**: 400-500 lines (approaching limit)
- **FAIL**: >500 lines (exceeds limit)

**Exceptions:**
- None - all files must comply
- Even generated files should be split if large

**Implementation:**
```python
def check_file_size(file_path: Path) -> tuple[str, int]:
    """Check file size against limits.

    Returns: (status, line_count)
      status: 'pass', 'warn', or 'fail'
    """
    with open(file_path) as f:
        lines = len(f.readlines())

    if lines > 500:
        return ('fail', lines)
    elif lines > 400:
        return ('warn', lines)
    else:
        return ('pass', lines)
```

### 2. Link Validation

**Rule:** All internal links must resolve to existing files

**Check process:**
1. Parse markdown files for links
2. Extract internal links (relative paths)
3. Verify target files exist
4. Report broken links with source location

**Link patterns detected:**
```markdown
[Link text](relative/path/file.md)
[Link text](../other/file.md)
[Link text](#anchor) ← Skipped (same-file anchor)
[Link text](https://...) ← Skipped (external)
```

**Thresholds:**
- **PASS**: 0 dead links
- **WARN**: 1-2 dead links
- **FAIL**: 3+ dead links

**What counts as broken:**
- Link points to non-existent file
- Link uses incorrect relative path
- Link to moved/renamed file

**What doesn't count:**
- External URLs (not validated)
- Anchor links within same file
- Links to intentionally excluded files (e.g., templates)

**Implementation:**
```python
def check_links(file_path: Path, context_root: Path) -> list[dict]:
    """Check all internal links in file.

    Returns: List of broken links with:
      - source_file
      - line_number
      - link_text
      - target_path
    """
    broken_links = []

    with open(file_path) as f:
        for line_num, line in enumerate(f, 1):
            # Parse markdown links: [text](path)
            for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', line):
                link_text, target = match.groups()

                # Skip external links
                if target.startswith(('http://', 'https://', '#')):
                    continue

                # Resolve relative path
                target_path = (file_path.parent / target).resolve()

                if not target_path.exists():
                    broken_links.append({
                        'source_file': str(file_path),
                        'line_number': line_num,
                        'link_text': link_text,
                        'target_path': str(target),
                    })

    return broken_links
```

### 3. Duplication Detection

**Rule:** Content duplication should be <20%

**Check process:**
1. Hash paragraph-level blocks from each file
2. Identify identical hashes across files
3. Calculate duplication percentage
4. Report duplicated content

**What counts as duplication:**
- Identical paragraph blocks (3+ lines)
- Copy-pasted sections
- Repeated definitions
- Duplicate code examples

**What doesn't count:**
- Headers and navigation (expected)
- Short repeated phrases (<3 lines)
- Standard formatting elements
- Intentional repetition for clarity

**Thresholds:**
- **PASS**: <10% duplication
- **WARN**: 10-20% duplication
- **FAIL**: >20% duplication

**Algorithm:**
```python
def detect_duplication(files: list[Path]) -> float:
    """Detect content duplication across files.

    Returns: Duplication percentage (0-100)
    """
    # Hash all paragraph blocks
    block_hashes = {}  # hash -> list of (file, line_num)

    for file_path in files:
        blocks = extract_paragraph_blocks(file_path)
        for line_num, block in blocks:
            block_hash = hashlib.md5(block.encode()).hexdigest()
            if block_hash not in block_hashes:
                block_hashes[block_hash] = []
            block_hashes[block_hash].append((file_path, line_num))

    # Count duplicates (blocks appearing in 2+ files)
    total_blocks = sum(len(locs) for locs in block_hashes.values())
    duplicate_blocks = sum(
        len(locs) - 1
        for locs in block_hashes.values()
        if len(locs) > 1
    )

    return (duplicate_blocks / total_blocks) * 100 if total_blocks > 0 else 0
```

### 4. Token Budget Validation

**Rule:** Total tokens should fit within practical limits

**Check process:**
1. Estimate tokens for each file
2. Sum total tokens
3. Compare against configured limit
4. Report budget usage

**Default limits:**
- Small project: 50K tokens
- Medium project: 100K tokens
- Large project: 200K tokens
- Configurable via settings

**Thresholds:**
- **PASS**: <80% of limit
- **WARN**: 80-100% of limit
- **FAIL**: >100% of limit

**Token estimation:**
```python
def estimate_tokens(text: str) -> int:
    """Estimate token count using character heuristic.

    Approximation: 1 token ≈ 4 characters
    """
    return len(text) // 4
```

**More accurate (if needed):**
```python
def estimate_tokens_precise(text: str) -> int:
    """More accurate token estimation.

    Uses word-based heuristic: 1 token ≈ 0.75 words
    """
    words = len(text.split())
    return int(words / 0.75)
```

## Fast Mode vs Standard Mode

### Fast Mode Checks

**Included (fast):**
- ✅ File size validation (just count lines)
- ✅ Token budget check (sum estimates)

**Skipped (slow):**
- ❌ Link validation (requires parsing)
- ❌ Detailed duplication (requires hashing)

**Performance:**
- Target: <2 seconds for 200 files
- Optimization: Minimal I/O, no complex analysis

### Standard Mode Checks

**All checks performed:**
- ✅ File size validation
- ✅ Token budget check
- ✅ Link validation
- ✅ Duplication detection

**Performance:**
- More thorough, takes longer
- Acceptable: 5-15 seconds for 200 files
- Worth the wait for comprehensive results

## Exit Code Determination

### Logic Flow

```python
def determine_exit_code(results: ValidationResults) -> int:
    """Determine exit code from validation results.

    Returns:
      0 = PASS (all checks passed)
      1 = WARN (warnings but no failures)
      2 = FAIL (one or more critical failures)
    """
    # Check for failures
    if (
        results.files_over_limit > 0 or
        results.dead_links > 2 or
        results.duplication > 20 or
        results.token_budget > 100
    ):
        return 2  # FAIL

    # Check for warnings
    if (
        results.files_approaching_limit > 0 or
        results.dead_links > 0 or
        results.duplication > 10 or
        results.token_budget > 80
    ):
        return 1  # WARN

    # All good
    return 0  # PASS
```

### Status Priority

When multiple issues exist, use worst status:

1. **FAIL** (exit 2) - Any critical violation
2. **WARN** (exit 1) - No failures, but warnings present
3. **PASS** (exit 0) - No issues whatsoever

## Configuration

### Customizable Thresholds

Users can override defaults in `.dewey/config.yml`:

```yaml
quality_check:
  file_size:
    warn_threshold: 400
    fail_threshold: 500

  token_budget:
    limit: 200000
    warn_percentage: 80
    fail_percentage: 100

  duplication:
    warn_percentage: 10
    fail_percentage: 20

  dead_links:
    warn_count: 2
    fail_count: 3
```

### Enforcement Levels

**Strict mode** (recommended for mature projects):
```yaml
quality_check:
  mode: strict
  file_size:
    fail_threshold: 400  # Lower threshold
  duplication:
    fail_percentage: 10   # Lower threshold
```

**Lenient mode** (for new or growing projects):
```yaml
quality_check:
  mode: lenient
  file_size:
    warn_threshold: 500
    fail_threshold: 700   # Higher threshold
  duplication:
    fail_percentage: 30   # Higher threshold
```

## Validation Report Format

### Structured Output

Script outputs JSON for Claude to parse:

```json
{
  "summary": {
    "files_checked": 47,
    "total_tokens": 125340,
    "token_budget_percentage": 62.7,
    "duplication_percentage": 15.0
  },
  "failures": [
    {
      "type": "file_size",
      "file": "IMPLEMENTATION_PLAN.md",
      "lines": 973,
      "threshold": 500
    },
    {
      "type": "dead_link",
      "source": "README.md",
      "line": 45,
      "target": "docs/archived-guide.md"
    }
  ],
  "warnings": [
    {
      "type": "file_size",
      "file": "api-reference.md",
      "lines": 420,
      "threshold": 400
    }
  ],
  "exit_code": 2
}
```

Claude formats this into human-readable report.

## Edge Cases

### Empty Files

**Rule:** Files with 0 lines pass validation
**Rationale:** Placeholders are acceptable

### Binary Files

**Rule:** Skip non-text files
**Detection:** File extension or binary content check

### Symbolic Links

**Rule:** Follow symlinks, validate targets
**Behavior:** Treat same as regular files

### Hidden Files

**Rule:** Skip files starting with `.` (except `.md` files)
**Rationale:** Usually not part of context

### Excluded Paths

**Rule:** Skip configured directories
**Default exclusions:**
- `.git/`
- `node_modules/`
- `.dewey/backups/`
- `archive/`

## Error Handling

### File Read Errors

**Issue:** Permission denied, file locked, etc.
**Behavior:** Skip file, report warning, continue

### Malformed Markdown

**Issue:** Invalid markdown syntax
**Behavior:** Best-effort parsing, report warnings

### Configuration Errors

**Issue:** Invalid config file
**Behavior:** Use defaults, warn user

### Script Failures

**Issue:** Python script crashes
**Behavior:** Return exit code 3, report error to Claude
