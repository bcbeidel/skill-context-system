# Issue Detection Reference

Guide for identifying, categorizing, and prioritizing context issues.

## Issue Categories

### 🔴 High Priority Issues

**Criteria:** Immediate impact on usability, performance, or maintainability

**Types:**

1. **Files >500 lines**
   - **Impact:** Hard to navigate, poor scanability
   - **Detection:** Line count > 500
   - **Action:** `/dewey:split filename.md`
   - **Urgency:** If >1000 lines, URGENT

2. **Files >10K tokens**
   - **Impact:** Significant context window usage
   - **Detection:** Token count > 10,000
   - **Action:** Split or compress
   - **Urgency:** HIGH

3. **Dead links**
   - **Impact:** Broken navigation, user confusion
   - **Detection:** Links to non-existent files
   - **Action:** Fix or remove
   - **Urgency:** Medium-High

4. **Critical duplication (>20%)**
   - **Impact:** Wasted tokens, maintenance burden
   - **Detection:** Identical or near-identical content blocks
   - **Action:** Deduplicate, consolidate
   - **Urgency:** High if >30% duplication

5. **Files >1000 lines**
   - **Impact:** Unusable, must split
   - **Detection:** Line count > 1000
   - **Action:** URGENT split needed
   - **Urgency:** CRITICAL

### 🟡 Medium Priority Issues

**Criteria:** Should be addressed but not blocking

**Types:**

1. **Files 300-500 lines**
   - **Impact:** Approaching limit
   - **Detection:** Line count in range
   - **Action:** Monitor, plan split if growing
   - **Urgency:** Preventive

2. **Unused files**
   - **Impact:** Wasted tokens, cluttered context
   - **Detection:** Loaded but never cited
   - **Action:** Archive or remove
   - **Urgency:** Medium

3. **Inefficient organization**
   - **Impact:** Navigation difficulty
   - **Detection:** Many small related files
   - **Action:** Consolidate or reorganize
   - **Urgency:** Medium

4. **Verbose documentation (>15 T/L)**
   - **Impact:** Token inefficiency
   - **Detection:** Tokens/line ratio > 15
   - **Action:** Compress, edit for conciseness
   - **Urgency:** Medium

5. **Moderate duplication (10-20%)**
   - **Impact:** Some waste
   - **Detection:** Repeated patterns
   - **Action:** Review and deduplicate
   - **Urgency:** Medium

6. **Unbalanced distribution**
   - **Impact:** Inconsistent file sizing
   - **Detection:** High variance in file sizes
   - **Action:** Reorganize structure
   - **Urgency:** Low-Medium

### 🟢 Low Priority Issues

**Criteria:** Optional improvements, nice-to-have

**Types:**

1. **Minor optimizations**
   - **Impact:** Small efficiency gains
   - **Detection:** Files <50 lines, many similar
   - **Action:** Consider consolidation
   - **Urgency:** Low

2. **Style inconsistencies**
   - **Impact:** Minor navigation friction
   - **Detection:** Inconsistent formatting
   - **Action:** Standardize formatting
   - **Urgency:** Low

3. **Potential future issues**
   - **Impact:** May become problems
   - **Detection:** Files at 250-300 lines
   - **Action:** Monitor growth
   - **Urgency:** Very Low

## Detection Patterns

### Large File Detection

**Algorithm:**
```python
if lines > 1000:
    priority = "CRITICAL"
    urgency = "URGENT"
elif lines > 500:
    priority = "HIGH"
    urgency = "HIGH"
elif lines > 400:
    priority = "MEDIUM"
    urgency = "WATCH"
elif lines > 300:
    priority = "LOW"
    urgency = "MONITOR"
```

### Duplication Detection

