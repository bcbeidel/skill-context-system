<objective>
Scaffold an empty knowledge base with the standard directory structure and template files.
</objective>

<required_reading>
Load `references/kb-spec-summary.md` for context on the KB specification.
</required_reading>

<process>
## Step 1: Determine target directory

If `$ARGUMENTS` contains a path, use that. Otherwise use the current working directory.

Confirm with user: "I'll create a knowledge base in `<directory>`. What role does this KB serve? (e.g., 'Paid Media Analyst', 'Platform Engineer')"

## Step 2: Run scaffold script

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/scaffold.py --target <directory> --role "<role_name>"
```

## Step 3: Report results

Show the user what was created and suggest next steps:
- "Use `/dewey:curate add` to start adding topics"
- "Edit AGENTS.md to refine the persona definition"
- "Create domain area directories as your KB takes shape"
</process>

<success_criteria>
- Directory structure created
- AGENTS.md generated with role name
- index.md generated
- User informed of next steps
</success_criteria>
