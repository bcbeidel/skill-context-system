<objective>
Create a proposal from an external URL, pre-filling the source in frontmatter for manual distillation.
</objective>

<process>
## Step 1: Get the source URL

Ask the user for:

1. **URL** -- The external source to ingest (e.g., a documentation page, blog post, or article)
2. **Topic name** -- What topic does this source relate to? (e.g., "Bid Strategies")
3. **Relevance** -- How relevant is this to the role? (`core`, `supporting`, or `peripheral`)

If any of these were provided in `$ARGUMENTS`, use those values instead of asking.

## Step 2: Create the proposal with source pre-filled

Run the propose script to create the proposal:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/curate/scripts/propose.py --kb-root <kb_root> --topic "<topic_name>" --relevance "<relevance>" --proposed-by "ingest" --rationale "Ingested from: <url>"
```

Then update the proposal file's frontmatter to include the URL in the sources list.

## Step 3: Report what was created

Show the user:
- `docs/_proposals/<slug>.md` -- Proposal with source URL pre-filled

## Step 4: Guide manual distillation

"This is a v1 stub -- automated content extraction is not yet implemented. To complete this topic:

1. **Read the source** at `<url>`
2. **Fill in the template sections** based on what you learn:
   - **Why This Matters** -- Why this topic is important for the role
   - **In Practice** -- Concrete, actionable guidance from the source
   - **Key Guidance** -- The most important principles or takeaways
3. **Validate and promote** -- Use `/dewey:health` to validate, then `/dewey:curate promote` to move it into a domain area"
</process>

<success_criteria>
- Proposal file created in docs/_proposals/
- Source URL captured in frontmatter or rationale
- User understands they need to manually distill the source content
- User has clear path to validate and promote the ingested topic
</success_criteria>
