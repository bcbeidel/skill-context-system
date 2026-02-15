<objective>
Analyze coverage gaps by comparing AGENTS.md role responsibilities against knowledge base contents.
</objective>

<process>
## Step 1: Parse AGENTS.md

Read `AGENTS.md` from the KB root. Extract these three things:

1. **Role definition** -- The role title from the `# Role:` heading (first H1)
2. **Persona scope** -- The prose description in the "Who You Are" section. This describes the agent's expertise and behavioral scope. Note the domains and skills it mentions -- these define what the KB _should_ cover.
3. **Manifest entries** -- Inside the `<!-- dewey:kb:begin -->` / `<!-- dewey:kb:end -->` markers, extract:
   - **Domain areas** -- Each H3 heading (e.g., `### python-foundations`)
   - **Topics per area** -- Rows in the markdown table under each H3 (columns: Topic, Description). An area with no table rows is empty.

If AGENTS.md does not exist, report: "No AGENTS.md found. Use `/dewey:init` to create one."

## Step 2: Scan docs/ contents

Walk the `docs/` directory structure. Build a map of:

- **Domain areas** -- Directories under `docs/` (excluding `_proposals/` and other `_` prefixed dirs)
- **Topics per area** -- .md files in each area (excluding overview.md and .ref.md files)
- **Overview presence** -- Whether each area has an overview.md
- **Reference presence** -- Whether each topic has a .ref.md companion

## Step 3: Identify gaps

Compare the AGENTS.md persona scope and manifest against docs/ contents:

### 3a. Persona-vs-KB gaps

Read the persona description from "Who You Are" and the role title. Identify domains, skills, or expertise areas the persona mentions that are **not covered** by any existing domain area or topic in docs/. Use judgment -- the persona is prose, not a structured list, so look for described capabilities that have no corresponding KB content.

Example: If the role says "building Streamlit applications that scale toward production Snowflake deployments" but there is no topic covering Snowflake integration patterns, flag it:

"**Gap:** The persona describes '<capability>' but no domain area or topic covers this."

### 3b. Manifest-vs-filesystem orphans

Compare the manifest entries (from Step 1) against the actual docs/ filesystem (from Step 2):

- **In manifest but missing from filesystem:** A topic row in AGENTS.md points to a file that doesn't exist in docs/. Flag: "**Broken link:** Manifest lists `<topic>` at `<path>` but file does not exist."
- **In filesystem but missing from manifest:** A topic .md file exists in docs/ but has no corresponding row in the AGENTS.md manifest table. Flag: "**Orphan:** `<path>` exists in docs/ but is not listed in the AGENTS.md manifest."

### 3c. Thin areas

For each domain area, check content depth:
- Has only an overview.md and no topics -> **Thin: overview only**
- Has topics but all at the same depth -> **Thin: single depth level**
- Has fewer than 2 topics -> **Thin: minimal coverage**

## Step 4: Present the coverage report

```
## Coverage Report

### Summary
- Role: <role title>
- Persona scope areas identified: <N>
- Domain areas in manifest: <N>
- Total topics in manifest: <N>
- Total topic files in docs/: <N>

### Persona Gaps (described scope not covered by KB)

| Capability from Persona | Suggested Area | Priority |
|------------------------|---------------|----------|
| <capability> | <suggested area name> | <high/medium/low> |

### Manifest/Filesystem Mismatches

| Issue | Path | Action |
|-------|------|--------|
| Broken link | <manifest path> | Create file or remove manifest entry |
| Orphan file | <filesystem path> | Add to AGENTS.md manifest or consider removing |

### Thin Areas (minimal coverage)

| Area | Topics | Issue |
|------|--------|-------|
| <area> | <count> | Overview only / Single depth / Minimal topics |
```

## Step 5: Suggest next steps

- For gaps -> "Use `/dewey:curate add` or `/dewey:curate propose` to create content for these responsibilities."
- For orphans -> "Update AGENTS.md to include these topics, or evaluate whether they should be removed."
- For thin areas -> "Expand these areas with working-knowledge and reference files."
</process>

<success_criteria>
- AGENTS.md is parsed for role title, persona scope, and manifest entries (domain areas + topic tables)
- Knowledge directory structure is fully scanned
- Persona gaps identify described capabilities without corresponding KB content
- Manifest/filesystem mismatches identify broken links and orphan files
- Thin areas flag domain areas needing deeper coverage
- Recommendations point to specific Dewey skills for remediation
</success_criteria>
