# Dewey Context Optimizer - Implementation Plan v2.1

**Created**: 2026-02-10
**Updated**: 2026-02-10 (Refactored to stdlib-only)
**Status**: Active Development
**Version**: 0.0.2
**Current Phase**: Phase 0 Complete + Refactored → Phase 1 (Core Skills)

---

## Overview

Dewey is a **Claude Code plugin** that optimizes context management through intelligent skills. This plan focuses on building an excellent Claude Code experience first, with multi-provider support deferred to later phases.

**Design Philosophy**:
- **Skills-first**: All features exposed as native `/dewey-*` skills
- **No API keys**: Leverage existing Claude Code session
- **Zero additional cost**: Included in user's Claude usage
- **Python helpers**: Support identification and file operations
- **One provider, done well**: Claude Code excellence before expansion

**Key Principles**:
- Measure before optimizing
- Skills over separate CLI tools
- Quick wins first
- Data-driven decisions
- Transparent recommendations (PRs, not auto-commits)

---

## Refactoring to Stdlib-Only (Feb 2026)

**Key Decision**: Removed all external dependencies and restructured to follow Claude Code best practices.

### Motivation

Initial exploration revealed that:
1. **No external dependencies needed**: Core Python modules (token_counter, file_splitter) only used stdlib
2. **Click dependency unnecessary**: Only used in CLI scripts, easily replaced with argparse
3. **Package installation friction**: Users had to run pip install, creating setup complexity
4. **Structure misalignment**: Commands in `commands/` instead of `skills/*/SKILL.md` format

### Changes Made

**Removed Dependencies** (v0.0.2):
- ❌ pandas (never actually used)
- ❌ pyyaml (never actually used)
- ❌ click (replaced with argparse)
- ❌ requests (never actually used)
- ❌ gitpython (never actually used)
- ❌ anthropic (uses Claude Code session instead)

**Restructured to Skills Format**:
```
Before:                          After:
commands/analyze.md       →     skills/analyze/SKILL.md
commands/split.md         →     skills/split/SKILL.md
src/dewey/core/...        →     skills/*/scripts/...
```

**Benefits**:
- ✅ Zero installation complexity (no pip install needed)
- ✅ Faster loading (no external imports)
- ✅ Follows official Claude Code plugin patterns
- ✅ Portable across all Python 3.9+ environments
- ✅ No dependency version conflicts
- ✅ Simpler maintenance

### Lessons Learned

1. **Start simple**: External dependencies weren't needed for core functionality
2. **Follow platform patterns**: Claude Code has well-defined best practices
3. **Question assumptions**: "We'll need pandas/requests" was never validated
4. **Stdlib is powerful**: Python 3.9+ has everything needed for file analysis

### Implementation Status

- ✅ Removed unimplemented command skeletons (report, check, optimize)
- ✅ Converted CLI scripts from Click to argparse
- ✅ Created skills/analyze/ and skills/split/ structure
- ✅ Updated all tests to use new import paths
- ✅ All 44 tests passing
- ✅ Zero runtime dependencies

Focus now on implemented features (analyze, split) before adding new capabilities.

---

## Architecture

### Skill-Based Design Pattern

```
┌─────────────────────────────────────────────────────────┐
│                  Claude Code Session                     │
│                                                          │
│  User: /dewey-split large-file.md                      │
│    ↓                                                     │
│  Skill Definition: .claude/skills/dewey-split.md       │
│    ↓                                                     │
│  Python Helpers: dewey/core/compaction/                 │
│    - Identify large files                               │
│    - Read content                                        │
│    ↓                                                     │
│  Claude Analysis: (uses current session - no API!)     │
│    - Semantic understanding                              │
│    - Anthropic best practices                           │
│    - Intelligent refactoring                             │
│    ↓                                                     │
│  Python Helpers: Write files, create backups            │
│    ↓                                                     │
│  Report: Display results to user                        │
└─────────────────────────────────────────────────────────┘
```

### File Structure

