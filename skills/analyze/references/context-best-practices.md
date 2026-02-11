# Context Best Practices Reference

Principles for organizing context files based on Anthropic's recommendations and Claude Code patterns.

## Core Principles

### 1. Scannable Main Files

**Goal:** Claude should understand file purpose in <10 seconds

**Characteristics:**
- Clear title and purpose
- Overview/summary at top
- Key concepts visible immediately
- Navigation to details
- Typically <200 lines

**Anti-pattern:**
- Long introduction before content
- Deep nesting before key information
- No clear structure or headings

### 2. Topical Organization

**Goal:** Related content grouped logically

**Characteristics:**
- One topic per file
- Clear boundaries between topics
- Related files in subdirectories
- Descriptive file names

**Structure example:**
```
context/
├── overview.md (project summary)
├── specs/
│   ├── api-spec.md
│   └── data-model.md
├── guides/
│   ├── setup.md
│   └── deployment.md
└── references/
    ├── architecture.md
    └── decisions.md
```

**Anti-pattern:**
- Everything at root level
- Mixed topics in single files
- Unclear categorization

### 3. Semantic Coherence

**Goal:** Don't break mid-concept

**Characteristics:**
- Complete sections in each file
- Natural break points
- Self-contained units
- Proper context for references

**When splitting:**
- ✅ Split by chapter/phase/topic
- ✅ Split at major section boundaries
- ❌ Don't split mid-section
- ❌ Don't split mid-paragraph

### 4. Information Preservation

**Goal:** No data loss during optimization

**Characteristics:**
- All original content retained
- Clear links to related content
- Backup before destructive operations
- Version control integration

**When refactoring:**
- Always create backups
- Verify all content migrated
- Test navigation links
- Commit changes atomically

### 5. Clear Navigation

**Goal:** Easy to find related information

**Characteristics:**
- Bidirectional links
- Table of contents in main files
- Reference sections
- Clear file naming

**Link patterns:**
```markdown
Main file:
See [detailed API documentation](references/api-details.md)

Reference file:
← Back to [main documentation](../README.md)
```

## File Size Guidelines

### Optimal Ranges

**Small files (<500 lines):**
- Quick reference material
- Focused topics
- Scannable content
- Majority of files should be here

**Medium files (150-300 lines):**
- Sweet spot for main files
- Detailed documentation
- Tutorial content

**Large files (>500 lines):**
- Should be rare (0-2% of files)
- Candidates for splitting
- Often indicate multiple topics

### Line Count Thresholds

| Lines | Status | Action |
|-------|--------|--------|
| <50 | Tiny | Consider consolidation |
| 50-150 | Small | Good for references |
| 150-300 | Optimal | Sweet spot for main files |
| 300-500 | Large | Monitor, plan split |
| 500-1000 | Very Large | Split recommended |
| >1000 | Critical | Split urgently |

### Token Density

**Tokens per line (T/L):**
- 5-8: Code, structured data
- 8-12: Optimal prose
- 12-15: Verbose
- >15: Compression opportunity

**Examples:**
```markdown
Concise (9 T/L): "The API returns JSON with user data."
Verbose (18 T/L): "The API endpoint will return a JSON formatted response that contains the user data."
```

## Directory Structure Patterns

### Flat Structure (Small Projects)

```
context/
├── README.md
├── setup.md
├── api-guide.md
└── troubleshooting.md
```

**When to use:** <20 files

### Categorized Structure (Medium Projects)

```
context/
├── README.md
├── specs/
│   ├── api.md
│   └── data.md
├── guides/
│   ├── setup.md
│   └── usage.md
└── references/
    └── architecture.md
```

**When to use:** 20-100 files

### Deep Structure (Large Projects)

```
context/
├── README.md
├── overview/
│   ├── vision.md
│   └── architecture.md
├── features/
│   ├── auth/
│   │   ├── overview.md
│   │   └── references/
│   └── api/
│       ├── overview.md
│       └── references/
└── operations/
    ├── deployment.md
    └── monitoring.md
```

**When to use:** >100 files

## Naming Conventions

### File Names

**Good:**
- `api-overview.md`
- `setup-guide.md`
- `phase-1-tasks.md`
- `testing-strategy.md`

