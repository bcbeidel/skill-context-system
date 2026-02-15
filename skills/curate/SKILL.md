---
name: curate
description: Add, propose, promote, and ingest content in a knowledge base following the KB specification
---

<essential_principles>
## What This Skill Does

Manages the content lifecycle for a knowledge base. Handles adding topics from templates, proposing additions for review, promoting validated proposals into domain areas, and ingesting content from external sources.

## Core Workflow

1. **Add topics** -- Create working-knowledge and reference files from templates in a domain area
2. **Propose additions** -- Submit topics for review before committing them to the KB
3. **Promote proposals** -- Move validated proposals from _proposals/ into their target domain area
4. **Ingest from URL** -- Create a proposal pre-filled with an external source for manual distillation

## Design Philosophy

- **Collaborative curation** -- Both humans and agents can propose, review, and add content
- **Source primacy** -- Every topic should trace back to authoritative sources
- **Templates guide quality** -- Consistent structure ensures every topic covers what matters
- **Proposals before promotion** -- The review step catches low-quality or redundant content early

## Key Variables

- `$ARGUMENTS` -- Arguments passed to this skill (workflow name and parameters)
- `${CLAUDE_PLUGIN_ROOT}` -- Root directory of the Dewey plugin
</essential_principles>

<intake>
Managing content in a knowledge base.

**Available actions:**
- `add` -- Create a new topic in a domain area from the template
- `propose` -- Submit a topic proposal for review
- `promote` -- Move a validated proposal into a domain area
- `ingest` -- Create a proposal from an external URL (stub)

Parse the action from `$ARGUMENTS`. If no arguments provided, present the options and ask the user which action to take.
</intake>

<routing>
## Argument-Based Routing

Parse `$ARGUMENTS`:

- Starts with `add` or contains `--add` -> Route to `workflows/curate-add.md`
- Starts with `propose` or contains `--propose` -> Route to `workflows/curate-propose.md`
- Starts with `promote` or contains `--promote` -> Route to `workflows/curate-promote.md`
- Starts with `ingest` or contains `--ingest` -> Route to `workflows/curate-ingest.md`
- No arguments -> Present interactive menu and route based on selection
</routing>

<workflows_index>
## Available Workflows

All workflows in `workflows/`:

| Workflow | Purpose |
|----------|---------|
| curate-add.md | Create a new topic in a domain area from template |
| curate-propose.md | Submit a topic proposal for review |
| curate-promote.md | Promote a validated proposal into a domain area |
| curate-ingest.md | Create a proposal from an external URL (stub) |
</workflows_index>

<scripts_integration>
## Python Helper Scripts

Located in `scripts/`:

**create_topic.py** -- Create topic files in a domain area
- Creates working-knowledge (.md) and reference (.ref.md) files
- Uses templates from the init skill
- Safe: never overwrites existing files

**Usage:**
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/curate/scripts/create_topic.py --kb-root <root> --area <area> --topic "<name>" --relevance "<relevance>"
```

**propose.py** -- Create a proposal file
- Creates a proposal in knowledge/_proposals/
- Includes frontmatter with status, proposed_by, rationale
- Safe: never overwrites existing proposals

**Usage:**
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/curate/scripts/propose.py --kb-root <root> --topic "<name>" --relevance "<relevance>" --proposed-by "<who>" --rationale "<why>"
```

**promote.py** -- Move a proposal into a domain area
- Strips proposal-specific frontmatter (status, proposed_by, rationale)
- Copies cleaned content to target area
- Deletes the original proposal file

**Usage:**
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/curate/scripts/promote.py --kb-root <root> --proposal "<slug>" --target-area "<area>"
```
</scripts_integration>

<success_criteria>
Curation is successful when:

- Content follows the topic template structure
- Sources are referenced in frontmatter
- Frontmatter is complete with title, relevance, and date
- Template sections are filled in (Why This Matters, In Practice, Key Guidance, Watch Out For, Go Deeper)
- AGENTS.md manifest reflects the current KB contents
- index.md is updated to include new topics
</success_criteria>
