<objective>
Run full Tier 1 + Tier 2 assessment and surface a Tier 3 decision queue for human judgment.
</objective>

<process>
## Step 1: Run Tier 1 + Tier 2

Execute the audit workflow (health-audit.md) to produce the combined Tier 1 + Tier 2 report. Present the summary.

## Step 2: Build the Tier 3 decision queue

Scan the KB for items that require human judgment. These are decisions that cannot be resolved by deterministic checks or LLM assessment alone.

### 2a. Relevance questions

For entries where Tier 2 flagged weak relevance or where the role has evolved:
- "Is `<topic>` still relevant to this role?"
- "Does the relevance statement for `<topic>` accurately reflect current needs?"

### 2b. Scope decisions

For entries with low utilization (if `.dewey/utilization/` data exists) or narrow relevance:
- "Should `<topic>` be pruned? It has not been referenced in <N> days."
- "Should `<area>` be consolidated? It contains only an overview and one topic."

### 2c. Proposal decisions

Scan `docs/_proposals/` for pending proposals:
- "Pending proposal: `<slug>` -- <title>. Accept, reject, or revise?"

If no proposals exist, skip this section.

### 2d. Conflict resolution

For entries where Tier 2 detected source drift (KB claims differ from source material):
- "KB says `<claim>` but source now says `<updated claim>`. Update KB, keep current, or investigate?"

## Step 3: Present the decision queue

Format as an interactive decision list:

```
## Tier 3: Decisions for Human Review

### Relevance (<N> items)

1. **<topic>** -- Is this still relevant to the role?
   - Current relevance: "<relevance statement>"
   - Concern: <why this was flagged>
   - Options: Keep / Update relevance / Remove

### Scope (<N> items)

2. **<topic or area>** -- Should this be pruned or consolidated?
   - Reason: <low utilization / narrow scope>
   - Options: Keep / Prune / Consolidate into <suggestion>

### Proposals (<N> items)

3. **<proposal slug>** -- <title>
   - Proposed by: <who>
   - Rationale: <why>
   - Options: Accept (promote) / Reject (delete) / Revise

### Conflicts (<N> items)

4. **<topic>** -- Source drift detected
   - KB claim: "<current claim>"
   - Source says: "<updated claim>"
   - Options: Update KB / Keep current / Investigate further
```

## Step 4: Process decisions

For each item, ask the user for their decision. Based on the response:

- **Keep** -> No action; optionally update `last_validated` to today
- **Update relevance** -> Edit the frontmatter relevance field
- **Remove / Prune** -> Note for manual deletion (never auto-delete KB content)
- **Accept proposal** -> Run `/dewey:curate promote` for the proposal
- **Reject proposal** -> Note for manual deletion of the proposal file
- **Update KB** -> Edit the content to reflect updated source information, update `last_validated`
- **Investigate further** -> Add to a follow-up list for deeper research

## Step 5: Summary

After all decisions are processed, present a summary:

```
## Review Complete

- Decisions made: <N>
- Content updated: <N> entries
- Proposals accepted: <N>
- Proposals rejected: <N>
- Items deferred: <N>
- Follow-up needed: <N>
```
</process>

<success_criteria>
- Tier 1 + Tier 2 assessment completes before Tier 3
- Decision queue is organized by category (relevance, scope, proposals, conflicts)
- Each item presents clear options, not open-ended questions
- Human decisions are recorded and acted upon
- No content is auto-deleted; removals are flagged for manual action
- Summary captures all decisions made during the review
</success_criteria>
