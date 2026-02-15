<objective>
Analyze coverage gaps by comparing AGENTS.md role responsibilities against knowledge base contents.
</objective>

<process>
## Step 1: Parse AGENTS.md

Read `AGENTS.md` from the KB root. Extract:

1. **Role name** -- The role this KB serves
2. **Responsibilities** -- The key responsibilities or behavioral expectations listed
3. **Manifest entries** -- The domain areas and topics listed in the manifest section

If AGENTS.md does not exist, report: "No AGENTS.md found. Use `/dewey:init` to create one."

## Step 2: Scan docs/ contents

Walk the `docs/` directory structure. Build a map of:

- **Domain areas** -- Directories under `docs/` (excluding `_proposals/` and other `_` prefixed dirs)
- **Topics per area** -- .md files in each area (excluding overview.md and .ref.md files)
- **Overview presence** -- Whether each area has an overview.md
- **Reference presence** -- Whether each topic has a .ref.md companion

## Step 3: Identify gaps

Compare AGENTS.md responsibilities against docs/ contents:

### 3a. Responsibility gaps

For each responsibility listed in AGENTS.md, check whether there is a corresponding domain area or topic. Flag responsibilities with no matching content:

"**Gap:** Responsibility '<responsibility>' has no corresponding domain area or topic."

Use semantic matching -- the responsibility text may not exactly match a directory name, so look for reasonable correspondence.

### 3b. Orphan content

For each domain area and topic in docs/, check whether it connects to a responsibility in AGENTS.md. Flag content with no matching responsibility:

"**Orphan:** Topic '<topic>' in '<area>' is not connected to any listed responsibility."

### 3c. Thin areas

For each domain area, check content depth:
- Has only an overview.md and no topics -> **Thin: overview only**
- Has topics but all at the same depth -> **Thin: single depth level**
- Has fewer than 2 topics -> **Thin: minimal coverage**

## Step 4: Present the coverage report

```
## Coverage Report

### Summary
- Role: <role name>
- Responsibilities tracked: <N>
- Domain areas: <N>
- Total topics: <N>
- Coverage score: <responsibilities with content / total responsibilities>

### Gaps (responsibilities without content)

| Responsibility | Suggested Area | Priority |
|----------------|---------------|----------|
| <responsibility> | <suggested area name> | <high/medium/low> |

### Orphans (content without responsibility)

| Content | Area | Suggestion |
|---------|------|------------|
| <topic> | <area> | Add to AGENTS.md manifest / Consider removing |

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
- AGENTS.md is parsed for responsibilities and manifest entries
- Knowledge directory structure is fully scanned
- Gaps identify responsibilities without corresponding content
- Orphans identify content not connected to responsibilities
- Thin areas flag domain areas needing deeper coverage
- Recommendations point to specific Dewey skills for remediation
</success_criteria>