```
dewey/
├── .claude/
│   └── skills/              # Skill definitions
│       ├── dewey-split.md
│       ├── dewey-analyze.md
│       ├── dewey-report.md
│       ├── dewey-optimize.md
│       └── dewey-check.md
├── src/dewey/
│   ├── core/
│   │   ├── measurement/     # Token counting, frequency tracking
│   │   ├── compaction/      # File splitting, deduplication
│   │   ├── memory/          # Session management, promotion
│   │   └── analytics/       # Dashboard generation, KPIs
│   └── skills/              # Skill implementation helpers
│       ├── split_skill.py
│       ├── analyze_skill.py
│       └── report_skill.py
├── scripts/                 # Helper CLI tools
│   ├── identify-large-files.py
│   └── analyze-usage.py
└── tests/                   # Comprehensive test suite
```

---

## Phase 0: Foundation ✅ COMPLETE + REFACTORED

**Goal**: Establish baseline and infrastructure
**Status**: Complete and refactored to stdlib-only

### Completed Tasks

- ✅ **Task 0.1**: Project Structure Setup
- ✅ **Task 0.2**: Core Dependencies Setup (removed in refactoring)
- ✅ **Task 0.3**: Token Inventory Script
- ✅ **Task 0.4**: Session Tracking Template
- ✅ **Task 0.5**: Baseline Measurement Report
- ✅ **Task 0.6**: Intelligent File Splitting (skill-based!)
- ✅ **Refactoring**: Converted to stdlib-only, skills-based structure

**Key Achievements**:
- Established skill-based design pattern
- Zero external dependencies
- Follows Claude Code best practices

---

## Phase 1: Core Claude Code Skills (Weeks 2-3)

**Goal**: Build essential skills for context optimization
**Focus**: Measurement, analysis, and quick wins

### Task 1.1: `/dewey-analyze` Skill
**Priority**: High
**Dependencies**: Task 0.5
**Estimate**: M

**Description**: Analyze context usage and generate insights

**Acceptance Criteria**:
- [ ] Skill definition: `.claude/skills/dewey-analyze.md`
- [ ] Usage: `/dewey-analyze [directory]`
- [ ] Analyzes all files in context
- [ ] Reports: token usage, file sizes, distribution
- [ ] Identifies optimization opportunities
- [ ] Generates actionable recommendations
- [ ] No API key required (uses session)

**Implementation**:
```python
# src/dewey/skills/analyze_skill.py
def analyze_context(directory: Path) -> AnalysisReport:
    """
    Python helpers:
    1. Scan directory for files
    2. Count tokens, lines, sizes
    3. Return data to skill

    Skill (Claude):
    4. Analyze patterns
    5. Identify issues (large files, duplicates, etc.)
    6. Generate recommendations
    7. Format report
    """
```

**Output Example**:
```
📊 Context Analysis Report
================================

Total Files: 47
Total Tokens: 125,000
Average: 2,659 tokens/file

⚠️  Issues Found:
  1. 3 files over 500 lines
  2. Duplicate content detected (15%)
  3. 5 files loaded but never cited

💡 Recommendations:
  1. /dewey-split IMPLEMENTATION_PLAN.md
  2. /dewey-dedupe context/
  3. Archive unused files
```

---

### Task 1.2: `/dewey-report` Skill
**Priority**: High
**Dependencies**: Task 1.1
**Estimate**: S

**Description**: Generate weekly dashboard reports

**Acceptance Criteria**:
- [ ] Skill definition: `.claude/skills/dewey-report.md`
- [ ] Usage: `/dewey-report [--weekly|--monthly]`
- [ ] Reads CSV logs from measurement tracking
- [ ] Generates markdown dashboard
- [ ] Shows trends (week-over-week)
- [ ] Highlights wins and concerns
- [ ] Saves to `.claude/analytics/dashboard.md`

**Implementation**:
```python
# Uses pandas to analyze frequency.csv logs
# Skill formats insights and trends
```

---

### Task 1.3: Token Counter Module (Enhanced)
**Priority**: Medium
**Dependencies**: Task 0.3
**Estimate**: M

**Acceptance Criteria**:
- [x] Module: `src/core/measurement/token_counter.py` (exists)
- [ ] Enhanced with precise token counting (tiktoken)
- [ ] Support for different model tokenizers
- [ ] Batch processing optimization
- [ ] Type hints and comprehensive tests

