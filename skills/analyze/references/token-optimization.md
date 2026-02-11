# Token Optimization Reference

Strategies and techniques for reducing token usage while preserving information quality.

## Understanding Tokens

### What Are Tokens?

**Definition:** Tokens are the basic units that language models process. Roughly:
- 1 token ≈ 4 characters of English text
- 1 token ≈ ¾ of a word
- 100 tokens ≈ 75 words

**Examples:**
```
"Hello world" = 2 tokens
"API endpoint" = 3 tokens
"The quick brown fox" = 4 tokens
```

### Why Optimize Tokens?

**Benefits:**
1. **Faster processing** - Less to read and analyze
2. **Lower costs** - Token-based pricing
3. **Better context** - More room for relevant information
4. **Improved focus** - Signal vs noise ratio

**When NOT to optimize:**
- Clarity would be reduced
- Information would be lost
- Time investment > benefit

## Optimization Strategies

### 1. File Splitting

**How it works:**
- Break large files into scannable main + detailed references
- Claude loads only what's needed
- Effective token management through selective loading

**Savings:** 10-15% overhead reduction
**Best for:** Files >500 lines
**Command:** `/dewey:split filename.md`

**Example:**
```
Before: PLAN.md (10,000 tokens, 973 lines)

After:
├── PLAN.md (1,500 tokens, 187 lines) ← scannable
└── references/PLAN/
    ├── phase-1.md (3,000 tokens)
    ├── phase-2-3.md (4,500 tokens)
    └── completion.md (1,000 tokens)

Total: 10,000 tokens (same content)
But main file is 85% smaller!
```

**Key point:** Not about reducing total tokens, but improving usability

### 2. Deduplication

**How it works:**
- Identify repeated content across files
- Keep canonical version
- Link to canonical from other locations

**Savings:** 10-30% depending on duplication level
**Best for:** Documentation with copied sections

**Common duplication sources:**
- Copy-pasted instructions
- Repeated definitions
- Duplicated examples
- Multiple similar guides

**Example:**
```
Before (3 files, each 1000 tokens):
- guide-1.md: [intro] + [shared setup] + [specific content]
- guide-2.md: [intro] + [shared setup] + [specific content]
- guide-3.md: [intro] + [shared setup] + [specific content]
Total: 3,000 tokens

After:
- setup.md: [shared setup] (500 tokens)
- guide-1.md: [intro] + [link to setup] + [specific] (700 tokens)
- guide-2.md: [intro] + [link to setup] + [specific] (700 tokens)
- guide-3.md: [intro] + [link to setup] + [specific] (700 tokens)
Total: 2,600 tokens (13% savings)
```

### 3. Compression/Editing

**How it works:**
- Rewrite verbose content more concisely
- Remove redundant explanations
- Use clearer, more direct language

**Savings:** 20-40% for verbose content
**Best for:** Files with >15 tokens/line

**Techniques:**

**Remove redundancy:**
```
Before (verbose):
"The API endpoint will return a JSON formatted response that contains
the user data including the username and email address."

After (concise):
"The API returns JSON with username and email."

Savings: 20 tokens → 9 tokens (55% reduction)
```

**Eliminate filler words:**
```
Before: "In order to set up the system, you will need to..."
After: "To set up: ..."

Before: "It is important to note that..."
After: "Note: ..."
```

**Use lists instead of prose:**
```
Before (prose):
"The system supports authentication via OAuth, JWT tokens, and API keys.
OAuth is best for user-facing applications, JWT tokens work well for
microservices, and API keys are good for server-to-server."

After (list):
Authentication methods:
- OAuth: User-facing apps
- JWT: Microservices
- API keys: Server-to-server

Savings: ~40% more concise
```

**Active voice over passive:**
```
Before: "The data is processed by the system..."
After: "The system processes data..."
```

### 4. Archival

**How it works:**
- Move unused/old files out of active context
- Preserve in archive directory
- Can be retrieved if needed

**Savings:** 100% of archived file tokens
**Best for:** Outdated docs, completed phases

**Archival structure:**
```
archive/
├── 2025/
│   ├── old-spec.md
│   └── deprecated-guide.md
└── 2026/
    └── completed-phase.md
```

**When to archive:**
- Documentation for completed/removed features
- Old meeting notes (>90 days)
- Superseded specifications
- Historical context not actively needed

**Keep an index:**
```markdown
# Archive Index

## 2025 Archives
- `old-spec.md` - Original API spec, replaced by v2
- `deprecated-guide.md` - Setup for old auth system
```

### 5. Consolidation

**How it works:**
- Combine many small related files
- Reduces navigation overhead
- Better context locality

**Savings:** 5-10% overhead reduction
**Best for:** Many files <100 lines on related topics

