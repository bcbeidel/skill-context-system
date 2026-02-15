<objective>
Submit a topic proposal for review before adding it to the knowledge base.
</objective>

<process>
## Step 1: Gather proposal details

Ask the user for:

1. **Topic name** -- What is the proposed topic? (e.g., "Audience Segmentation")
2. **Relevance** -- How relevant is this to the role? (`core`, `supporting`, or `peripheral`)
3. **Rationale** -- Why should this topic be added to the KB?
4. **Proposed by** -- Who is proposing this? (e.g., a human name or "agent")

If any of these were provided in `$ARGUMENTS`, use those values instead of asking.

## Step 2: Run propose script

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/curate/scripts/propose.py --kb-root <kb_root> --topic "<topic_name>" --relevance "<relevance>" --proposed-by "<proposed_by>" --rationale "<rationale>"
```

## Step 3: Report what was created

Show the user the proposal file that was created:
- `docs/_proposals/<slug>.md`

## Step 4: Explain the proposal lifecycle

"The proposal has been created in `docs/_proposals/`. Next steps:

1. **Validate the proposal** -- Use `/dewey:health` to run validators against the KB and check proposal quality
2. **Review and refine** -- Edit the proposal file to flesh out the template sections if desired
3. **Promote when ready** -- Use `/dewey:curate promote` to move the proposal into a domain area once it has been validated"
</process>

<success_criteria>
- Proposal file created in docs/_proposals/
- Frontmatter includes topic name, relevance, proposed_by, and rationale
- User understands that proposals need validation before promotion
</success_criteria>
