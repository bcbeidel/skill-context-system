---
name: init
description: Bootstrap a new knowledge base with the standard directory structure, AGENTS.md, and content templates
---

<essential_principles>
## What This Skill Does

Creates a new knowledge base conforming to the KB specification. Scaffolds the directory structure, generates AGENTS.md (persona + manifest), index.md (human TOC), and optionally pre-creates domain areas based on a role description.

## Core Workflow

1. **Determine target directory** -- Where the KB will live (default: current directory)
2. **Get role name** -- What role this KB serves
3. **Python scaffolds structure** -- Creates directories and template files
4. **Claude proposes domain areas** (if from-role) -- Suggests initial organization based on the role
5. **Reports what was created** -- Summary of files and directories

## Design Philosophy

- **Safe by default** -- Never overwrites existing files
- **Minimal viable KB** -- Scaffolds the structure, not the content
- **Templates guide quality** -- Every generated file follows the content format spec
- **Human refines** -- The scaffold is a starting point, not a finished product

## Key Variables

- `$ARGUMENTS` -- Arguments passed to this skill (target directory and flags)
- `${CLAUDE_PLUGIN_ROOT}` -- Root directory of the Dewey plugin
</essential_principles>

<intake>
Setting up a new knowledge base.

**Default behavior:** Scaffold an empty KB structure with templates.
**From role:** Use `--role "Role Name"` to have Claude propose initial domain areas.

If no `$ARGUMENTS` provided, ask for the role name.
</intake>

<routing>
## Argument-Based Routing

Parse `$ARGUMENTS`:

- Contains `--role` -> Route to `workflows/init-from-role.md`
- Otherwise -> Route to `workflows/init-empty.md`

Both workflows use the same Python scaffold script. The from-role workflow adds a step where Claude proposes domain areas before scaffolding.
</routing>

<workflows_index>
## Available Workflows

All workflows in `workflows/`:

| Workflow | Purpose |
|----------|---------|
| init-empty.md | Scaffold empty KB structure with templates |
| init-from-role.md | Propose domain areas from role description, then scaffold |
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
- Creates directory structure (knowledge/, _proposals/, .dewey/)
- Generates AGENTS.md, index.md, overview.md from templates
- Safe: never overwrites existing files
- Returns summary of what was created

**templates.py** -- Content template rendering
- Renders all KB file types (AGENTS.md, index.md, overview.md, topic.md, topic.ref.md, proposal.md)
- Includes correct frontmatter with today's date
- Follows the content format spec

**Usage in workflows:**
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/scaffold.py --target <dir> --role "Role Name" [--areas "Area One,Area Two"]
```
</scripts_integration>

<success_criteria>
Init is successful when:

- Directory structure matches the KB spec
- AGENTS.md exists with role name and manifest structure
- knowledge/index.md exists with TOC structure
- knowledge/_proposals/ directory exists
- .dewey/ directories exist (health, history, utilization)
- No existing files were overwritten
- All generated files have valid frontmatter
</success_criteria>
