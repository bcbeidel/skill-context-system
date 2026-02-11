# Context System - Dewey Plugin Development

This repository contains **Dewey**, a context optimization plugin for Claude Code.

## What is Dewey?

Dewey is a Claude Code plugin that helps you intelligently manage, analyze, and optimize your context files using LLM-based analysis. It uses your existing Claude Code session - no additional API keys or costs required.

## Quick Start

### Load the Plugin

```bash
cd /path/to/context-system
claude --plugin-dir ./dewey
```

### Use Commands

```
/dewey:analyze .
/dewey:split large-file.md
```

## Documentation

- **[Plugin README](dewey/README.md)** - Complete plugin documentation
- **[Implementation Plan](IMPLEMENTATION_PLAN.md)** - Development roadmap

## Plugin Structure

```
dewey/
├── .claude-plugin/plugin.json    # Plugin manifest
├── commands/                      # User-invoked commands
├── src/dewey/                     # Python implementation
├── tests/                         # Test suite
└── README.md                      # Plugin documentation
```

## Development Status

**Version**: 0.0.1 (Early Development)

- ✅ Phase 0: Foundation complete
- 🔄 Phase 1: Core commands in progress
- 📋 Phase 2-3: Planned

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for details.

## Project Files

- `dewey/` - Plugin implementation
- `IMPLEMENTATION_PLAN.md` - Development roadmap v2.0
- `README.md` - This file

---

**For full plugin documentation, see [dewey/README.md](dewey/README.md)**
