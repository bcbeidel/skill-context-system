<objective>
Run Tier 1 deterministic checks followed by Tier 2 LLM-assisted quality assessment on flagged or stale entries.
</objective>

<process>
## Step 1: Run Tier 1 checks and Tier 2 pre-screening

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/health/scripts/check_kb.py --knowledge-base-root <knowledge_base_root> --both
```

Capture the JSON output. It contains two top-level sections:
- **`tier1`** -- `issues` (list of deterministic check failures) and `summary` (aggregate counts).
- **`tier2`** -- `queue` (list of items with trigger type and pre-computed context) and `summary` (trigger counts).

Present the Tier 1 summary as in the health-check workflow.

The Tier 2 pre-screener runs 9 deterministic triggers on each file and returns a structured queue with context data for each item. Present the trigger summary:

| Trigger | Count | Description |
|---------|-------|-------------|
| source_drift | N | Files with stale or missing last_validated dates |
| depth_accuracy | N | Files where word count or prose ratio doesn't match depth |
| source_primacy | N | Working files with low inline citation density |
| why_quality | N | Working files with missing or thin "Why This Matters" |
| concrete_examples | N | Working files with missing or abstract "In Practice" |
| citation_quality | N | Working files with duplicate inline citation URLs |
| source_authority | N | Working files where all sources are community-tier |
| provenance_completeness | N | Working files with incomplete Source Evaluation provenance |
| recommendation_coverage | N | Working files where >50% of recommendations lack citations |

"**Tier 2 evaluation queue:** <N> items across <M> files."

### Calibration Anchors

Before assessing queue items, review these reference verdicts to ensure consistent thresholds across all evaluations:

**source_drift — Flag:**
The source URL has been updated with new API endpoints, changed pricing tiers, or deprecated features not reflected in the KB entry. The KB makes claims the source no longer supports.

**source_drift — OK:**
Minor wording changes or page redesign, but the substantive claims and recommendations in the KB still align with the source content.

**depth_accuracy — Flag:**
A working-depth file where "In Practice" contains only bold-header + 2-bullet enumeration lists (no scenarios, worked examples, or code). Reads as a reference checklist rather than actionable working guidance.

**depth_accuracy — OK:**
A working-depth file where low prose ratio is caused by code blocks, tables, and markdown link URLs. The non-prose elements ARE the substance.

**why_quality — Flag:**
"Why This Matters" describes *what* the topic is ("Fair lending laws regulate marketing practices") without explaining *why* it matters to this role ("Non-compliant targeting can trigger regulatory action and halt campaigns").

**why_quality — OK:**
"Why This Matters" connects the topic to role outcomes, stakes, or consequences. The reader understands what they risk by ignoring this topic.

**concrete_examples — Flag:**
"In Practice" describes a process in abstract terms ("configure the schema," "set up the pipeline") without a single code block, config snippet, table, or specific value. A prose description of what an example "might look like" also counts as a flag.

**concrete_examples — OK:**
"In Practice" includes worked scenarios with specific names, values, or artifacts (code blocks, tables, inventory entries, SQL snippets). Someone could follow this in a real implementation.

**source_primacy — Flag:**
10 recommendations with only 1 inline citation. OR: the same generic documentation URL cited 3+ times for different claims. The citations don't trace to information that specifically supports each claim.

**source_primacy — OK:**
8 recommendations with 3 inline citations from distinct, specific sources. Each cited URL leads to content directly addressing the claim it backs. Uncited items are standard practice or experience-based cautions.

**citation_quality — Flag:**
A single documentation index page (e.g., the Feature Store overview) cited to back claims about PII handling, offline stores, AND encoding strategies. The URL is technically relevant but too broad to serve as provenance for any specific claim.

**citation_quality — OK:**
Each inline citation links to a page or section that directly addresses the specific claim. Different claims cite different URLs, or the same URL only when it genuinely covers both claims.

**source_authority — Flag:**
All three sources are Medium articles by anonymous authors with no verifiable credentials. No official documentation, academic source, or recognized industry authority anchors the claims.

**source_authority — OK:**
One of three sources is a community blog, but the other two are official documentation and an RFC. The community source adds practical color; the authoritative sources anchor the factual claims.

**provenance_completeness — Flag:**
Source Evaluation section contains a narrative assessment ("these sources look good") but no structured provenance block. There's no machine-readable record of when sources were evaluated, what claims were verified, or whether counter-evidence was sought.

**provenance_completeness — OK:**
Source Evaluation section contains both a narrative assessment and a complete `<!-- dewey:provenance {...} -->` block with `evaluated` date, `sources` list, `counter_evidence` findings, and `cross_validation` with `claims_total > 0`.

**recommendation_coverage — Flag:**
Key Guidance lists 8 recommendations but only 1 has an inline citation. The reader cannot trace most guidance to any supporting evidence.

**recommendation_coverage — OK:**
Key Guidance lists 6 recommendations with 4 inline citations. The 2 uncited items are common-sense cautions ("test in staging first") that don't require external backing.

## Step 2: Perform Tier 2 LLM assessment

Iterate the queue items from Step 1. Each item includes pre-computed context data -- use it to focus assessment rather than manually counting or re-reading.

### 2a. Source drift

For items with `trigger: source_drift`, the context includes `source_urls`. For each URL, use the **WebFetch** tool to retrieve the current content:

```
WebFetch(url=<source_url>, prompt="Summarize the key claims and recommendations in this document")
```

Compare the fetched content against the claims in the knowledge base entry. Flag if:
- The knowledge base entry makes claims not supported by the sources
- The sources have been updated with information not reflected in the knowledge base entry
- Sources are no longer accessible (WebFetch returns an error)

If a source URL cannot be fetched (timeout, 404, paywall), note: "Source drift check skipped for `<url>` -- not accessible." and continue with the remaining sources.

### 2b. Depth label accuracy

For items with `trigger: depth_accuracy`, the context includes `declared_depth`, `word_count`, `prose_ratio`, and expected ranges. Use these metrics to guide evaluation:
- **overview** -- Should orient: what is this area, why it matters, how topics connect. Should NOT contain detailed how-to guidance.
- **working** -- Should have actionable guidance: In Practice examples, Key Guidance, Watch Out For. Should NOT be terse/scannable-only.
- **reference** -- Should be terse and scannable: tables, lists, lookup patterns. Should NOT have lengthy narrative.

Flag if the content does not match its declared depth.

### 2c. "Why This Matters" quality

For items with `trigger: why_quality`, the context includes `has_section`, `word_count`, and `min_required`. Evaluate:
- Does it explain **why**, not just **what**?
- Does it connect to the role's goals and outcomes?
- Would someone unfamiliar with the topic understand the stakes?

Flag if the section reads as a description rather than a motivation.

### 2d. "In Practice" concreteness

For items with `trigger: concrete_examples`, the context includes `has_section`, `has_code_block`, `has_table`, `has_numeric_example`, and `section_word_count`. Evaluate:
- Does it contain a **concrete example** (specific scenario, numbers, names)?
- Could someone follow this guidance in a real situation?
- Is it actionable, not just theoretical?

Flag if the section is abstract or generic.

### 2e. Source primacy

For items with `trigger: source_primacy`, the context includes `recommendation_count`, `inline_source_count`, and `sections_checked`. Evaluate whether the guidance is adequately backed by inline citations to authoritative sources.

### 2f. Citation quality

For items with `trigger: citation_quality`, the context includes `duplicate_urls`, `total_inline_citations`, and `unique_inline_citations`. Evaluate whether the duplicated URLs genuinely support each claim they're cited for, or whether they are generic pages being reused to satisfy citation count thresholds. A single documentation index page cited 3 times for different claims is a flag; the same URL cited for closely related points within a single recommendation may be OK.

### 2g. Source authority

For items with `trigger: source_authority`, the context includes `source_count` and `classifications` (a map of URL to authority tier). All sources are classified as community-tier (Medium, dev.to, Stack Overflow, Reddit, etc.) with no authoritative anchor. Evaluate:

- Do the community sources cite or reference authoritative primary sources that could be added to frontmatter?
- Are the claims experience-based opinions (acceptable from community sources) or factual assertions that need authoritative backing?
- Would adding an official documentation link, RFC, or academic source strengthen the entry?

Flag if the entry makes factual claims that should be anchored to authoritative sources. OK if the entry is primarily experience-based guidance where community voices are the natural authority.

### 2h. Provenance completeness

For items with `trigger: provenance_completeness`, the context includes `has_section`, `has_provenance_block`, and `missing_fields`. The Source Evaluation section exists but the structured provenance block is missing or incomplete. Evaluate:

- If no provenance block: does the narrative assessment contain enough information to reconstruct one (evaluation date, source list, counter-evidence search)?
- If missing fields: which fields are absent (`evaluated`, `sources`, `counter_evidence`, `cross_validation`)?
- Is the Source Evaluation substantive enough that adding the provenance block is a straightforward formatting task, or does the evaluation itself need to be redone?

Flag with specific guidance on which fields to add. If the narrative is thin, recommend re-running the source evaluation workflow rather than just adding an empty provenance block.

### 2i. Recommendation coverage

For items with `trigger: recommendation_coverage`, the context includes `total_recommendations`, `cited_recommendations`, `uncited_recommendations`, and `uncited_ratio`. More than 50% of recommendations in Key Guidance and Watch Out For lack inline citations. Evaluate:

- Which uncited recommendations make factual claims that need backing vs. common-sense cautions that don't?
- For factual claims, can you identify appropriate sources via WebFetch?
- Are the existing citations high-quality, or is the entry broadly under-sourced?

Flag if uncited items include specific factual claims, platform behaviors, or quantitative thresholds. OK if uncited items are experience-based cautions ("always test in staging," "prefer simplicity") that don't require external evidence.

## Step 3: Persist results

Write the combined Tier 2 assessment to `.dewey/health/tier2-report.json` so `health-review.md` can read results without re-running:

```python
import json
from pathlib import Path

