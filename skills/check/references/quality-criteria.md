# Quality Criteria Reference

Standards for defining high-quality context organization.

## Core Quality Principles

### 1. Scannability

**Definition:** Claude should understand file purpose and content in <10 seconds

**Criteria:**
- Clear title and overview at top
- Logical structure with headers
- Key information visible without scrolling far
- Table of contents for longer files

**Violations:**
- Wall of text with no structure
- Important info buried deep in file
- No clear purpose statement
- Poor or missing headers

### 2. File Size Discipline

**Definition:** Files should be focused and manageable

**Criteria:**
- <500 lines per file (hard limit)
- <400 lines preferred (soft limit)
- <300 lines optimal for references
- 150-200 lines ideal for main files

**Rationale:**
- 500+ lines hard to scan
- Difficult to reference specific sections
- Often indicates multiple topics
- Navigation becomes challenging

**Violations:**
- Files >500 lines
- Single file approaching 1000 lines
- No plan to split growing files

### 3. Link Integrity

**Definition:** All internal links must resolve correctly

**Criteria:**
- Links point to existing files
- Relative paths are correct
- No broken references
- Bidirectional links maintained

**Violations:**
- Dead links to non-existent files
- Links to moved/renamed files
- Incorrect relative paths
- Orphaned references

### 4. Minimal Duplication

