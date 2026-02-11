# Dewey Universal Context Optimizer - Implementation Plan

**Created**: 2026-02-10
**Status**: Planning Phase Complete
**Current Phase**: Phase 0 (Foundation)

---

## Overview

This plan implements "Dewey" - a universal context optimization plugin compatible with Claude Code, OpenAI Codex, and Google Gemini. The approach follows "Start Small" philosophy: measure first, optimize incrementally, validate continuously.

**Key Principles**:
- Measure before optimizing
- One change at a time
- Quick wins first
- Data-driven decisions
- Transparent recommendations (PRs, not auto-commits)

---

## Phase 0: Foundation (Week 1) - Quick Start

**Goal**: Establish baseline and infrastructure

### Task 0.1: Project Structure Setup ✅ COMPLETE
**Spec**: spec-0-quick-start.md
**Dependencies**: None
**Estimate**: S (Small)

**Acceptance Criteria**:
- [x] Create `dewey/` directory structure as defined in seed prompt
- [x] Initialize Python package with `pyproject.toml`
- [x] Set up `src/`, `tests/`, `scripts/`, `templates/` directories
- [x] Create `README.md` with project overview
- [x] Initialize git repository with `.gitignore`

**Implementation**:
```bash
mkdir -p dewey/{src,tests,scripts,templates}
cd dewey
git init
```

### Task 0.2: Core Dependencies Setup
**Spec**: spec-0-quick-start.md
**Dependencies**: Task 0.1
**Estimate**: S

**Acceptance Criteria**:
- [ ] Create `pyproject.toml` with dependencies: pandas, pyyaml, click, pytest, ruff, mypy
- [ ] Set up virtual environment
- [ ] Install development dependencies
- [ ] Configure ruff and mypy

**Implementation**:
```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Task 0.3: Token Inventory Script
**Spec**: spec-0-quick-start.md, spec-1-measurement.md
**Dependencies**: Task 0.2
**Estimate**: M (Medium)

**Acceptance Criteria**:
- [ ] Script counts all files in context directory
- [ ] Estimates tokens (4 chars ≈ 1 token)
- [ ] Outputs CSV: file, lines, bytes, tokens
- [ ] Can run in <10 seconds on 200 files
- [ ] Saves to `~/.claude/analytics/context-inventory.csv`

**Implementation**:
```python
# scripts/analyze-usage.py --inventory
def count_tokens(file_path):
    with open(file_path) as f:
        content = f.read()
    return len(content) // 4  # 4 chars ≈ 1 token
```

### Task 0.4: Session Tracking Template
**Spec**: spec-0-quick-start.md, spec-3-memory-tier.md
**Dependencies**: Task 0.2
**Estimate**: S

**Acceptance Criteria**:
- [ ] Create session template with sections: Goal, Files Used, Outcomes, Learnings
- [ ] Template in `.claude/sessions/template.md`
- [ ] Documentation for manual usage
- [ ] Example session file included

**Implementation**:
```markdown
# Session: [YYYY-MM-DD] - [Brief Title]
## Goal
What I'm trying to accomplish

## Files Loaded
- file1.md (reason)
- file2.md (reason)

## Outcomes
What happened

## Learnings
What to remember
```

### Task 0.5: Baseline Measurement Report
**Spec**: spec-0-quick-start.md
**Dependencies**: Task 0.3
**Estimate**: S

**Acceptance Criteria**:
- [ ] Run token inventory on test repository
- [ ] Generate baseline report: total files, total tokens, file size distribution
- [ ] Save to `~/.claude/analytics/baseline.txt`
- [ ] Report includes top 10 largest files

**Implementation**:
```bash
python scripts/analyze-usage.py --inventory --report
```

### Task 0.6: First Quick Win - File Splitting
**Spec**: spec-0-quick-start.md, spec-2-compaction.md
**Dependencies**: Task 0.5
**Estimate**: M

**Acceptance Criteria**:
- [ ] Identify files >500 lines from inventory
- [ ] Script to split file into main + references/
- [ ] Update wikilinks automatically
- [ ] Before/after comparison report
- [ ] Backup created before splitting

**Implementation**:
```python
# scripts/consolidate.sh --split large-file.md
def split_file(path, max_lines=500):
    # Split into main (first 150 lines) + references/
    pass
