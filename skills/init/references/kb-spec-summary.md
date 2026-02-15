# Knowledge Base Specification Summary

Reference for the full spec: `docs/plans/2026-02-14-knowledge-base-spec-design.md`

## Core Principles

1. **Source Primacy** -- Curate and point to primary sources, don't replace them
2. **Dual Audience** -- Serve both agent (efficient) and human (learnable)
3. **Three-Dimensional Quality** -- Relevance, accuracy/freshness, structural fitness
4. **Collaborative Curation** -- Human judgment + agent coverage, both validated
5. **Provenance & Traceability** -- Every entry carries source and validation date
6. **Domain-Shaped Organization** -- Structure mirrors the practitioner's mental model
7. **Right-Sized Scope** -- Include what's needed, exclude what isn't
8. **Empirical Feedback** -- Observable signals guide curation decisions
9. **Progressive Disclosure** -- Layered: metadata -> summary -> full -> deep
10. **Explain the Why** -- Causal reasoning, not just facts
11. **Concrete Before Abstract** -- Examples first, then generalize
12. **Multiple Representations** -- Important concepts at multiple depths

## Directory Structure

```
project-root/
├── AGENTS.md                       # Persona + manifest (<100 lines)
├── knowledge/
│   ├── index.md                    # Human TOC
│   ├── <domain-area>/
│   │   ├── overview.md             # Orientation (depth: overview)
│   │   ├── <topic>.md              # Working knowledge (depth: working)
│   │   └── <topic>.ref.md          # Expert reference (depth: reference)
│   └── _proposals/                 # Staged additions pending validation
└── .dewey/
    ├── health/                     # Quality scores per entry
    ├── history/                    # Change log, baselines
    └── utilization/                # Reference tracking
```

## Content Format

All knowledge files carry YAML frontmatter:

```yaml
---
sources:
  - url: https://example.com/primary-source
    title: "Source Title"
last_validated: 2026-02-10
relevance: "One line: who does this help and when"
depth: working  # overview | working | reference
---
```

- **sources** -- Primary source URLs (enforces source primacy)
- **last_validated** -- Date of last verification (enables freshness checks)
- **relevance** -- Information scent for agents and humans scanning the manifest
- **depth** -- Position in the progressive disclosure chain

## Content Depths

| Depth | File | Purpose |
|-------|------|---------|
| overview | overview.md | Orientation: what, why, how it connects |
| working | topic.md | Working knowledge with inline sources |
| reference | topic.ref.md | Expert reference: terse, scannable |

## AGENTS.md Constraints

- Under 100 lines
- Defines role persona and behavioral expectations
- Manifest: names and one-line descriptions only (progressive disclosure Level 1)
- Two entry points: AGENTS.md for agents, index.md for humans

## Key Rules

- Domain areas named for how a practitioner thinks (not technical categories)
- Every .md file includes frontmatter with sources, last_validated, relevance, depth
- `_proposals/` is the staging area for collaborative curation
- `.dewey/` holds tooling metadata invisible to KB consumers
- Never overwrite existing files during scaffolding
