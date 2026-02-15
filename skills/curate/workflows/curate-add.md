<objective>
Create a new topic in a domain area using the standard topic template.
</objective>

<process>
## Step 1: Gather topic details

Ask the user for:

1. **Domain area** -- Which domain area directory should this topic go in? (e.g., "campaign-management")
2. **Topic name** -- What is the topic called? (e.g., "Bid Strategies")
3. **Relevance** -- How relevant is this to the role? (`core`, `supporting`, or `peripheral`)

If any of these were provided in `$ARGUMENTS`, use those values instead of asking.

## Step 2: Verify the domain area exists

Check that `knowledge/<area>/` exists in the KB root. If it does not, inform the user and suggest creating it first or choosing an existing area.

## Step 3: Run create_topic script

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/curate/scripts/create_topic.py --kb-root <kb_root> --area <area> --topic "<topic_name>" --relevance "<relevance>"
```

## Step 4: Report what was created

Show the user the files that were created:
- `knowledge/<area>/<slug>.md` -- Working-knowledge file
- `knowledge/<area>/<slug>.ref.md` -- Expert-reference companion

## Step 5: Remind user of next steps

"The topic files have been created from the template. To complete this topic:

1. **Fill in the template sections:**
   - Why This Matters -- Why this topic is important for the role
   - In Practice -- Concrete, actionable guidance
   - Key Guidance -- The most important principles
   - Watch Out For -- Common mistakes and pitfalls
   - Go Deeper -- Links to the reference file and external sources

2. **Update the KB manifest:**
   - Add the topic to `AGENTS.md` under the appropriate domain area
   - Add the topic to `knowledge/index.md`"
</process>

<success_criteria>
- Topic working-knowledge file created
- Topic reference file created
- User informed of template sections to complete
- User reminded to update AGENTS.md and index.md
</success_criteria>