```

---

## Phase 1: Measurement System (Weeks 2-4)

**Goal**: Build analytics foundation for data-driven optimization

### Task 1.1: Token Counter Module
**Spec**: spec-1-measurement.md
**Dependencies**: Task 0.3
**Estimate**: M

**Acceptance Criteria**:
- [ ] Python module `src/core/measurement/token_counter.py`
- [ ] Accurate token estimation (4 chars ≈ 1 token)
- [ ] Support for different encodings (UTF-8, ASCII)
- [ ] Type hints and docstrings
- [ ] Unit tests with >80% coverage

**Implementation**:
```python
def estimate_tokens(text: str) -> int:
    """Estimate tokens using 4 chars ≈ 1 token heuristic"""
    return len(text) // 4
```

### Task 1.2: Frequency Tracker Module
**Spec**: spec-1-measurement.md
**Dependencies**: Task 1.1
**Estimate**: M

**Acceptance Criteria**:
- [ ] Module `src/core/measurement/frequency_tracker.py`
- [ ] CSV logging: timestamp, file, tokens, session_id
- [ ] Thread-safe logging
- [ ] Log rotation (keep 90 days)
- [ ] Tests for concurrent access

**Implementation**:
```python
# Logs to ~/.claude/analytics/frequency.csv
def log_file_load(file_path: str, tokens: int, session_id: str):
    pass
```

### Task 1.3: Citation Tracker Module
**Spec**: spec-1-measurement.md
**Dependencies**: Task 1.2
**Estimate**: L (Large)

**Acceptance Criteria**:
- [ ] Module `src/core/measurement/citation_tracker.py`
- [ ] Grep-based phrase matching (extract key phrases from files)
- [ ] Track which loaded files appear in responses
- [ ] CSV output: file, citation_count, utilization_rate
- [ ] Handle edge cases (partial matches, synonyms)

**Implementation**:
```python
def extract_key_phrases(file_path: str) -> List[str]:
    """Extract headers, code blocks, unique terms"""
    pass

def check_citations(response: str, loaded_files: List[str]) -> Dict:
    """Check which files were referenced in response"""
    pass
```

### Task 1.4: Analytics Logger
**Spec**: spec-4-analytics.md
**Dependencies**: Task 1.3
**Estimate**: M

**Acceptance Criteria**:
- [ ] Module `src/core/analytics/logger.py`
- [ ] Unified logging interface for all trackers
- [ ] Structured logging (JSON + CSV)
- [ ] Privacy-preserving (no PII in logs)
- [ ] Configurable log levels

**Implementation**:
```python
class AnalyticsLogger:
    def log_session(self, session_data: dict): pass
    def log_file_load(self, file_data: dict): pass
    def log_citation(self, citation_data: dict): pass
```

### Task 1.5: Weekly Dashboard Generator
**Spec**: spec-4-analytics.md
**Dependencies**: Task 1.4
**Estimate**: L

**Acceptance Criteria**:
- [ ] Module `src/core/analytics/dashboard_generator.py`
- [ ] Pandas-based analysis of CSV logs
- [ ] Markdown report with metrics:
  - Context utilization
  - Token efficiency
  - Most/least valuable files
  - Citation rates
  - Week-over-week trends
- [ ] Automated generation via cron/scheduler
- [ ] Tests with sample data

**Implementation**:
```python
def generate_weekly_dashboard() -> str:
    """Generate markdown dashboard from analytics CSVs"""
    # Read frequency.csv, citations.csv
    # Calculate metrics
    # Format as markdown
    pass
```

---

## Phase 2: Optimization & Memory (Month 2)

**Goal**: Implement compaction and mid-term memory tier

### Task 2.1: File Splitter
**Spec**: spec-2-compaction.md
**Dependencies**: Task 0.6
**Estimate**: L

**Acceptance Criteria**:
- [ ] Module `src/core/compaction/file_splitter.py`
- [ ] Automated splitting for files >500 lines
- [ ] Preserves first 150 lines as main file
- [ ] Moves remaining content to references/ subdirectory
- [ ] Updates all wikilinks across repository
- [ ] Creates git commits with clear history
- [ ] Dry-run mode for preview

**Implementation**:
```python
def split_large_file(path: str, max_lines: int = 500) -> SplitResult:
    """Split file into main + references/"""
    pass

