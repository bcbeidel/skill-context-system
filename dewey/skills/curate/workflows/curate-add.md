<objective>
Create or update a topic in a domain area, research primary sources, and draft initial content for the user's review.
</objective>

<process>
## Step 1: Resolve topic and area from intake context

The intake classifier has already identified the user's intent. Extract:

- **Topic name** — from the user's free-text input
- **Domain area** — auto-detect:
  1. If only one domain area exists under the knowledge directory, use it
  2. If the user mentioned an area, use that
  3. Otherwise, list available areas and ask the user to pick one
- **Relevance** — default to `core` unless the user specified otherwise
- **Mode** — `new` (create topic) or `update` (modify existing topic). The intake classifier sets this.

Do NOT ask the user for information that can be inferred. Get moving quickly.

## Step 2: Verify the domain area and create topic files

Check that `docs/<area>/` exists. If it does not, inform the user and suggest creating it first.

Run the create_topic script:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/curate/scripts/create_topic.py --kb-root <kb_root> --area <area> --topic "<topic_name>" --relevance "<relevance>"
```

### If mode is `update` (updating an existing topic):

1. Read the existing topic file at `docs/<area>/<slug>.md`
2. Present the current content to the user: "Here's what's currently in this topic:"
3. Ask: "What would you like to change or add?"
4. Skip to Step 3 (Research, evaluate, and draft) but scope the research to the specific changes requested. Steps 3.2-3.5 and Step 4 apply proportionally -- new claims get full source evaluation and cross-validation treatment; existing unchanged content is skipped.
5. In Step 5 (Present draft), show a diff of what changed rather than the full content

## Step 3: Research, evaluate, and draft

Read AGENTS.md to understand the role context, then follow sub-steps 3.1 through 3.5. Consult `@dewey/skills/curate/references/source-evaluation.md` for full methodology details.

### 3.1 Discover candidate sources

Search for 5-7 candidate sources (more than needed to allow exclusions). Use the source hierarchy to guide your search -- prefer higher tiers:

1. Official documentation (specs, API references, language docs)
2. Institutional sources (.edu, .gov, standards bodies)
3. Peer-reviewed publications (papers, conference proceedings)
4. Recognized expert content (named experts with verifiable credentials)
5. High-quality practitioner content (well-regarded blogs, talks)
6. Community consensus (Stack Overflow, GitHub discussions)

**Search techniques:** Use site-scoped searches (`site:docs.python.org`), quoted exact terms, recency filtering for fast-moving domains, and author-focused searches for known experts.

### 3.2 Evaluate each source

For each candidate, apply SIFT lateral reading: leave the source, search what others say about it and its author/organization. Then score on five dimensions (1-5 scale):

| Dimension | 5 (highest) | 1 (lowest) |
|-----------|-------------|------------|
| Authority | RFC author, official docs maintainer | Anonymous blog, no credentials visible |
| Accuracy | Peer-reviewed, claims with inline citations | Contains known errors, contradicts primary sources |
| Currency | Updated within 6 months or covers stable topic | Outdated, explicitly superseded |
| Purpose | Purely informational, no commercial interest | Primarily promotional or misleading |
| Corroboration | Key claims confirmed by 3+ independent sources | Contradicted by other credible sources |

**Decision:** Include (average >= 3.5), include with caveat (2.5-3.4), or exclude (< 2.5). Aim for 3-5 included sources from 2+ independent organizations.

### 3.3 Counter-evidence search

After finding supporting sources, actively search for contradicting perspectives:

- `"problems with <topic>"`, `"limitations of <topic>"`
- `"<topic> considered harmful"`, `"alternatives to <topic>"`

If credible counter-evidence is found, note it for inclusion in Watch Out For or as qualifying language. If none is found, note as a positive signal.

### 3.4 Draft content

Draft content for both files using the evaluated sources:

**Working-knowledge file** (`<slug>.md`):
- **Why This Matters** -- Causal reasoning: what problem this solves, why this approach
- **In Practice** -- A concrete, worked example applied realistically
- **Key Guidance** -- Actionable recommendations with inline source citations
- **Watch Out For** -- Common mistakes, edge cases, things that change
- **Go Deeper** -- Links to reference file and primary sources

**Reference companion** (`<slug>.ref.md`):
- Terse, scannable quick-lookup version of the key guidance

Calibrate confidence language to source consensus:

| Source Agreement | Language |
|-----------------|----------|
| >80% agree | State as fact |
| 50-80% agree | Use "generally" or "typically" |
| 30-50% agree | Use "some evidence suggests" |
| <30% agree | Present competing views or omit |

Update frontmatter `sources:` field with the actual primary sources found.

### 3.5 Build Source Evaluation section

Add a `## Source Evaluation` section at the bottom of the working-knowledge file:

1. **Visible summary table:**

   ```markdown
   | Source | Authority | Accuracy | Currency | Purpose | Corroboration | Decision |
   |--------|-----------|----------|----------|---------|---------------|----------|
   | [Title](url) | 4 | 5 | 4 | 5 | 4 | include |
   ```

