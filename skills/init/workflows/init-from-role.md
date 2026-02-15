<objective>
Propose initial domain areas based on a role description, then scaffold the knowledge base.
</objective>

<required_reading>
Load `references/kb-spec-summary.md` for context on the KB specification.
</required_reading>

<process>
## Step 1: Determine target directory and role

Parse `$ARGUMENTS` for `--role "Role Name"` and optional target directory.

## Step 2: Propose domain areas

Based on the role name, propose 3-5 domain areas that reflect how a practitioner in this role thinks about their work. Present to the user:

"For a **<role name>**, I'd suggest organizing the knowledge base around these domain areas:

1. **Area Name** -- brief description of what this covers
2. **Area Name** -- brief description
3. **Area Name** -- brief description

These should map to the major responsibility areas of the role. Would you like to adjust these before I create the structure?"

**Key principle:** Domain-Shaped Organization. Use the practitioner's mental model, not technical categories.

## Step 3: Run scaffold script with areas

After user confirms or adjusts:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/scaffold.py --target <directory> --role "<role_name>" --areas "<area1>,<area2>,<area3>"
```

## Step 4: Report results

Show what was created. For each domain area, note the overview.md that was generated and suggest the user start by:
- Filling in the "What This Covers" section of each overview.md
- Identifying 2-3 primary sources per domain area
- Using `/dewey:curate add` to create the first topics
</process>

<success_criteria>
- Domain areas proposed and confirmed by user
- Directory structure created with domain area directories
- Each domain area has an overview.md
- AGENTS.md manifest includes all domain areas
- User has clear next steps for populating the KB
</success_criteria>