def update_wikilinks(old_path: str, new_paths: List[str]):
    """Update [[wikilinks]] across repository"""
    pass
```

### Task 2.2: Duplicate Content Detector
**Spec**: spec-2-compaction.md
**Dependencies**: Task 2.1
**Estimate**: L

**Acceptance Criteria**:
- [ ] Module `src/core/compaction/duplicate_detector.py`
- [ ] Paragraph-level hashing (MD5 or SHA256)
- [ ] Identify duplicates across files
- [ ] Report with locations and similarity scores
- [ ] Suggestion to consolidate to canonical location
- [ ] Ignore code blocks and common boilerplate

**Implementation**:
```python
def hash_paragraphs(file_path: str) -> Dict[str, str]:
    """Return {hash: paragraph_text}"""
    pass

def find_duplicates(repo_path: str) -> List[Duplicate]:
    """Find duplicate paragraphs across files"""
    pass
```

### Task 2.3: Dead Link Checker
**Spec**: spec-2-compaction.md
**Dependencies**: Task 2.1
**Estimate**: M

**Acceptance Criteria**:
- [ ] Module `src/core/compaction/duplicate_detector.py` (extended)
- [ ] Parse [[wikilinks]] and [markdown](links)
- [ ] Verify targets exist
- [ ] Report broken links with suggestions
- [ ] CI/CD integration (fail on broken links)

**Implementation**:
```python
def check_links(file_path: str) -> List[BrokenLink]:
    """Check all links in file"""
    pass
```

### Task 2.4: Time-Based Archival
**Spec**: spec-2-compaction.md
**Dependencies**: Task 2.2
**Estimate**: M

**Acceptance Criteria**:
- [ ] Script to archive files >90 days old
- [ ] Configurable age threshold
- [ ] Moves to `archive/YYYY/` directory
- [ ] Creates searchable index
- [ ] Preserves git history

**Implementation**:
```bash
# scripts/archive-old-files.sh --age=90
```

### Task 2.5: Extractive Summarizer
**Spec**: spec-2-compaction.md
**Dependencies**: Task 2.4
**Estimate**: L

**Acceptance Criteria**:
- [ ] Module `src/core/compaction/extractive_summarizer.py`
- [ ] TF-IDF based summarization (no LLM)
- [ ] 90%+ information retention
- [ ] Configurable compression ratio (5:1 to 10:1)
- [ ] Validation with sample documents

**Implementation**:
```python
from sklearn.feature_extraction.text import TfidfVectorizer

def extractive_summarize(text: str, ratio: float = 0.2) -> str:
    """Extract most important sentences using TF-IDF"""
    pass
```

### Task 2.6: Session Manager
**Spec**: spec-3-memory-tier.md
**Dependencies**: Task 0.4
**Estimate**: M

**Acceptance Criteria**:
- [ ] Module `src/core/memory/session_manager.py`
- [ ] Automated session file creation
- [ ] Week-based organization
- [ ] Session metadata tracking
- [ ] Integration with session hooks

**Implementation**:
```python
class SessionManager:
    def start_session(self, title: str): pass
    def end_session(self): pass
    def log_learning(self, content: str): pass
```

### Task 2.7: Promotion Engine
**Spec**: spec-3-memory-tier.md
**Dependencies**: Task 2.6
**Estimate**: L

**Acceptance Criteria**:
- [ ] Module `src/core/memory/promotion_engine.py`
- [ ] Deterministic promotion rules:
  - Age >7 days + referenced 3+ times → Promote
  - Referenced 5+ times → Promote (any age)
  - Score <0.3 → Discard
  - Score 0.3-0.6 → Keep in mid-term
- [ ] Weekly review workflow
- [ ] Manual approval required
- [ ] Tests for all promotion paths

**Implementation**:
```python
def calculate_promotion_score(session_file: str) -> float:
    """Calculate score based on age, references, validation"""
    pass