**Implementation**:
```python
def estimate_tokens_precise(text: str, model: str = "claude-3") -> int:
    """Use tiktoken for precise counting"""
```

---

### Task 1.4: Frequency Tracker Module
**Priority**: Medium
**Dependencies**: Task 1.3
**Estimate**: M

**Description**: Track which files are loaded in each session

**Acceptance Criteria**:
- [ ] Module: `src/core/measurement/frequency_tracker.py`
- [ ] CSV logging: timestamp, file, tokens, session_id
- [ ] Thread-safe logging
- [ ] Log rotation (keep 90 days)
- [ ] Integration with Claude Code hooks (if available)

**Implementation**:
```python
# Logs to ~/.claude/analytics/frequency.csv
def log_file_load(file_path: str, tokens: int, session_id: str):
    """Log file access for analytics"""
```

---

### Task 1.5: `/dewey-check` Skill
**Priority**: High
**Dependencies**: Tasks 1.1, 1.3
**Estimate**: M

**Description**: Pre-commit hook style checks for context quality

**Acceptance Criteria**:
- [ ] Skill definition: `.claude/skills/dewey-check.md`
- [ ] Usage: `/dewey-check [--fast]`
- [ ] Validates:
  - File sizes <500 lines
  - No dead links
  - No excessive duplication
  - Token budget within limits
- [ ] Fast mode: <2 seconds for 200 files
- [ ] Exit codes: pass/warn/fail
- [ ] Integration with git hooks (optional)

**Implementation**:
```python
def check_context_quality(directory: Path) -> QualityReport:
    """Run quality checks and return report"""
```

---

## Phase 2: Optimization Skills (Weeks 4-6)

**Goal**: Implement intelligent optimization features
**Focus**: Compaction, deduplication, memory management

### Task 2.1: `/dewey-split` Skill ✅ COMPLETE
**Priority**: High
**Dependencies**: Task 0.6
**Estimate**: L

**Status**: Complete (implemented in Task 0.6)

**Features**:
- ✅ Intelligent file splitting with semantic analysis
- ✅ Uses current Claude Code session (no API key)
- ✅ Follows Anthropic best practices
- ✅ Creates topically organized references
- ✅ Backup and navigation

---

### Task 2.2: `/dewey-dedupe` Skill
**Priority**: High
**Dependencies**: Task 2.1
**Estimate**: L

**Description**: Identify and remove duplicate content

**Acceptance Criteria**:
- [ ] Skill definition: `.claude/skills/dewey-dedupe.md`
- [ ] Usage: `/dewey-dedupe [directory] [--dry-run]`
- [ ] Paragraph-level hashing
- [ ] Identifies duplicates across files
- [ ] Skill (Claude) decides:
  - Which instance to keep (canonical)
  - How to update references
  - Whether content is truly duplicate
- [ ] Preserves git history
- [ ] Creates consolidation report

**Implementation**:
```python
# Python: Hash paragraphs, find matches
# Skill: Semantic analysis, decide canonical location
# Python: Update files, create report
```

---

### Task 2.3: `/dewey-archive` Skill
**Priority**: Medium
**Dependencies**: Task 1.4
**Estimate**: M

**Description**: Archive old or unused files

**Acceptance Criteria**:
- [ ] Skill definition: `.claude/skills/dewey-archive.md`
- [ ] Usage: `/dewey-archive [--age=90] [--unused]`
- [ ] Identifies candidates:
  - Files older than N days
  - Files never cited in sessions
  - Files with low access frequency
- [ ] Skill reviews and confirms candidates
- [ ] Moves to `archive/YYYY/` with searchable index
- [ ] Preserves git history

---

### Task 2.4: `/dewey-session` Skill
**Priority**: Medium
**Dependencies**: Task 0.4
**Estimate**: M

**Description**: Manage session documentation and learnings

**Acceptance Criteria**:
- [ ] Skill definition: `.claude/skills/dewey-session.md`
- [ ] Usage:
  - `/dewey-session start "Session Title"`
  - `/dewey-session log "Learning or outcome"`
  - `/dewey-session end`
