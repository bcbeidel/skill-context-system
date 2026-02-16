# Dewey -- Knowledge Base Management for Claude Code

Dewey is a Claude Code plugin that helps you build, curate, and maintain structured knowledge bases. It implements a specification for role-specific knowledge bases that serve both AI agents and humans.

## Why

AI agents produce better outputs when they have access to curated, relevant knowledge. But knowledge bases serve two consumers: the **agent** (who needs structured, token-efficient context) and the **human** (who needs readable, navigable content). Dewey defines a standard for what a well-formed knowledge base looks like and provides skills to create and maintain one.

Dewey currently runs as a Claude Code plugin. The knowledge base output format is designed to be provider-agnostic -- cross-provider support (Codex, Gemini CLI, Cursor, etc.) is a future goal.

## Skills

| Skill | Purpose |
|-------|---------|
| `/dewey:curate` | Single entry point for all knowledge-base content operations: discover domains, scaffold structure, add/update topics, ingest URLs, manage proposals and curation plan |
| `/dewey:health` | Validate quality, check freshness, analyze coverage gaps, generate reports |
| `/dewey:report-issue` | Submit bug reports, feature ideas, or feedback to the Dewey GitHub repo |

### `/dewey:curate`

The curate skill uses free-text intake -- describe what you want and Claude routes to the right workflow. No subcommands needed.

**Workflows:**

- **discover** -- Guided conversation to identify what knowledge domains matter for a role, then scaffold the structure
- **setup** -- Bootstrap a new knowledge base with directory structure, AGENTS.md, and templates
- **add** -- Research a topic, draft working-knowledge and reference files, update all indexes (also supports updating existing topics)
- **propose** -- Submit a topic proposal for review before committing
- **promote** -- Move a validated proposal into a domain area
- **ingest** -- Ingest an external URL, evaluate source quality, then propose new content or update existing topics
- **plan** -- Create or update a curation plan that tracks coverage goals

```
# Just tell it what you want:
/dewey:curate I want to start a knowledge base for platform engineering
/dewey:curate add a topic about dependency injection in python-foundations
/dewey:curate ingest https://example.com/article-about-observability
/dewey:curate what's in my curation plan?
```

### `/dewey:health`

Three-tier health model for knowledge base validation:

**Tier 1 -- Deterministic (Python):** 18 validators in `validators.py` plus 6 cross-file validators in `cross_validators.py`. Checks frontmatter, section ordering, cross-references, size bounds, coverage gaps, freshness, source URLs, readability (Flesch-Kincaid), duplicate content, naming conventions, and more. Auto-fix available for common issues.

**Tier 2 -- LLM-Assisted (Claude):** Pre-screener with 9 triggers in `tier2_triggers.py` flags files needing deeper review. Claude evaluates: source drift, depth accuracy, why-quality, in-practice concreteness, source primacy, citation quality, source authority, provenance completeness, recommendation coverage.

**Tier 3 -- Human Judgment:** Surfaces decisions requiring human input: relevance questions, scope decisions, pending proposals, conflict resolution.

```
/dewey:health check my knowledge base
/dewey:health what's gone stale?
/dewey:health run a full audit
```

## Knowledge Base Structure

A Dewey-conformant knowledge base looks like:

```
project-root/
  AGENTS.md                          # Role persona + topic manifest
  .claude/rules/dewey-kb.md           # KB instructions + domain area index
  docs/
    <domain-area>/
      overview.md                    # Area orientation (depth: overview)
      <topic>.md                     # Working knowledge (depth: working)
      <topic>.ref.md                 # Expert reference (depth: reference)
    _proposals/                      # Staged additions pending review
  .dewey/
    health/                          # Quality scores and tier 2 reports
    history/                         # Health check snapshots over time
    utilization/                     # Reference tracking log
```

Every knowledge file carries YAML frontmatter: `sources`, `last_validated`, `relevance`, and `depth`.

## Design Principles

Twelve principles grounded in agent context research (Anthropic, OpenAI) and cognitive science (Sweller, Vygotsky, Paivio, Bjork, Pirolli, Kalyuga, Dunlosky).

### From Agent Context Research

1. **Source Primacy** -- The knowledge base is a curated guide, not a replacement for primary sources. Every entry points to one. When an agent or human needs to go deeper, the path is always clear.
2. **Dual Audience** -- Every entry serves the agent (structured, token-efficient context) and the human (readable, navigable content). When these conflict, favor human readability -- agents are more adaptable readers.
3. **Three-Dimensional Quality** -- Content quality measured across relevance, accuracy/freshness, and structural fitness simultaneously.
4. **Collaborative Curation** -- Either the human or an agent can propose additions, but all content passes through validation. The human brings domain judgment. The agent brings systematic coverage. Neither is sufficient alone.
5. **Provenance & Traceability** -- Every piece of knowledge carries metadata about where it came from, when it was last validated, and why it's in the knowledge base.
6. **Domain-Shaped Organization** -- Organized around the domain's natural structure, not file types or technical categories. The taxonomy should feel intuitive to a practitioner.
7. **Right-Sized Scope** -- Contains what's needed to be effective in the role, and no more. The curation act is as much about what you exclude as what you include.
8. **Empirical Feedback** -- Observable signals about knowledge base health: coverage gaps, stale entries, unused content. Proxy metrics inform curation decisions.
9. **Progressive Disclosure** -- Layered access so agents can discover what's available without loading everything. Metadata -> summaries -> full content -> deep references.