def suggest_promotions() -> List[PromotionCandidate]:
    """Suggest files ready for promotion"""
    pass
```

---

## Phase 3: Automation & Multi-Provider (Month 3+)

**Goal**: CI/CD loops, multi-provider support, slash commands

### Task 3.1: Provider Base Interface
**Spec**: spec-6-multi-provider.md
**Dependencies**: None (parallel to Phase 2)
**Estimate**: M

**Acceptance Criteria**:
- [ ] Module `src/providers/base.py`
- [ ] Abstract base class with methods:
  - `load_context()`
  - `get_config()`
  - `validate_structure()`
  - `install_templates()`
- [ ] Type hints for provider interface
- [ ] Documentation for creating new adapters

**Implementation**:
```python
from abc import ABC, abstractmethod

class ProviderAdapter(ABC):
    @abstractmethod
    def load_context(self) -> List[str]: pass

    @abstractmethod
    def get_config(self) -> dict: pass

    @abstractmethod
    def validate_structure(self) -> ValidationResult: pass
```

### Task 3.2: Claude Code Adapter
**Spec**: spec-6-multi-provider.md
**Dependencies**: Task 3.1
**Estimate**: M

**Acceptance Criteria**:
- [ ] Module `src/providers/claude.py`
- [ ] Implements base adapter interface
- [ ] Supports `.claude/` directory conventions
- [ ] Parses `CLAUDE.md` configuration
- [ ] Validates [[wikilinks]] format
- [ ] Max file size: 500 lines

**Implementation**:
```python
class ClaudeAdapter(ProviderAdapter):
    config_path = ".claude/CLAUDE.md"
    context_dir = "context/"
    link_format = "wikilinks"
```

### Task 3.3: Codex Adapter
**Spec**: spec-6-multi-provider.md
**Dependencies**: Task 3.1
**Estimate**: M

**Acceptance Criteria**:
- [ ] Module `src/providers/codex.py`
- [ ] Supports `AGENTS.md` and `SKILL.md`
- [ ] Context directory: `docs/` or `context/`
- [ ] Markdown links format
- [ ] Max file size: 1000 lines

**Implementation**:
```python
class CodexAdapter(ProviderAdapter):
    config_path = "AGENTS.md"
    context_dir = ["docs/", "context/"]
    link_format = "markdown"
```

### Task 3.4: Gemini Adapter
**Spec**: spec-6-multi-provider.md
**Dependencies**: Task 3.1
**Estimate**: M

**Acceptance Criteria**:
- [ ] Module `src/providers/gemini.py`
- [ ] Supports `.gemini/config.yaml`
- [ ] Context directory: `.gemini/context/`
- [ ] Both link formats supported
- [ ] Max file size: 800 lines

**Implementation**:
```python
class GeminiAdapter(ProviderAdapter):
    config_path = ".gemini/config.yaml"
    context_dir = ".gemini/context/"
    link_format = "both"
```

### Task 3.5: Provider Auto-Detection
**Spec**: spec-6-multi-provider.md
**Dependencies**: Tasks 3.2, 3.3, 3.4
**Estimate**: S

**Acceptance Criteria**:
- [ ] Function `detect_provider(repo_path)`
- [ ] Checks for `.claude/`, `AGENTS.md`, `.gemini/`
- [ ] Returns provider name or "unknown"
- [ ] 95%+ accuracy on test repositories
- [ ] Tests for all provider types

**Implementation**:
```python
def detect_provider(repo_path: Path) -> str:
    if (repo_path / ".claude").exists():
        return "claude"
    elif (repo_path / "AGENTS.md").exists():
        return "codex"
    elif (repo_path / ".gemini").exists():
        return "gemini"
    else:
        return "unknown"
```

### Task 3.6: Slash Command Framework
**Spec**: spec-7-slash-commands.md
**Dependencies**: Task 3.5
**Estimate**: L

**Acceptance Criteria**:
- [ ] Module `src/cli/commands.py`
- [ ] Click-based CLI framework
- [ ] Commands: init, check, report, fix, status, analyze, session, pr, help
- [ ] Unified interface across providers
- [ ] Progress indicators for long operations
- [ ] Markdown output

**Implementation**:
```python
import click