- [ ] Tracks files loaded in session
- [ ] Records outcomes and learnings
- [ ] Suggests promotions (session → long-term memory)
- [ ] Integration with session template

**Implementation**:
```python
class SessionManager:
    def start_session(self, title: str): pass
    def log_learning(self, content: str): pass
    def end_session(self): pass
```

---

### Task 2.5: `/dewey-promote` Skill
**Priority**: Medium
**Dependencies**: Task 2.4
**Estimate**: L

**Description**: Promote session learnings to long-term memory

**Acceptance Criteria**:
- [ ] Skill definition: `.claude/skills/dewey-promote.md`
- [ ] Usage: `/dewey-promote [session-file]`
- [ ] Deterministic rules:
  - Age >7 days + referenced 3+ times → promote
  - Referenced 5+ times → promote (any age)
  - Score <0.3 → discard
- [ ] Skill (Claude) reviews and decides:
  - Extract key insights
  - Determine target location (main context vs reference)
  - Rewrite for long-term clarity
- [ ] Requires user approval before promotion

---

## Phase 3: Automation & CI/CD (Weeks 7-10)

**Goal**: Automated optimization loops and quality gates
**Focus**: CI/CD integration, self-improvement, PR generation

### Task 3.1: `/dewey-optimize` Skill
**Priority**: High
**Dependencies**: Tasks 2.1-2.5
**Estimate**: L

**Description**: Run full optimization suite

**Acceptance Criteria**:
- [ ] Skill definition: `.claude/skills/dewey-optimize.md`
- [ ] Usage: `/dewey-optimize [--auto-approve]`
- [ ] Runs full analysis pipeline:
  1. Identify large files → suggest splits
  2. Find duplicates → suggest consolidation
  3. Detect unused files → suggest archival
  4. Check for dead links → suggest fixes
  5. Review session learnings → suggest promotions
- [ ] Generates optimization PR
- [ ] User reviews before applying
- [ ] Creates detailed changelog

---

### Task 3.2: KPI Evaluation Module
**Priority**: High
**Dependencies**: Task 1.1
**Estimate**: M

**Description**: Evaluate context quality KPIs

**Acceptance Criteria**:
- [ ] Module: `src/core/analytics/kpi_checker.py`
- [ ] Evaluates:
  - Context utilization (min 60%)
  - Token efficiency (min 70%)
  - File size max (500 lines)
  - Duplicate content (max 5%)
  - Dead links (0)
  - Citation rate (min 40%)
- [ ] Exit codes: 0 (pass), 1 (warn), 2 (fail)
- [ ] JSON output for CI/CD parsing
- [ ] Integration with `/dewey-check`

---

### Task 3.3: GitHub Actions Workflow Template
**Priority**: High
**Dependencies**: Task 3.2
**Estimate**: M

**Description**: CI/CD workflow for context quality

**Acceptance Criteria**:
- [ ] File: `templates/.github/workflows/dewey-quality.yml`
- [ ] Triggers: weekly + on push to context files
- [ ] Runs KPI checks
- [ ] Invokes `/dewey-optimize` skill (if Claude Code API available)
- [ ] Creates PR with recommendations
- [ ] Human approval required before merge
- [ ] Configurable via `.dewey/config.yml`

**Implementation**:
```yaml
name: Dewey Context Quality
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  push:
    paths:
      - 'context/**'
      - '.claude/**'
```

---

### Task 3.4: Self-Improvement Detection
**Priority**: Medium
**Dependencies**: Task 3.1
**Estimate**: L

**Description**: Dewey analyzes its own usage patterns

**Acceptance Criteria**:
- [ ] Module: `src/core/analytics/self_improvement.py`
- [ ] Analyzes patterns across repositories using Dewey
- [ ] Detects:
  - Common feature requests (15%+ of repos)
  - Bug patterns
  - Performance issues
  - UX friction points
- [ ] Creates PR on Dewey repository with improvements
- [ ] Examples:
  - "50% of users need custom thresholds → add config"
  - "Split skill timing out on 2000+ line files → optimize"

---

### Task 3.5: `/dewey-doctor` Skill
**Priority**: Medium
**Dependencies**: Tasks 3.1, 3.2
**Estimate**: M