report_dir = Path("<knowledge_base_root>") / ".dewey" / "health"
report_dir.mkdir(parents=True, exist_ok=True)
(report_dir / "tier2-report.json").write_text(json.dumps(report, indent=2))
```

## Step 4: Present combined report

Format the combined Tier 1 + Tier 2 report:

```
## Audit Report

### Tier 1: Deterministic Checks
<summary from Step 1>

### Tier 2: LLM Assessment
<N> entries evaluated.

| File | Source Drift | Depth Accuracy | Why Quality | In Practice Quality | Source Primacy | Source Authority | Provenance | Rec Coverage |
|------|-------------|----------------|-------------|---------------------|---------------|-----------------|------------|--------------|
| <path> | OK / Flag | OK / Flag | OK / Flag | OK / Flag | OK / Flag | OK / Flag | OK / Flag | OK / Flag |

### Detailed Findings
<for each flagged item, provide specific reasoning and a recommendation>
```

## Step 5: Suggest next steps

- Entries with Tier 2 flags -> "Re-validate these entries against their sources and update the content."
- Entries with depth mismatches -> "Consider changing the depth label or restructuring the content."
- Entries with weak Why/In Practice -> "Strengthen these sections with causal reasoning and concrete examples."
- If many entries are flagged -> "Consider running `/dewey:health review` to surface items for human decision."

## Step 6: Remediation standards

When fixing flagged items (either now or in a follow-up session), all new content must meet the same standards that triggered the original flag:

**Source Primacy fixes:**
- Each citation must link to a page that directly addresses the specific claim. A generic documentation index is not adequate backing for a specific technical recommendation.
- Do not reuse the same URL for multiple distinct claims unless the page genuinely covers both.
- If you cannot find a specific source for a claim, state it as experience-based guidance ("in most implementations," "typically") rather than fabricating a citation.

**Concrete Example fixes:**
- Examples must be implementable artifacts: code blocks, config snippets, schema fragments, table entries with realistic values.
- A prose description of what an example "might look like" does not satisfy the concrete examples requirement.

**Overview/orientation fixes:**
- New prose making factual claims (latency values, architectural relationships, platform behaviors) must cite sources or qualify with hedging language.
- Do not introduce uncited factual assertions while fixing other issues.

**Source Authority fixes:**
- Add at least one authoritative source (official docs, RFC, .gov/.edu, recognized industry authority) to anchor the factual claims.
- Community sources may remain alongside authoritative ones — they add practical perspective. But they cannot be the sole backing for factual assertions.

**Provenance fixes:**
- Add the `<!-- dewey:provenance {...} -->` block with all required fields: `evaluated`, `sources` (non-empty list), `counter_evidence`, `cross_validation` (with `claims_total > 0`).
- If the Source Evaluation narrative is thin, re-run the source evaluation workflow from `curate-add` (Steps 3-4) rather than fabricating provenance metadata.

**Recommendation Coverage fixes:**
- Add inline citations to recommendations that make specific factual claims, cite quantitative thresholds, or describe platform-specific behaviors.
- Experience-based cautions ("test in staging," "start simple") do not require citations — qualify them with hedging language instead.
- Do not add citations to generic documentation pages just to improve the ratio. Each citation must link to content that directly supports the specific recommendation.

**Self-check:** Before completing remediation, verify that every new paragraph you wrote would pass the same Tier 2 assessment that flagged the original content.

## Step 7: Verify remediation

After making fixes, re-run the combined check to confirm improvements and detect regressions:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/health/scripts/check_kb.py --knowledge-base-root <knowledge_base_root> --both
```

Compare the results against the initial run from Step 1:

1. **File count:** Same, increased, or decreased? A decrease may indicate lost content.
2. **Previously flagged items:** Are they resolved or still present?
3. **New issues:** Did remediation introduce new Tier 1 failures or Tier 2 triggers?

Update `.dewey/health/tier2-report.json` with the **post-remediation** assessment. The report on disk must always reflect the current state of the knowledge base, not a prior state.

If new issues were introduced, address them before finalizing. The report is not complete until it reflects the actual current content.
</process>

<success_criteria>
- Combined `--both` invocation runs successfully, producing tier1 and tier2 sections
- Tier 1 results are presented and Tier 2 pre-screener produces a structured trigger queue with context data
- Assessment agents consult calibration anchors before evaluating
- Each Tier 2 assessment uses pre-computed context to focus evaluation
- Combined report clearly separates Tier 1 and Tier 2 findings
- Results are persisted to `.dewey/health/tier2-report.json`
- Recommendations are actionable and specific to each finding
- Remediation content meets the same quality standards as existing content
- Post-remediation verification confirms fixes and detects regressions
- Final tier2-report.json reflects the current state, not pre-remediation state
</success_criteria>
