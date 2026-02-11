# Dewey - Context Optimization Plugin for Claude Code

**Version**: 0.0.1 (Early Development)
**Status**: Phase 0 Complete, Phase 1 In Progress

Dewey is a Claude Code plugin that helps you intelligently manage, analyze, and optimize your context files. It uses the Claude Code session to provide smart recommendations without requiring additional API keys or costs.

---

## Features

### ✅ Available Now

- **`/dewey:split`** - Intelligently split large files (>500 lines) using LLM analysis
  - Maintains semantic coherence
  - Creates topically organized references
  - Follows Anthropic's best practices
  - Automatic backups

- **`/dewey:analyze`** - Comprehensive context analysis
  - Token usage and distribution
  - File size analysis
  - Identifies optimization opportunities
  - Prioritized recommendations

### 🚧 Coming Soon (Phase 1)

- **`/dewey:report`** - Generate weekly/monthly dashboards
- **`/dewey:check`** - Pre-commit quality checks
- **Token tracking** - Frequency and citation tracking
- **Baseline comparisons** - Track improvements over time

### 📋 Planned (Phase 2-3)

- **`/dewey:dedupe`** - Remove duplicate content
- **`/dewey:archive`** - Archive old/unused files
- **`/dewey:optimize`** - Full optimization suite
- **CI/CD integration** - Automated quality gates
- **Session management** - Track learnings and outcomes

---

## Installation

### Local Development

Load the plugin during development:

```bash
claude --plugin-dir ./dewey
```

### From Marketplace (Future)

Once published:

```bash
/plugin install dewey
```

---

## Quick Start

### 1. Analyze Your Context

```
/dewey:analyze context/
```

This scans your context directory and provides:
- Token usage statistics
- Distribution analysis
- Identified issues (large files, duplicates, etc.)
- Specific commands to run
- Estimated impact

### 2. Split Large Files

```
/dewey:split IMPLEMENTATION_PLAN.md
```

Uses Claude (in your current session) to:
- Analyze content semantically
- Create scannable main file
- Organize details into topical references
- Maintain all information with clear navigation

### 3. Preview Before Splitting

```
/dewey:split IMPLEMENTATION_PLAN.md --dry-run
```

Shows what would be created without writing files.

---

## Plugin Structure

```
dewey/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── commands/                  # User-invoked commands
│   ├── analyze.md            # /dewey:analyze
│   ├── split.md              # /dewey:split
│   ├── report.md             # /dewey:report (planned)
│   ├── check.md              # /dewey:check (planned)
│   └── optimize.md           # /dewey:optimize (planned)
├── src/dewey/                 # Python helper modules
│   ├── core/
│   │   ├── measurement/      # Token counting, frequency tracking
│   │   ├── compaction/       # File splitting, deduplication
│   │   ├── memory/           # Session management
│   │   └── analytics/        # Dashboard generation
│   └── skills/               # Skill helper functions
│       └── analyze_skill.py
├── scripts/                   # CLI utilities
│   ├── analyze-usage.py      # Token inventory
│   └── identify-large-files.py
├── tests/                     # Comprehensive test suite
└── templates/                 # Configuration templates
```

---

## Design Philosophy

### Skills-First Architecture

All features are exposed as **commands** that you invoke:
- `/dewey:analyze` - User calls explicitly
- `/dewey:split` - User calls explicitly

Commands use:
1. **Python helpers** for file operations and data collection
2. **Claude (your session)** for intelligent analysis and decisions
3. **No additional API keys** - uses existing Claude Code session
4. **Zero additional cost** - included in your Claude usage

### Key Principles

- **Measure before optimizing** - Always analyze first
- **Transparent recommendations** - Show impact before changes
- **Semantic understanding** - LLM-based, not mechanical
- **Best practices** - Follows Anthropic's context guidelines
- **User control** - Commands require explicit invocation

---

## Commands Reference

### `/dewey:analyze [directory]`

Analyze context usage and generate recommendations.

**Arguments**:
- `directory` - Directory to analyze (default: current)
- `--detailed` - Include file-by-file breakdown
- `--baseline` - Save as baseline for comparisons
- `--threshold N` - Custom large file threshold

**Example**:
```
/dewey:analyze context/ --baseline
```

### `/dewey:split file.md`

Intelligently split large files.

**Arguments**:
- `file.md` - File to split
- `--dry-run` - Preview without writing
- `--max-lines N` - Custom threshold (default: 500)
- `--target-lines N` - Target main size (default: 150)

**Example**:
```
/dewey:split IMPLEMENTATION_PLAN.md --dry-run
```

### `/dewey:report` (Coming Soon)

Generate dashboard reports.

### `/dewey:check` (Coming Soon)

Run quality checks.

### `/dewey:optimize` (Coming Soon)

Full optimization suite.

---

## Development

### Prerequisites

- Python 3.9+
- Claude Code 1.0.33+

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/dewey.git
cd dewey

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Test coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### Testing the Plugin

Load your development version:

```bash
claude --plugin-dir ./dewey
```

Then use the commands:
```
/dewey:analyze .
/dewey:split large-file.md
```

---

## Project Status

### Phase 0: Foundation ✅ Complete

- [x] Project structure
- [x] Core dependencies
- [x] Token inventory script
- [x] Session tracking templates
- [x] Baseline measurements
- [x] Intelligent file splitting (skill-based)
- [x] Plugin restructuring (aligned with official system)

### Phase 1: Core Commands 🔄 In Progress

- [x] `/dewey:split` command
- [x] `/dewey:analyze` command (implementation done, testing in progress)
- [ ] `/dewey:report` command
- [ ] `/dewey:check` command
- [ ] Enhanced token counter
- [ ] Frequency tracker

### Phase 2-3: Optimization & Automation 📋 Planned

See [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) for full roadmap.

---

## Documentation

- [Implementation Plan](../IMPLEMENTATION_PLAN.md) - Full development roadmap
- [Plugin System Alignment](.dewey/reports/plugin-system-alignment.md) - Official Claude Code plugin specs
- [Skill-Based Splitting](SKILL_BASED_SPLITTING.md) - File splitting approach
- [Plan v2 Changes](PLAN_V2_CHANGES.md) - Evolution of the implementation plan

---

## Contributing

Dewey is in early development (v0.0.1). We welcome:
- Bug reports
- Feature suggestions
- Code contributions
- Documentation improvements

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines (coming soon).

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Built for [Claude Code](https://code.claude.com/)
- Follows [Anthropic's context best practices](https://code.claude.com/docs/)
- Inspired by the need for intelligent context management

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/dewey/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/dewey/discussions)
- **Documentation**: [Official Docs](https://github.com/yourusername/dewey/docs)

---

**Status**: Early development - use with caution and always backup your files!

**Version**: 0.0.1
**Last Updated**: 2026-02-10