**Heuristics (when analysis script doesn't detect):**
- Files with very similar names
- Files with similar token counts
- Multiple files covering same topic
- Repeated section headers across files

**Confirmation needed:**
- Manual review of content
- Paragraph-level comparison
- Semantic similarity check

### Unused File Detection

**Indicators:**
- Old files (>90 days)
- Never referenced in other files
- No inbound links
- Low citation frequency (if tracked)

**Caution:**
- May be intentionally archived
- May be seasonal documentation
- Verify before suggesting removal

### Structural Issues

**Indicators:**
- Many files at root (>50 without subdirectories)
- No clear categorization
- Inconsistent naming conventions
- Mix of different content types in same directory

## Prioritization Framework

### Impact Assessment

**High Impact:**
- Affects >20% of context tokens
- Blocks navigation or usability
- Causes confusion or errors

**Medium Impact:**
- Affects 5-20% of tokens
- Reduces efficiency
- Minor friction

**Low Impact:**
- Affects <5% of tokens
- Aesthetic or organizational

### Effort Assessment

**Low Effort:**
- Single command execution
- <5 minutes
- Automated with skill

**Medium Effort:**
- Multiple steps
- 5-30 minutes
- Some manual work

**High Effort:**
- Complex reorganization
- >30 minutes
- Significant manual review

### Priority Matrix

| Impact/Effort | Low | Medium | High |
|--------------|-----|--------|------|
| **High** | 🔴 URGENT | 🔴 HIGH | 🟡 HIGH |
| **Medium** | 🟡 HIGH | 🟡 MED | 🟢 MED |
| **Low** | 🟢 MED | 🟢 LOW | 🟢 LOW |

**Quick Wins:** High impact, low effort (URGENT priority)
**Strategic:** High impact, high effort (HIGH priority)
**Efficiency gains:** Medium impact, low effort (MEDIUM priority)
**Optional:** Low impact (LOW priority)

## Recommendation Generation

### Template for High Priority Issues

```
🔴 High Priority ([count] issues)

1. [Issue description]
   → [Specific command with exact filename]
   → Impact: [estimated tokens saved]
   → Time: [estimate in minutes]
   → Urgency: [URGENT/HIGH]
```

### Template for Medium Priority Issues

```
🟡 Medium Priority ([count] issues)

1. [Issue description]
   → [Action needed, may not be single command]
   → Impact: [estimated tokens saved or benefit]
   → Time: [estimate]
```

### Template for Low Priority Issues

```
🟢 Low Priority ([count] issues)

Consider: [general category of improvements]
- [Example 1]
- [Example 2]

Optional, address when time permits.
```

## Impact Estimation Guidelines

### Token Savings for Splits

**Formula:**
```
Savings = Original_Tokens * Overhead_Factor
Overhead_Factor = 0.10 to 0.15 (10-15%)
```

**Reasoning:**
- Main file becomes scannable overview
- References loaded only when needed
- Navigation links add small overhead
- Net savings: 10-15% of original size

**Example:**
- Original: 10,000 tokens
- After split: 1,500 (main) + 8,000 (refs) = 9,500
- Savings: 500 tokens (5% overhead)
- But: Main file now much more useful

### Token Savings for Deduplication

**Formula:**
```
Savings = Duplicate_Percentage * Total_Tokens
```

**Example:**
- Total: 100,000 tokens
- 15% duplication detected
- Savings: 15,000 tokens

**Caution:** Don't overestimate
- Some "duplication" may be intentional
- Headers, navigation naturally repeat
- Estimate conservatively (half of detected duplication)

### Token Savings for Compression

**Formula:**
```
Savings = Verbose_Tokens * Compression_Rate
Compression_Rate = 0.20 to 0.40 (20-40%)
```

**Factors affecting rate:**
- Very verbose (>18 T/L): 40% possible
- Moderately verbose (15-18 T/L): 30% possible
- Slightly verbose (12-15 T/L): 20% possible

## Common Patterns

### The Monolith
**Symptom:** One file >1000 lines
**Cause:** Initial document grew without refactoring
**Solution:** Split into main + topical references
**Priority:** CRITICAL

### The Sprawl
**Symptom:** 100+ files, most <100 lines
**Cause:** Over-granular organization
**Solution:** Consolidate related small files
**Priority:** MEDIUM

### The Duplicate
**Symptom:** Similar content in multiple files
**Cause:** Copy-paste documentation, lack of DRY principle
**Solution:** Deduplicate, create canonical sources
**Priority:** HIGH (if >20% duplication)

### The Orphan
**Symptom:** Files with no inbound links, old timestamps
**Cause:** Outdated documentation not removed
**Solution:** Archive or remove after verification
**Priority:** MEDIUM
