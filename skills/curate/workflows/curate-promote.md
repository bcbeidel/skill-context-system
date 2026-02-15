<objective>
Promote a validated proposal from _proposals/ into a domain area in the knowledge base.
</objective>

<process>
## Step 1: List pending proposals

Scan `knowledge/_proposals/` for .md files. Present the list to the user:

"Here are the pending proposals:

1. `<slug>.md` -- <title from frontmatter>
2. `<slug>.md` -- <title from frontmatter>
..."

If there are no proposals, inform the user: "No pending proposals found in `knowledge/_proposals/`. Use `/dewey:curate propose` to create one."

## Step 2: Select proposal and target area

Ask the user:

1. **Which proposal** to promote (by number or slug name)
2. **Target domain area** -- Which domain area directory should it go into? (e.g., "campaign-management")

If these were provided in `$ARGUMENTS`, use those values instead of asking.

## Step 3: Verify the target area exists

Check that `knowledge/<target_area>/` exists. If not, inform the user and suggest creating it first.

## Step 4: Run promote script

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/curate/scripts/promote.py --kb-root <kb_root> --proposal "<slug>" --target-area "<target_area>"
```

## Step 5: Report what happened

Show the user:
- The proposal file was removed from `knowledge/_proposals/`
- The topic file was created at `knowledge/<target_area>/<slug>.md`
- Proposal-specific frontmatter (status, proposed_by, rationale) was stripped

## Step 6: Remind user of next steps

"The proposal has been promoted. To finalize:

1. **Update AGENTS.md** -- Add the new topic to the manifest under the `<target_area>` domain area
2. **Update index.md** -- Add the topic to `knowledge/index.md`
3. **Fill in content** -- Complete any remaining template sections in the promoted file"
</process>

<success_criteria>
- Proposal file removed from _proposals/
- Topic file created in target domain area
- Proposal-specific frontmatter stripped
- User reminded to update AGENTS.md and index.md
</success_criteria>