### From Cognitive Science Research

10. **Explain the Why** -- Causal explanations produce better comprehension and retention than stating facts alone. Every entry explains not just what to do, but why.
11. **Concrete Before Abstract** -- Lead with examples and worked scenarios, then build toward the abstraction. Concrete concepts create stronger memory traces.
12. **Multiple Representations** -- Important concepts should exist at multiple levels of depth (overview, working knowledge, reference). Material that helps novices can hinder experts and vice versa -- label each level clearly so readers self-select.

See the [design principles reference](dewey/skills/health/references/design-principles.md) for detailed rationale and research sources.

## Tech Stack

- Python 3.9+ (stdlib only -- zero dependencies)
- Markdown with YAML frontmatter
- Claude Code skills framework

## Development

```bash
git clone https://github.com/bcbeidel/dewey.git
cd dewey

# Symlink the plugin for local development
ln -s "$(pwd)/dewey" ~/.claude/plugins/dewey

# Run tests
python3 -m pytest tests/ -v
```

## Project Structure

```
dewey/
  .claude-plugin/plugin.json         # Plugin manifest
  skills/
    curate/                           # All knowledge-base content operations
      SKILL.md
      scripts/create_topic.py, propose.py, promote.py, scaffold.py, templates.py, config.py
      workflows/curate-discover.md, curate-setup.md, curate-add.md, curate-propose.md,
               curate-promote.md, curate-ingest.md, curate-plan.md
      references/knowledge-base-spec-summary.md, source-evaluation.md
    health/                           # Quality validation
      SKILL.md
      scripts/validators.py, cross_validators.py, auto_fix.py, check_knowledge_base.py,
              tier2_triggers.py, history.py, utilization.py, log_access.py,
              hook_log_access.py
      workflows/health-check.md, health-audit.md, health-review.md,
               health-coverage.md, health-freshness.md
      references/validation-rules.md, quality-dimensions.md, design-principles.md
    report-issue/                       # GitHub issue submission
      SKILL.md
      workflows/report-issue-submit.md
tests/                                # Test suite (536 tests)
```

## Status

| Feature | Status |
|---------|--------|
| Knowledge base scaffolding | Complete |
| Domain discovery | Complete |
| Content lifecycle (add, propose, promote) | Complete |
| URL ingestion with source evaluation | Complete |
| Curation plan management | Complete |
| Tier 1 deterministic health checks | Complete (18 validators + 6 cross-validators) |
| Tier 2 LLM-assisted health assessments | Complete (9 triggers + audit workflow) |
| Readability and duplicate content detection | Complete |
| Auto-fix for common issues | Complete |
| Health history and baselines | Complete |
| Utilization tracking | Infrastructure complete, auto-capture pending ([#3](https://github.com/bcbeidel/dewey/issues/3)) |
| Tier 3 human decision queue | Designed, not yet tested ([#2](https://github.com/bcbeidel/dewey/issues/2)) |
| CI/CD eval pipeline | Planned ([#4](https://github.com/bcbeidel/dewey/issues/4)) |
| Cross-provider support | Planned — [MCP server](https://github.com/bcbeidel/dewey/issues/1), [Cursor](https://github.com/bcbeidel/dewey/issues/5), [Copilot/Codex](https://github.com/bcbeidel/dewey/issues/6), [Gemini CLI](https://github.com/bcbeidel/dewey/issues/7), [Windsurf](https://github.com/bcbeidel/dewey/issues/8) |
| Research: design principle validation | Planned — [context effectiveness](https://github.com/bcbeidel/dewey/issues/9), [cognitive load](https://github.com/bcbeidel/dewey/issues/10), [information foraging](https://github.com/bcbeidel/dewey/issues/11), [source provenance](https://github.com/bcbeidel/dewey/issues/12), [multi-agent sharing](https://github.com/bcbeidel/dewey/issues/13) |

## Documentation

- [Design Principles](dewey/skills/health/references/design-principles.md) -- The twelve principles guiding knowledge base content
- [Knowledge Base Spec Summary](dewey/skills/curate/references/knowledge-base-spec-summary.md) -- Structural specification reference
- [CHANGELOG](CHANGELOG.md) -- Release history