**Description**: Diagnose context health issues

**Acceptance Criteria**:
- [ ] Skill definition: `.claude/skills/dewey-doctor.md`
- [ ] Usage: `/dewey-doctor`
- [ ] Comprehensive health check:
  - KPI evaluation
  - Performance analysis
  - Best practices compliance
  - Common anti-patterns
- [ ] Prescribes fixes with priority
- [ ] Interactive: can auto-apply fixes
- [ ] Explains reasoning for each recommendation

---

## Phase 4: Advanced Features (Weeks 11-14)

**Goal**: Polish, performance, and advanced capabilities
**Focus**: Citation tracking, summarization, quality scoring

### Task 4.1: Citation Tracker Module
**Priority**: Medium
**Dependencies**: Task 1.4
**Estimate**: L

**Description**: Track which files are actually used in responses

**Acceptance Criteria**:
- [ ] Module: `src/core/measurement/citation_tracker.py`
- [ ] Grep-based phrase matching
- [ ] Tracks which loaded files appear in Claude's responses
- [ ] CSV output: file, citation_count, utilization_rate
- [ ] Integration with frequency tracker
- [ ] Identifies "dead weight" files (loaded but never cited)

---

### Task 4.2: Extractive Summarizer
**Priority**: Low
**Dependencies**: Task 2.1
**Estimate**: L

**Description**: Create compact summaries of reference files

**Acceptance Criteria**:
- [ ] Module: `src/core/compaction/summarizer.py`
- [ ] TF-IDF based summarization (no LLM needed)
- [ ] 90%+ information retention
- [ ] Configurable compression ratio (5:1 to 10:1)
- [ ] Validation with sample documents
- [ ] Option to use skill (Claude) for better summaries

---

### Task 4.3: `/dewey-compress` Skill
**Priority**: Low
**Dependencies**: Task 4.2
**Estimate**: M

**Description**: Compress verbose files

**Acceptance Criteria**:
- [ ] Skill definition: `.claude/skills/dewey-compress.md`
- [ ] Usage: `/dewey-compress file.md [--ratio=0.5]`
- [ ] Uses Claude to intelligently compress
- [ ] Maintains key information
- [ ] Better than extractive summarization
- [ ] Creates side-by-side comparison

---

### Task 4.4: Quality Scoring System
**Priority**: Low
**Dependencies**: Tasks 3.2, 4.1
**Estimate**: M

**Description**: Score context files by quality/usefulness

**Acceptance Criteria**:
- [ ] Module: `src/core/analytics/quality_scorer.py`
- [ ] Scores based on:
  - Citation frequency
  - Token efficiency
  - Recency of updates
  - Structural quality
  - Best practices compliance
- [ ] Grade: A-F per file
- [ ] Recommendations for low-scoring files
- [ ] Integration with `/dewey-report`

---

## Phase 5: Testing & Documentation (Ongoing)

**Goal**: Comprehensive tests and user documentation
**Focus**: Test coverage, examples, guides

### Task 5.1: Skill Integration Tests
**Priority**: High
**Dependencies**: Phase 1-2 tasks
**Estimate**: L

**Acceptance Criteria**:
- [ ] Tests in `tests/skills/`
- [ ] Test each skill end-to-end
- [ ] Mock Claude Code skill system
- [ ] Test error handling
- [ ] Test edge cases
- [ ] Coverage >80% for skill helpers

---

### Task 5.2: User Guide
**Priority**: High
**Dependencies**: Phase 1-2
**Estimate**: M

**Acceptance Criteria**:
- [ ] File: `docs/USER_GUIDE.md`
- [ ] Installation instructions
- [ ] Skill reference (all `/dewey-*` commands)
- [ ] Examples and workflows
- [ ] Troubleshooting guide
- [ ] Best practices

---

### Task 5.3: Skill Examples Repository
**Priority**: Medium
**Dependencies**: Phase 1-2
**Estimate**: S

**Acceptance Criteria**:
- [ ] Directory: `examples/`
- [ ] Sample context repository
- [ ] Before/after examples
- [ ] Video demonstrations (optional)
- [ ] Common workflows documented