**Example:**
```
Before:
- note-1.md (50 lines)
- note-2.md (45 lines)
- note-3.md (60 lines)
- note-4.md (40 lines)
Total: 195 lines in 4 files
Overhead: ~20 lines (headers, separators)

After:
- notes-collection.md (185 lines)
Total: 185 lines in 1 file
Savings: 10 lines (5% overhead reduction)
```

**When NOT to consolidate:**
- Files serve different purposes
- Would exceed 500 lines
- Topics are unrelated

## Optimization Decision Tree

```
File >500 lines?
├─ Yes → Split it
└─ No → Continue

Multiple small (<100 line) related files?
├─ Yes → Consider consolidation
└─ No → Continue

Content duplicated across files?
├─ Yes → Deduplicate
└─ No → Continue

Tokens/line >15?
├─ Yes → Compress/edit
└─ No → Continue

File unused (>90 days, no references)?
├─ Yes → Archive
└─ No → Keep as-is
```

## Measuring Impact

### Before Optimization

```
/dewey:analyze --baseline
```

Establishes:
- Current token count
- File distribution
- Problem areas

### After Optimization

```
/dewey:analyze --compare
```

Shows:
- Token reduction
- File count changes
- Improvement percentage

### Calculate ROI

**Time investment:**
- Split large file: ~5-10 minutes
- Deduplicate: ~15-30 minutes
- Compress: ~20-40 minutes
- Archive: ~5 minutes

**Token savings:**
- Split: 10-15% of file size
- Deduplicate: 10-30% of duplicated content
- Compress: 20-40% of verbose content
- Archive: 100% of archived files

**ROI calculation:**
```
Example: 1 hour spent optimizing
- Split 2 files: 15,000 tokens → 13,500 (1,500 saved)
- Deduplicate: 20% of 10,000 → 2,000 saved
- Archive old docs: 5,000 saved
Total saved: 8,500 tokens

If this context is used daily, that's 8,500 tokens saved per day.
Over a month: 255,000 tokens saved
```

## Advanced Techniques

### Extractive Summarization

**When to use:** Reference documentation that's rarely consulted

**How:**
1. Identify key sentences using TF-IDF
2. Extract most important content
3. Create "summary" version
4. Link to full version if needed

**Savings:** 60-80% reduction
**Tradeoff:** Information density increases

### Hierarchical Loading

**Pattern:**
```
context/
├── quick-start.md (always loaded)
├── common/
│   └── frequent-tasks.md (loaded often)
└── deep/
    └── advanced-topics.md (loaded rarely)
```

**Strategy:**
- Organize by access frequency
- Most-used content in scannable files
- Rarely-used content in detailed references

### Smart Linking

**Instead of copying:**
```markdown
See [full API documentation](references/api-full.md) for:
- Authentication details
- Rate limiting
- Error codes
```

**Benefits:**
- Single source of truth
- Reduced duplication
- Easier maintenance

## Anti-Patterns to Avoid

### Over-Optimization

**Problem:** Sacrificing clarity for tokens
```
Bad: "API ret JSON w/ usr data"
Good: "API returns JSON with user data"
```

**Rule:** Optimize tokens, not readability

### Premature Optimization

**Problem:** Optimizing before measuring
**Solution:** Always run analysis first
**Remember:** Optimize highest-impact areas first

### Optimization Theater

**Problem:** Tiny optimizations with no real benefit
**Example:** Removing 50 tokens from a 100,000 token context
**Solution:** Focus on >5% impact optimizations

### Breaking Semantic Boundaries

**Problem:** Splitting mid-section to hit line count
**Solution:** Always split at natural boundaries

### Removing Context

**Problem:** Deleting explanatory text to save tokens
**Solution:** Edit for conciseness, don't remove context

## Best Practices

### 1. Measure First
Always establish baseline before optimizing

### 2. Prioritize Impact
Focus on changes that save >5% tokens

### 3. Preserve Information
Never lose content in pursuit of token reduction

### 4. Verify Changes
Run comparison analysis after optimization

### 5. Iterate
Optimization is ongoing, not one-time

### 6. Document Decisions
Note why content was split/archived/consolidated

### 7. Version Control
Commit optimization changes atomically

### 8. Test Navigation
Ensure links work after reorganization

## Maintenance Schedule

### Weekly
- Quick scan for new large files
- Monitor token growth

### Monthly
- Full analysis with comparison
- Address new issues
- Archive old content

### Quarterly
- Major reorganization if needed
- Review effectiveness of previous optimizations
- Adjust strategy based on results

## Success Metrics

**Token efficiency:**
- Target: <100K tokens for responsive context
- Stretch: <50K tokens for optimal performance

**File health:**
- 0 files >500 lines
- <5% files >300 lines
- Average file: 500-2000 tokens

**Distribution balance:**
- 60-80% files <500 tokens
- 20-30% files 500-2000 tokens
- <10% files 2000-5000 tokens
- <2% files >5000 tokens

**Maintenance:**
- Monthly token growth <10%
- Issues addressed within 1 week
- No files >1000 lines ever