@click.group()
def dewey():
    """Universal context optimization"""
    pass

@dewey.command()
@click.option('--provider', default='auto')
def init(provider):
    """Initialize Dewey in repository"""
    pass
```

### Task 3.7: Extension Packaging - Claude Code
**Spec**: spec-7-slash-commands.md
**Dependencies**: Task 3.6
**Estimate**: M

**Acceptance Criteria**:
- [ ] Directory `src/extensions/claude/`
- [ ] `manifest.yaml` with permissions
- [ ] Entry point script
- [ ] Installation via `claude code install dewey`
- [ ] Commands registered automatically

**Implementation**:
```yaml
# src/extensions/claude/manifest.yaml
name: dewey
version: 1.0.0
commands:
  - name: dewey
    script: ./dewey.py
```

### Task 3.8: Extension Packaging - Codex
**Spec**: spec-7-slash-commands.md
**Dependencies**: Task 3.6
**Estimate**: M

**Acceptance Criteria**:
- [ ] Directory `src/extensions/codex/`
- [ ] `extension.json` configuration
- [ ] Installation via `codex extensions add dewey`

### Task 3.9: Extension Packaging - Gemini
**Spec**: spec-7-slash-commands.md
**Dependencies**: Task 3.6
**Estimate**: M

**Acceptance Criteria**:
- [ ] Directory `src/extensions/gemini/`
- [ ] `plugin.yaml` configuration
- [ ] Installation via `gemini plugins install dewey`

### Task 3.10: KPI Evaluation Script
**Spec**: spec-5-dual-cicd-loops.md
**Dependencies**: Task 1.5
**Estimate**: M

**Acceptance Criteria**:
- [ ] Module `src/cicd/kpi_checker.py`
- [ ] Evaluates:
  - Context utilization (min 60%)
  - Token efficiency (min 70%)
  - File size max (500 lines)
  - Duplicate content (max 5%)
  - Dead links (0)
- [ ] Exit codes: 0 (pass), 1 (warn), 2 (fail)
- [ ] JSON output for CI/CD parsing

**Implementation**:
```python
def check_kpis(repo_path: str) -> KPIResult:
    """Evaluate context quality KPIs"""
    pass
```

### Task 3.11: Recommendation Engine
**Spec**: spec-5-dual-cicd-loops.md
**Dependencies**: Task 3.10
**Estimate**: L

**Acceptance Criteria**:
- [ ] Module `src/cicd/recommendation_engine.py`
- [ ] Categories:
  - File splitting (>500 lines)
  - Duplicate removal
  - Archive old content (>90 days)
  - Load optimization (high load, low citation)
  - Missing context
- [ ] Priority ranking (high/medium/low)
- [ ] Impact estimates (token savings, effort)

**Implementation**:
```python
def generate_recommendations(repo_path: str) -> List[Recommendation]:
    """Analyze repo and suggest optimizations"""
    pass
```

### Task 3.12: PR Generator - Loop 2 (Target Repo)
**Spec**: spec-5-dual-cicd-loops.md
**Dependencies**: Task 3.11
**Estimate**: L

**Acceptance Criteria**:
- [ ] Module `src/reports/pr_generator.py`
- [ ] Creates PR with:
  - KPI summary
  - Prioritized recommendations
  - Specific changes (diffs)
  - Expected impact
  - Trend analysis
- [ ] Uses GitHub API
- [ ] Markdown formatting
- [ ] Transparent (human reviews before merge)

**Implementation**:
```python
def create_optimization_pr(repo_path: str) -> str:
    """Generate PR with context optimization suggestions"""
    # Analyze repo
    # Generate recommendations
    # Format as PR body
    # Create PR via GitHub API
    pass
```

### Task 3.13: Self-Improvement Detector - Loop 1 (Dewey)
**Spec**: spec-5-dual-cicd-loops.md
**Dependencies**: Task 3.11
**Estimate**: L

**Acceptance Criteria**:
- [ ] Module `src/cicd/self_improvement.py`
- [ ] Detects patterns in Dewey's own usage
- [ ] Suggests improvements to Dewey itself
- [ ] Creates PR on Dewey repository
- [ ] Examples:
  - Missing feature used by 15%+ of repos
  - Bug pattern detected
  - Performance optimization opportunity

**Implementation**:
```python
def detect_self_improvement_opportunities() -> List[Improvement]:
    """Analyze Dewey's usage patterns across repos"""
    pass