---

## Phase 6: Multi-Provider Expansion (Future)

**Goal**: Extend to Codex, Gemini, and other providers
**Status**: Deferred until Claude Code implementation proven

This phase will leverage learnings from Claude Code to create provider adapters for:
- OpenAI Codex
- Google Gemini
- Other LLM CLI tools

**Approach**: Extract common patterns, create provider abstraction layer, implement adapters.

---

## Skills Summary

### Phase 1 (Core)
- `/dewey-analyze` - Analyze context usage
- `/dewey-report` - Generate dashboard
- `/dewey-check` - Quality checks

### Phase 2 (Optimization)
- `/dewey-split` - Split large files ✅
- `/dewey-dedupe` - Remove duplicates
- `/dewey-archive` - Archive old files
- `/dewey-session` - Manage sessions
- `/dewey-promote` - Promote learnings

### Phase 3 (Automation)
- `/dewey-optimize` - Full optimization suite
- `/dewey-doctor` - Health diagnosis

### Phase 4 (Advanced)
- `/dewey-compress` - Compress verbose files

---

## Success Criteria

### Phase 0 Complete ✅
- [x] Token inventory working
- [x] Session template created
- [x] Baseline measurements taken
- [x] File splitting with skill-based design

### Phase 1 Complete
- [ ] All core skills functional
- [ ] Measurement tracking automated
- [ ] Weekly reports generating
- [ ] Quality checks integrated

### Phase 2 Complete
- [ ] All optimization skills working
- [ ] Session management operational
- [ ] Promotion engine suggesting candidates
- [ ] >80% test coverage

### Phase 3 Complete
- [ ] CI/CD workflow templates ready
- [ ] Automated optimization PRs generating
- [ ] Self-improvement detecting patterns
- [ ] Quality gates preventing regressions

### Ready for Multi-Provider Expansion
- [ ] Claude Code plugin proven valuable
- [ ] User adoption validated
- [ ] Architecture patterns documented
- [ ] Provider abstraction layer designed

---

## Completion Promise

When Phase 1-3 complete and Claude Code plugin validated, output:

```
<promise>DEWEY CLAUDE CODE PLUGIN COMPLETE</promise>
```

**Final Verification**:
- [ ] All core skills functional
- [ ] Test coverage >80%
- [ ] User guide complete
- [ ] CI/CD templates working
- [ ] Real-world usage validated
- [ ] Ready for multi-provider expansion

---

## Task Summary by Phase

- **Phase 0**: 6 tasks ✅ **COMPLETE**
- **Phase 1**: 5 tasks (Core Skills)
- **Phase 2**: 5 tasks (Optimization Skills)
- **Phase 3**: 5 tasks (Automation & CI/CD)
- **Phase 4**: 4 tasks (Advanced Features)
- **Phase 5**: 3 tasks (Testing & Documentation)
- **Phase 6**: Deferred (Multi-Provider)

**Total**: 28 active tasks (vs 44 in original plan)
**Estimated Effort**: ~6-8 weeks (vs 8-12 weeks)

---

## Key Changes from v1.0

### Removed/Deferred
- ❌ Multi-provider support (Codex, Gemini) - Phase 6
- ❌ Separate CLI tools - Replaced with skills
- ❌ API key management - Uses session
- ❌ Provider auto-detection - Single provider
- ❌ Extension packaging - Claude Code only

### Added/Enhanced
- ✅ Skill-based design pattern throughout
- ✅ `/dewey-*` command namespace
- ✅ Session-based LLM integration
- ✅ Simplified architecture
- ✅ Faster time to value

### Philosophy Shift
- **From**: Universal multi-provider tool
- **To**: Excellent Claude Code plugin first, expand later
- **Benefit**: Faster development, better focus, validated approach

---

## Notes

- All skills use Claude Code session (no API keys)
- Python helpers support file operations
- Skills provide intelligence and analysis
- Focus on user experience and simplicity
- Multi-provider expansion after validation
- Continuous testing and documentation

---

**Current Status**: Phase 0 complete, starting Phase 1
**Next Task**: Task 1.1 - `/dewey-analyze` skill
**Updated**: 2026-02-10
