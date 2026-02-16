<objective>
Submit a topic proposal for review before adding it to the knowledge base.
</objective>

<process>
## Step 1: Resolve proposal details from intake

The intake classifier identified a proposal intent. Extract:

- **Topic name** — from the user's free-text input
- **Relevance** — default to `core` unless specified
- **Proposed by** — default to `agent` unless specified
- **Rationale** — if not clear from context, ask the user: "Why should this topic be in the knowledge base?"

## Step 2: Check for knowledge base overlap

Before creating the proposal, check whether the topic already exists:

1. Scan the knowledge base directory for any existing topic file whose name or frontmatter title matches the proposed topic (use fuzzy matching -- e.g., "Audience Segmentation" matches `audience-segmentation.md`)
2. Scan `<knowledge-dir>/_proposals/` for any pending proposal with a matching topic name

If a match is found:
- **Existing topic:** "A topic matching '<name>' already exists at `<path>`. Did you mean to update it with `/dewey:curate add`, or is this a distinct topic?"
- **Pending proposal:** "A pending proposal for '<name>' already exists at `<knowledge-dir>/_proposals/<slug>.md`. Review or promote it instead?"

Only proceed if the user confirms it is a genuinely new topic.

## Step 3: Run propose script

Verify that `<knowledge-dir>/_proposals/` exists. If not, create it:
```bash
mkdir -p <kb_root>/<knowledge-dir>/_proposals
```

Then run the propose script:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/curate/scripts/propose.py --kb-root <kb_root> --topic "<topic_name>" --relevance "<relevance>" --proposed-by "<proposed_by>" --rationale "<rationale>"
```

## Step 4: Report what was created

Show the user the proposal file that was created:
- `<knowledge-dir>/_proposals/<slug>.md`

## Step 5: Explain the proposal lifecycle

"The proposal has been created in `<knowledge-dir>/_proposals/`. Next steps:

1. **Validate the proposal** -- Use `/dewey:health` to run validators against the knowledge base and check proposal quality
2. **Review and refine** -- Edit the proposal file to flesh out the template sections if desired
3. **Promote when ready** -- Use `/dewey:curate promote` to move the proposal into a domain area once it has been validated"
</process>

<success_criteria>
- Proposal file created in <knowledge-dir>/_proposals/
- Frontmatter includes topic name, relevance, proposed_by, and rationale
- User understands that proposals need validation before promotion
</success_criteria>