```

### Task 3.14: CI/CD Workflow - Loop 1 (Dewey)
**Spec**: spec-5-dual-cicd-loops.md
**Dependencies**: Task 3.13
**Estimate**: M

**Acceptance Criteria**:
- [ ] File `.github/workflows/dewey-ci.yml`
- [ ] Runs on Dewey repository
- [ ] Triggered weekly + on push
- [ ] Evaluates Dewey's own quality
- [ ] Creates PR with improvements
- [ ] Tests must pass before PR creation

**Implementation**:
```yaml
# .github/workflows/dewey-ci.yml
name: Dewey Self-Improvement
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  push:
    branches: [main]
```

### Task 3.15: CI/CD Workflow Template - Loop 2 (Target)
**Spec**: spec-5-dual-cicd-loops.md
**Dependencies**: Task 3.12
**Estimate**: M

**Acceptance Criteria**:
- [ ] File `templates/.github/workflows/dewey-checks.yml`
- [ ] Installed to target repo via `dewey init`
- [ ] Runs weekly
- [ ] Checks quality gates
- [ ] Creates PR with optimization suggestions
- [ ] Configurable via `.dewey/config.yml`

**Implementation**:
```yaml
# templates/.github/workflows/dewey-checks.yml
name: Dewey Context Optimization
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
```

### Task 3.16: Pre-Commit Hooks
**Spec**: spec-5-dual-cicd-loops.md
**Dependencies**: Task 3.10
**Estimate**: S

**Acceptance Criteria**:
- [ ] Template `templates/hooks/pre-commit`
- [ ] Validates:
  - File size <500 lines
  - No dead links
  - No duplicates >5%
- [ ] Fast (<2 seconds for 200 files)
- [ ] Installed via `dewey init`

**Implementation**:
```bash
#!/bin/bash
# templates/hooks/pre-commit
dewey check --fast || exit 1
```

---

## Phase 4: Testing & Documentation (Ongoing)

**Goal**: Comprehensive tests and documentation

### Task 4.1: Unit Tests - Measurement
**Dependencies**: Tasks 1.1-1.3
**Estimate**: M

**Acceptance Criteria**:
- [ ] Tests in `tests/test_measurement.py`
- [ ] Coverage >80% for measurement modules
- [ ] Edge cases tested
- [ ] Mock file system for isolation

### Task 4.2: Unit Tests - Compaction
**Dependencies**: Tasks 2.1-2.5
**Estimate**: M

**Acceptance Criteria**:
- [ ] Tests in `tests/test_compaction.py`
- [ ] Coverage >80% for compaction modules
- [ ] Test file splitting, deduplication, summarization

### Task 4.3: Unit Tests - Memory Tier
**Dependencies**: Tasks 2.6-2.7
**Estimate**: M

**Acceptance Criteria**:
- [ ] Tests in `tests/test_memory.py`
- [ ] Coverage >80% for memory modules
- [ ] Test promotion rules and session management

### Task 4.4: Unit Tests - CI/CD
**Dependencies**: Tasks 3.10-3.16
**Estimate**: L

**Acceptance Criteria**:
- [ ] Tests in `tests/test_cicd_loops.py`
- [ ] Test both loops independently
- [ ] Mock GitHub API calls
- [ ] Test PR generation

### Task 4.5: Integration Tests - Providers
**Dependencies**: Tasks 3.2-3.5
**Estimate**: L

**Acceptance Criteria**:
- [ ] Tests in `tests/test_providers/`
- [ ] Test each provider adapter
- [ ] Test auto-detection
- [ ] Test with sample repositories

### Task 4.6: Integration Tests - Slash Commands
**Dependencies**: Task 3.6
**Estimate**: M

**Acceptance Criteria**:
- [ ] Tests in `tests/test_commands/`
- [ ] Test all commands: init, check, report, fix, status
- [ ] Test error handling
- [ ] Test help system

### Task 4.7: End-to-End Workflow Test
**Dependencies**: All previous tasks
**Estimate**: L

**Acceptance Criteria**:
- [ ] Script `tests/integration/test_workflow.sh`
- [ ] Tests complete workflow:
  1. `dewey init`
  2. Run baseline measurements
  3. Apply optimizations
  4. Generate dashboard
  5. Create PR
- [ ] Works on sample repository
- [ ] Validates all outputs

### Task 4.8: Documentation - User Guide
**Dependencies**: Task 3.6
**Estimate**: M

**Acceptance Criteria**:
- [ ] `docs/USER_GUIDE.md` created
- [ ] Installation instructions for all providers
- [ ] Command reference
- [ ] Configuration guide
- [ ] Troubleshooting section

### Task 4.9: Documentation - Architecture
**Dependencies**: All implementation tasks
**Estimate**: M

**Acceptance Criteria**:
- [ ] `docs/ARCHITECTURE.md` created
- [ ] System overview diagram
- [ ] Component descriptions
- [ ] Provider adapter pattern explained
- [ ] CI/CD loop details

### Task 4.10: Documentation - Provider Differences
**Dependencies**: Tasks 3.2-3.4
**Estimate**: S

**Acceptance Criteria**:
- [ ] `docs/PROVIDERS.md` created
- [ ] Comparison table
- [ ] Provider-specific guidance
- [ ] Migration guide between providers

---

## Success Criteria

### Phase 0 Complete
- [ ] Token inventory script working
- [ ] Session template created
- [ ] Baseline measurements taken
- [ ] One file split successfully

### Phase 1 Complete
- [ ] CSV logging captures >90% of sessions
- [ ] Weekly dashboard generates automatically
- [ ] Citation tracking working
- [ ] All measurement tests passing

### Phase 2 Complete
- [ ] File splitter handles >500 line files
- [ ] Duplicate detector finds duplicates
- [ ] Session manager tracks learnings
- [ ] Promotion engine suggests candidates
- [ ] All compaction tests passing

### Phase 3 Complete
- [ ] All 3 provider adapters working
- [ ] Auto-detection 95%+ accurate
- [ ] All slash commands functional
- [ ] Extensions installable in all providers
- [ ] Loop 1: Dewey self-improvement working
- [ ] Loop 2: Target repo optimization working
- [ ] Both loops generate PRs (not auto-commits)
- [ ] Pre-commit hooks prevent regressions
- [ ] All CI/CD tests passing

### Phase 4 Complete
- [ ] Test coverage >80%
- [ ] All integration tests passing
- [ ] Documentation complete
- [ ] Ready for production use

---

## Completion Promise

When all phases complete and tests pass, output:

```
<promise>DEWEY UNIVERSAL CONTEXT OPTIMIZER COMPLETE</promise>
```

**Final Verification**:
- [ ] All 43 tasks completed
- [ ] Test coverage >80%
- [ ] Type checks pass (mypy)
- [ ] Lint checks pass (ruff)
- [ ] Integration tests pass for all 3 providers
- [ ] Weekly dashboard generates successfully
- [ ] Dual CI/CD loops operational
- [ ] Transparent PRs generated (not auto-commits)
- [ ] Multi-provider support validated
- [ ] Documentation complete
- [ ] Installation tested in all providers

---

## Task Summary by Phase

- **Phase 0**: 6 tasks (S:4, M:2)
- **Phase 1**: 5 tasks (M:4, L:1)
- **Phase 2**: 7 tasks (S:0, M:3, L:4)
- **Phase 3**: 16 tasks (S:2, M:9, L:5)
- **Phase 4**: 10 tasks (S:1, M:5, L:4)

**Total**: 44 tasks
**Estimated Effort**: ~8-12 weeks

---

## Notes

- Tasks can be parallelized within phases (use subagents)
- Each task should be completed fully before moving to next
- Tests are mandatory for all core functionality
- Documentation should be updated as features are built
- Follow "Start Small" philosophy - measure before optimizing
- Transparency is key - generate PRs for review, not auto-commits