**Avoid:**
- `doc1.md` (not descriptive)
- `API_Overview.md` (inconsistent casing)
- `api overview.md` (spaces)
- `the-api-overview-and-guide.md` (too long)

**Pattern:** `[topic]-[type].md` or `[topic].md`

### Directory Names

**Good:**
- `references/`
- `specs/`
- `guides/`
- `phase-1/`

**Avoid:**
- `misc/` (too vague)
- `stuff/` (unprofessional)
- `old/` (archive instead)

## Split Strategy

### When to Split

**Triggers:**
- File >500 lines
- Multiple distinct topics
- Hard to navigate
- Difficult to reference specific section

**Don't split if:**
- Content is cohesive
- <400 lines
- Would create artificial boundaries

### How to Split

**Process:**
1. Identify natural sections
2. Group related sections
3. Create main overview
4. Move details to references
5. Add bidirectional links
6. Verify no information lost

**Main file should contain:**
- Executive summary
- Key concepts
- High-level structure
- Links to detailed sections
- Typically 150-200 lines

**Reference files should contain:**
- Detailed information
- Implementation specifics
- Examples and tutorials
- Typically 200-400 lines each

### Reference File Organization

**Pattern:**
```
references/
└── [original-filename]/
    ├── topic-1.md
    ├── topic-2.md
    └── topic-3.md
```

**Example:**
```
IMPLEMENTATION_PLAN.md (main, 187 lines)
references/IMPLEMENTATION_PLAN/
├── phase-1-measurement.md
├── phase-2-3-optimization.md
└── testing-completion.md
```

## Link Patterns

### Internal Links

**Relative links preferred:**
```markdown
[Detailed API docs](references/api-details.md)
[Setup guide](../guides/setup.md)
```

**Absolute links for external:**
```markdown
[Anthropic Docs](https://docs.anthropic.com)
```

### Navigation Blocks

**In main files:**
```markdown
## Related Documentation

- [API Reference](references/api-reference.md)
- [Setup Guide](guides/setup.md)
- [Troubleshooting](guides/troubleshooting.md)
```

**In reference files:**
```markdown
---
**Navigation:** ← [Main Documentation](../../README.md)
---
```

## Maintenance Practices

### Regular Review

**Weekly:**
- Check for new large files
- Monitor token growth
- Review recent additions

**Monthly:**
- Full analysis (`/dewey:analyze --compare`)
- Archive unused files
- Consolidate small files

**Quarterly:**
- Directory reorganization
- Update navigation
- Refresh documentation

### Version Control

**Commit practices:**
- Atomic commits per optimization
- Clear commit messages
- Tag major reorganizations

**Branch strategy:**
- Use branches for large refactors
- Review before merging
- Rollback if issues

### Documentation

**Track changes:**
- Maintain CHANGELOG.md
- Document organizational decisions
- Note optimization results

## Common Anti-Patterns

### The Monolith
**Problem:** Single >1000 line file
**Solution:** Split into main + references
**Prevention:** Split proactively at 500 lines

### The Maze
**Problem:** Deep nesting (>4 levels)
**Solution:** Flatten structure
**Prevention:** Keep depth ≤3 levels

### The Junk Drawer
**Problem:** `misc/` or `other/` with unrelated files
**Solution:** Properly categorize or archive
**Prevention:** Always find proper category

### The Duplicate
**Problem:** Same content in multiple files
**Solution:** Deduplicate, create canonical source
**Prevention:** Link instead of copying

### The Orphan
**Problem:** Files with no inbound links
**Solution:** Archive if truly unused
**Prevention:** Review usage regularly

### The Novel
**Problem:** Extremely verbose documentation
**Solution:** Edit for conciseness
**Prevention:** Target 8-12 tokens/line

## Optimization Workflow

### Step 1: Measure
Run analysis to establish baseline:
```
/dewey:analyze --baseline
```

### Step 2: Identify
Find highest-impact opportunities:
- Large files (>500 lines)
- Duplicate content
- Unused files

### Step 3: Optimize
Execute optimizations in priority order:
1. Split critical files (>1000 lines)
2. Split large files (>500 lines)
3. Deduplicate content
4. Archive unused files

### Step 4: Verify
Confirm improvements:
```
/dewey:analyze --compare
```

### Step 5: Maintain
Regular monitoring:
- Weekly: Quick check
- Monthly: Full analysis
- Quarterly: Reorganization if needed
