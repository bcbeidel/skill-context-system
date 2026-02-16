# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test

```bash
python3 -m pytest tests/ -v
python3 -m pytest tests/ -v -k "not test_scaffold_sandbox"  # skip slow scaffold test
```

No build step. No dependencies beyond Python 3.9+ stdlib.

## Architecture

Dewey is a Claude Code plugin that helps build, curate, and maintain structured knowledge bases. The knowledge base output format is designed to be provider-agnostic, but Dewey currently only runs as a Claude Code plugin. Cross-provider support is a future goal.

### Plugin Structure

```
dewey/
  .claude-plugin/plugin.json       # Plugin manifest
  skills/
    <skill>/
      SKILL.md                     # Entry point: description, routing, intake logic
      workflows/                   # Multi-step processes Claude follows
      scripts/                     # Python helpers (stdlib-only, data collection)
      references/                  # Domain knowledge for Claude to consult
```

**Division of labor:** Python handles data collection, file operations, and deterministic validation. Claude handles analysis, judgment, and user interaction.

### Skills

| Skill | Purpose |
|-------|---------|
| `curate` | Single entry point for all knowledge-base content operations: discover domains, scaffold structure, add/update topics, ingest URLs, manage proposals and curation plan |
| `health` | Validate quality, check freshness, analyze coverage gaps, generate reports |
| `report-issue` | Submit bug reports, feature ideas, or general feedback to the Dewey GitHub repo via `gh` |

### Three-Tier Health Model

1. **Tier 1 -- Deterministic (Python)** -- Fast automated checks run by `check_knowledge_base.py`. 18 per-file validators in `validators.py` (frontmatter, sections, size bounds, readability, sources, freshness, and more) plus 6 cross-file validators in `cross_validators.py` (manifest sync, curation plan sync, proposal integrity, link graph, duplicate detection, naming conventions). Auto-fix available via `auto_fix.py`. CI-friendly. No LLM required.
2. **Tier 2 -- LLM-Assisted (Claude)** -- Pre-screener in `tier2_triggers.py` flags files with context data. Claude evaluates flagged items: source drift, depth accuracy, why-quality, in-practice concreteness, source primacy.
3. **Tier 3 -- Human Judgment** -- Surfaces decisions requiring human input: relevance questions, scope decisions, pending proposals, conflict resolution.

### Utilization Tracking

A Claude Code `PostToolUse` hook on the `Read` tool automatically logs when an agent reads a knowledge-base topic file. Data feeds into `generate_recommendations()` which surfaces stale-high-use, expand-depth, low-utilization, and never-referenced files. Scaffold auto-generates the hook config. Claude Code-specific (other agents don't get auto-tracking).

### Design Principles

Twelve principles grounded in agent context research and cognitive science guide knowledge base content. See @dewey/skills/health/references/design-principles.md for the full list.

## Conventions

For the canonical script pattern, see `validators.py`. For the canonical test pattern, see `tests/skills/health/test_validators.py`. Python and test conventions are in `.claude/rules/`.

### Issue Format

All validators and triggers return `list[dict]` (always a list, even if empty):

```python
# Tier 1 validators
{"file": str, "message": str, "severity": "fail" | "warn"}

# Tier 2 triggers
{"file": str, "trigger": str, "reason": str, "context": dict}
```

### Content Depths

| Depth | Purpose | Size (lines) |
|-------|---------|-------------|
| `overview` | Area orientation: what, why, how it connects | 5-150 |
| `working` | Actionable guidance with examples | 10-400 |
| `reference` | Terse, scannable lookup | 3-150 |

## Gotchas

- IMPORTANT: Python 3.9 runtime -- `str | None` works in annotations (with `from __future__ import annotations`) but NOT in `isinstance()`, default values, or other runtime expressions. Use `Optional[str]` there.
- Scripts must be runnable standalone (`if __name__ == "__main__"` with argparse) -- do not create scripts that only work as imports.
- Cross-skill imports require the `sys.path.insert(0, ...)` pattern with idempotency check -- do not use relative imports or package `__init__.py`.
- Test temp dirs must use `self.tmpdir` from setUp/tearDown -- never write to the actual project directory.
- Validators and triggers always return `list[dict]`, never a single dict, raw string, or None.
- Hook scripts must never fail -- wrap in `except Exception` and always exit 0.

## Known Limitations

- Tier 3 human decision queue: designed in `health-review.md` but not yet tested ([#2](https://github.com/bcbeidel/dewey/issues/2))
- Utilization auto-capture: hook exists but auto-capture not yet wired up ([#3](https://github.com/bcbeidel/dewey/issues/3))
- Cross-provider support: Knowledge-base output format is provider-agnostic by design, but Dewey currently only runs as a Claude Code plugin ([#1](https://github.com/bcbeidel/dewey/issues/1))