2. **Counter-evidence summary:** One line describing what was searched for and what was found.

3. **Hidden provenance block:** `<!-- dewey:provenance { ... } -->` JSON with full structured data (see `source-evaluation.md` for format specification).

## Step 4: Cross-validate draft

Before presenting to the user, verify that the draft accurately reflects its sources.

### 4.1 Decompose key claims

Extract factual and recommendation claims from Key Guidance and Watch Out For. Break compound claims into atomic, verifiable statements (one assertion each). Skip subjective judgments.

### 4.2 Triangulate each claim

For each claim, check support from 2+ evaluated sources. Track whether each source supports, partially supports, or contradicts the claim.

### 4.3 Calibrate confidence language

Verify that the draft language matches the consensus level from Step 3.4. Adjust overconfident claims (e.g., stating a weakly-supported claim as fact) and under-confident claims (e.g., hedging a universally-agreed point).

### 4.4 Record cross-validation results

Add cross-validation results to the `<!-- dewey:provenance -->` block: total claims verified, consensus breakdown, and any claims modified or removed during verification.

## Step 5: Present draft and get approval

Present the complete draft to the user with a brief source quality summary:

> "This draft draws on N sources (average authority X/5). M of N key claims are supported by 2+ independent sources."

Cite which sources informed each section. Ask: "Does this capture your understanding, or should I adjust anything?"

The human brings domain judgment. Accept their edits and corrections. If they approve, proceed. If they have changes, revise and re-present.

## Step 6: Write approved content and update manifest

Write the approved content to both topic files, then update the three index files below. When updating AGENTS.md or CLAUDE.md, only modify content between `<!-- dewey:kb:begin -->` / `<!-- dewey:kb:end -->` markers.

### 6a. AGENTS.md — add topic to the domain area table

The managed section contains domain area headings like `### area-slug`. Under each heading is a topic table. Add a row to the table for the new topic:

```markdown
### python-foundations

| Topic | Description |
|-------|-------------|
| [Project Structure](docs/python-foundations/project-structure.md) | src layout, UI/logic separation, pyproject.toml |
```

- If no table exists yet under the heading, create one with the header row + separator + new row
- Link format: `[Topic Name](docs/<area>/<slug>.md)` — always include the file path
- Description: one-line summary of the topic
- Do NOT use bullet lists — always use a table row with a linked path

### 6b. overview.md — add topic to table AND populate Key Sources

Make two updates to `docs/<area>/overview.md`:

**"How It's Organized" table** — add a row for the new topic:

```markdown
| [Project Structure](project-structure.md) | src layout, UI/logic separation |
```

Links are relative within the area directory, so use `<slug>.md` (not the full `docs/<area>/` path).

**"Key Sources" section** — replace `<!-- placeholder -->` (or any empty placeholder) with the primary sources found during research:

```markdown
## Key Sources
- [src layout vs flat layout](https://packaging.python.org/...) -- Python Packaging User Guide
- [Multipage apps with st.Page](https://docs.streamlit.io/...) -- Streamlit Docs
```

List the 3-5 authoritative sources that were used during the research step. Never leave this as a placeholder.

### 6c. CLAUDE.md — verify domain area is listed

CLAUDE.md's Domain Areas table lists areas, not individual topics. After adding a topic, verify the area already appears in the table (it should if the area was initialized). If the area is missing, add a row:

```markdown
| area-name | `docs/area-slug/` | [overview.md](docs/area-slug/overview.md) |
```

If the area is already listed, no changes needed — do not add individual topics to CLAUDE.md.

## Step 7: Rebuild index.md

Regenerate the table of contents so the new topic appears:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/curate/scripts/scaffold.py --target <kb_root> --rebuild-index
```

## Step 8: Update curation plan

If `.dewey/curation-plan.md` exists, check for an item matching the topic name just added (case-insensitive match on the name portion before ` -- `). If found, mark it as done by changing `- [ ]` to `- [x]`. Update `last_updated` in the frontmatter to today's date.
</process>

<success_criteria>
- Topic working-knowledge file created with researched content
- Topic reference file created with terse quick-lookup version
- Primary sources identified and cited in frontmatter and inline
- Sources evaluated using the 5-dimension rubric before inclusion
- At least 3 included sources from 2+ independent organizations
- Counter-evidence search performed and documented
- Key claims cross-validated against 2+ sources
- Confidence language calibrated to consensus level
- Source Evaluation section present with visible table and `<!-- dewey:provenance -->` block
- Content reviewed and approved by the user
- AGENTS.md has a linked table row (`[Topic](docs/<area>/<slug>.md)`) under the domain area heading — not a bullet
- overview.md "How It's Organized" has a linked table row (`[Topic](<slug>.md)`) for the topic
- overview.md "Key Sources" is populated with actual sources found during research — not a placeholder
- CLAUDE.md domain area is present in the Domain Areas table
</success_criteria>
