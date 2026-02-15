<objective>
Submit a topic proposal for review before adding it to the knowledge base.
</objective>

<process>
## Step 1: Parse arguments and gather proposal details

Parse `$ARGUMENTS` for topic name, relevance, rationale, and proposed-by. Valid invocations:

- `/dewey:curate propose Audience Segmentation` -- topic name only
- `/dewey:curate propose Audience Segmentation --relevance supporting` -- topic name + relevance
- `/dewey:curate propose Audience Segmentation --relevance supporting --rationale "Needed for campaign targeting"` -- topic name + relevance + rationale
- `/dewey:curate propose Audience Segmentation --proposed-by "Jane"` -- topic name + proposed-by

**Defaults** (apply when not provided):
- Relevance → `core`
- Proposed by → `agent`
- Rationale → ask the user (this is the one field that should always be explicitly provided)

For any required field not provided in `$ARGUMENTS` and not covered by a default, ask the user.

## Step 2: Check for KB overlap

Before creating the proposal, check whether the topic already exists:

1. Scan `docs/` for any existing topic file whose name or frontmatter title matches the proposed topic (use fuzzy matching -- e.g., "Audience Segmentation" matches `audience-segmentation.md`)
2. Scan `docs/_proposals/` for any pending proposal with a matching topic name

If a match is found:
- **Existing topic:** "A topic matching '<name>' already exists at `<path>`. Did you mean to update it with `/dewey:curate add`, or is this a distinct topic?"
- **Pending proposal:** "A pending proposal for '<name>' already exists at `docs/_proposals/<slug>.md`. Review or promote it instead?"

Only proceed if the user confirms it is a genuinely new topic.

## Step 3: Run propose script

Verify that `docs/_proposals/` exists. If not, create it:
```bash
mkdir -p <kb_root>/docs/_proposals
```

Then run the propose script:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/curate/scripts/propose.py --kb-root <kb_root> --topic "<topic_name>" --relevance "<relevance>" --proposed-by "<proposed_by>" --rationale "<rationale>"
```

## Step 4: Report what was created

Show the user the proposal file that was created:
- `docs/_proposals/<slug>.md`

## Step 5: Explain the proposal lifecycle

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
