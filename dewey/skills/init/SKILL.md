---
name: init
description: Bootstrap a new knowledge base — evaluates the repo, asks what you're trying to accomplish, and scaffolds a structure around your goals
---

<essential_principles>
## What This Skill Does

Creates a new knowledge base conforming to the KB specification. Evaluates the existing repo, asks the user what they're trying to accomplish, proposes domain areas that match their mental model, and scaffolds the directory structure with AGENTS.md, CLAUDE.md, index.md, and domain area overviews.

## Core Workflow

1. **Evaluate the repo** -- Look at what already exists (README, files, git history)
2. **Ask what they're trying to accomplish** -- Understand goals, not just role titles
3. **Propose persona and domain areas** -- Mirror how they think about the work
4. **Scaffold** -- Create directories and template files
5. **Report and suggest next steps** -- Point to `/dewey:curate add`

## Design Philosophy

- **Goal-driven** -- Start from what the user wants to accomplish, not a role label
- **Safe by default** -- Merges KB sections into existing files using markers; never destroys user content
- **Minimal viable KB** -- Scaffolds the structure, not the content
- **Templates guide quality** -- Every generated file follows the content format spec

## Key Variables

- `$ARGUMENTS` -- Arguments passed to this skill (optional context about goals)
- `${CLAUDE_PLUGIN_ROOT}` -- Root directory of the Dewey plugin
</essential_principles>

<intake>
Setting up a new knowledge base.

Route all invocations to `workflows/init.md`. If `$ARGUMENTS` provides context about what the user is trying to accomplish, pass it through so the workflow can skip the question.
</intake>

<workflows_index>
## Available Workflows

All workflows in `workflows/`:

| Workflow | Purpose |
|----------|---------|
| init.md | Evaluate repo, understand goals, propose domains, scaffold KB |
</workflows_index>

<references_index>
## Domain Knowledge

All references in `references/`:

| Reference | Content |
|-----------|---------|
| kb-spec-summary.md | Summary of the KB specification principles and structure |
</references_index>

<scripts_integration>
## Python Helper Scripts

Located in `scripts/`:

**scaffold.py** -- Main scaffolding script
- Creates directory structure (docs/, _proposals/, .dewey/)
- Generates AGENTS.md, CLAUDE.md, index.md, overview.md from templates
- `merge_managed_section` -- safely merges KB content into existing files using markers
- Safe: merges into existing files without destroying user content
- Returns summary of what was created (includes curate plan with `--starter-topics`)

**templates.py** -- Content template rendering
- Renders all KB file types (AGENTS.md, CLAUDE.md, index.md, overview.md, topic.md, topic.ref.md, proposal.md)
- `render_claude_md_section` / `render_agents_md_section` -- managed content without markers
- `render_curate_plan` -- actionable starter topic commands for post-scaffold guidance
- Uses `MARKER_BEGIN` / `MARKER_END` constants for managed-section boundaries
- Includes correct frontmatter with today's date
- Follows the content format spec

**Usage in workflows:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/scaffold.py --target <dir> --role "Persona description" [--areas "Area One,Area Two"] [--starter-topics '{"Area One": ["Topic A", "Topic B"]}']
```
</scripts_integration>

<success_criteria>
Init is successful when:

- User's goals understood before scaffolding
- Domain areas proposed and confirmed by user
- Directory structure matches the KB spec
- AGENTS.md exists with persona and manifest structure
- CLAUDE.md exists with KB discovery pointers (for Claude Code)
- docs/index.md exists with TOC structure
- docs/_proposals/ directory exists
- .dewey/ directories exist (health, history, utilization)
- Existing CLAUDE.md and AGENTS.md have KB content merged (not overwritten)
- All generated files have valid frontmatter
</success_criteria>
