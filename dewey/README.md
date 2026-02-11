# Dewey - Universal Context Optimization Plugin

**"Dewey"** (like the Dewey Decimal System) - A universal context librarian that organizes and optimizes LLM context across providers.

## Overview

Dewey is a universal context optimization plugin compatible with major LLM CLI providers:
- **Claude Code** (Anthropic)
- **OpenAI Codex**
- **Google Gemini**

### Key Features

- 📊 **Signal-to-Noise Measurement** - Track which context is actually helpful
- 📦 **Compaction Strategies** - Prevent context accumulation through file organization
- 🧠 **Mid-Term Memory Tier** - Staging area for learnings before permanent promotion
- 🔄 **Dual CI/CD Feedback Loops**:
  - **Loop 1**: Self-improving (Dewey's own repository)
  - **Loop 2**: Target repository optimization (once installed)

### Philosophy

- **Transparent**: All changes are recommendations visible in PRs, not automated commits
- **Data-Driven**: Measure first, optimize based on metrics
- **Universal**: Works across LLM providers with provider-specific adapters
- **Local**: No servers, no external dependencies - just scripts, data, and visible recommendations

## Installation

### Via Provider Extension Systems (Recommended)

```bash
# Claude Code
claude code install dewey

# OpenAI Codex
codex extensions add dewey

# Google Gemini
gemini plugins install dewey
```

### Via pip

```bash
pip install dewey-context-optimizer

# Register with your provider
cd /path/to/your/repo
dewey register  # Auto-detects provider
```

## Quick Start

### 1. Initialize in Your Repository

```bash
cd /path/to/your/repo
dewey init
```

This creates:
- `.dewey/config.yml` - Configuration
- `.github/workflows/dewey-checks.yml` - CI/CD Loop 2 (weekly optimization)
- Pre-commit hooks for quality gates

### 2. Run Initial Check

```bash
dewey check
```

This shows:
- Context utilization
- Token efficiency
- File size issues
- Duplicate content
- Dead links

### 3. Generate Optimization Report

```bash
dewey report
```

This analyzes your context and suggests specific improvements:
- Files to split (>500 lines)
- Duplicates to consolidate
- Old content to archive
- Load optimization opportunities

### 4. Apply Fixes

```bash
# Review and apply specific recommendations
dewey fix split-large-files
dewey fix archive-old-content

# Or generate a PR with all recommendations
dewey pr
```

## Slash Commands

When installed as an extension, Dewey provides slash commands in your CLI:

| Command | Description |
|---------|-------------|
| `/dewey init` | Initialize Dewey in repository |
| `/dewey check` | Run KPI evaluation, show metrics |
| `/dewey report` | Generate optimization recommendations |
| `/dewey fix [issue]` | Apply specific recommendation |
| `/dewey status` | Show current context health |
| `/dewey analyze [file]` | Analyze specific file |
| `/dewey session start` | Start session tracking |
| `/dewey session end` | End session, capture learnings |
| `/dewey pr` | Generate optimization PR |
| `/dewey help` | Show available commands |

## Architecture

### Three-Tier Memory System

- **Short-term** (Working Memory): Current session, in-context, ephemeral
- **Mid-term** (Episodic Memory): 7 days, session files, staged learnings
- **Long-term** (Semantic Memory): Permanent, context/ files, validated knowledge

### Provider Adapters

Dewey uses a provider adapter pattern to work across different LLM CLIs:

```python
from dewey.providers import detect_provider

provider = detect_provider("/path/to/repo")
# Returns: "claude", "codex", "gemini", or "unknown"
```

Each adapter handles provider-specific conventions:
- Configuration file locations
- Context directory structure
- Link formats (wikilinks vs markdown)
- File size limits

### Dual CI/CD Loops

**Loop 1: Dewey Self-Improvement**
- Runs on Dewey's own repository
- Detects patterns across usage in multiple repos
- Creates PRs to improve Dewey itself
- Example: "Add YAML frontmatter support" (detected in 15% of repos)

**Loop 2: Target Repository Optimization**
- Runs weekly on your repository
- Evaluates context quality metrics
- Creates PR with specific optimization suggestions
- You review and merge (or close) the PR

Both loops are **transparent** - they create pull requests for human review, never auto-commit.

## Key Metrics

Dewey tracks these metrics to guide optimization:

- **Context Utilization**: % of available tokens used (target: 30-50%)
- **Token Efficiency**: Useful output / total tokens (target: >0.70)
- **Information Density**: Actionable tokens / total tokens (target: >0.70)
- **Precision@5**: Relevant files in top 5 loaded (target: >0.70)
- **Citation Rate**: Files referenced / files loaded (target: >70%)

## Development Status

**Current Version**: 0.1.0 (Alpha)

This is an active development project. Not all features are implemented yet.

See `IMPLEMENTATION_PLAN.md` for the roadmap.

## Contributing

Contributions welcome! See the implementation plan for tasks that need work.

## License

MIT

## Learn More

- [User Guide](docs/USER_GUIDE.md) - Detailed usage instructions
- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [Provider Guide](docs/PROVIDERS.md) - Provider-specific differences