**Definition:** Content should follow DRY principle (Don't Repeat Yourself)

**Criteria:**
- <10% duplication ideal
- <20% acceptable
- >20% needs attention
- Canonical sources for shared info

**Acceptable duplication:**
- Headers and navigation
- Brief context setting
- Standard disclaimers
- Consistent formatting

**Unacceptable duplication:**
- Copy-pasted sections
- Duplicate definitions
- Repeated instructions
- Multiple versions of same content

### 5. Token Efficiency

**Definition:** Context should fit comfortably within practical limits

**Criteria:**
- <80% of target budget is healthy
- 80-100% is approaching limits
- >100% requires optimization
- Steady or declining growth over time

**Practical limits:**
- Small project: 20-50K tokens
- Medium project: 50-100K tokens
- Large project: 100-200K tokens

**Violations:**
- Exceeding practical limits
- Rapid unbounded growth
- No optimization when at limits

## Quality Dimensions

### Structural Quality

**Good structure:**
```
context/
├── README.md (overview)
├── quick-start.md (getting started)
├── specs/ (detailed specifications)
│   ├── api-spec.md
│   └── data-model.md
└── guides/ (how-to documentation)
    ├── setup.md
    └── deployment.md
```

**Poor structure:**
```
context/
├── file1.md
├── file2.md
├── notes.md
├── doc.md
├── misc.md
└── stuff.md
```

### Content Quality

**Clear writing:**
- Concise and direct
- Active voice preferred
- 8-12 tokens per line
- Technical accuracy

**Poor writing:**
- Verbose and rambling
- Passive voice overused
- >15 tokens per line
- Vague or imprecise

### Maintenance Quality

**Well-maintained:**
- Recent updates
- No dead links
- Consistent formatting
- Version controlled

**Poorly maintained:**
- Outdated information
- Broken links
- Inconsistent style
- No change tracking

## Validation Thresholds

### File Size Thresholds

| Lines | Status | Action Required |
|-------|--------|-----------------|
| <300 | ✅ Excellent | None |
| 300-400 | ✅ Good | Monitor |
| 400-500 | ⚠️ Warning | Plan split |
| 500-1000 | ❌ Fail | Split now |
| >1000 | 🚨 Critical | Split urgently |

### Token Budget Thresholds

| Usage | Status | Action Required |
|-------|--------|-----------------|
| <60% | ✅ Healthy | None |
| 60-80% | ✅ Good | Monitor |
| 80-90% | ⚠️ Warning | Optimize soon |
| 90-100% | ❌ Fail | Optimize now |
| >100% | 🚨 Critical | Emergency optimization |

### Duplication Thresholds

| Level | Status | Action Required |
|-------|--------|-----------------|
| <5% | ✅ Excellent | None |
| 5-10% | ✅ Good | None |
| 10-20% | ⚠️ Warning | Consider deduplication |
| 20-30% | ❌ Fail | Deduplicate |
| >30% | 🚨 Critical | Major cleanup needed |

### Link Quality Thresholds

| Broken Links | Status | Action Required |
|--------------|--------|-----------------|
| 0 | ✅ Perfect | None |
| 1-2 | ⚠️ Warning | Fix soon |
| 3-5 | ❌ Fail | Fix now |
| >5 | 🚨 Critical | Audit all links |

## Quality Scoring

### Overall Score Calculation

```python
score = (
    file_size_score * 0.30 +
    token_budget_score * 0.25 +
    link_quality_score * 0.25 +
    duplication_score * 0.20
)
```

### Grade Ranges

| Score | Grade | Interpretation |
|-------|-------|----------------|
| 90-100 | A | Excellent quality |
| 80-89 | B | Good quality |
| 70-79 | C | Acceptable, some issues |
| 60-69 | D | Multiple issues, needs work |
| <60 | F | Poor quality, requires attention |

## Quality Improvement Strategies

### For Poor File Size Scores

1. **Identify large files** - List all files >400 lines
2. **Analyze content** - Determine if multiple topics
3. **Plan splits** - Define logical boundaries
4. **Execute splits** - Use `/dewey:split`
5. **Verify** - Confirm all files <500 lines

### For Poor Token Budget Scores

1. **Run analysis** - `/dewey:analyze --baseline`
2. **Identify opportunities** - Large files, duplication
3. **Prioritize** - High impact optimizations first
4. **Execute** - Split, deduplicate, compress
5. **Measure** - `/dewey:analyze --compare`

### For Poor Link Quality

1. **Identify dead links** - Check validation report
2. **Categorize** - Moved, renamed, or deleted files
3. **Fix links** - Update paths or remove
4. **Verify** - Re-run check
5. **Prevent** - Test links before committing

### For High Duplication

1. **Identify duplicates** - Run full analysis
2. **Determine canonical** - Which version to keep
3. **Update references** - Link to canonical
4. **Remove duplicates** - Delete redundant copies
5. **Verify** - Check duplication level reduced

## Maintenance Best Practices

### Before Commit

Always run quality check:
```bash
/dewey:check
```

Fix any failures before committing.

### Weekly

Monitor context health:
```bash
/dewey:analyze
```

Address warnings proactively.

### Monthly

Full optimization:
```bash
/dewey:analyze --compare
/dewey:optimize  # when implemented
```

Archive old content, split growing files.

### Quarterly

Major review:
- Reorganize directory structure
- Update navigation
- Refresh outdated docs
- Validate all links

## Red Flags

### Immediate Action Needed

- ❌ Any file >1000 lines
- ❌ Token budget >120%
- ❌ >5 dead links
- ❌ >30% duplication

### Address Soon

- ⚠️ Multiple files 400-500 lines
- ⚠️ Token budget 90-100%
- ⚠️ 1-2 dead links
- ⚠️ 20-30% duplication

### Monitor

- 👀 Files approaching 400 lines
- 👀 Token budget 80-90%
- 👀 10-20% duplication
- 👀 Growing context without optimization

## Quality Goals

### Short-Term (This Week)

- ✅ Zero files >500 lines
- ✅ Zero dead links
- ✅ Duplication <20%
- ✅ Pass quality checks

### Medium-Term (This Month)

- ✅ All files <400 lines
- ✅ Token budget <80%
- ✅ Duplication <10%
- ✅ Consistent structure

### Long-Term (This Quarter)

- ✅ Optimal file sizes (150-300 lines)
- ✅ Token budget <60%
- ✅ Duplication <5%
- ✅ Automated quality gates
